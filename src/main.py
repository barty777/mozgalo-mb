import os
from datetime import datetime

import numpy as np
from keras import optimizers
from keras.callbacks import EarlyStopping, ModelCheckpoint, BaseLogger, TensorBoard
from keras.models import Model
from keras.utils import to_categorical
from keras.preprocessing.image import ImageDataGenerator, array_to_img, img_to_array, load_img
from sklearn.model_selection import train_test_split

import utils
from metrics import Metrics, top_3_acc
from model import XceptionModel

DATASET_ROOT_PATH = 'data/mozgalo_split'

def preprocess_image(img):
    return img
    #img_array = img_to_array(img)
    # TODO: Preprocessing
    #return array_to_img(img_array)

def get_callbacks(weights_file="models/weights.ep:{epoch:02d}-vloss:{val_loss:.4f}.hdf5",
                  save_epochs=1, patience=5, min_delta=0):
    """

    :param weights_file: string, path to save the model file.
    :param save_epochs: Interval (number of epochs) between checkpoints.
    :param patience: number of epochs with no improvement after which training will be stopped.
    :param min_delta: minimum change in the monitored quantity to qualify as an improvement,
     i.e. an absolute change of less than min_delta, will count as no improvement.
    :return: List of Keras callbacks
    """
    loggers = list()
    loggers.append(EarlyStopping(monitor='val_loss', min_delta=min_delta, patience=patience,
                                 verbose=1))

    loggers.append(ModelCheckpoint(weights_file, monitor='val_loss', verbose=1,
                                   save_best_only=True, save_weights_only=False,
                                   period=save_epochs))
    loggers.append(BaseLogger())

    # Validation data is not available when using flow_from_directory
    # loggers.append(Metrics())

    save_time = datetime.now().strftime('%d-%m-%Y_%H:%M:%S')
    loggers.append(TensorBoard(log_dir=os.path.join("logs", save_time)))

    return loggers

def main():
    # Paramaters
    num_classes = 25
    batch_size = 64
    num_channels = 3
    input_size = (299, 150) # h x w
    epochs = 50
    learning_rate = 0.001

    # Use 35% data for experiments due to speed issues
    sample = 0.35
    assert 0 < sample <= 1

    # Number of feed workers (should be equal to the number of virtual CPU threads)
    workers = 8

    # create the base pre-trained model
    # Keras will automatically download pre-trained weights if they are missing
    predictions, base_model = XceptionModel((*input_size, num_channels), num_classes)

    # this is the model we will train
    model = Model(inputs=base_model.input, outputs=predictions)

    # Create data generators
    train_datagen = ImageDataGenerator(preprocessing_function=preprocess_image,
                                        samplewise_center=True,
                                        samplewise_std_normalization=True,
                                        rotation_range=7,
                                        zoom_range=(0.8, 1.2),
                                        width_shift_range=0.1,
                                        height_shift_range=0.1)

    validation_datagen = ImageDataGenerator(preprocessing_function=preprocess_image,
                                            samplewise_center=True,
                                            samplewise_std_normalization=True)

    # this is a generator that will and indefinitely
    # generate batches of augmented image data
    # target_size: tuple of integers (height, width)
    train_flow = train_datagen.flow_from_directory(
            DATASET_ROOT_PATH + '/train',
            target_size=input_size,
            batch_size=batch_size,
            class_mode='categorical')

    validation_flow = validation_datagen.flow_from_directory(
        DATASET_ROOT_PATH + '/validation',
        target_size=input_size,
        batch_size=batch_size,
        class_mode='categorical')

    optimizer = optimizers.RMSprop(lr=learning_rate)
    model.compile(optimizer=optimizer,
                  loss='categorical_crossentropy',
                  metrics=['accuracy', top_3_acc])

    # train the model on the new data for a few epochs
    model.fit_generator(
            train_flow,
            workers=workers,
            max_queue_size=round(workers * 1.7), # tweak if needed
            use_multiprocessing=False,
            steps_per_epoch=round((sample * train_flow.sample_size)) // batch_size,
            epochs=epochs,
            callbacks=get_callbacks(),
            shuffle=True,
            validation_data=validation_flow,
            validation_steps=round((sample * validation_flow.sample_size)) // batch_size)

if __name__ == "__main__":
    # Set seeds for reproducible results
    utils.set_random_seeds()
    main()
