from lazylinop import LazyLinOp
from lazylinop.basicops import eye
import numpy as np


def diff(N, n: int = 1,
         prepend: int = 0, append: int = 0, backend="numpy"):
    """Returns a :class:`.LazyLinOp` ``L`` that calculates the n-th
    discrete difference of an input vector.

    Shape of ``L`` is $(M,~N)$ where $M = prepend + N + append - n$.

    Args:
        N: ``int``
            Size of the input.

        n : ``int``, optional
            The number of times values are differenced (default is 1).
            If zero, the input is returned as-is.

        prepend, append : ``int``, optional
            Prepend or append input vector with a number of zeros equals to
            the argument, prior to performing the difference.
            By default it is equal to 0.

        backend: ``str``, optional
            - ``'numpy'`` (default) uses ``numpy.diff``.
            - ``'lazylinop'`` uses Lazylinop composition.

    Returns:
        :class:`.LazyLinOp`

    .. seealso::
        `NumPy diff function <https://numpy.org/doc/stable/
        reference/generated/numpy.diff.html>`_.

    Examples:
        >>> import numpy as np
        >>> import lazylinop as lz
        >>> x = np.array([1, 2, 2, 4, 2, 2, 1])
        >>> D = diff(x.shape[0])
        >>> y = D @ x
        >>> np.allclose(np.array([1,  0,  2, -2,  0, -1]), y)
        True
    """

    if n < 0 or n >= N:
        raise Exception("n must be positive and lower than N,"
                        + "the size of the input")
    if prepend < 0 or append < 0:
        raise Exception("prepend/append must be positive")

    if n == 0:
        return eye(N)

    if backend == "numpy":
        out_size = N - n + prepend + append

        def _matmat(x):
            opts = {}
            if prepend > 0:
                opts["prepend"] = np.zeros((prepend, x.shape[1]),
                                           dtype=x.dtype)
            if append > 0:
                opts["append"] = np.zeros((append, x.shape[1]),
                                          dtype=x.dtype)
            return np.diff(x, n, axis=0, **opts)

        def _rmatmat(y):
            out = np.zeros((y.shape[0] + n, y.shape[1]), dtype=y.dtype)
            out[n:] = y
            for _ in range(n):
                out[:-1, :] = out[:-1, :] - out[1:, :]
            return out[prepend: y.shape[0] - append + n, :]

        return LazyLinOp(shape=(out_size, N), matmat=_matmat, rmatmat=_rmatmat)

    elif backend == "lazylinop":
        # from lazylinop import pad

        if n == 1:
            N_Op = N + prepend + append
            Op = -eye(N_Op - 1, N_Op) + eye(N_Op - 1, N_Op, k=1)
            if prepend > 0 or append > 0:
                # FIXME: use upstream lz.pad once
                # https://gitlab.inria.fr/faustgrp/lazylinop/-/issues/158
                # is fixed
                Op = Op @ eye(N + prepend + append, N, -prepend)
                # Op = Op @ pad(N, prepend, append)
            return Op
        else:
            return diff(N - 1 + prepend + append, n - 1) @ diff(
                N, 1, prepend=prepend, append=append
            )

    else:
        raise Exception("backend must be 'numpy' or 'lazylinop'")
