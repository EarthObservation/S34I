Ensemble learning method for Co-Ni alteration mapping 
======================================================

This project implements an ensemble classification model using SVM, Random Forest, and Neural Networks (ANN) to classify PRISMA satellite imagery into two classes: alteration and host rock.

The final predictions are made using a soft voting classifier combining the three models' outputs.

Data

The dataset includes satellite imagery processed using dimensionality reduction techniques. It is structured as:

* Bands representing the reduced feature set (ICA or PCA from the satellite
* A target variable with class labels (0)alteration or (1)host rock

Predicting on New Data
The script supports prediction on new  images by loading the bands (same dimensionality reduction), normalizing them, and applying the trained voting classifier to generate classification results.

Model Details

The project employs the following classifiers:

* Support Vector Machine (SVM): A linear classifier that maximizes the margin between classes.
* Random Forest (RF): An ensemble classifier that aggregates predictions from multiple decision trees.
* Artificial Neural Networks (ANN): A neural network model that adapts its structure during training.
* The ensemble uses soft voting to combine the classifiers’ predictions.

Evaluation

The models are evaluated using the following metrics:

* Accuracy: The proportion of correct predictions.
* Precision: The proportion of positive predictions that are actually correct.
* Recall: The proportion of actual positives that are correctly identified.
* F1 Score: The harmonic mean of precision and recall.
* ROC AUC: Area Under the Receiver Operating Characteristic Curve.
* Confusion matrices are also displayed to analyze the classification performance for each model.
