import pandas as pd
import joblib
import os

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import(
    accuracy_score,
    classification_report,
    confusion_matrix
)

from preprocessing.preprocess import load_data, clean_data, prepare_features

# ============================
# File Paths
# ============================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

DATA_PATH = os.path.join(
    BASE_DIR,
    "data",
    "career_dataset.csv"
)

MODEL_PATH = os.path.join(
    BASE_DIR,
    "models",
    "career_model.pkl"
)


# ============================
# Load Dataset
# ============================

df = pd.read_csv(DATA_PATH)

print("Dataset Loaded Successfully!")
print("Dataset Shape : ", df.shape)

# ============================
# Separate features and target
# ============================

x = df.drop("career", axis=1)

y = df["career"]

print("\n Features : ")
print(x.columns.tolist())

print("\n Target : ")
print(y.name)


# ============================
# Split The Data Set
# ============================

x_train, x_test, y_train, y_test = train_test_split(
    x,
    y,
    test_size=0.5,
    random_state=42,
    stratify=y
)

print("\n Training Data : ", x_train.shape)
print("Testing Data : ", x_test.shape)


# ============================
# Create Random forest Model
# ============================

model = RandomForestClassifier(
    n_estimators=200,
    random_state=42
)

# ============================
# Train The Model
# ============================

print("\n Training Model..... ")

model.fit(x_train, y_train)

print("Model training Completed!")

# ============================
# Make Predictions
# ============================

y_pred = model.predict(x_test)

# ============================
# Calculate Accuracy
# ============================

accuracy = accuracy_score(
    y_test,
    y_pred
)

print("\n Model Accuracy : ")
print(f"{accuracy:.2%}")


# ============================
# Clissification Report
# ============================

print("\n Classification Report : ")

print(
    classification_report(
        y_test,
        y_pred,
        zero_division=0
    )
)

# ============================
# confusion Matrixs
# ============================

print("\n Confusion Matrix : ")

print(
    confusion_matrix(
        y_test,
        y_pred
    )
)

# ============================
# Save The Trained Data
# ============================

joblib.dump(
    model,
    MODEL_PATH
)

print("\n Model Saved Successfully!")

print(
    "saved to : ",
    MODEL_PATH
)