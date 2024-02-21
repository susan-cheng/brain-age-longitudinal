import os
import argparse
import pandas as pd

from pyment.models import get as get_model, ModelType
from pyment.data import AsyncNiftiGenerator, NiftiDataset

import keras
from keras.callbacks import CSVLogger
from keras.callbacks import ModelCheckpoint
from tensorflow.keras.optimizers.schedules import CosineDecay


# load train, validation, and test datasets
def load_datasets(args):
    args.labels_path = os.path.join('labels', args.split)
    args.train_labels = os.path.join(args.labels_path,
                                     args.fold + '_train.csv')
    args.val_labels = os.path.join(args.labels_path, args.fold + '_val.csv')
    args.test_labels = os.path.join(args.labels_path, args.fold + '_test.csv')
    args.train_dataset = NiftiDataset.from_folder(args.folder,
                                                  show_missing_warnings=False,
                                                  labels=args.train_labels,
                                                  target='age')
    args.val_dataset = NiftiDataset.from_folder(args.folder,
                                                show_missing_warnings=False,
                                                labels=args.val_labels,
                                                target='age')
    args.test_dataset = NiftiDataset.from_folder(args.folder,
                                                 show_missing_warnings=False,
                                                 labels=args.test_labels,
                                                 target='age')
    return args


# load generators from datasets
def load_generators(args):
    preprocessor = lambda x: x / 255. if args.normalize else x

    if args.threads is None or args.threads == 1:
        raise NotImplementedError(('Predicting from synchronous generator '
                                   'is not implemented'))

    args.train_gen = AsyncNiftiGenerator(args.train_dataset,
                                         preprocessor=preprocessor,
                                         batch_size=args.batch_size,
                                         threads=args.threads,
                                         infinite=True,
                                         shuffle=True)
    args.val_gen = AsyncNiftiGenerator(args.val_dataset,
                                       preprocessor=preprocessor,
                                       batch_size=args.batch_size,
                                       threads=args.threads,
                                       infinite=True,
                                       shuffle=True)
    args.test_gen = AsyncNiftiGenerator(args.test_dataset,
                                        preprocessor=preprocessor,
                                        batch_size=args.batch_size,
                                        threads=args.threads)
    return args


# set steps by reducing if only doing a quick test
def set_steps(args):
    if args.quick_test:
        args.steps_tr = 2
        args.steps_val = 2
        args.steps_te = None
    else:
        args.steps_tr = args.train_gen.batches
        args.steps_val = args.val_gen.batches
        args.steps_te = None
    return args


# callbacks
def set_callbacks(args):
    args.monitor = 'val_mae'
    args.cb = None

    if args.log_path is not None:
        args.cb = []
        os.makedirs(args.log_path, exist_ok=True)

        # stream epoch results
        args.csv_filename = os.path.join(args.log_path, 'log.csv')
        args.cb.append(CSVLogger(args.csv_filename))

        # save best model
        args.bw_filepath = os.path.join(args.log_path, 'best_model.h5')
        args.cb.append(
            ModelCheckpoint(filepath=args.bw_filepath,
                            monitor=args.monitor,
                            verbose=1,
                            save_best_only=True,
                            mode='min'))

        # save models after every epoch
        if not args.save_best_only:
            args.cp_filepath = os.path.join(args.log_path, 'epochs',
                                            '{epoch:04d}.h5')
            args.cb.append(
                ModelCheckpoint(filepath=args.cp_filepath, verbose=1))
    return args


# set model with hyperparameters
def set_model(args):
    # load
    args.model = get_model(args.model_name,
                           weights=args.weights,
                           dropout=args.dropout_rate,
                           weight_decay=args.weight_decay,
                           prediction_range=None)

    # layers to train
    if args.last_layer_only:
        for layer in args.model.layers:
            if layer.name == 'Regression3DSFCN/predictions':
                layer.trainable = True
            else:
                layer.trainable = False
    else:
        args.model.trainable = True

    # learning rate decay
    args.decay_steps = args.train_gen.batches * args.lr_decay_epochs
    args.lr = CosineDecay(initial_learning_rate=args.initial_learning_rate,
                          decay_steps=args.decay_steps)
    args.model.compile(optimizer=keras.optimizers.Adam(learning_rate=args.lr),
                       loss=keras.losses.MeanSquaredError(),
                       metrics=['mae', 'mse'])
    args.model.summary()

    return args


# configure training parameters, callbacks, etc.
def config_training(args):
    args = set_steps(args)
    args = set_callbacks(args)
    args = set_model(args)
    return args


