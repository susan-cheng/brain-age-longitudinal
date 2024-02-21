import os
import pandas as pd
from generate_maps_by_image import generate_for_image

# variables
pred_file = 'output/prediction/finetuned/predictions.csv'
data_path = 'data/prediction/cropped/images'
out_path = 'output/interp/guided_backprop_maps'

# loop through predictions
df_pred = pd.read_csv(pred_file, index_col=0)
for id in df_pred.index:
    weights = os.path.join(df_pred.loc[id, 'src_path'], 'best_model.h5')
    generate_for_image(id, data_path, out_path, weights)
