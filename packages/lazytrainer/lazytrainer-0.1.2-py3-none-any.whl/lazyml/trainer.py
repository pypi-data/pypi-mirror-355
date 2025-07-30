import pandas as pd
import numpy as np
import joblib
import matplotlib.pyplot as plt
from sklearn.linear_model import SGDRegressor
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from tqdm import tqdm
import csv


class LazyTrainer:
    def __init__(
        self,
        data_path,
        target_col,
        features=None,
        categorical_cols=None,
        model_type="sgd",
        scaling="standard",
        test_size=0.2
    ):
        self.data_path = data_path
        self.target_col = target_col
        self.features = features
        self.categorical_cols = categorical_cols
        self.model_type = model_type
        self.scaling = scaling
        self.test_size = test_size
        self.encoders = {}
        self.scaler = StandardScaler()
        self.model = None
        self.X_train = self.X_test = self.y_train = self.y_test = None

    def _load_data(self):
        try:
            with open(self.data_path, 'r') as f:
                sample = f.read(1024)
                f.seek(0)
                dialect = csv.Sniffer().sniff(sample)
                df = pd.read_csv(f, dialect=dialect)
        except Exception:
            df = pd.read_csv(self.data_path)  # fallback to comma-delimited
        return df


    def preprocess(self):
        df = self._load_data()

        if not self.features:
            self.features = [col for col in df.columns if col != self.target_col]

        if not self.categorical_cols:
            self.categorical_cols = [col for col in self.features if df[col].dtype == "object"]

        for col in self.categorical_cols:
            if col in df.columns:
                enc = LabelEncoder()
                df[col] = enc.fit_transform(df[col])
                self.encoders[col] = enc
            else:
                print(f"Warning: Column '{col}' not found. Skipping.")

        X = df[self.features]
        y = df[self.target_col]

        if self.scaling == "standard":
            X = self.scaler.fit_transform(X)
        else:
            X = X.values

        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            X, y, test_size=self.test_size, random_state=42
        )

    def train(self):
        print("Starting training...")
        self.preprocess()

        if self.model_type == "sgd":
            self.model = SGDRegressor(max_iter=5000, learning_rate='adaptive', eta0=0.01, random_state=42)
        else:
            raise ValueError("Only 'sgd' model is currently supported.")

        for _ in tqdm(range(1), desc="Training"):
            self.model.fit(self.X_train, self.y_train)

    def evaluate(self):
        y_pred = self.model.predict(self.X_test)
        mae = mean_absolute_error(self.y_test, y_pred)
        r2 = r2_score(self.y_test, y_pred)
        mean_val = np.mean(self.y_test)

        accuracy = max(0, 100 - (mae / mean_val * 100)) if mean_val > 0 else 0

        print("Model Accuracy:", round(accuracy, 2), "%")
        print("R² Score:", round(r2, 4))

        return {"accuracy": accuracy, "r2_score": r2, "mae": mae}

    def plot_summary(self, save_path="prediction_plot.png"):
        y_pred = self.model.predict(self.X_test)
        plt.figure(figsize=(8, 5))
        plt.scatter(self.y_test, y_pred, color='blue', alpha=0.5)
        plt.xlabel("Actual")
        plt.ylabel("Predicted")
        plt.title("Prediction Summary")
        plt.grid(True)
        plt.savefig(save_path)
        plt.close()

    def save(self, model_path="lazy_model.pkl"):
        joblib.dump(self.model, model_path)

    def save_scaler(self, scaler_path="lazy_scaler.pkl"):
        joblib.dump(self.scaler, scaler_path)

    def save_encoders(self, path_prefix="encoder_"):
        for col, enc in self.encoders.items():
            joblib.dump(enc, f"{path_prefix}{col}.pkl")
