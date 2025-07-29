from lazylinop import LazyLinOp
import numpy as np


def zeros(shape):
    """
    Returns a zero :py:class:`LazyLinOp`.

    .. admonition:: Fixed memory cost
        :class: admonition note

        Whatever is the shape of the ``zeros``, it has the same memory cost.

    Args:
        shape: (``tuple[int, int]``)
             The operator shape.

    Example:
        >>> import numpy as np
        >>> import lazylinop as lz
        >>> Lz = lz.zeros((10, 12))
        >>> x = np.random.rand(12)
        >>> Lz @ x
        array([0., 0., 0., 0., 0., 0., 0., 0., 0., 0.])

    .. seealso:: `numpy.zeros <https://numpy.org/doc/stable/reference/
        generated/numpy.zeros.html>`_.
    """

    def _matmat(x, shape):
        # shape[1] == x.shape[0] (because of LazyLinOp)
        # x.ndim == 2
        return np.zeros((shape[0], x.shape[1]), dtype=x.dtype)
    return LazyLinOp(shape, matmat=lambda x:
                     _matmat(x, shape),
                     rmatmat=lambda x: _matmat(x, (shape[1],
                                                   shape[0])))
