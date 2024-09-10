# -*- coding: utf-8 -*-

# start with the general imports
import numpy as np
import seaborn as sns; sns.set()
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import VotingRegressor
from sklearn.ensemble import StackingRegressor
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from lightgbm import LGBMRegressor
from catboost import CatBoostRegressor
from sklearn.ensemble import AdaBoostRegressor
from sklearn.ensemble import GradientBoostingRegressor
from xgboost import XGBRegressor
import rasterio as rio


# Set random seed for reproducibility
np.random.seed(42)

# Load the data
path = '.../training_areas_30_11.csv'
S2_dataset = pd.read_csv(path, sep=';')


# Create features (X) by dropping the target column 'Depth'
X_S2 = S2_dataset.drop('Depth', axis=1) # use 4 bands
#X_S2 = S2_dataset.drop('B1', axis=1) # change the column name if you want to use 3 bands
X_S2 = np.array(X_S2)
print("Features shape: {}".format(X_S2.shape))

# Create target (y) as the 'Depth' column
y_S2 = S2_dataset['Depth']  
y_S2= np.array(y_S2)
print("Target shape: {}".format(y_S2.shape))

# Split the data into training and test sets
X_train, X_test, y_train, y_test = train_test_split(X_S2, y_S2, train_size=0.7, random_state=42)
print("X_train shape: {}".format(X_train.shape))
print("y_train shape: {}".format(y_train.shape))
print("X_test shape: {}".format(X_test.shape))
print("y_test shape: {}".format(y_test.shape)) 

# List all estimators in the ensemble
estimators = [('lgbm', LGBMRegressor(random_state=42)),
              ('catb', CatBoostRegressor(random_state=42)),
              ('adab', AdaBoostRegressor(random_state=42)),
              ('gbr', GradientBoostingRegressor(random_state=42))]

# Option 1
# Create and fit a VotingRegressor
voting_reg = VotingRegressor(estimators=estimators, n_jobs=-1, verbose=True)
final_reg = voting_reg.fit(X_train, y_train)

# Make predictions with the VotingRegressor
y_pred = final_reg.predict(X_test)
print('R2 score: {:.2f}'.format(r2_score(y_test, y_pred)))
print('Root mean square error (RMSE): {:.2f}'.format(np.sqrt(mean_squared_error(y_test, y_pred))))
print('Mean absolute error: {:.2f}'.format(mean_absolute_error(y_test, y_pred)))

# Option 2
# Create and fit a StackingRegressor
final_estimator = XGBRegressor(tree_method="hist")

reg = StackingRegressor(
    estimators=estimators,
    final_estimator=final_estimator,
    cv=5,
    n_jobs=-1)

stacking_reg = reg.fit(X_train, y_train)

# Make predictions with the StackingRegressor
y_pred_stack = stacking_reg.predict(X_test)
print('R2 score: {:.2f}'.format(r2_score(y_test, y_pred_stack)))
print('Root mean square error (RMSE): {:.2f}'.format(np.sqrt(mean_squared_error(y_test, y_pred_stack))))
print('Mean absolute error: {:.2f}'.format(mean_absolute_error(y_test, y_pred_stack)))


# Compare with DummyRegressor (R^2)
# Mean strategy
dummy_regr = DummyRegressor(strategy="mean")
dummy_regr.fit(X_train, y_train)
dummy_regr.predict(X_test)
print('R2 score dummy mean: {:.2f}'.format(dummy_regr.score(X_test, y_test)))

# Median strategy
dummy_regr = DummyRegressor(strategy="median")
dummy_regr.fit(X_train, y_train)
dummy_regr.predict(X_test)
print('R2 score dummy median: {:.2f}'.format(dummy_regr.score(X_test, y_test)))

# Quantile strategy (75th percentile)
dummy_regr = DummyRegressor(strategy="quantile", quantile=0.75)
dummy_regr.fit(X_train, y_train)
dummy_regr.predict(X_test)
print('R2 score dummy Q3: {:.2f}'.format(dummy_regr.score(X_test, y_test)))


# The next step is to use a gridsearchCV or RandomizedSearchCV to tune the models' parameters
'''In this example we opted to use the default parameters for each model.
However, users are advised to tune the model parameters for better performance.'''

## Predict the whole image
# Load the Sentinel-2 bands
image_folder = '.../S2/2021/5_best/'
b1 = rio.open(image_folder+'Rrs_443_11_30.tif') 
b2 = rio.open(image_folder+'Rrs_492_11_30.tif')
b3 = rio.open(image_folder+'Rrs_560_11_30.tif')
b4 = rio.open(image_folder+'Rrs_665_11_30.tif')

B1 = b1.read(1).astype('float32')
B2 = b2.read(1).astype('float32')
B3 = b3.read(1).astype('float32')
B4 = b4.read(1).astype('float32')


# Stack the bands into a single image
img = np.dstack([B1, B2, B3, B4])
print(img.shape)

# Reshape the image for prediction
reshaped_img = img.reshape(-1,4)
print(reshaped_img.shape)

# Predict the image
class_prediction = final_reg.predict(reshaped_img) #Make sure you select the stacking or voting ensemble

# Reshape the prediction back into a 2D matrix
class_prediction = class_prediction.reshape(img[:, :, 0].shape)
print(class_prediction.shape)

# Convert prediction to float
class_prediction = class_prediction.astype(float)

# Export the final image to a TIFF file
Imb_acc = rio.open('...\SDB_11_30.tiff','w', driver='Gtiff', width = b4.width, height = b4.height, 
                   count=1, crs = b4.crs,  transform = b4.transform, dtype='float64')
Imb_acc.write(class_prediction,1)
Imb_acc.close()

