from pathlib import Path

# Root project directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# App directories
APP_DIR = PROJECT_ROOT / "app"
SRC_DIR = PROJECT_ROOT / "src"
DATA_DIR = PROJECT_ROOT / "data"
TESTS_DIR = PROJECT_ROOT / "tests"

# Data subdirectories
INPUTS_DIR = DATA_DIR / "inputs"
OUTPUTS_DIR = DATA_DIR / "outputs"
RUNS_DIR = DATA_DIR / "runs"
GROUND_TRUTH_DIR = DATA_DIR / "ground_truth"
SAMPLES_DIR = DATA_DIR / "samples"

# Prototype directories
PROTOTYPE1_DIR = SRC_DIR / "prototype1"
PROTOTYPE2_DIR = SRC_DIR / "prototype2"
PROTOTYPE3_DIR = SRC_DIR / "prototype3"

# Default settings
DEFAULT_RUN_PREFIX = "run"
DEFAULT_ENCODING = "utf-8"
