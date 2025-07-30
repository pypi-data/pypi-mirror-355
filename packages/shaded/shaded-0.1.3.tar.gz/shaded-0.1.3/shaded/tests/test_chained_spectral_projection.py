from shaded.chained_spectral_projector import GeneralProjectionLearner
from sklearn.datasets import load_iris
from sklearn.metrics.pairwise import euclidean_distances
import numpy as np
import pytest

iris = load_iris()
X = iris.data
y = iris.target


def mean_distances(X):
    distances = euclidean_distances(X)
    len_X = len(X)
    dim_factor = 1 / (2 ** 1 / len_X)
    return dim_factor * np.sum(distances) / (len_X ** 2 - len_X)


def mean_distances_per_group(X, y):
    classes = set(y)
    mean_group_dist = []
    for class_ in classes:
        mean_group_dist.append(mean_distances(X[y == class_]))
    return np.mean(mean_group_dist)


# TODO: Repair test
@pytest.mark.skip(reason='Need to understand this before repairing')
@pytest.mark.parametrize(
    'X, y, short_chain, long_chain',
    [
        (
            X,
            y,
            ({'type': 'lda', 'args': {'n_components': 2}},),
            (
                {'type': 'lda', 'args': {'n_components': 2}},
                {'type': 'lda', 'args': {'n_components': 1}},
            ),
        )
    ],
)
def test_GeneralProjectionLearner_lda(X, y, short_chain, long_chain):
    """
    Mostly a smoke test, with the addition of testing that the mean of the intra-group distances decreases after
    projection using lda but increases with the number of components used in lda. The means are corrected for the
    numbers of dimensions following the length of the diagonal of a simplex
    """
    # find initial mean distances:
    mean_distance = mean_distances_per_group(X, y)

    # get the mean group distances for the short chain
    gpl = GeneralProjectionLearner(chain=short_chain)
    short_projected_X = gpl.fit_transform(X, y)
    short_mean = mean_distances_per_group(short_projected_X, y)

    # get the mean group distances for the long chain
    gpl = GeneralProjectionLearner(chain=long_chain)
    long_projected_X = gpl.fit_transform(X, y)
    long_mean = mean_distances_per_group(long_projected_X, y)

    assert (
        mean_distance > long_mean > short_mean
    ), 'Something is not right about the mean distances in the projected space'


# TODO: Repair test
@pytest.mark.skip(reason='Need to understand this before repairing')
def test_general_projection_learner():
    # PCA's components seems to be orthonormal
    from shaded.chained_spectral_projector import GeneralProjectionLearner
    from sklearn.datasets import load_iris

    #
    # data = load_iris()
    # X = data['data']
    # y = data['target']

    # chain = ({'type': 'pca', 'args': {'n_components': 1}}, {'type': 'pca', 'args': {'n_components': 1}})
    #
    # gpl = GeneralProjectionLearner(chain=chain)
    # XX = gpl.fit_transform(X=X, y=y, ortho=True)
    # XXX = gpl.project(X)
    # XXXX = gpl.space_residue(X)
    #
    # from oplot.plot_data_set import scatter_and_color_according_to_y
    #
    # print(gpl.scalings)
    # scatter_and_color_according_to_y(XX, y)
    # scatter_and_color_according_to_y(XXX, y)
    # scatter_and_color_according_to_y(XXXX, y)

    chain = ({'type': 'log_spaced', 'args': {'n_components': 8, 'chunk_size': 64}},)
    X = np.random.random((100, 33))
    # X = None
    gpl = GeneralProjectionLearner(chain=chain)
    gpl.fit(X=X, ortho=False)

    # print(gpl.scalings)
