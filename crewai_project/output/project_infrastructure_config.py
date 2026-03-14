```bash
# Create the main project directory
mkdir ml_pipeline_project
cd ml_pipeline_project

# Set up a Python virtual environment
python3 -m venv .venv
source .venv/bin/activate # On Windows, use: .venv\Scripts\activate

# Create the required directory structure
mkdir src
mkdir config
mkdir data
mkdir models

echo "Project directory structure and virtual environment created successfully."
``````toml
# pyproject.toml
[project]
name = "ml_pipeline_project"
version = "0.1.0"
description = "A foundational infrastructure for an ML pipeline."
authors = [
    { name = "HARSH RAJ", email = "harsh.raj@example.com" },
]
license = { text = "MIT" } # Or choose an appropriate license
readme = "README.md"
requires-python = ">=3.9" # Specify your target Python version
keywords = ["machine-learning", "pipeline", "configuration", "fastapi"]

# Core dependencies for the ML pipeline and API
dependencies = [
    "torch", # Or "tensorflow" if you prefer TensorFlow
    "pandas",
    "scikit-learn",
    "fastapi",
    "uvicorn[standard]", # ASGI server for FastAPI
    "python-dotenv",     # For environment variables
    "PyYAML",            # For YAML configuration files
]

[project.urls]
Homepage = "https://github.com/yourusername/ml_pipeline_project"
Issues = "https://github.com/yourusername/ml_pipeline_project/issues"

[build-system]
requires = ["setuptools>=61.0"] # Standard build backend for most Python projects
build-backend = "setuptools.build_meta"

# Optional: Configuration for testing or linting tools (example using pytest)
[tool.pytest.ini_options]
min_version = "6.0"
addopts = "--strict-markers --cov=src"
testpaths = ["tests"]

[tool.setuptools.packages.find]
where = ["src"] # Tell setuptools to look for packages in the 'src' directory
``````bash
pip install -e . # The -e . flag installs the project in editable mode and its dependencies
``````ini
# .env
# Environment-specific variables and sensitive data
APP_ENV="development"
DEBUG_MODE="True"
DATABASE_URL="sqlite:///./data/app.db" # Example database path
ML_MODEL_SAVE_PATH="models/latest_model.pt" # Example path for model saving
CONFIG_PATH="config/config.yaml" # Path to the main YAML configuration
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
``````python
# src/config_manager.py
import os
import yaml
from dotenv import load_dotenv

class ConfigManager:
    """
    Manages loading configurations from .env and YAML files.
    Prioritizes environment variables over YAML configuration.
    """
    _instance = None # Singleton instance

    def __new__(cls, yaml_config_path: str = None):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, yaml_config_path: str = None):
        if self._initialized:
            return

        # Load environment variables from .env file
        load_dotenv()

        # Determine the path to the YAML config file
        # Prioritize constructor argument, then .env, then default
        self._yaml_config_path = yaml_config_path or os.getenv("CONFIG_PATH", "config/config.yaml")

        self._yaml_config = {}
        if os.path.exists(self._yaml_config_path):
            try:
                with open(self._yaml_config_path, 'r') as f:
                    self._yaml_config = yaml.safe_load(f)
            except yaml.YAMLError as e:
                print(f"Error parsing YAML configuration at {self._yaml_config_path}: {e}")
            except Exception as e:
                print(f"Error loading YAML configuration at {self._yaml_config_path}: {e}")
        else:
            print(f"Warning: YAML configuration file not found at {self._yaml_config_path}. Using empty config.")

        self._initialized = True

    def get(self, key: str, default=None):
        """
        Retrieves a configuration value.
        Prioritizes environment variables (case-insensitive, underscores for dots)
        over values from the YAML file (dot-separated for nested keys).

        Example: config.get("data.raw_data_path") or config.get("APP_ENV")
        """
        # 1. Check direct environment variable (uppercase, dots replaced with underscores)
        env_key_snake_case = key.upper().replace('.', '_')
        env_val = os.getenv(env_key_snake_case)
        if env_val is not None:
            return env_val

        # 2. Check YAML configuration
        parts = key.split('.')
        current_val = self._yaml_config
        for part in parts:
            if isinstance(current_val, dict) and part in current_val:
                current_val = current_val[part]
            else:
                return default # Key not found in YAML path
        return current_val

# Create a global instance for easy access throughout the application
config = ConfigManager()

# Example usage:
if __name__ == "__main__":
    print("--- Testing ConfigManager ---")

    # From .env
    print(f"App Environment (from .env): {config.get('APP_ENV')}")
    print(f"Debug Mode (from .env): {config.get('DEBUG_MODE')}")
    print(f"Database URL (from .env): {config.get('DATABASE_URL')}")

    # From config.yaml
    print(f"App Name (from config.yaml): {config.get('app.name')}")
    print(f"Data Test Split Ratio (from config.yaml): {config.get('data.test_split_ratio')}")
    print(f"Model N Estimators (from config.yaml): {config.get('model.hyperparameters.n_estimators')}")
    print(f"API Port (from config.yaml): {config.get('api.port')}")

    # Override example: If we set ML_MODEL_SAVE_PATH in .env, it overrides.
    # We already have it in .env, so it will be picked from there.
    print(f"ML Model Save Path (from .env): {config.get('ML_MODEL_SAVE_PATH')}")

    # Non-existent key
    print(f"Non-existent key (default None): {config.get('non_existent.key')}")
    print(f"Non-existent key (default 'default_value'): {config.get('another.key', 'default_value')}")
``````python
# src/main.py
from src.config_manager import config
from fastapi import FastAPI
import uvicorn

# Initialize FastAPI app
app = FastAPI(
    title=config.get("app.name"),
    version=config.get("app.version"),
    description=config.get("app.description"),
)

@app.get("/")
async def read_root():
    return {
        "message": "Welcome to the ML Pipeline API!",
        "environment": config.get("APP_ENV"),
        "model_name": config.get("model.name"),
        "api_port": config.get("api.port")
    }

@app.get("/config_details")
async def get_config_details():
    return {
        "app_name": config.get("app.name"),
        "debug_mode": config.get("DEBUG_MODE"),
        "raw_data_path": config.get("data.raw_data_path"),
        "model_n_estimators": config.get("model.hyperparameters.n_estimators"),
        "db_url": config.get("DATABASE_URL"),
        "model_save_path": config.get("ML_MODEL_SAVE_PATH")
    }

if __name__ == "__main__":
    # Example of how to access configurations directly
    print(f"--- Application Startup Details ---")
    print(f"App Name: {config.get('app.name')}")
    print(f"App Version: {config.get('app.version')}")
    print(f"Debug Mode: {config.get('DEBUG_MODE')}")
    print(f"Model Output Path: {config.get('model.output_model_path')}")
    print(f"API Host: {config.get('api.host')}, Port: {config.get('api.port')}")

    # Run the FastAPI application
    uvicorn.run(
        "src.main:app",
        host=config.get("api.host"),
        port=int(config.get("api.port")),
        reload=config.get("api.reload", False) # Reload only in development
    )
```### Project Initialization and Directory Setup

