import pandas as pd
import pickle
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report

# Load your dataset
data = pd.read_csv("../data/Training Data.csv")

# Clean up: Remove unused columns
X = data.drop(["Id", "Risk_Flag"], axis=1)
y = data["Risk_Flag"]

# Consistency: Ensure correct column names
X.rename(columns={
    "Married/Single": "marital_status",
    "CURRENT_JOB_YRS": "job_years",
    "CURRENT_HOUSE_YRS": "house_years"
}, inplace=True)

# Label encoding
label_encoders = {}
for col in X.select_dtypes(include="object").columns:
    le = LabelEncoder()
    le.fit(X[col])
    X[col] = le.transform(X[col])
    label_encoders[col] = le

# Train/test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Model training
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Evaluation
y_pred = model.predict(X_test)
print("Classification Report:\n", classification_report(y_test, y_pred))

# Save model
output_dir = os.path.dirname(__file__)
with open(os.path.join(output_dir, "loan_model.pkl"), "wb") as f:
    pickle.dump(model, f)
with open(os.path.join(output_dir, "label_encoders.pkl"), "wb") as f:
    pickle.dump(label_encoders, f)

print("Model & encoders saved.")
