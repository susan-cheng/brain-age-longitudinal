import os
import argparse
import numpy as np
import pandas as pd
import nibabel as nib
import matplotlib.pyplot as plt
from nilearn.image import resample_to_img


# convenience function to return path of parcellation
def path(args, file):
    return (os.path.join(args.parcellations_path, file))


# plot feature contributions
def plot_feature_contributions(args):
    # sort and normalize
    contribution_ranks = np.argsort(args.all_contributions)[::-1]
    features = np.array(args.all_features)[contribution_ranks]
    tissue_types = (np.array(args.all_is_wm)[contribution_ranks]).astype(int)
    contributions = np.array(args.all_contributions)[contribution_ranks]
    contributions /= np.sum(contributions)

    # setup
    ticks = np.arange(len(contributions))
    color_map = {0: 'dimgray', 1: 'whitesmoke'}
    colors = [color_map[tissue_type] for tissue_type in tissue_types]

    # plot
    plt.figure(figsize=(10, 6))
    plt.bar(ticks,
            contributions,
            color=colors,
            edgecolor='black',
            linewidth=1.2)
    plt.ylabel('Relative Contribution', fontsize=20)
    plt.xticks(ticks, features, rotation=90, fontsize=14)
    plt.yticks(fontsize=14)

    # color and bold
    ventricle_labels = ['gCC', 'bCC', 'sCC', 'Fx', 'Fx/ST', 'TAP', 'Put+Cau']
    elderly_labels = ['Default', 'Cont', 'SomMot', 'SalVentAttn', 'UF']
    child_labels = ['Vis', 'SS', 'CST', 'PCT', 'SLF', 'PLIC']
    for label in plt.gca().get_xticklabels():
        label_text = label.get_text()
        if label_text in ventricle_labels:
            label.set_color('red')
        if label_text in elderly_labels:
            label.set_color('magenta')
        if label_text in child_labels:
            label.set_color('blue')

    # add legend
    legend_elements = [
        plt.Rectangle((0, 0), 1, 1, color=color_map[1], label='White Matter'),
        plt.Rectangle((0, 0), 1, 1, color=color_map[0], label='Gray Matter')
    ]
    legend = plt.legend(handles=legend_elements, fontsize=18)
    for rect in legend.legendHandles:
        rect.set_edgecolor('black')
        rect.set_linewidth(1.2)

    # save
    os.makedirs(args.out_path, exist_ok=True)
    out_file = os.path.join(args.out_path,
                            os.path.basename(args.map_file).split('.')[0])
    plt.savefig(out_file, bbox_inches='tight')


# calculate feature contributions for a given parcellation
# and return updated lists
def calculate_feature_contributions(features, parcels, labels, is_wm, args):
    for feature in features:
        # select feature labels
        feature_labels = pd.DataFrame()
        if isinstance(feature, str):
            feature_labels = labels[labels['label'] == feature]
        elif isinstance(feature, list):
            for region in feature:
                region_labels = labels[labels['label'].str.contains(region)]
                feature_labels = feature_labels.append(region_labels)

        # calculate averaged contribution
        feature_mask = np.isin(parcels, feature_labels['number'])
        contribution = np.nanmean(args.map_array[feature_mask])

        # update lists
        if isinstance(feature, str):
            args.all_features = args.all_features + [feature]
        elif isinstance(feature, list):
            if len(feature) > 1:
                feature = [region[:3] for region in feature]
            args.all_features = args.all_features + ['+'.join(feature)]
        args.all_is_wm = args.all_is_wm + [is_wm]
        args.all_contributions = args.all_contributions + [contribution]

    return (args)


# wrapper to calculate all feature contributions
def calculate_all_feature_contributions(args):
    # load
    args.map_img = nib.load(args.map_file)
    args.map_array = args.map_img.get_fdata()
    args.brain_mask = nib.load(args.brain_mask_file).get_fdata() > 0
    args.all_features = list()
    args.all_contributions = list()
    args.all_is_wm = list()

    # keep top x percent of features
    thr = np.percentile(args.map_array[args.brain_mask],
                        args.percentile_threshold)
    args.map_array[args.map_array < thr] = 0

    # cortical gray matter
    file = 'Schaefer2018_400Parcels_7Networks_order_FSLMNI152_1mm.nii.gz'
    parcels = nib.load(path(args, file)).get_fdata()
    file = 'Schaefer2018_400Parcels_7Networks_order.txt'
    labels = pd.read_table(path(args, file),
                           names=['number', 'label'],
                           usecols=[0, 1])
    labels['label'] = labels['label'].str.split('_').apply(lambda x: x[2])
    features = labels['label'].unique()
    is_wm = False
    args = calculate_feature_contributions(features, parcels, labels, is_wm,
                                           args)

    # subcortical gray matter
    file = 'AAL3v1_1mm.nii'
    parcels = resample_to_img(nib.load(path(args, file)),
                              args.map_img,
                              interpolation='nearest').get_fdata()
    file = 'AAL3v1_1mm.nii.txt'
    labels = pd.read_table(path(args, file),
                           sep=' ',
                           names=['number', 'label'],
                           usecols=[0, 1])
    features = [['Hippocampus', 'Amygdala'], ['Putamen', 'Caudate'], ['Thal']]
    is_wm = False
    args = calculate_feature_contributions(features, parcels, labels, is_wm,
                                           args)

    # white matter
    file = 'WM_48_ROIs_1mm.nii.gz'
    parcels = nib.load(path(args, file)).get_fdata()
    file = 'WM_labels.xlsx'
    labels = pd.read_excel(path(args, file), sheet_name='ROI_48', header=1)
    labels['number'] = labels.iloc[:, 0].str.split('_', expand=True)[0]
    labels['number'] = labels['number'].astype(int)
    labels['label'] = labels['Abbreviation']
    features = labels['label'].unique()
    is_wm = True
    args = calculate_feature_contributions(features, parcels, labels, is_wm,
                                           args)

    # plot
    plot_feature_contributions(args)


# pass in arguments
if __name__ == '__main__':
    parser = argparse.ArgumentParser(('Calculate and display feature '
                                      'contributions based on GM and WM '
                                      'parcellations'))

    parser.add_argument('-m',
                        '--map_file',
                        required=True,
                        help=('Path to map file'))
    parser.add_argument('-o',
                        '--out_path',
                        required=True,
                        help=('Path to store output images'))
    parser.add_argument('-p',
                        '--percentile_threshold',
                        required=False,
                        default=90,
                        help=('Percentile threshold for calculating feature '
                              'contributions, e.g. a threshold of 90 will '
                              'calculate based on the top 10 percent of '
                              'features within the brain'))
    parser.add_argument('-b',
                        '--brain_mask_file',
                        required=True,
                        help=('Path to brain mask file for calculating '
                              'percentile threshold'))
    parser.add_argument('-a',
                        '--parcellations_path',
                        required=True,
                        help=('Path to GM and WM parcellations. Assumes the '
                              'parcellations follow the same format as those '
                              'provided in the repository'))

    args = parser.parse_args()
    calculate_all_feature_contributions(args)
