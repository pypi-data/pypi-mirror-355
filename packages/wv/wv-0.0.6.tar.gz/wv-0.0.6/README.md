# wv
Weighted Principal Component Analysis using Expectation Maximization

To install:	```pip install wv```

## Overview
The `wv` package offers a sophisticated approach to Principal Component Analysis (PCA) through the implementation of Weighted Expectation Maximization PCA (EMPCA). This method is particularly useful for handling datasets with noisy or incomplete entries, as it allows for the incorporation of weights that can vary across observations and variables. This package provides tools not only for EMPCA but also includes implementations for classic PCA and a lower rank matrix approximation method, both of which can be used for comparative analysis.

## Key Features
- **Weighted EMPCA**: Iteratively solves PCA with weighted data, ideal for datasets with missing or uncertain values.
- **Classic PCA**: A straightforward implementation of PCA using Singular Value Decomposition (SVD), without support for weighted data.
- **Lower Rank Matrix Approximation**: An alternative method that iteratively approximates data using a set of model vectors that are not necessarily orthonormal.
- **Model Inspection**: After computation, users can inspect eigenvectors, coefficients, and reconstructed models to analyze the principal components and the variance explained by them.

## Installation
To install the package, use the following pip command:
```bash
pip install wv
```

## Usage

### Weighted EMPCA
To perform Weighted EMPCA on your data, you can use the `empca` function. Here is an example of how to use it:

```python
import numpy as np
from wv import empca

# Example data and weights
data = np.random.normal(size=(100, 10))
weights = np.ones_like(data)  # Equal weights
weights[data < 0] = 0.5  # Lower weight for negative values

# Perform EMPCA
model = empca(data, weights, niter=10, nvec=3)

# Access the eigenvectors and model data
eigenvectors = model.eigvec
reconstructed_data = model.model
```

### Classic PCA
For datasets without the need for weighting, you can use the `classic_pca` function:

```python
from wv import classic_pca

# Example data
data = np.random.normal(size=(100, 10))

# Perform classic PCA
model = classic_pca(data)

# Eigenvectors
eigenvectors = model.eigvec
```

### Lower Rank Matrix Approximation
This method is useful for datasets where the goal is to approximate the data without necessarily obtaining orthonormal vectors:

```python
from wv import lower_rank

# Example data and weights
data = np.random.normal(size=(100, 10))
weights = np.ones_like(data)

# Perform lower rank approximation
model = lower_rank(data, weights, niter=10, nvec=3)

# Model vectors
model_vectors = model.eigvec
```

## Documentation

### Classes and Functions

#### `Model`
A class for storing the results of PCA computations. It includes the following attributes:
- `eigvec`: Eigenvectors of the model.
- `data`: Original data used in the model.
- `weights`: Weights applied to the data.
- `coeff`: Coefficients to reconstruct the data using the eigenvectors.
- `model`: Reconstructed data using the eigenvectors and coefficients.

#### `empca`
Function to perform Weighted EMPCA. Parameters include:
- `data`: Data matrix.
- `weights`: Corresponding weights matrix.
- `niter`: Number of iterations for the EM algorithm.
- `nvec`: Number of eigenvectors to compute.
- `smooth`: Optional smoothing parameter.
- `randseed`: Seed for the random number generator.

#### `classic_pca`
Function to perform classic PCA using SVD. It only requires the data matrix and optionally the number of eigenvectors.

#### `lower_rank`
Function for lower rank matrix approximation. Similar to `empca` but does not enforce orthonormality of the resulting vectors.

### Additional Tools
- **`SavitzkyGolay`**: A utility class for smoothing signals using the Savitzky-Golay filter. Useful for preprocessing data or smoothing eigenvectors in the context of PCA.

## Contributing
Contributions to the `wv` package are welcome. Please ensure that any pull requests or issues are clear and reproducible.

## License
This project is licensed under the MIT License - see the LICENSE file for details.