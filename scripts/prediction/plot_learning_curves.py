import argparse
import pandas as pd
import matplotlib.pyplot as plt

# plot learning curves from finetuning
def plot_learning_curves(args):
    log = pd.read_csv(args.log_path)
    train_mae = log['mae'].to_list()
    val_mae = log['val_mae'].to_list()

    plt.figure()
    plt.plot(train_mae)
    plt.plot(val_mae)
    plt.xlabel('Epoch')
    plt.ylabel('MAE')
    plt.legend(['Training MAE', 'Validation MAE'])

    if args.destination is not None:
        plt.savefig(args.destination)

# pass in arguments
if __name__ == '__main__':
    parser = argparse.ArgumentParser(('Plot training and validation learning '
                                      'curves from finetuning'))
    
    parser.add_argument('-l',
                        '--log_path',
                        type=str,
                        required=True,
                        help='Path to logged metrics from training')
    parser.add_argument('-d',
                        '--destination',
                        type=str,
                        default=None,
                        help='Path to save figure to')

    args = parser.parse_args()
    plot_learning_curves(args)