First, let's create the project directory, set up the virtual environment, and establish the core folder structure.



---

### `pyproject.toml` for Dependency Management

This file will manage our project's dependencies using the modern `[project]` table from PEP 621.

Create `pyproject.toml` in the root of `ml_pipeline_project` and add the following content:



**Install Dependencies:**

After creating `pyproject.toml`, install the dependencies within your active virtual environment:



---

### Centralized Configuration System

We'll use `.env` for environment-specific variables (like API keys, sensitive paths) and `config.yaml` for structured application settings and hyperparameters. `python-dotenv` and `PyYAML` will be used to load these.

#### 1. `.env` File

Create a file named `.env` in the root of `ml_pipeline_project` and add the following:



#### 2. `config/config.yaml` File

Create `config/config.yaml` inside the `config/` directory with example ML parameters:



#### 3. `src/config_manager.py` (Python Configuration Loader)

This Python module will handle loading both `.env` variables and parsing the `config.yaml` file, providing a unified interface to access configurations.

Create `src/config_manager.py` within the `src/` directory and add the following content:



#### 4. `src/main.py` (Demonstration of Configuration Loading)

To demonstrate that the configuration system works, create a simple `main.py` file.

Create `src/main.py` within the `src/` directory and add the following content:



---

### Verify the Setup

1.  **Activate Virtual Environment:**
    ```bash
    source .venv/bin/activate
    ```
2.  **Run the `config_manager` test:**
    ```bash
    python src/config_manager.py
    ```
    You should see output demonstrating that configurations from both `.env` and `config.yaml` are loaded correctly.
3.  **Run the FastAPI application:**
    ```bash
    python src/main.py
    ```
    This will start the FastAPI server. You can then open your browser or use `curl` to test the endpoints:
    *   `http://127.0.0.1:8000/`
    *   `http://127.0.0.1:8000/config_details`

This setup provides a robust, modular, and configurable foundation for your ML pipeline, ready for further development of model training, evaluation, and deployment logic within the `src/` directory.