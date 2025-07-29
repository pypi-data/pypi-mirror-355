"""
AutoML Utils - Foundation Functions
==================================

Core utility functions for the AutoML package.
These are the building blocks used throughout the system.
"""

import pandas as pd
import numpy as np
import warnings
from typing import Tuple, Union, Dict, Any, Optional

# Type hints for better code documentation
DataInput = Union[np.ndarray, pd.DataFrame, list]
TargetInput = Union[np.ndarray, pd.Series, list]


def validate_input_data(X: DataInput, y: TargetInput) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Convert and validate input data for AutoML processing.
    
    Takes various input formats and converts them to clean pandas DataFrame and Series.
    Performs basic validation to ensure data is suitable for machine learning.
    
    Args:
        X: Feature data (numpy array, pandas DataFrame, or list)
        y: Target variable (numpy array, pandas Series, or list)
        
    Returns:
        Tuple[pd.DataFrame, pd.Series]: Clean feature DataFrame and target Series
        
    Raises:
        ValueError: If data shapes don't match or data is invalid
        TypeError: If data types can't be converted
        
    Example:
        >>> import numpy as np
        >>> X = np.array([[1, 2], [3, 4], [5, 6]])
        >>> y = np.array([0, 1, 0])
        >>> X_clean, y_clean = validate_input_data(X, y)
        >>> print(X_clean.shape, y_clean.shape)
        (3, 2) (3,)
    """
    try:
        # Convert X to DataFrame
        if isinstance(X, pd.DataFrame):
            X_df = X.copy()
        elif isinstance(X, (np.ndarray, list)):
            X_array = np.array(X)
            
            # Handle 1D arrays (single feature)
            if X_array.ndim == 1:
                X_array = X_array.reshape(-1, 1)
            elif X_array.ndim > 2:
                raise ValueError(f"Features X must be 1D or 2D, got {X_array.ndim}D array")
            
            # Create column names
            n_features = X_array.shape[1]
            columns = [f'feature_{i}' for i in range(n_features)]
            X_df = pd.DataFrame(X_array, columns=columns)
        else:
            raise TypeError(f"X must be numpy array, pandas DataFrame, or list. Got {type(X)}")
        
        # Convert y to Series
        if isinstance(y, pd.Series):
            y_series = y.copy()
        elif isinstance(y, (np.ndarray, list)):
            y_array = np.array(y)
            
            # Handle multi-dimensional targets
            if y_array.ndim > 1:
                if y_array.shape[1] == 1:
                    y_array = y_array.ravel()
                else:
                    raise ValueError(f"Target y must be 1D, got shape {y_array.shape}")
            
            y_series = pd.Series(y_array, name='target')
        else:
            raise TypeError(f"y must be numpy array, pandas Series, or list. Got {type(y)}")
        
        # Validate shapes match
        if len(X_df) != len(y_series):
            raise ValueError(
                f"X and y must have same number of samples. "
                f"X has {len(X_df)} samples, y has {len(y_series)} samples"
            )
        
        # Check for empty data
        if len(X_df) == 0:
            raise ValueError("Cannot work with empty dataset")
        
        if X_df.shape[1] == 0:
            raise ValueError("X must have at least one feature")
        
        # Reset indices to ensure they match
        X_df = X_df.reset_index(drop=True)
        y_series = y_series.reset_index(drop=True)
        
        # Basic data validation
        if X_df.isnull().all().all():
            raise ValueError("X contains only missing values")
        
        if y_series.isnull().all():
            raise ValueError("y contains only missing values")
        
        # Warn about high missing data
        missing_X_pct = (X_df.isnull().sum().sum() / X_df.size) * 100
        missing_y_pct = (y_series.isnull().sum() / len(y_series)) * 100
        
        if missing_X_pct > 50:
            warnings.warn(f"X has {missing_X_pct:.1f}% missing values. Consider data cleaning.")
        
        if missing_y_pct > 10:
            warnings.warn(f"y has {missing_y_pct:.1f}% missing values. Consider data cleaning.")
        
        return X_df, y_series
        
    except Exception as e:
        raise ValueError(f"Error validating input data: {str(e)}")


def detect_task_type(y: pd.Series) -> str:
    """
    Automatically detect if the task is classification or regression.
    
    Analyzes the target variable to determine the machine learning task type.
    Uses several heuristics to make an intelligent guess.
    
    Args:
        y: Target variable as pandas Series
        
    Returns:
        str: Either "classification" or "regression"
        
    Example:
        >>> import pandas as pd
        >>> y_cls = pd.Series([0, 1, 0, 1, 1])
        >>> detect_task_type(y_cls)
        'classification'
        >>> y_reg = pd.Series([1.5, 2.3, 3.7, 4.1])
        >>> detect_task_type(y_reg)
        'regression'
    """
    try:
        # Remove missing values for analysis
        y_clean = y.dropna()
        
        if len(y_clean) == 0:
            raise ValueError("Cannot detect task type: all target values are missing")
        
        # Check data type
        dtype = y_clean.dtype
        
        # If explicitly categorical or string, it's classification
        if dtype == 'object' or dtype.name == 'category':
            return 'classification'
        
        # If boolean, it's classification
        if dtype == 'bool':
            return 'classification'
        
        # For numeric data, use heuristics
        n_unique = y_clean.nunique()
        n_samples = len(y_clean)
        
        # Very few unique values suggests classification
        if n_unique <= 2:
            return 'classification'
        
        # If unique values are less than 5% of samples and less than 20, likely classification
        unique_ratio = n_unique / n_samples
        if unique_ratio < 0.05 and n_unique <= 20:
            return 'classification'
        
        # Check if all values are integers (might be classification)
        if y_clean.dtype in ['int64', 'int32', 'int16', 'int8']:
            # If small range of integers, likely classification
            if n_unique <= 10:
                return 'classification'
            
            # If integers are consecutive starting from 0 or 1, likely classification
            unique_values = sorted(y_clean.unique())
            if unique_values == list(range(min(unique_values), max(unique_values) + 1)):
                if len(unique_values) <= 20:
                    return 'classification'
        
        # Check for float values that might be rounded integers
        if y_clean.dtype in ['float64', 'float32']:
            # If all float values are actually whole numbers
            if (y_clean == y_clean.astype(int)).all():
                if n_unique <= 10:
                    return 'classification'
        
        # Default to regression for continuous numeric data
        return 'regression'
        
    except Exception as e:
        # If we can't determine, default to regression as it's more general
        warnings.warn(f"Could not detect task type ({str(e)}), defaulting to regression")
        return 'regression'


def calculate_basic_stats(X: pd.DataFrame, y: pd.Series) -> Dict[str, Any]:
    """
    Calculate basic statistics about the dataset.
    
    Provides essential information about data characteristics that will be used
    throughout the AutoML pipeline for decision making.
    
    Args:
        X: Feature DataFrame
        y: Target Series
        
    Returns:
        Dict containing basic statistics about the data
        
    Example:
        >>> import pandas as pd
        >>> X = pd.DataFrame({'a': [1, 2, None], 'b': ['x', 'y', 'z']})
        >>> y = pd.Series([0, 1, 0])
        >>> stats = calculate_basic_stats(X, y)
        >>> print(stats['n_samples'])
        3
    """
    try:
        stats = {}
        
        # Basic shape information
        stats['n_samples'] = len(X)
        stats['n_features'] = len(X.columns)
        
        # Task type
        stats['task_type'] = detect_task_type(y)
        
        # Missing value analysis
        missing_X = X.isnull().sum()
        stats['missing_values'] = {
            'total_missing_X': missing_X.sum(),
            'missing_percentage_X': (missing_X.sum() / X.size) * 100,
            'features_with_missing': missing_X[missing_X > 0].to_dict(),
            'missing_y': y.isnull().sum(),
            'missing_percentage_y': (y.isnull().sum() / len(y)) * 100
        }
        
        # Feature type analysis
        numeric_features = X.select_dtypes(include=[np.number]).columns.tolist()
        categorical_features = X.select_dtypes(include=['object', 'category']).columns.tolist()
        boolean_features = X.select_dtypes(include=['bool']).columns.tolist()
        
        stats['feature_types'] = {
            'numeric': numeric_features,
            'categorical': categorical_features,
            'boolean': boolean_features,
            'n_numeric': len(numeric_features),
            'n_categorical': len(categorical_features),
            'n_boolean': len(boolean_features)
        }
        
        # Target variable analysis
        if stats['task_type'] == 'classification':
            value_counts = y.value_counts()
            stats['target_info'] = {
                'unique_values': y.nunique(),
                'class_distribution': value_counts.to_dict(),
                'is_balanced': (value_counts.min() / value_counts.max()) > 0.1 if len(value_counts) > 1 else True,
                'majority_class_percentage': (value_counts.max() / len(y)) * 100
            }
        else:
            stats['target_info'] = {
                'mean': float(y.mean()) if not y.isnull().all() else None,
                'std': float(y.std()) if not y.isnull().all() else None,
                'min': float(y.min()) if not y.isnull().all() else None,
                'max': float(y.max()) if not y.isnull().all() else None,
                'unique_values': y.nunique()
            }
        
        # Data quality indicators
        stats['data_quality'] = {
            'has_missing_values': stats['missing_values']['total_missing_X'] > 0 or stats['missing_values']['missing_y'] > 0,
            'high_missing_X': stats['missing_values']['missing_percentage_X'] > 20,
            'high_missing_y': stats['missing_values']['missing_percentage_y'] > 10,
            'has_categorical': len(categorical_features) > 0,
            'all_numeric': len(categorical_features) == 0 and len(boolean_features) == 0
        }
        
        # Size-based recommendations
        if stats['n_samples'] < 100:
            stats['size_category'] = 'very_small'
        elif stats['n_samples'] < 1000:
            stats['size_category'] = 'small'
        elif stats['n_samples'] < 10000:
            stats['size_category'] = 'medium'
        else:
            stats['size_category'] = 'large'
        
        # Calculate a simple data quality score (0-1)
        quality_score = 1.0
        
        # Penalize missing data
        missing_penalty = min(stats['missing_values']['missing_percentage_X'] / 100 * 0.5, 0.3)
        quality_score -= missing_penalty
        
        # Penalize very small datasets
        if stats['n_samples'] < 50:
            quality_score -= 0.3
        elif stats['n_samples'] < 100:
            quality_score -= 0.1
        
        # Penalize datasets with too many features relative to samples
        if stats['n_features'] > stats['n_samples']:
            quality_score -= 0.2
        
        stats['quality_score'] = max(0.0, min(1.0, quality_score))
        
        return stats
        
    except Exception as e:
        # Return minimal stats if calculation fails
        return {
            'n_samples': len(X) if X is not None else 0,
            'n_features': len(X.columns) if X is not None else 0,
            'task_type': 'unknown',
            'error': str(e),
            'quality_score': 0.0
        }


# Test section - run this file directly to test the functions
if __name__ == "__main__":
    print("🧪 Testing AutoML Utils Functions")
    print("=" * 50)
    
    # Test 1: Classification data (Iris dataset)
    print("\n📊 Test 1: Classification Data (Iris-like)")
    try:
        from sklearn.datasets import make_classification
        X_cls, y_cls = make_classification(n_samples=150, n_features=4, n_classes=3, 
                                          n_informative=3, random_state=42)
        
        # Test validation
        X_df, y_series = validate_input_data(X_cls, y_cls)
        print(f"✅ Data validation: X shape {X_df.shape}, y shape {y_series.shape}")
        
        # Test task detection
        task = detect_task_type(y_series)
        print(f"✅ Task detection: {task}")
        
        # Test statistics
        stats = calculate_basic_stats(X_df, y_series)
        print(f"✅ Basic stats: {stats['n_samples']} samples, {stats['n_features']} features")
        print(f"   Quality score: {stats['quality_score']:.2f}")
        print(f"   Task type: {stats['task_type']}")
        
    except Exception as e:
        print(f"❌ Classification test failed: {e}")
    
    # Test 2: Regression data
    print("\n📈 Test 2: Regression Data")
    try:
        from sklearn.datasets import make_regression
        X_reg, y_reg = make_regression(n_samples=200, n_features=5, noise=0.1, random_state=42)
        
        # Test validation
        X_df, y_series = validate_input_data(X_reg, y_reg)
        print(f"✅ Data validation: X shape {X_df.shape}, y shape {y_series.shape}")
        
        # Test task detection
        task = detect_task_type(y_series)
        print(f"✅ Task detection: {task}")
        
        # Test statistics
        stats = calculate_basic_stats(X_df, y_series)
        print(f"✅ Basic stats: {stats['n_samples']} samples, {stats['n_features']} features")
        print(f"   Quality score: {stats['quality_score']:.2f}")
        print(f"   Target mean: {stats['target_info']['mean']:.2f}")
        
    except Exception as e:
        print(f"❌ Regression test failed: {e}")
    
    # Test 3: Mixed data types
    print("\n🔀 Test 3: Mixed Data Types")
    try:
        # Create mixed data
        import pandas as pd
        X_mixed = pd.DataFrame({
            'numeric1': [1.5, 2.3, 3.7, 4.1, 5.9],
            'numeric2': [10, 20, 30, 40, 50],
            'categorical': ['A', 'B', 'A', 'C', 'B'],
            'boolean': [True, False, True, True, False]
        })
        y_mixed = pd.Series([0, 1, 0, 1, 1])
        
        # Test validation
        X_df, y_series = validate_input_data(X_mixed, y_mixed)
        print(f"✅ Data validation: X shape {X_df.shape}, y shape {y_series.shape}")
        
        # Test task detection
        task = detect_task_type(y_series)
        print(f"✅ Task detection: {task}")
        
        # Test statistics
        stats = calculate_basic_stats(X_df, y_series)
        print(f"✅ Mixed data stats:")
        print(f"   Numeric features: {stats['feature_types']['n_numeric']}")
        print(f"   Categorical features: {stats['feature_types']['n_categorical']}")
        print(f"   Boolean features: {stats['feature_types']['n_boolean']}")
        
    except Exception as e:
        print(f"❌ Mixed data test failed: {e}")
    
    # Test 4: Error handling
    print("\n⚠️  Test 4: Error Handling")
    try:
        # Test mismatched shapes
        X_bad = [[1, 2], [3, 4]]
        y_bad = [1, 2, 3]  # Different length
        
        try:
            validate_input_data(X_bad, y_bad)
            print("❌ Should have raised error for mismatched shapes")
        except ValueError as e:
            print(f"✅ Correctly caught shape mismatch: {str(e)[:50]}...")
        
        # Test empty data
        try:
            validate_input_data([], [])
            print("❌ Should have raised error for empty data")
        except ValueError as e:
            print(f"✅ Correctly caught empty data: {str(e)[:50]}...")
            
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
    
    print("\n🎉 All tests completed!")
    print("\n💡 Next steps:")
    print("   1. Create automl/data_analyzer.py")
    print("   2. Test with your own datasets")
    print("   3. Build the feature engineering module")
