Satellite Derived Bathymetry (SDB) for shallow waters using nested boosting techniques 
==========================================================================================


This project implements an ensemble learning approach to predict bathymetry (Depth) based on Sentinel-2 input features, Bathymetry Map and Isobaths Contours.

The dataset (csv format) should include the following:

* Input features (bands)

* A target column Depth

The following ensemble models are used:

* Voting Regressor: Combines predictions from several different models by averaging.
* Stacking Regressor: Trains multiple models and uses another model to combine their outputs.

The base regressors include:

* LightGBM Regressor
* CatBoost Regressor
* XGBoost Regressor
* AdaBoost Regressor
* GradientBoosting Regressor
* Evaluation
Metrics for evaluation:

* R² Score: Measures the proportion of variance captured by the model.
* Mean Squared Error (MSE): Measures the average squared difference between predicted and actual values.
