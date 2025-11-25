# src/config.py
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
CSIC_DIR = os.path.join(DATA_DIR, "csic_2010")
CSIC_CSV = os.path.join(DATA_DIR, "csic_database.csv")
MODELS_DIR = os.path.join(PROJECT_ROOT, "models")

# training params
ISO_CONTAMINATION = 0.05
ISO_NESTIMATORS = 50
RF_N_ESTIMATORS = 50
RANDOM_STATE = 42

# metadata path
MODEL_METADATA = os.path.join(MODELS_DIR, "metadata.json")
