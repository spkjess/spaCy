from typing import Tuple, Callable
from thinc.api import Model
from thinc.types import Ragged, Ints1d


def extract_spans() -> Model[Tuple[Ragged, Ragged], Ragged]:
    """Extract spans from a sequence of source arrays, as specified by an array
    of (start, end) indices. The output is a ragged array of the
    extracted spans.
    """
    return Model(
        "extract_spans", forward, layers=[], refs={}, attrs={}, dims={}, init=init
    )


def init(model, X=None, Y=None):
    pass


def forward(
    model: Model, source_spans: Tuple[Ragged, Ragged], is_train: bool
) -> Tuple[Ragged, Callable]:
    """Get subsequences from source vectors."""
    ops = model.ops
    X, spans = source_spans
    assert spans.dataXd.ndim == 2
    indices = _get_span_indices(ops, spans, X.lengths)
    Y = Ragged(X.dataXd[indices], spans.dataXd[:, 1] - spans.dataXd[:, 0])
    x_shape = X.dataXd.shape
    x_lengths = X.lengths

    def backprop_windows(dY: Ragged) -> Tuple[Ragged, Ragged]:
        dX = Ragged(ops.alloc2f(*x_shape), x_lengths)
        ops.scatter_add(dX.dataXd, indices, dY.dataXd)
        return (dX, spans)

    return Y, backprop_windows


def _get_span_indices(ops, spans: Ragged, lengths: Ints1d) -> Ints1d:
    """Construct a flat array that has the indices we want to extract from the
    source data. For instance, if we want the spans (5, 9), (8, 10) the
    indices will be [5, 6, 7, 8, 8, 9].
    """
    indices = []
    offset = 0
    for i, length in enumerate(lengths):
        spans_i = spans[i].dataXd + offset
        for j in range(spans_i.shape[0]):
            indices.append(ops.xp.arange(spans_i[j, 0], spans_i[j, 1]))
        offset += length
    return ops.flatten(indices)
