# src/calmcarz/__init__.py

# Define the package version
__version__ = "0.1.0"

# Import functions from your modules to make them accessible
# at the top level of the package
from .calm import calm_correction
from .carz import calculate_carz, calculate_tas

# Optional: Define what `from calmcarz import *` imports
__all__ = ["calm_correction", "calculate_carz", "calculate_tas"]
