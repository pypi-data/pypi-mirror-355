# shaded

**shaded** provides tools for linear spectral feature extraction and dimension reduction, with a focus on fast, interpretable projections for machine learning and signal processing.

---

## Features

- **PseudoLda**: Fast, approximate Linear Discriminant Analysis (LDA) using class centers.
- **PseudoPca**: Fast, approximate Principal Component Analysis (PCA) using random hyperplanes.
- **PairwiseLda**: LDA projections for every pair of classes.
- **Chained Spectral Projectors**: Compose multiple projection methods in sequence.
- **Band Projection Matrix**: Utilities for frequency band bucketing and projection.
- **Linear Algebra Utilities**: Null space, projection, and residue computations.

---

## Installation

```bash
pip install shaded
```

---

## Usage Examples

### PseudoLda: Fast LDA-like Projection

```python
from shaded.pseudo_lda import PseudoLda
from sklearn.datasets import load_iris

X, y = load_iris(return_X_y=True)
plda = PseudoLda(n_components=2)
plda.fit(X, y)
X_proj = plda.transform(X)
print(X_proj.shape)  # (n_samples, 2)
```

### PseudoPca: Fast PCA-like Projection

```python
from shaded.pseudo_pca import PseudoPca

ppca = PseudoPca(n_components=2)
ppca.fit(X)
X_proj = ppca.transform(X)
print(X_proj.shape)  # (n_samples, 2)
```

### PairwiseLda: LDA for All Class Pairs

```python
from shaded.pair_wise_lda import PairwiseLda

pwlda = PairwiseLda(n_components=2)
pwlda.fit(X, y)
X_proj = pwlda.transform(X)
print(X_proj.shape)
```

### Chained Spectral Projectors

Chain multiple projections (e.g., PCA followed by LDA):

```python
from shaded.chained_spectral_projector import GeneralProjectionLearner

chain = (
    {'type': 'pca', 'args': {'n_components': 3}},
    {'type': 'lda', 'args': {'n_components': 2}},
)
gpl = GeneralProjectionLearner(chain=chain)
X_proj = gpl.fit_transform(X, y)
print(X_proj.shape)  # (n_samples, 5)
```

### Band Projection Matrix

Create frequency band buckets and projection matrices:

```python
from shaded.band_projection_matrix import make_band_proj_matrix

proj_matrix = make_band_proj_matrix(n_buckets=5, n_freq=20)
print(proj_matrix.shape)  # (5, 20)
```

---

## API Overview

- `PseudoLda`: Fast LDA-like projection for well-separated clusters.
- `PseudoPca`: Fast PCA-like projection using random hyperplanes.
- `PairwiseLda`: LDA projections for all class pairs.
- `GeneralProjectionLearner`: Chain and compose projections (PCA, LDA, etc.).
- `band_projection_matrix`: Create frequency band buckets and projection matrices.
- `linalg_utils`: Linear algebra helpers (null space, projection, residue).

---

## Testing

Unit tests are provided for core linear algebra and projection utilities. To run tests:

```bash
pytest shaded/tests/
```

---

## License

[Specify your license here]

---

Let me know if you want to add more advanced examples or further API details!