# run training
def run_training(args):
    args.history = args.model.fit(args.train_gen,
                                  epochs=args.max_epochs,
                                  verbose=2,
                                  steps_per_epoch=args.steps_tr,
                                  validation_data=args.val_gen,
                                  validation_steps=args.steps_val,
                                  callbacks=args.cb)
    return args


# generate predictions on test set
def predict_brain_age(args):
    args.ids = args.test_gen.dataset.ids
    args.labels = args.test_gen.dataset.y

    if args.log_path is not None:
        args.model.load_weights(args.bw_filepath)

    args.predictions = args.model.predict(args.test_gen, steps=args.steps_te)
    if args.model.type == ModelType.REGRESSION:
        args.predictions = args.predictions.squeeze()

    # save
    args.df = pd.DataFrame({
        'age': args.labels,
        'prediction': args.predictions
    },
                           index=args.ids)
    destination_dir = os.path.dirname(args.destination)
    if not os.path.exists(destination_dir):
        os.makedirs(destination_dir)
    args.df.to_csv(args.destination)

    return args


# wrapper function
def finetune_and_predict_brain_age(args):
    keras.utils.set_random_seed(0)
    args = load_datasets(args)
    args = load_generators(args)

    args = config_training(args)
    args = run_training(args)
    args = predict_brain_age(args)


# pass in arguments
if __name__ == '__main__':
    parser = argparse.ArgumentParser(('Performs finetuning'))

    parser.add_argument('-f',
                        '--folder',
                        required=True,
                        help=('Folder containing images'))
    parser.add_argument('-m',
                        '--model_name',
                        required=True,
                        help='Name of the model to use (e.g. sfcn-reg)')
    parser.add_argument('-w',
                        '--weights',
                        required=False,
                        default=None,
                        help='Weights to load in the model')
    parser.add_argument('-b',
                        '--batch_size',
                        required=True,
                        type=int,
                        help='Batch size to use while training and predicting')
    parser.add_argument('-t',
                        '--threads',
                        required=False,
                        default=None,
                        type=int,
                        help=('Number of threads to use for reading '
                              'data. If not set, a synchronous '
                              'generator will be used'))
    parser.add_argument('-n',
                        '--normalize',
                        action='store_true',
                        help=('If set, images will be normalized to range '
                              '(0, 1) before prediction'))
    parser.add_argument('-d',
                        '--destination',
                        required=True,
                        help=('Path where CSV containing ids, labels '
                              'and predictions are stored'))

    parser.add_argument('-s',
                        '--split',
                        required=True,
                        help=('Indicator of train/test split '
                              '(e.g. 10-fold)'))
    parser.add_argument('-o',
                        '--fold',
                        required=True,
                        help=('Indicator of train/test fold (e.g. 0)'))
    parser.add_argument('-e',
                        '--max_epochs',
                        required=False,
                        default=35,
                        type=int,
                        help=('Maximum number of epochs for '
                              'finetuning'))
    parser.add_argument('-a',
                        '--last_layer_only',
                        action='store_true',
                        help=('If set, only finetune the last layer'))
    parser.add_argument('-r',
                        '--dropout_rate',
                        required=False,
                        default=0.3,
                        type=float,
                        help=('Probability of dropout for dropout '
                              'layers'))
    parser.add_argument('-g',
                        '--weight_decay',
                        required=False,
                        default=1e-3,
                        type=float,
                        help=('Weight decay hyperparameter'))
    parser.add_argument('-i',
                        '--initial_learning_rate',
                        required=False,
                        default=1e-3,
                        type=float,
                        help=('Initial learning rate '
                              'hyperparameter'))
    parser.add_argument('-l',
                        '--lr_decay_epochs',
                        required=False,
                        default=25,
                        type=int,
                        help=('Number of epochs for '
                              'cosine learning rate '
                              'decay'))
    parser.add_argument('-c',
                        '--log_path',
                        required=False,
                        default=None,
                        help=('Path to directory where intermediate results '
                              'are saved. If None, these are not saved, and '
                              'best weights would not be restored.'))
    parser.add_argument('-v',
                        '--save_best_only',
                        action='store_true',
                        help=('If set, only the best weights are saved. If '
                              'not set, weights are saved every epoch'))
    parser.add_argument('-q',
                        '--quick_test',
                        action='store_true',
                        help=('If set, only 2 steps per epoch are used for '
                              'training to enable a quick test.'))

    args = parser.parse_args()

    finetune_and_predict_brain_age(args)
