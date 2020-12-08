import tensorflow as tf
from tensorflow import keras
import numpy as np
import pandas as pd
import model
from datetime import date
from contextlib import redirect_stdout
import os


def make_save_directory():
    """
    Creates directory to save losses and weights for each run
    returns - path to the directory
    """
    today = str(date.today())
    run_number = 0
    save_dir = '../../models/FCNN/Run_' + today + '_' + str(run_number) 
    
    while (os.path.exists(save_dir)):
        run_number += 1
        save_dir = '../../models/FCNN/Run_' + today + '_' + str(run_number) 

    print("SAVE DIR: " + save_dir)
    os.makedirs(save_dir)
    assert(os.path.isdir(save_dir))
    return save_dir


def print_network(save_dir, net):
    """
    Print network layers to text file in save directory
    save_dir - location to save file
    model - keras model 
    """
    fname = os.path.join(save_dir, 'modelsummary.txt')
    with open(fname, 'w') as f:
        with redirect_stdout(f):
            net.summary()


def load_data():
    """
    Loads and normalizes data
    returns - tf.data.Dataset objects in the following order 
    training parton data, training reco data, validation parton data,
    validation reco data
    """
    data = np.loadtxt('../../data/txt/matchttbarDataTot.txt', skiprows=2)
    partonPtMax = np.max(data[:, 0], axis=0)
    partonPtMin = np.min(data[:, 0], axis=0)
    partonMean = np.mean(data[:, 1:3], axis=0)
    partonStd = np.std(data[:, 1:3], axis=0)
    partonEMax = np.max(data[:, 3], axis=0)
    partonEMin = np.min(data[:, 3], axis=0)
    
    pfPtMax = np.max(data[:, 4], axis=0)
    pfPtMin = np.min(data[:, 4], axis=0)
    pfMean = np.mean(data[:, 5:7], axis=0)
    pfStd = np.std(data[:, 5:7], axis=0)
    pfEMax = np.max(data[:, 7], axis=0)
    pfEMin = np.min(data[:, 7], axis=0)

    data[:, 0] = (data[:, 0] - partonPtMin)/partonPtMax
    data[:, 1:3] = (data[:, 1:3] - partonMean)/partonStd
    data[:, 3] = (data[:, 3] - partonEMin)/partonEMax
    data[:, 4] = (data[:, 4] - pfPtMin)/pfPtMax
    data[:, 5:7] = (data[:, 5:7] - pfMean)/pfStd
    data[:, 7] = (data[:, 7] - pfEMin)/pfEMax
    index = int(0.8*len(data))
    print("Number of training examples: {}".format(index))
    print("Number of validation examples: {}".format(len(data) - index))
    train = data[:index, :]
    trainParton = train[:, :4]
    trainPf = train[:, 4:]
    validate = data[index:, :]
    validateParton = validate[:, :4]
    validatePf = validate[:, 4:]
    return trainParton, trainPf, validateParton, validatePf


def train(net, trainParton, trainPf, validateParton, validatePf, save_dir):
    """
    Trains network, saves losses as well as weights every 5 epochs
    net - keras model
    trainParton - parton 4-momenta for training
    trainPf - reco 4-momenta for training
    validateParton - parton 4-momenta for validation
    validatePf - reco 4-momenta for validation
    """
    checkpoint_path = os.path.join(save_dir, 'training/cp.cpkt')
    checkpoint_dir = os.path.dirname(checkpoint_path)

    cp_callback = tf.keras.callbacks.ModelCheckpoint(filepath=checkpoint_path,
            save_weights_only=True,
            verbose=1,
            save_best_only=True)

    net.compile(optimizer=keras.optimizers.Adam(learning_rate=1e-4),
           loss=keras.losses.MeanAbsoluteError(),
           metrics=[keras.metrics.MeanAbsoluteError()])

    history = net.fit(trainParton,
            trainPf,
            batch_size=64,
            epochs=1000,
            validation_data=(validateParton, validatePf),
            callbacks=[cp_callback])

    loss = pd.Series(history.history['loss'])
    val_loss = pd.Series(history.history['val_loss'])

    loss_df = pd.DataFrame({'Training Loss': loss, 'Validation Loss': val_loss})
    fname = os.path.join(save_dir, 'losses.csv')
    loss_df.to_csv(fname)


def main():
    save_dir = make_save_directory()
    net = model.make_model()
    print_network(save_dir, net)
    trainParton, trainPf, validateParton, validatePf = load_data()
    train(net, trainParton, trainPf, validateParton, validatePf, save_dir)

    
        
    
    
if __name__ == "__main__":
    main()

