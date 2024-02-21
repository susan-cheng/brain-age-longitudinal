import os
import math
import argparse
import numpy as np
import nibabel as nib
from scipy import ndimage
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator


# reshape slice to new_width and new_height
# requires new_height >= slice.shape[1] (old height)
def reshape_slice(slice, new_width, new_height):
    # resize to match new_width
    slice = ndimage.zoom(slice, new_width / slice.shape[0], order=0)

    # pad to match new_height
    pad_int = new_height - slice.shape[1]
    assert (pad_int >= 0)
    pad_width = ((0, 0), (math.floor(pad_int / 2), math.ceil(pad_int / 2)))
    slice = np.pad(slice, pad_width=pad_width)

    return (slice)


# show and save 2D slices
def display_map_slices(args):
    # load
    map_array = nib.load(args.map_file).get_fdata()
    template_array = nib.load(args.template_file).get_fdata()
    if not os.path.exists(args.out_path):
        os.makedirs(args.out_path)

    # loop through slices
    for slice in args.slices:
        if slice[0] == 'x':
            brain_slice = template_array[slice[1], :, :]
            map_slice = map_array[slice[1], :, :]
        elif slice[0] == 'z':
            brain_slice = template_array[:, :, slice[1]]
            map_slice = map_array[:, :, slice[1]]
        else:
            raise ValueError('Slice dimension not supported')
        map_slice = map_slice.astype(float)
        out_file = os.path.basename(args.map_file).split('.')[0] + \
            ('_%s%d.png') % (slice[0], slice[1])

        # threshold
        if args.percentile_thresholds:
            brain_mask = nib.load(args.brain_mask_file).get_fdata() > 0
            lower_thr = np.percentile(map_array[brain_mask],
                                      args.thresholds[0])
            upper_thr = np.percentile(map_array[brain_mask],
                                      args.thresholds[1])
        else:
            lower_thr = args.thresholds[0]
            upper_thr = args.thresholds[1]

        map_slice[map_slice < lower_thr] = np.nan
        map_slice[map_slice > upper_thr] = upper_thr

        # resize to match z slice shape
        if slice[0] == 'x':
            map_slice = reshape_slice(map_slice, map_slice.shape[1],
                                      map_slice.shape[0])
            brain_slice = reshape_slice(brain_slice, brain_slice.shape[1],
                                        brain_slice.shape[0])

        # plot
        plt.figure(figsize=(10, 15))
        plt.imshow(brain_slice.T, cmap='gray', origin='lower')
        im = plt.imshow(map_slice.T,
                        cmap=args.colormap,
                        origin='lower',
                        vmin=lower_thr,
                        vmax=upper_thr)
        plt.gca().invert_xaxis()
        plt.axis('off')

        # save
        plt.savefig(os.path.join(args.out_path, out_file), transparent=True)

        # colorbar
        if args.colorbar:
            plt.figure()
            locator = MaxNLocator(nbins=1)
            cbar = plt.colorbar(im,
                                location='left',
                                ticks=locator,
                                ax=plt.gca())
            cbar.ax.tick_params(labelsize=20)
            plt.axis('off')
            plt.savefig(os.path.join(args.out_path,
                                     out_file.split('.')[0] + '_colorbar.png'),
                        transparent=True,
                        bbox_inches='tight')


# pass in arguments
if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        ('Display thresholded map slices overlaid '
         'on a template (MNI152) brain'))

    parser.add_argument('-m',
                        '--map_file',
                        required=True,
                        help=('Path to map file'))
    parser.add_argument('-t',
                        '--template_file',
                        required=True,
                        help=('Path to template file'))
    parser.add_argument('-o',
                        '--out_path',
                        required=True,
                        help=('Path to store output images'))
    parser.add_argument('-c',
                        '--colorbar',
                        action='store_true',
                        help=('If set, save separate png of colorbar'))
    parser.add_argument('-l',
                        '--colormap',
                        required=False,
                        default='inferno',
                        help=('Colormap of overlaid map'))
    parser.add_argument('-r',
                        '--thresholds',
                        required=False,
                        default=[90, 99],
                        help=('Lower and upper thresholds '
                              'for map coloring'))
    parser.add_argument('-p',
                        '--percentile_thresholds',
                        action='store_true',
                        help=('If set, thresholds will be used as percentiles '
                              'of map values within the brain'))
    parser.add_argument('-b',
                        '--brain_mask_file',
                        required=False,
                        help=('Path to brain mask file for calculating '
                              'percentile thresholds'))
    parser.add_argument('-s',
                        '--slices',
                        required=False,
                        default=[('x', 97), ('z', 68), ('z', 89), ('z', 135)],
                        help=('Slice coordinates to display'))

    args = parser.parse_args()
    display_map_slices(args)
