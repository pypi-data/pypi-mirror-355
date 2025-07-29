from lazylinop import LazyLinOp
from lazylinop.basicops import ones, zeros
import numpy as np
from warnings import warn


def cumsum(N: int):
    """
    Returns a :class:`.LazyLinOp` ``L`` associated to the
    cumulative sum of an input of size ``N``.

    Shape of ``L`` is $(N,~N)$.

    Args:
        N: ``int``
            Size of the input array.

    Returns:
        :class:`.LazyLinOp`

    Examples:
        >>> import numpy as np
        >>> import lazylinop as lz
        >>> N = 4
        >>> x = np.arange(N)
        >>> x
        array([0, 1, 2, 3])
        >>> L = lz.basicops.tri(N)
        >>> y = L @ x
        >>> y_ = np.cumsum(x)
        >>> np.allclose(y, y_)
        True
    """
    return tri(N, M=N, k=0)


def tri(N: int, M: int = None, k: int = 0, disable_jit: bool = False):
    """
    Returns a :class:`.LazyLinOp` ``L`` associated to a matrix such
    that its lower triangular part is filled with ones.
    Above given diagonal ``k``, matrix is filled with zeros.

    Shape of ``L`` is $(N,~M)$ where $M = N$ by default.

    :class:`.LazyLinOp` ``L = tri(N, k=0)`` corresponds to a lower
    triangular matrix of shape $(N,~N)$ and its transposition ``L.T``
    corresponds to an upper triangular matrix.

    Args:
        N: ``int``
            Number of rows.
        M: ``int``, optional
            Number of columns.
            By default ``M`` is equal to ``N``.
        k: ``int``, optional
            The sub-diagonal at and below which the matrix
            is filled with ones (the rest being filled by zeroes).

            - $k<0$ below the main diagonal.
            - $k=0$ corresponds to the main diagonal (default).
              When called with $k=0$ (default), the resulting
              operator ``L`` performs a cumulative sum.
            - $k>0$ above the main diagonal.

    Returns:
        :class:`.LazyLinOp`

    Examples:
        >>> import numpy as np
        >>> import lazylinop as lz
        >>> N = 4
        >>> x = np.arange(N)
        >>> x
        array([0, 1, 2, 3])
        >>> L = lz.basicops.tri(N)
        >>> y = L @ x
        >>> y_ = np.cumsum(x)
        >>> np.allclose(y, y_)
        True

    .. seealso::
        - `NumPy tri function <https://numpy.org/doc/
          stable/reference/generated/numpy.tri.html>`_,
        - `NumPy cumsum function <https://numpy.org/doc/stable/
          reference/generated/numpy.cumsum.html>`_.
    """

    def njit(*args, **kwargs):
        def dummy(f):
            return f
        return dummy

    def prange(n):
        return range(n)

    try:
        import numba as nb
        from numba import njit, prange
        nb.config.THREADING_LAYER = "omp"
        T = nb.config.NUMBA_NUM_THREADS
        nb.config.DISABLE_JIT = disable_jit
    except ImportError:
        warn("Did not find Numba.")
        T = 1

    P = N if M is None else M

    if N <= 0 or P <= 0:
        raise ValueError("N and M must be > 0.")

    if k < 0 and -k >= N:
        return zeros((N, P))

    if k > 0 and k >= P:
        return ones((N, P))

    @njit(cache=True)
    def _matmat(x):
        batch_size = x.shape[1]
        y = np.zeros((N, batch_size), dtype=x.dtype)
        for b in range(batch_size):
            if k == 0:
                for i in range(N):
                    for j in range(min(i + 1, P)):
                        y[i, b] += x[j, b]
            elif k < 0:
                for i in range(-k, N, 1):
                    for j in range(min(i + 1 + k, P)):
                        y[i, b] += x[j, b]
            else:
                for i in range(N):
                    for j in range(min(P, i + 1 + k)):
                        y[i, b] += x[j, b]
        return y

    @njit(cache=True)
    def _rmatmat(x):
        batch_size = x.shape[1]
        y = np.zeros((P, batch_size), dtype=x.dtype)
        for b in range(batch_size):
            if k == 0:
                for i in range(P):
                    for j in range(i, N, 1):
                        y[i, b] += x[j, b]
            elif k < 0:
                for i in range(P):
                    for j in range(i - k, N):
                        y[i, b] += x[j, b]
            else:
                for i in range(P):
                    for j in range(max(0, i - k), N, 1):
                        y[i, b] += x[j, b]
        return y

    return LazyLinOp(
        shape=(N, P),
        matmat=lambda x: _matmat(x),
        rmatmat=lambda x: _rmatmat(x)
    )
