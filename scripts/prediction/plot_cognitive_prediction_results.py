# preliminary
import os
import argparse
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.stats import t
import matplotlib.pyplot as plt
from statannotations.Annotator import Annotator
from statannotations.stats.StatTest import StatTest

sns.set(style="whitegrid")

# t test definition
def ttest_corrected_resampled(a, b, portion, threshold=0):
    assert(len(a) > 1)
    assert(len(a) == len(b))

    accuracy_vec = b - a
    K = len(accuracy_vec)
    corrected_variance = (1/K + portion) * np.var(accuracy_vec)
    mu = np.mean(accuracy_vec)
    
    tval = (mu - threshold) / np.sqrt(corrected_variance)
    p = 2 * t.cdf(-abs(tval), df=K-1)
    return tval, p

# convert variable name to plotting name
def var2name(pred):
    pred_map = {
        "future_ch_global_cog": "Global Cognition",
        "future_ch_ef": "Executive Function",
        "future_ch_vm": "Verbal Memory",
        "future_ch_vsm": "Visual Memory",
        "future_ch_attn": "Attention",
        "future_ch_proc_speed": "Processing Speed",

        "nepsy_naming": "Naming",
        "nepsy_inhibition": "Inhibition",
        "nepsy_switching": "Switching",
        "wcst_tess": "WCST"
    }
    
    return pred_map.get(pred)
                 
# boxplot wrapper
def boxplot(args):
    # variables
    data = args.df
    x = 'outcome'
    y = 'corr'
    hue = 'features'
    hue_order = ['demographics', 'demographics + baseline BAG', 
                 'demographics + baseline BAG + change in BAG']

    # plot
    plt.figure(figsize=(10, 8))
    order = np.sort(data[x].unique())
    ax = sns.boxplot(data=data, x=x, y=y, order=order, hue=hue, 
                     hue_order=hue_order)
    
    # statistical comparisons
    pairs = []
    for x_i in order:
        for i in range(len(hue_order) - 1):
            pairs.append(((x_i, hue_order[i]), (x_i, hue_order[i + 1])))
        if len(hue_order) > 2:
            pairs.append(((x_i, hue_order[0]), (x_i, hue_order[2])))
    annotator = Annotator(ax, pairs, data=data, x=x, y=y, order=order, hue=hue, 
                          hue_order=hue_order)
    test = StatTest(func=ttest_corrected_resampled,
                    test_long_name='t-test_corrected_resampled',
                    test_short_name='t-test_corr',
                    portion=1/data['fold'].max())
    annotator.configure(test=test, comparisons_correction=args.correction, 
                        text_format='star', loc='inside')
    annotator.apply_and_annotate()

    # styling
    locs, labels = plt.xticks()
    for label in labels:
        if label.get_text() in ['future_ch_ef', 'nepsy_inhibition']:
            label.set_fontweight('bold')
        label.set_text(var2name(label.get_text()))
    plt.xlabel(args.xlabel, fontsize='large')
    plt.xticks(locs, labels, fontsize='large', rotation=90)
    plt.ylabel('Correlation', fontsize='large')
    plt.yticks(fontsize='large')
    plt.ylim(-1, 1)
    plt.legend(loc='lower right')
    plt.tight_layout()

    # save
    if args.output_file is not None:
        os.makedirs(os.path.dirname(args.output_file), exist_ok=True)
        plt.savefig(args.output_file)

# load data from all CV files into one dataframe
def load_data(args):
    args.df = pd.DataFrame()
    for file in args.cv_result_files:
        df_temp = pd.read_csv(file, index_col=0)
        df_temp = df_temp[(df_temp['rep'] <= args.n_repeats) & \
                          (df_temp['ext'] == args.ext) & \
                          (df_temp['model'] == args.model)]
        args.df = pd.concat([args.df, df_temp])

    return args

# main
def plot_cognitive_prediction_results(args):
    args = load_data(args)
    args = boxplot(args)

# pass in arguments
if __name__ == '__main__':
    parser = argparse.ArgumentParser(('Plot results of predicting cognition '
                                      'from brain age (and demographics)'))
    
    parser.add_argument('--ext',
                        required=True,
                        help='Extension for BAG (pretrained, finetuned)')
    parser.add_argument('--cv_result_files',
                        required=True,
                        nargs='+',
                        help=('Paths to files containing CV results'))
    parser.add_argument('--output_file',
                        required=False,
                        default=None,
                        help=('Path to save plot'))
    parser.add_argument('--xlabel',
                        required=False,
                        default='',
                        type=str,
                        help=('x label for plot'))  
    parser.add_argument('--n_repeats',
                        required=False,
                        default=1,
                        type=int,
                        help=('Number of CV repeats to plot'))
    parser.add_argument('--correction',
                        required=False,
                        default='BH',
                        type=str,
                        help=('Method for multiple comparison correction '
                              '(used by statannotations)'))   
    parser.add_argument('--model',
                        required=False,
                        default='KRR',
                        type=str,
                        help=('Prediction model used'))   

    args = parser.parse_args()

    plot_cognitive_prediction_results(args)