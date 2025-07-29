"""
AutoML Data Analyzer
====================

Comprehensive data analysis module that builds on the foundation utils.
Provides deep insights into data characteristics and quality to guide
algorithm selection and preprocessing decisions.
"""

import pandas as pd
import numpy as np
import warnings
from typing import Dict, List, Any, Tuple, Optional
from scipy import stats
from sklearn.feature_selection import mutual_info_classif, mutual_info_regression
from sklearn.preprocessing import LabelEncoder

# Import our foundation functions
from .utils import validate_input_data, detect_task_type, calculate_basic_stats


class DataAnalyzer:
    """
    Comprehensive data analysis for AutoML.
    
    Analyzes data characteristics, quality issues, and relationships
    to provide intelligent recommendations for preprocessing and algorithm selection.
    """
    
    def __init__(self, verbose: bool = True):
        """
        Initialize the DataAnalyzer.
        
        Args:
            verbose: Whether to print analysis progress and warnings
        """
        self.verbose = verbose
        self.analysis_results = {}
        
    def analyze(self, X, y, task: Optional[str] = None) -> Dict[str, Any]:
        """
        Perform comprehensive data analysis.
        
        This is the main entry point that orchestrates all analysis steps.
        
        Args:
            X: Feature data (various formats accepted)
            y: Target variable (various formats accepted)
            task: Optional task type override ('classification' or 'regression')
            
        Returns:
            Dict containing comprehensive analysis results
            
        Example:
            >>> analyzer = DataAnalyzer()
            >>> analysis = analyzer.analyze(X, y)
            >>> print(f"Recommended algorithms: {analysis['recommended_algorithms']}")
        """
        try:
            if self.verbose:
                print("🔍 Starting comprehensive data analysis...")
            
            # Step 1: Validate and clean input data
            X_clean, y_clean = validate_input_data(X, y)
            
            # Step 2: Get basic statistics
            basic_stats = calculate_basic_stats(X_clean, y_clean)
            
            # Override task type if provided
            if task is not None:
                basic_stats['task_type'] = task
            
            # Step 3: Detailed feature analysis
            if self.verbose:
                print("   📊 Analyzing features...")
            feature_analysis = self._analyze_features(X_clean, y_clean, basic_stats['task_type'])
            
            # Step 4: Data quality assessment
            if self.verbose:
                print("   🔍 Assessing data quality...")
            quality_analysis = self._analyze_data_quality(X_clean, y_clean)
            
            # Step 5: Outlier detection
            if self.verbose:
                print("   🎯 Detecting outliers...")
            outlier_analysis = self._detect_outliers(X_clean, y_clean)
            
            # Step 6: Feature relationships
            if self.verbose:
                print("   🔗 Analyzing feature relationships...")
            relationship_analysis = self._analyze_relationships(X_clean, y_clean, basic_stats['task_type'])
            
            # Step 7: Algorithm recommendations
            if self.verbose:
                print("   🤖 Generating algorithm recommendations...")
            algorithm_recommendations = self._recommend_algorithms(basic_stats, feature_analysis, quality_analysis)
            
            # Step 8: Preprocessing recommendations
            preprocessing_recommendations = self._recommend_preprocessing(feature_analysis, quality_analysis, outlier_analysis)
            
            # Combine all analysis results
            self.analysis_results = {
                **basic_stats,
                'feature_analysis': feature_analysis,
                'data_quality': quality_analysis,
                'outlier_analysis': outlier_analysis,
                'relationship_analysis': relationship_analysis,
                'recommended_algorithms': algorithm_recommendations,
                'recommended_preprocessing': preprocessing_recommendations,
                'analysis_timestamp': pd.Timestamp.now(),
                'analyzer_version': '1.0.0'
            }
            
            if self.verbose:
                print("✅ Data analysis complete!")
                self._print_summary()
            
            return self.analysis_results
            
        except Exception as e:
            error_msg = f"Data analysis failed: {str(e)}"
            if self.verbose:
                print(f"❌ {error_msg}")
            
            # Return minimal analysis with error info
            return {
                'error': error_msg,
                'task_type': 'unknown',
                'recommended_algorithms': ['random_forest'],
                'quality_score': 0.0,
                'analysis_failed': True
            }
    
    def _analyze_features(self, X: pd.DataFrame, y: pd.Series, task: str) -> Dict[str, Any]:
        """Analyze individual features in detail."""
        try:
            feature_analysis = {
                'numeric_features': {},
                'categorical_features': {},
                'feature_importance': {},
                'problematic_features': []
            }
            
            # Analyze numeric features
            numeric_cols = X.select_dtypes(include=[np.number]).columns
            for col in numeric_cols:
                feature_analysis['numeric_features'][col] = self._analyze_numeric_feature(X[col])
            
            # Analyze categorical features
            categorical_cols = X.select_dtypes(include=['object', 'category']).columns
            for col in categorical_cols:
                feature_analysis['categorical_features'][col] = self._analyze_categorical_feature(X[col])
            
            # Calculate feature importance if possible
            try:
                feature_analysis['feature_importance'] = self._calculate_feature_importance(X, y, task)
            except Exception:
                feature_analysis['feature_importance'] = {}
            
            # Identify problematic features
            feature_analysis['problematic_features'] = self._identify_problematic_features(X, feature_analysis)
            
            return feature_analysis
            
        except Exception as e:
            return {'error': f"Feature analysis failed: {str(e)}"}
    
    def _analyze_numeric_feature(self, series: pd.Series) -> Dict[str, Any]:
        """Analyze a single numeric feature."""
        try:
            analysis = {
                'dtype': str(series.dtype),
                'missing_count': series.isnull().sum(),
                'missing_percentage': (series.isnull().sum() / len(series)) * 100,
                'unique_count': series.nunique(),
                'unique_percentage': (series.nunique() / len(series)) * 100
            }
            
            # Statistics for non-missing values
            clean_series = series.dropna()
            if len(clean_series) > 0:
                analysis.update({
                    'mean': float(clean_series.mean()),
                    'std': float(clean_series.std()),
                    'min': float(clean_series.min()),
                    'max': float(clean_series.max()),
                    'median': float(clean_series.median()),
                    'skewness': float(clean_series.skew()),
                    'kurtosis': float(clean_series.kurtosis())
                })
                
                # Detect potential issues
                analysis['issues'] = []
                
                if analysis['std'] == 0:
                    analysis['issues'].append('constant_feature')
                elif analysis['std'] < 1e-10:
                    analysis['issues'].append('very_low_variance')
                
                if abs(analysis['skewness']) > 2:
                    analysis['issues'].append('highly_skewed')
                
                if analysis['unique_count'] == 1:
                    analysis['issues'].append('single_value')
                elif analysis['unique_percentage'] > 95:
                    analysis['issues'].append('high_cardinality')
                
            return analysis
            
        except Exception:
            return {'error': 'Numeric feature analysis failed'}
    
    def _analyze_categorical_feature(self, series: pd.Series) -> Dict[str, Any]:
        """Analyze a single categorical feature."""
        try:
            analysis = {
                'dtype': str(series.dtype),
                'missing_count': series.isnull().sum(),
                'missing_percentage': (series.isnull().sum() / len(series)) * 100,
                'unique_count': series.nunique(),
                'unique_percentage': (series.nunique() / len(series)) * 100
            }
            
            # Value counts and distribution
            clean_series = series.dropna()
            if len(clean_series) > 0:
                value_counts = clean_series.value_counts()
                analysis.update({
                    'most_frequent': value_counts.index[0] if len(value_counts) > 0 else None,
                    'most_frequent_count': int(value_counts.iloc[0]) if len(value_counts) > 0 else 0,
                    'most_frequent_percentage': (value_counts.iloc[0] / len(clean_series)) * 100 if len(value_counts) > 0 else 0,
                    'value_distribution': value_counts.head(10).to_dict()
                })
                
                # Detect potential issues
                analysis['issues'] = []
                
                if analysis['unique_count'] == 1:
                    analysis['issues'].append('single_value')
                elif analysis['unique_count'] > len(clean_series) * 0.9:
                    analysis['issues'].append('very_high_cardinality')
                elif analysis['unique_count'] > 50:
                    analysis['issues'].append('high_cardinality')
                
                if analysis['most_frequent_percentage'] > 95:
                    analysis['issues'].append('dominant_category')
                
            return analysis
            
        except Exception:
            return {'error': 'Categorical feature analysis failed'}
    
    def _analyze_data_quality(self, X: pd.DataFrame, y: pd.Series) -> Dict[str, Any]:
        """Comprehensive data quality assessment."""
        try:
            quality = {
                'overall_score': 1.0,
                'issues': [],
                'warnings': [],
                'recommendations': []
            }
            
            # Check for duplicate rows
            duplicate_count = X.duplicated().sum()
            if duplicate_count > 0:
                duplicate_pct = (duplicate_count / len(X)) * 100
                quality['issues'].append(f'duplicate_rows: {duplicate_count} ({duplicate_pct:.1f}%)')
                quality['overall_score'] -= min(duplicate_pct / 100 * 0.3, 0.2)
                quality['recommendations'].append('Consider removing duplicate rows')
            
            # Check for constant features
            constant_features = []
            for col in X.select_dtypes(include=[np.number]).columns:
                if X[col].nunique() <= 1:
                    constant_features.append(col)
            
            if constant_features:
                quality['issues'].append(f'constant_features: {constant_features}')
                quality['overall_score'] -= len(constant_features) / len(X.columns) * 0.2
                quality['recommendations'].append('Remove constant features')
            
            # Check for high missing data
            missing_pct = (X.isnull().sum().sum() / X.size) * 100
            if missing_pct > 50:
                quality['issues'].append(f'very_high_missing_data: {missing_pct:.1f}%')
                quality['overall_score'] -= 0.4
                quality['recommendations'].append('Consider data collection improvement')
            elif missing_pct > 20:
                quality['warnings'].append(f'high_missing_data: {missing_pct:.1f}%')
                quality['overall_score'] -= 0.2
                quality['recommendations'].append('Implement robust missing value handling')
            
            # Check sample size adequacy
            n_samples, n_features = X.shape
            if n_samples < 100:
                quality['warnings'].append(f'small_sample_size: {n_samples} samples')
                quality['overall_score'] -= 0.3
                quality['recommendations'].append('Consider collecting more data')
            elif n_features > n_samples:
                quality['warnings'].append(f'more_features_than_samples: {n_features} features, {n_samples} samples')
                quality['overall_score'] -= 0.2
                quality['recommendations'].append('Consider feature selection or dimensionality reduction')
            
            # Check for class imbalance (classification only)
            if detect_task_type(y) == 'classification':
                value_counts = y.value_counts()
                if len(value_counts) > 1:
                    imbalance_ratio = value_counts.min() / value_counts.max()
                    if imbalance_ratio < 0.1:
                        quality['issues'].append(f'severe_class_imbalance: ratio {imbalance_ratio:.3f}')
                        quality['overall_score'] -= 0.2
                        quality['recommendations'].append('Consider class balancing techniques')
                    elif imbalance_ratio < 0.3:
                        quality['warnings'].append(f'class_imbalance: ratio {imbalance_ratio:.3f}')
                        quality['overall_score'] -= 0.1
            
            # Ensure score is between 0 and 1
            quality['overall_score'] = max(0.0, min(1.0, quality['overall_score']))
            
            return quality
            
        except Exception as e:
            return {
                'overall_score': 0.0,
                'error': f"Quality analysis failed: {str(e)}",
                'issues': ['analysis_failed'],
                'warnings': [],
                'recommendations': ['Review data manually']
            }
    
    def _detect_outliers(self, X: pd.DataFrame, y: pd.Series) -> Dict[str, Any]:
        """Detect outliers in numeric features."""
        try:
            outlier_analysis = {
                'features_with_outliers': {},
                'outlier_summary': {
                    'total_outliers': 0,
                    'features_affected': 0,
                    'outlier_percentage': 0.0
                }
            }
            
            numeric_cols = X.select_dtypes(include=[np.number]).columns
            total_outliers = 0
            
            for col in numeric_cols:
                series = X[col].dropna()
                if len(series) < 4:  # Need at least 4 points for outlier detection
                    continue
                
                # IQR method
                Q1 = series.quantile(0.25)
                Q3 = series.quantile(0.75)
                IQR = Q3 - Q1
                
                if IQR > 0:  # Avoid division by zero
                    lower_bound = Q1 - 1.5 * IQR
                    upper_bound = Q3 + 1.5 * IQR
                    
                    outliers_mask = (series < lower_bound) | (series > upper_bound)
                    outlier_count = outliers_mask.sum()
                    
                    if outlier_count > 0:
                        outlier_analysis['features_with_outliers'][col] = {
                            'count': int(outlier_count),
                            'percentage': float((outlier_count / len(series)) * 100),
                            'lower_bound': float(lower_bound),
                            'upper_bound': float(upper_bound),
                            'outlier_values': series[outliers_mask].head(10).tolist()
                        }
                        total_outliers += outlier_count
            
            # Summary statistics
            outlier_analysis['outlier_summary'] = {
                'total_outliers': int(total_outliers),
                'features_affected': len(outlier_analysis['features_with_outliers']),
                'outlier_percentage': float((total_outliers / len(X)) * 100) if len(X) > 0 else 0.0
            }
            
            return outlier_analysis
            
        except Exception as e:
            return {
                'error': f"Outlier detection failed: {str(e)}",
                'features_with_outliers': {},
                'outlier_summary': {'total_outliers': 0, 'features_affected': 0, 'outlier_percentage': 0.0}
            }
    
    def _analyze_relationships(self, X: pd.DataFrame, y: pd.Series, task: str) -> Dict[str, Any]:
        """Analyze relationships between features and target."""
        try:
            relationship_analysis = {
                'feature_target_correlations': {},
                'feature_correlations': {},
                'highly_correlated_pairs': []
            }
            
            # Feature-target relationships
            numeric_cols = X.select_dtypes(include=[np.number]).columns
            
            if len(numeric_cols) > 0 and task == 'regression':
                # For regression, calculate Pearson correlation with target
                for col in numeric_cols:
                    if X[col].nunique() > 1:  # Skip constant features
                        try:
                            corr = X[col].corr(y)
                            if not np.isnan(corr):
                                relationship_analysis['feature_target_correlations'][col] = float(corr)
                        except Exception:
                            continue
            
            # Feature-feature correlations (only for numeric features)
            if len(numeric_cols) >= 2:
                try:
                    corr_matrix = X[numeric_cols].corr()
                    
                    # Find highly correlated pairs
                    high_corr_threshold = 0.8
                    for i in range(len(corr_matrix.columns)):
                        for j in range(i+1, len(corr_matrix.columns)):
                            corr_value = corr_matrix.iloc[i, j]
                            if abs(corr_value) > high_corr_threshold:
                                relationship_analysis['highly_correlated_pairs'].append({
                                    'feature1': corr_matrix.columns[i],
                                    'feature2': corr_matrix.columns[j],
                                    'correlation': float(corr_value)
                                })
                    
                    # Store top correlations for each feature
                    for col in numeric_cols:
                        correlations = corr_matrix[col].drop(col).abs().sort_values(ascending=False)
                        relationship_analysis['feature_correlations'][col] = correlations.head(3).to_dict()
                        
                except Exception:
                    pass  # Skip if correlation calculation fails
            
            return relationship_analysis
            
        except Exception as e:
            return {
                'error': f"Relationship analysis failed: {str(e)}",
                'feature_target_correlations': {},
                'feature_correlations': {},
                'highly_correlated_pairs': []
            }
    
    def _calculate_feature_importance(self, X: pd.DataFrame, y: pd.Series, task: str) -> Dict[str, float]:
        """Calculate feature importance using mutual information."""
        try:
            # Prepare data for mutual information
            X_encoded = X.copy()
            
            # Encode categorical variables
            label_encoders = {}
            for col in X.select_dtypes(include=['object', 'category']).columns:
                le = LabelEncoder()
                X_encoded[col] = le.fit_transform(X_encoded[col].astype(str))
                label_encoders[col] = le
            
            # Handle missing values (simple imputation for feature importance)
            X_filled = X_encoded.fillna(X_encoded.mean() if len(X_encoded.select_dtypes(include=[np.number]).columns) > 0 else 0)
            
            # Calculate mutual information
            if task == 'classification':
                # Encode target for classification
                y_encoded = LabelEncoder().fit_transform(y.astype(str))
                mi_scores = mutual_info_classif(X_filled, y_encoded, random_state=42)
            else:
                mi_scores = mutual_info_regression(X_filled, y, random_state=42)
            
            # Create feature importance dictionary
            feature_importance = dict(zip(X.columns, mi_scores))
            
            # Normalize to sum to 1
            total_importance = sum(mi_scores)
            if total_importance > 0:
                feature_importance = {k: v/total_importance for k, v in feature_importance.items()}
            
            return feature_importance
            
        except Exception:
            # If mutual information fails, return empty dict
            return {}
    
    def _identify_problematic_features(self, X: pd.DataFrame, feature_analysis: Dict) -> List[str]:
        """Identify features that might cause problems in ML."""
        problematic = []
        
        try:
            # Check numeric features
            for col, analysis in feature_analysis['numeric_features'].items():
                if 'issues' in analysis:
                    if any(issue in analysis['issues'] for issue in ['constant_feature', 'single_value']):
                        problematic.append(col)
            
            # Check categorical features
            for col, analysis in feature_analysis['categorical_features'].items():
                if 'issues' in analysis:
                    if any(issue in analysis['issues'] for issue in ['single_value', 'very_high_cardinality']):
                        problematic.append(col)
            
            return problematic
            
        except Exception:
            return []
    
    def _recommend_algorithms(self, basic_stats: Dict, feature_analysis: Dict, quality_analysis: Dict) -> List[str]:
        """Recommend algorithms based on data characteristics."""
        try:
            recommendations = []
            
            n_samples = basic_stats['n_samples']
            n_features = basic_stats['n_features']
            task = basic_stats['task_type']
            quality_score = quality_analysis['overall_score']
            
            # Base recommendations by task
            if task == 'classification':
                base_algorithms = ['random_forest', 'logistic_regression', 'gradient_boosting']
            else:
                base_algorithms = ['random_forest', 'linear_regression', 'gradient_boosting']
            
            # Adjust based on dataset size
            if n_samples < 100:
                # Small datasets: prefer simpler models
                if task == 'classification':
                    recommendations = ['logistic_regression', 'random_forest', 'svm']
                else:
                    recommendations = ['linear_regression', 'random_forest', 'ridge_regression']
            elif n_samples < 1000:
                # Medium datasets
                recommendations = base_algorithms
            elif n_samples < 10000:
                # Large datasets: can handle more complex models
                if task == 'classification':
                    recommendations = ['random_forest', 'gradient_boosting', 'xgboost', 'logistic_regression']
                else:
                    recommendations = ['random_forest', 'gradient_boosting', 'xgboost', 'linear_regression']
            else:
                # Very large datasets: prefer scalable algorithms
                if task == 'classification':
                    recommendations = ['xgboost', 'lightgbm', 'random_forest', 'neural_network']
                else:
                    recommendations = ['xgboost', 'lightgbm', 'random_forest', 'neural_network']
            
            # Adjust based on feature characteristics
            numeric_features = len(feature_analysis.get('numeric_features', {}))
            categorical_features = len(feature_analysis.get('categorical_features', {}))
            
            if categorical_features > numeric_features:
                # Many categorical features: tree-based methods work well
                tree_based = ['random_forest', 'gradient_boosting', 'xgboost']
                recommendations = [alg for alg in recommendations if alg in tree_based] + tree_based
            
            # Adjust based on data quality
            if quality_score < 0.5:
                # Low quality data: prefer robust algorithms
                robust_algorithms = ['random_forest', 'gradient_boosting']
                recommendations = [alg for alg in recommendations if alg in robust_algorithms] + robust_algorithms
            
            # Handle high-dimensional data
            if n_features > n_samples:
                if task == 'classification':
                    recommendations = ['logistic_regression', 'ridge_regression', 'lasso_regression', 'svm']
                else:
                    recommendations = ['ridge_regression', 'lasso_regression', 'elastic_net', 'svm']
            
            # Remove duplicates while preserving order
            seen = set()
            final_recommendations = []
            for alg in recommendations:
                if alg not in seen:
                    seen.add(alg)
                    final_recommendations.append(alg)
            
            # Ensure we have at least 2 algorithms and at most 5
            if len(final_recommendations) < 2:
                final_recommendations.extend(['random_forest', 'logistic_regression' if task == 'classification' else 'linear_regression'])
            
            return final_recommendations[:5]  # Limit to top 5
            
        except Exception:
            # Fallback recommendations
            if basic_stats.get('task_type') == 'classification':
                return ['random_forest', 'logistic_regression']
            else:
                return ['random_forest', 'linear_regression']
    
    def _recommend_preprocessing(self, feature_analysis: Dict, quality_analysis: Dict, outlier_analysis: Dict) -> Dict[str, List[str]]:
        """Recommend preprocessing steps based on analysis."""
        try:
            recommendations = {
                'required': [],
                'suggested': [],
                'optional': []
            }
            
            # Required preprocessing
            if any('missing' in issue for issue in quality_analysis.get('issues', [])):
                recommendations['required'].append('handle_missing_values')
            
            if feature_analysis.get('categorical_features'):
                recommendations['required'].append('encode_categorical_features')
            
            if feature_analysis.get('numeric_features'):
                recommendations['required'].append('scale_numeric_features')
            
            # Suggested preprocessing
            if outlier_analysis['outlier_summary']['outlier_percentage'] > 5:
                recommendations['suggested'].append('handle_outliers')
            
            if any('high_cardinality' in str(analysis) for analysis in feature_analysis.get('categorical_features', {}).values()):
                recommendations['suggested'].append('reduce_categorical_cardinality')
            
            if any('highly_skewed' in str(analysis) for analysis in feature_analysis.get('numeric_features', {}).values()):
                recommendations['suggested'].append('transform_skewed_features')
            
            # Optional preprocessing
            if len(feature_analysis.get('problematic_features', [])) > 0:
                recommendations['optional'].append('remove_problematic_features')
            
            if any('duplicate_rows' in issue for issue in quality_analysis.get('issues', [])):
                recommendations['optional'].append('remove_duplicates')
            
            return recommendations
            
        except Exception:
            return {
                'required': ['handle_missing_values', 'encode_categorical_features', 'scale_numeric_features'],
                'suggested': [],
                'optional': []
            }
    
    def _print_summary(self) -> None:
        """Print a concise summary of the analysis."""
        try:
            results = self.analysis_results
            
            print(f"\n📋 Analysis Summary:")
            print(f"   📊 Dataset: {results['n_samples']} samples, {results['n_features']} features")
            print(f"   🎯 Task: {results['task_type']}")
            print(f"   ⭐ Quality Score: {results['data_quality']['overall_score']:.2f}/1.0")
            
            if results['data_quality']['issues']:
                print(f"   ⚠️  Issues: {len(results['data_quality']['issues'])} found")
            
            if results['outlier_analysis']['outlier_summary']['outlier_percentage'] > 0:
                print(f"   🎯 Outliers: {results['outlier_analysis']['outlier_summary']['outlier_percentage']:.1f}% of data")
            
            print(f"   🤖 Recommended algorithms: {', '.join(results['recommended_algorithms'][:3])}")
            
        except Exception:
            print("   📋 Analysis summary not available")


