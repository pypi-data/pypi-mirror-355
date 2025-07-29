"""
SmartML Auto - Intelligent AutoML for Python
"""

from .core import AutoMLPredictor, train
from .data_analyzer import DataAnalyzer
from .feature_engineer import FeatureEngineer
from .model_selector import ModelSelector
from .utils import validate_input_data, detect_task_type, calculate_basic_stats

__version__ = "1.0.0"
__author__ = "David Johnson"

__all__ = [
    "train",
    "AutoMLPredictor",
    "DataAnalyzer",
    "FeatureEngineer",
    "ModelSelector",
    "validate_input_data",
    "detect_task_type", 
    "calculate_basic_stats",
    "__version__",
]
