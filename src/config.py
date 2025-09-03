import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = os.path.join(BASE_DIR, "data")
INDEX_DIR = os.path.join(DATA_DIR, "indexes")
BENCHMARK_DIR = os.path.join(BASE_DIR, "evaluation", "queries") 