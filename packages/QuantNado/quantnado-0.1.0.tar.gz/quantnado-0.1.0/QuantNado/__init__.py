import os
import warnings

# Suppress OpenMP messages
os.environ["OMP_DISPLAY_ENV"] = "FALSE"
os.environ["KMP_WARNINGS"] = "0"
os.environ["KMP_INIT_AT_FORK"] = "FALSE"

# Suppress specific pandas FutureWarnings (e.g., from pyranges)
warnings.filterwarnings("ignore", category=FutureWarning, message=".*observed=False.*")