# Test section - comprehensive testing of the DataAnalyzer
if __name__ == "__main__":
    print("🧪 Testing AutoML Data Analyzer")
    print("=" * 60)
    
    # Test 1: Classification data with mixed types
    print("\n📊 Test 1: Classification with Mixed Data Types")
    try:
        from sklearn.datasets import make_classification
        import pandas as pd
        
        # Create mixed classification data
        X_cls, y_cls = make_classification(n_samples=300, n_features=8, n_informative=5, 
                                          n_redundant=1, n_clusters_per_class=1, random_state=42)
        
        # Convert to DataFrame and add categorical features
        X_df = pd.DataFrame(X_cls, columns=[f'numeric_{i}' for i in range(8)])
        
        # Add categorical features
        np.random.seed(42)
        X_df['category_a'] = np.random.choice(['A', 'B', 'C'], size=300)
        X_df['category_b'] = np.random.choice(['High', 'Medium', 'Low'], size=300, p=[0.3, 0.5, 0.2])
        
        # Add some missing values
        X_df.loc[X_df.sample(30).index, 'numeric_0'] = np.nan
        
        # Create target with some class imbalance
        y_series = pd.Series(y_cls)
        
        # Test the analyzer
        analyzer = DataAnalyzer(verbose=True)
        analysis = analyzer.analyze(X_df, y_series)
        
        print(f"✅ Classification analysis complete!")
        print(f"   Quality score: {analysis['data_quality']['overall_score']:.2f}")
        print(f"   Recommended algorithms: {analysis['recommended_algorithms']}")
        print(f"   Problematic features: {len(analysis['feature_analysis']['problematic_features'])}")
        
    except Exception as e:
        print(f"❌ Classification test failed: {e}")
    
    # Test 2: Regression data with outliers
    print("\n📈 Test 2: Regression with Outliers")
    try:
        from sklearn.datasets import make_regression
        
        # Create regression data
        X_reg, y_reg = make_regression(n_samples=200, n_features=6, noise=0.1, random_state=42)
        X_df = pd.DataFrame(X_reg, columns=[f'feature_{i}' for i in range(6)])
        
        # Add outliers
        outlier_indices = np.random.choice(200, size=10, replace=False)
        X_df.loc[outlier_indices, 'feature_0'] *= 10  # Create outliers
        
        y_series = pd.Series(y_reg)
        
        # Test the analyzer
        analyzer = DataAnalyzer(verbose=True)
        analysis = analyzer.analyze(X_df, y_series)
        
        print(f"✅ Regression analysis complete!")
        print(f"   Outliers detected: {analysis['outlier_analysis']['outlier_summary']['total_outliers']}")
        print(f"   Features with outliers: {analysis['outlier_analysis']['outlier_summary']['features_affected']}")
        
    except Exception as e:
        print(f"❌ Regression test failed: {e}")
    
    # Test 3: Small dataset with quality issues
    print("\n⚠️  Test 3: Small Dataset with Quality Issues")
    try:
        # Create problematic small dataset
        X_small = pd.DataFrame({
            'constant_feature': [1, 1, 1, 1, 1],  # Constant
            'missing_feature': [1, 2, np.nan, np.nan, np.nan],  # Lots of missing
            'high_cardinality': ['a', 'b', 'c', 'd', 'e'],  # High cardinality for small data
            'normal_feature': [1.1, 2.2, 3.3, 4.4, 5.5]
        })
        y_small = pd.Series([0, 0, 1, 1, 1])
        
        # Test the analyzer
        analyzer = DataAnalyzer(verbose=True)
        analysis = analyzer.analyze(X_small, y_small)
        
        print(f"✅ Small dataset analysis complete!")
        print(f"   Issues found: {len(analysis['data_quality']['issues'])}")
        print(f"   Warnings: {len(analysis['data_quality']['warnings'])}")
        print(f"   Recommendations: {len(analysis['data_quality']['recommendations'])}")
        
    except Exception as e:
        print(f"❌ Small dataset test failed: {e}")
    
    # Test 4: Integration with utils functions
    print("\n🔗 Test 4: Integration with Utils Functions")
    try:
        # Test that analyzer works with various input formats
        X_numpy = np.random.random((100, 4))
        y_list = [0, 1] * 50
        
        analyzer = DataAnalyzer(verbose=False)
        analysis = analyzer.analyze(X_numpy, y_list)
        
        print(f"✅ Input format flexibility test passed!")
        print(f"   Task detected: {analysis['task_type']}")
        print(f"   Shape processed: {analysis['n_samples']} x {analysis['n_features']}")
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
    
    print("\n🎉 Data Analyzer testing completed!")
    print("\n💡 Next steps:")
    print("   1. Implement automl/feature_engineer.py")
    print("   2. Test analyzer with your own datasets")
    print("   3. Review analysis recommendations")
