import os
import argparse
import pandas as pd


# get predictions from optimal hyperparameters
def search_hyperparameters(args):
    all_pred = pd.DataFrame()

    # iterate over inner folders, e.g. folds
    for fol in args.inner_folders:
        ref_min_metric = float('inf')
        ref_pred = pd.DataFrame()

        # search config folders for best metric
        for config_path in args.config_paths:
            path = os.path.join(config_path, fol)
            log = pd.read_csv(os.path.join(path, 'log.csv'))
            min_metric = log[args.metric].min()
            if min_metric < ref_min_metric:
                ref_min_metric = min_metric
                ref_pred = pd.read_csv(os.path.join(path, args.file_name),
                                       index_col=0)
                ref_pred['src_path'] = path
        all_pred = all_pred.append(ref_pred)

    # save
    if args.destination is not None:
        destination_dir = os.path.dirname(args.destination)
        if not os.path.exists(destination_dir):
            os.makedirs(destination_dir)
        all_pred.to_csv(args.destination)


# pass in arguments
if __name__ == '__main__':
    parser = argparse.ArgumentParser(('Extracts predictions from optimal '
                                      'hyperparameters'))

    parser.add_argument('-p',
                        '--config_paths',
                        nargs='+',
                        default=[],
                        help='Paths config folders to search through')
    parser.add_argument('-i',
                        '--inner_folders',
                        nargs='+',
                        default=[],
                        help='Inner folders to search through, e.g. fold_0')
    parser.add_argument('-d',
                        '--destination',
                        type=str,
                        default=None,
                        help='Path to save final predictions to')
    parser.add_argument('-m',
                        '--metric',
                        type=str,
                        default='val_mae',
                        help='Metric to use for comparison among configs')
    parser.add_argument('-f',
                        '--file_name',
                        type=str,
                        default='test_pred.csv',
                        help='Name of file containing predictions per config')

    args = parser.parse_args()
    search_hyperparameters(args)
