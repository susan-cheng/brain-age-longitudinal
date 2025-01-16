# preliminary
import os
import argparse
import numpy as np
import pandas as pd
from sklearn.kernel_ridge import KernelRidge
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import GridSearchCV, RepeatedStratifiedKFold

# save results in csv
def save_results(args):
    if args.output_file is not None:
        # for each model
        lr_results = pd.DataFrame({'fold': args.folds, 'rep': args.reps, 
                                   'corr': args.lr_corrs})
        lr_results['model'] = 'LR'
        krr_results = pd.DataFrame({'fold': args.folds, 'rep': args.reps, 
                                    'corr': args.krr_corrs})
        krr_results['model'] = 'KRR'

        # combine and label
        results = pd.concat([lr_results, krr_results])
        features_str = 'demographics'
        if args.use_bl:
            features_str += ' + baseline BAG'
        if args.use_ch:
            features_str += ' + change in BAG'
        results['features'] = features_str
        results['study'] = args.name
        results['outcome'] = args.outcome
        results['ext'] = args.ext

        # save
        os.makedirs(os.path.dirname(args.output_file), exist_ok=True)
        results.to_csv(args.output_file, mode='a', 
                       header=not os.path.exists(args.output_file))

    return args

# calculate correlation between predictions and actual values
def corr(model, X, y):
    return np.corrcoef(model.predict(X), y)[1, 0]

# run repeated k-fold cross-validation
def run_cv(args):
    # setup
    args.folds = []
    args.reps = []
    args.lr_corrs = []
    args.krr_corrs = []
    args.rskf = RepeatedStratifiedKFold(n_splits=args.n_splits, 
                                        n_repeats=args.n_repeats, 
                                        random_state=args.random_state)
    y_bins = pd.qcut(args.y, q=8, labels=False, duplicates='drop')
    outer_split = args.rskf.split(args.X, y_bins)
    print(y_bins.value_counts())

    # loop through folds
    for i, (train_idx, test_idx) in enumerate(outer_split):
        X_train, X_test = args.X.iloc[train_idx], args.X.iloc[test_idx]
        y_train, y_test = args.y.iloc[train_idx], args.y.iloc[test_idx]
        args.folds.append(i % args.n_splits)
        args.reps.append(i // args.n_splits)

        # linear regression
        lr = LinearRegression()
        lr.fit(X_train, y_train)
        lr_corr = corr(lr, X_test, y_test)
        args.lr_corrs.append(lr_corr)

        # kernel ridge regression
        y_train_bins = y_bins.iloc[train_idx]
        inner_skf = RepeatedStratifiedKFold(n_splits=5, 
                                             n_repeats=1, 
                                             random_state=0)
        inner_split = inner_skf.split(X_train, y_train_bins)

        krr_cv = GridSearchCV(KernelRidge(kernel='cosine'), 
                              {'alpha': args.alphas}, 
                              scoring=corr, cv=inner_split)
        krr = krr_cv.fit(X_train, y_train).best_estimator_
        krr_corr = corr(krr, X_test, y_test)
        args.krr_corrs.append(krr_corr)

    return args

# load into input matrix X and outcome vector y
def load_data(args):
    # set default data file
    if args.data_file is None:
        if args.use_ch:
            args.xvar = 'ch_BAG_' + args.ext
        else:
            args.xvar = 'bl_BAG_' + args.ext
        args.data_file = os.path.join('..', '..', 'output', 'analysis', 
                                      'dataframes', '%s_%s_VS_%s.csv' 
                                      % (args.name, args.xvar, args.outcome))
    
    # set features
    args.features = args.covars
    if args.use_bl:
        args.features += ['bl_BAG_' + args.ext]
    if args.use_ch:
        args.features += ['ch_BAG_' + args.ext]

    # load
    args.df = pd.read_csv(args.data_file, index_col=0)
    args.X = args.df[args.features]
    args.y = args.df[args.outcome]

    return args

# main
def predict_cognition_from_brain_age(args):
    args = load_data(args)
    args = run_cv(args)
    args = save_results(args)

# pass in arguments
if __name__ == '__main__':
    parser = argparse.ArgumentParser(('Predict a cognitive measure from brain '
                                      'age and covariates using repeated '
                                      'k-fold cross-validation'))

    parser.add_argument('--name',
                        required=True,
                        help=('Study name (EDIS, SLABS, GUSTO)'))
    parser.add_argument('--ext',
                        required=True,
                        help='Extension for BAG (pretrained, finetuned)')
    parser.add_argument('--outcome',
                        required=True,
                        help='Cognitive measure/outcome to predict')
    parser.add_argument('--covars',
                        nargs='+',
                        default=['chron_age', 'sex'],
                        help='Covariates/demographics')
    parser.add_argument('--use_bl',
                        action='store_true',
                        help=('If set, use baseline BAG in prediction'))
    parser.add_argument('--use_ch',
                        action='store_true',
                        help=('If set, use change in BAG in prediction'))
    parser.add_argument('--data_file',
                        required=False,
                        default=None,
                        help=('Path to file containing data'))
    parser.add_argument('--output_file',
                        required=False,
                        default=None,
                        help=('Path to save cross validation results'))
    parser.add_argument('--n_splits',
                        required=False,
                        default=10,
                        type=int,
                        help=('Number of cross validation splits/folds'))
    parser.add_argument('--n_repeats',
                        required=False,
                        default=1,
                        type=int,
                        help=('Number of times to repeat cross validation'))
    parser.add_argument('--random_state',
                        required=False,
                        default=0,
                        type=int,
                        help=('Random seed for cross validation splits'))   
    parser.add_argument('--alphas',
                        nargs='+',
                        default=[0.00001, 0.0001, 0.001, 0.004, 0.007, 0.01, 
                                 0.04, 0.07, 0.1, 0.4, 0.7, 1, 1.5, 2, 2.5, 3, 
                                 3.5, 4, 5, 10, 15, 20],
                        help=('Regularization strengths to try for KRR'))

    args = parser.parse_args()

    predict_cognition_from_brain_age(args)