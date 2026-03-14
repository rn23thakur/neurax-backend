```python
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, MinMaxScaler
import joblib
import os
import yaml

# --- Minimal ConfigManager for Demonstration ---
# In a real project, this would be imported from `src/config_manager.py`.
# For a self-contained answer that can be run directly, we include a simple mock here.
class ConfigManager:
    """
    A minimal ConfigManager class to simulate loading configuration from config.yaml.
    In a real project, this would typically be imported from `src.config_manager`.
    """
    def __init__(self, config_path="config/config.yaml"):
        self.config = self._load_config(config_path)

    def _load_config(self, config_path):
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"Config file not found at {config_path}. Using hardcoded default config for demonstration.")
            # Fallback to a hardcoded config for demonstration if file not found
            return {
                "data": {
                    "raw_data_path": "data/raw/data.csv",
                    "processed_data_path": "data/processed/processed_data.parquet",
                    "test_split_ratio": 0.2,
                    "random_seed": 42,
                    "imputer_path": "models/imputer.joblib",
                    "scaler_path": "models/scaler.joblib"
                }
            }

    def get(self, key: str):
        keys = key.split('.')
        val = self.config
        for k in keys:
            if isinstance(val, dict):
                val = val.get(k)
            else:
                return None # Key not found or path is not a dictionary
            if val is None:
                return None
        return val
# --- End of Minimal ConfigManager ---


class DataProcessor:
    """
    A class to encapsulate the data ingestion and preprocessing workflow.
    Provides methods for data loading, cleaning, imputation, transformation,
    and splitting, ensuring reproducibility by saving transformation parameters.
    """
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.imputer = None
        self.scaler = None

        # Retrieve paths for saving models from config
        self.imputer_path = self.config_manager.get('data.imputer_path')
        self.scaler_path = self.config_manager.get('data.scaler_path')

        # Ensure the directories for saving artifacts exist
        if self.imputer_path:
            os.makedirs(os.path.dirname(self.imputer_path), exist_ok=True)
        if self.scaler_path:
            os.makedirs(os.path.dirname(self.scaler_path), exist_ok=True)

    def load_data(self, file_path: str) -> pd.DataFrame:
        """
        Loads data from the given file_path. Supports CSV and JSON formats.

        Args:
            file_path (str): The path to the data file.

        Returns:
            pd.DataFrame: The loaded data.

        Raises:
            FileNotFoundError: If the specified file does not exist.
            ValueError: If the file format is not supported.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Error: Data file not found at '{file_path}'.")

        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_path.endswith('.json'):
            df = pd.read_json(file_path)
        else:
            raise ValueError(f"Unsupported file format for '{file_path}'. Only .csv and .json are supported.")
        print(f"Data loaded successfully from '{file_path}'. Shape: {df.shape}")
        return df

    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Removes duplicate rows from the DataFrame.

        Args:
            df (pd.DataFrame): The input DataFrame.

        Returns:
            pd.DataFrame: The DataFrame with duplicate rows removed.
        """
        initial_rows = len(df)
        cleaned_df = df.drop_duplicates().copy()
        rows_removed = initial_rows - len(cleaned_df)
        if rows_removed > 0:
            print(f"Cleaned data: Removed {rows_removed} duplicate rows.")
        else:
            print("No duplicate rows found.")
        return cleaned_df

    def impute_missing_values(self, df: pd.DataFrame, strategy: str = 'mean', columns: list = None) -> pd.DataFrame:
        """
        Handles missing values in specified columns using a given strategy.
        Saves the fitted imputer for reproducibility.

        Args:
            df (pd.DataFrame): The input DataFrame.
            strategy (str): The imputation strategy ('mean', 'median', 'most_frequent', 'constant').
                            For 'constant', consider a default or explicit fill_value in a real scenario.
            columns (list): A list of column names to impute. If None, all numerical columns are imputed.

        Returns:
            pd.DataFrame: The DataFrame with imputed values.

        Raises:
            ValueError: If specified columns are not found in the DataFrame.
        """
        df_copy = df.copy()

        if columns is None:
            # Select all numerical columns for imputation by default
            cols_to_impute = df_copy.select_dtypes(include=np.number).columns.tolist()
            if not cols_to_impute:
                print("No numerical columns found to impute. Skipping imputation.")
                return df_copy
        else:
            # Validate that specified columns exist
            missing_cols = [col for col in columns if col not in df_copy.columns]
            if missing_cols:
                raise ValueError(f"Columns not found in DataFrame for imputation: {missing_cols}")
            cols_to_impute = columns

        # Filter to only columns that actually have missing values within the selected set
        actual_cols_to_impute = [col for col in cols_to_impute if df_copy[col].isnull().any()]

        if not actual_cols_to_impute:
            print(f"No missing values found in selected columns: {cols_to_impute}. Skipping imputation.")
            return df_copy

        # Initialize imputer
        if strategy == 'constant':
            # For constant strategy, a fill_value is needed. Defaulting to 0 for numerical demo.
            # In a real application, you might pass `fill_value` as an argument.
            imputer = SimpleImputer(strategy=strategy, fill_value=0)
            print(f"Warning: 'constant' strategy used for imputation. Defaulting fill_value to 0 for numerical columns.")
        else:
            imputer = SimpleImputer(strategy=strategy)

        # Fit and transform the imputer on the target columns
        df_copy[actual_cols_to_impute] = imputer.fit_transform(df_copy[actual_cols_to_impute])
        self.imputer = imputer  # Store the fitted imputer

        if self.imputer_path:
            joblib.dump(self.imputer, self.imputer_path)
            print(f"Missing values imputed using '{strategy}' strategy for columns: {actual_cols_to_impute}. Imputer saved to '{self.imputer_path}'")
        else:
            print("Warning: Imputer path not configured. Imputer will not be saved.")
        return df_copy

    def transform_features(self, df: pd.DataFrame, features_to_transform: list, scaler_type: str = 'StandardScaler') -> pd.DataFrame:
        """
        Applies feature scaling (StandardScaler or MinMaxScaler) to the specified features.
        Saves the fitted scaler for reproducibility.

        Args:
            df (pd.DataFrame): The input DataFrame.
            features_to_transform (list): A list of column names to apply scaling to.
            scaler_type (str): The type of scaler to use ('StandardScaler' or 'MinMaxScaler').

        Returns:
            pd.DataFrame: The DataFrame with transformed features.

        Raises:
            ValueError: If specified features are not found or an unsupported scaler_type is provided.
        """
        df_copy = df.copy()

        # Validate that specified features exist
        missing_features = [col for col in features_to_transform if col not in df_copy.columns]
        if missing_features:
            raise ValueError(f"Features not found in DataFrame for transformation: {missing_features}")

        # Initialize scaler based on type
        if scaler_type == 'StandardScaler':
            scaler = StandardScaler()
        elif scaler_type == 'MinMaxScaler':
            scaler = MinMaxScaler()
        else:
            raise ValueError(f"Unsupported scaler_type: '{scaler_type}'. Choose 'StandardScaler' or 'MinMaxScaler'.")

        # Fit and transform the scaler on the specified features
        df_copy[features_to_transform] = scaler.fit_transform(df_copy[features_to_transform])
        self.scaler = scaler  # Store the fitted scaler

        if self.scaler_path:
            joblib.dump(self.scaler, self.scaler_path)
            print(f"Features {features_to_transform} transformed using {scaler_type}. Scaler saved to '{self.scaler_path}'")
        else:
            print("Warning: Scaler path not configured. Scaler will not be saved.")
        return df_copy

    def split_data(self, df: pd.DataFrame, target_column: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
        """
        Splits the DataFrame into training and testing sets for features (X) and target (y).
        Uses test_size and random_state from the configuration.

        Args:
            df (pd.DataFrame): The input DataFrame.
            target_column (str): The name of the target column.

        Returns:
            tuple: X_train, X_test, y_train, y_test DataFrames/Series.

        Raises:
            ValueError: If the target_column is not found in the DataFrame.
        """
        if target_column not in df.columns:
            raise ValueError(f"Target column '{target_column}' not found in the DataFrame.")

        X = df.drop(columns=[target_column])
        y = df[target_column]

        test_size = self.config_manager.get('data.test_split_ratio')
        random_state = self.config_manager.get('data.random_seed')

        # Use stratify for classification targets if the number of unique classes is small
        stratify_y = y if y.nunique() <= 10 and y.dtype in [np.int64, np.object_] else None

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=stratify_y
        )
        print(f"Data split into training and testing sets (test_size={test_size}, random_state={random_state}).")
        print(f"X_train shape: {X_train.shape}, y_train shape: {y_train.shape}")
        print(f"X_test shape: {X_test.shape}, y_test shape: {y_test.shape}")
        return X_train, X_test, y_train, y_test


if __name__ == "__main__":
    print("--- DataProcessor Demonstration ---")

    # Define a temporary config path for the demo to avoid conflicts with actual project config
    DEMO_CONFIG_PATH = "config/demo_config.yaml"
    # Ensure config directory exists
    os.makedirs(os.path.dirname(DEMO_CONFIG_PATH), exist_ok=True)

    # Create a dummy config.yaml content for the demonstration
    dummy_config_content = f"""
    data:
      raw_data_path: "data/raw/dummy_data.csv"
      processed_data_path: "data/processed/processed_data.parquet"
      test_split_ratio: 0.2
      random_seed: 42
      imputer_path: "models/imputer.joblib"
      scaler_path: "models/scaler.joblib"
    """
    with open(DEMO_CONFIG_PATH, 'w') as f:
        f.write(dummy_config_content)
    print(f"Created a temporary dummy config file at '{DEMO_CONFIG_PATH}' for demonstration.")

    # Instantiate ConfigManager (using our local mock for the demo)
    config_manager = ConfigManager(config_path=DEMO_CONFIG_PATH)

    # Instantiate DataProcessor
    data_processor = DataProcessor(config_manager)

    # Ensure necessary directories exist for the demo
    os.makedirs("data/raw", exist_ok=True)
    os.makedirs("models", exist_ok=True)

    # 1. Create a dummy dataset
    print("\n--- Creating Dummy Dataset ---")
    dummy_data = {
        'feature1': [10, 20, 30, np.nan, 50, 10, 60, 70, np.nan, 80],
        'feature2': [1.1, 2.2, np.nan, 4.4, 5.5, 1.1, 6.6, 7.7, 8.8, 9.9],
        'feature3': ['A', 'B', 'A', 'C', 'B', 'A', 'D', 'C', 'B', 'E'],
        'duplicate_feature': [5, 6, 7, 8, 9, 5, 7, 8, 9, 10], # To show duplicates in other columns
        'target': [0, 1, 0, 1, 0, 1, 0, 1, 0, 1]
    }
    df = pd.DataFrame(dummy_data)
    # Add a duplicate row
    df.loc[len(df)] = [10, 1.1, 'A', 5, 0] # A duplicate of the first row

    print("Original DataFrame (with a duplicate row and missing values):")
    print(df)
    print(f"\nOriginal shape: {df.shape}")
    print(f"Missing values before imputation:\n{df.isnull().sum()}")

    # Simulate saving to a file and loading to demonstrate `load_data` method
    dummy_csv_path = config_manager.get('data.raw_data_path')
    df.to_csv(dummy_csv_path, index=False)
    print(f"\nDummy data saved to '{dummy_csv_path}' for loading demonstration.")

    # --- Run all the data processing steps ---

    # Step 1: Load data
    loaded_df = data_processor.load_data(dummy_csv_path)

    # Step 2: Clean data (remove duplicates)
    cleaned_df = data_processor.clean_data(loaded_df)
    print("\nDataFrame after cleaning (duplicates removed):")
    print(cleaned_df)
    print(f"Shape after cleaning: {cleaned_df.shape}")

    # Step 3: Impute missing values
    imputed_df = data_processor.impute_missing_values(cleaned_df, strategy='mean', columns=['feature1', 'feature2'])
    print(f"\nMissing values after imputation:\n{imputed_df.isnull().sum()}")
    print("DataFrame after imputation (first 5 rows of imputed features):")
    print(imputed_df[['feature1', 'feature2']].head())

    # Step 4: Transform features
    transformed_df = data_processor.transform_features(imputed_df, features_to_transform=['feature1', 'feature2'], scaler_type='StandardScaler')
    print("\nDataFrame after transformation (first 5 rows of scaled features):")
    print(transformed_df[['feature1', 'feature2']].head())
    print(f"Mean of feature1 after scaling: {transformed_df['feature1'].mean():.2f}")
    print(f"Std of feature1 after scaling: {transformed_df['feature1'].std():.2f}")

    # Step 5: Split data
    X_train, X_test, y_train, y_test = data_processor.split_data(transformed_df, target_column='target')

    # 4. Print the shapes of the resulting datasets
    print("\n--- Final Dataset Shapes ---")
    print(f"X_train shape: {X_train.shape}")
    print(f"X_test shape: {X_test.shape}")
    print(f"y_train shape: {y_train.shape}")
    print(f"y_test shape: {y_test.shape}")

    # 5. Confirm transformation parameters are saved
    print("\n--- Reproducibility Check ---")
    imputer_saved_path = config_manager.get('data.imputer_path')
    scaler_saved_path = config_manager.get('data.scaler_path')

    if imputer_saved_path and os.path.exists(imputer_saved_path):
        print(f"Imputer object saved successfully to: '{imputer_saved_path}'")
        try:
            loaded_imputer = joblib.load(imputer_saved_path)
            print(f"   - Loaded imputer type: {type(loaded_imputer)}")
            # print(f"   - Loaded imputer statistics: {loaded_imputer.statistics_}") # Can print stats for verification
        except Exception as e:
            print(f"   - Error loading imputer for verification: {e}")
    else:
        print(f"ERROR: Imputer object NOT found at '{imputer_saved_path}' or path not configured.")

    if scaler_saved_path and os.path.exists(scaler_saved_path):
        print(f"Scaler object saved successfully to: '{scaler_saved_path}'")
        try:
            loaded_scaler = joblib.load(scaler_saved_path)
            print(f"   - Loaded scaler type: {type(loaded_scaler)}")
            # print(f"   - Loaded scaler mean: {loaded_scaler.mean_}") # Can print stats for verification
        except Exception as e:
            print(f"   - Error loading scaler for verification: {e}")
    else:
        print(f"ERROR: Scaler object NOT found at '{scaler_saved_path}' or path not configured.")

    print("\n--- End of DataProcessor Demonstration ---")

    # Clean up dummy files created for the demo
    print("\n--- Cleaning up temporary demo files ---")
    if os.path.exists(DEMO_CONFIG_PATH):
        os.remove(DEMO_CONFIG_PATH)
        print(f"Removed '{DEMO_CONFIG_PATH}'")
    if os.path.exists(dummy_csv_path):
        os.remove(dummy_csv_path)
        print(f"Removed '{dummy_csv_path}'")
    if imputer_saved_path and os.path.exists(imputer_saved_path):
        os.remove(imputer_saved_path)
        print(f"Removed '{imputer_saved_path}'")
    if scaler_saved_path and os.path.exists(scaler_saved_path):
        os.remove(scaler_saved_path)
        print(f"Removed '{scaler_saved_path}'")
    print("Cleanup complete.")

``````yaml
# config/config.yaml
# Application-wide configurations and ML hyperparameters

app:
  name: "ML Pipeline Service"
  version: "1.0.0"
  description: "API for serving machine learning models"

data:
  raw_data_path: "data/raw/data.csv"
  processed_data_path: "data/processed/processed_data.parquet"
  test_split_ratio: 0.2
  random_seed: 42
  # --- New additions for reproducibility ---
  imputer_path: "models/imputer.joblib"  # Path to save the fitted imputer object
  scaler_path: "models/scaler.joblib"    # Path to save the fitted scaler object

model:
  name: "RandomForestClassifier"
  type: "classification"
  hyperparameters:
    n_estimators: 100
    max_depth: 10
    min_samples_leaf: 5
  output_model_path: "models/trained_model.joblib"
  metrics: ["accuracy", "precision", "recall", "f1_score"]

api:
  host: "0.0.0.0"
  port: 8000
  reload: true
```

