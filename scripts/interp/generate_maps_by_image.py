import os
import keras
import argparse
import nibabel as nib
import tensorflow as tf
import matplotlib.pyplot as plt
from pyment.models import get as get_model

keras.utils.set_random_seed(0)


# modify gradient
@tf.custom_gradient
def guidedRelu(x):

    def grad(dy):
        return tf.cast(dy > 0, tf.float32) * tf.cast(x > 0, tf.float32) * dy

    return tf.nn.relu(x), grad


# show and optionally save 2D slices
def show_slices(img, filename=None, x=77, y=127, z=73):
    # setup
    slice_0 = img[x, :, :]
    slice_1 = img[:, y, :]
    slice_2 = img[:, :, z]
    slices = [slice_0, slice_1, slice_2]

    # plot
    fig, axes = plt.subplots(1, len(slices), figsize=(15, 5))
    fig.tight_layout(pad=3.0)
    for i, slice in enumerate(slices):
        subfig = axes[i].imshow(slice.T, cmap="gray", origin="lower")
        plt.colorbar(subfig, ax=axes[i], fraction=0.046, pad=0.04)

    # save
    if filename is not None:
        plt.savefig(filename)


# map for given model
def generate_for_model(model, img, affine, filename, save_slices):
    # change to guided relu
    layer_dict = [
        layer for layer in model.layers[1:] if hasattr(layer, 'activation')
    ]
    for layer in layer_dict:
        if layer.activation == keras.activations.relu:
            layer.activation = guidedRelu

    # calculate gradients
    input = tf.expand_dims(img, axis=0)
    with tf.GradientTape() as tape:
        tape.watch(input)
        result = model(input)
    grads = tape.gradient(result, input)
    grads = grads.numpy().squeeze()

    # save
    if save_slices:
        show_slices(grads, filename=filename)
    map = nib.Nifti1Image(grads, affine)
    nib.save(map, filename)


# maps for given image
def generate_for_image(id,
                       data_path,
                       out_path,
                       weights,
                       save_slices=False,
                       normalize=True,
                       dropout_rate=0.3,
                       weight_decay=1e-3):
    # load
    nii_orig = nib.load(os.path.join(data_path, id + '.nii.gz'))
    img = nii_orig.get_fdata()
    if normalize:
        img = img / 255
    affine = nii_orig.affine

    # show input image
    if save_slices:
        path = os.path.join(out_path, 'input')
        os.makedirs(path, exist_ok=True)
        filename = os.path.join(path, id)
        show_slices(img, filename=filename)

    # for pretrained model
    model = get_model('sfcn-reg', weights='brain-age')
    path = os.path.join(out_path, 'pretrained')
    os.makedirs(path, exist_ok=True)
    filename = os.path.join(path, id)
    generate_for_model(model, img, affine, filename, save_slices)

    # for finetuned model
    if weights is not None:
        model = get_model('sfcn-reg',
                          weights=None,
                          dropout=dropout_rate,
                          weight_decay=weight_decay,
                          prediction_range=None)
        model.load_weights(weights)
        path = os.path.join(out_path, 'finetuned')
        os.makedirs(path, exist_ok=True)
        filename = os.path.join(path, id)
        generate_for_model(model, img, affine, filename, save_slices)


# pass in arguments
if __name__ == '__main__':
    parser = argparse.ArgumentParser(('Generate guided backpropagation map(s) '
                                      'for one image'))

    parser.add_argument('-i', '--id', required=True, help=('Image id'))
    parser.add_argument('-d',
                        '--data_path',
                        required=True,
                        help=('Path to input image'))
    parser.add_argument('-o',
                        '--out_path',
                        required=True,
                        help=('Path to store output maps (and slices if set)'))
    parser.add_argument('-w',
                        '--weights',
                        required=False,
                        default=None,
                        help=('Path to weights of finetuned model. If not '
                              'set, only pretrained map will be generated'))
    parser.add_argument('-s',
                        '--save_slices',
                        action='store_true',
                        help=('If set, slices of the input image and '
                              'generated maps will be saved for easy viewing'))
    parser.add_argument('-n',
                        '--normalize',
                        action='store_true',
                        help=('If set, images will be normalized to range '
                              '(0, 1) before map generation'))
    parser.add_argument('-r',
                        '--dropout_rate',
                        required=False,
                        default=0.3,
                        type=float,
                        help=('Probability of dropout for dropout layers'))
    parser.add_argument('-g',
                        '--weight_decay',
                        required=False,
                        default=1e-3,
                        type=float,
                        help=('Weight decay hyperparameter'))

    args = parser.parse_args()
    generate_for_image(args.id, args.data_path, args.out_path, args.weights,
                       args.save_slices, args.normalize, args.dropout_rate,
                       args.weight_decay)
