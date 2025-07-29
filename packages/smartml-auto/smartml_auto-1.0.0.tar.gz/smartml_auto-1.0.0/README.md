# SmartML Auto 🤖

**Intelligent AutoML that automatically analyzes your data, engineers features, and selects the best machine learning models.**

## Installation

```bash
pip install smartml-auto
```

## Quick Start

```python
import automl
from sklearn.datasets import load_iris

# Load data
iris = load_iris()
X, y = iris.data, iris.target

# Train model
predictor = automl.train(X, y, time_budget='fast')

# Make predictions
predictions = predictor.predict(X[:5])

# View results
predictor.summary()
```

## License

MIT License
