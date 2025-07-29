import numpy as np
import scipy as sp
from lazylinop import aslazylinop, LazyLinOp
from lazylinop.basicops import kron
from lazylinop.wip.signal import is_power_of_two
import os
import sys
import warnings
sys.setrecursionlimit(100000)


def fwht(N: int, backend: str = 'auto'):
    return wht(N, backend)


def wht(N: int, backend: str = 'auto'):
    r"""
    Returns a :class:`.LazyLinOp` ```L`` for the
    Fast-Walsh-Hadamard-Transform (WHT).

    Shape of ``L`` is $(N,~N)$.
    :octicon:`alert-fill;1em;sd-text-danger` N must be a power of 2.

    ``L`` is orthonormal and *symmetric* and
    the inverse WHT operator is ``L.T = L``.

    ``y = L @ x`` returns a vector of size $N$ that satisfies
    ``y = scipy.linalg.hadamard(N) @ x / np.sqrt(N)``.
    The implementation is however more efficient for large values of $N$.

    Of note, we provide an alias ``fwht`` of the ``wht`` function.

    Args:
        N: ``int``
            Size of the input (N > 0).
        backend: ``str``, optional
            Either 'auto' (default), 'direct', 'kronecker',
            'pyfaust' or 'scipy'.

            - 'auto' uses 'pyfaust' for ``N<=32768``, 'direct' otherwise.
              Of note, this condition depends on your hardware. It may change
              in the near future.
            - 'direct' uses ``N * log(N)`` algorithm and Numba jit
              to compute FWHT.
              Because of Numba jit, computation of the first ``F @ x``
              will be longer than the next one.

              - Larger the size ``N`` of the input is better
                the performances are.
              - Larger the batch is better the performances are.
            - 'kronecker' uses kron from lazylinop to compute FWHT.
            - 'pyfaust' (default) uses ``wht`` from pyfaust.
            - 'scipy' uses ``scipy.linalg.hadamard`` matrix.
              It could be memory consuming for large ``N``.

    Returns:
        LazyLinOp

    Examples:
        >>> import numpy as np
        >>> import scipy.linalg as spl
        >>> import lazylinop.signal as lzs
        >>> N = 16
        >>> x = np.random.randn(N)
        >>> H = lzs.fwht(N)
        >>> y = np.sqrt(N) * (H @ x)
        >>> np.allclose(y, spl.hadamard(N) @ x)
        True
        >>> np.allclose(H.T @ (H @ x), x)
        True
        >>> X = np.random.randn(N, 3)
        >>> Y = np.sqrt(N) * (H @ X)
        >>> np.allclose(Y, spl.hadamard(N) @ X)
        True

    .. seealso::
        - `Hadamard transform (Wikipedia) <https://en.wikipedia.org/
          wiki/Hadamard_transform>`_,
        - `scipy.linalg.hadamard <https://docs.scipy.org/doc/scipy/reference/
          generated/scipy.linalg.hadamard.html>`_,
        - `pyfaust wht <https://faustgrp.gitlabpages.inria.fr/faust/last-doc/
          html/namespacepyfaust.html#a35453cb41a399968807f4483a331669b>`_.
    """
    return _fwht_helper(N, backend)


def _fwht_helper(N: int, backend: str = 'auto', workers: int = None):
    r"""Builds a :class:`.LazyLinOp` Fast-Walsh-Hadamard-Transform.
    The size of the signal has to be a power of two greater than 1.
    We choose to normalize the :class:`.LazyLinOp` ``H`` of the FWHT,
    such that we have ``(H.T @ H).toarray()`` equal to the identity.
    In others words ``np.allclose(H.T @ (H @ x), x)`` returns ``True``.
    :octicon:`alert-fill;1em;sd-text-danger` Unlike ``fwht``,
    ``scipy.linalg.hadamard(N)`` function does not divide the Hadamard
    matrix by the square-root of the matrix order ``np.sqrt(N)``.

    Args:
        N: ``int``
            Size the input array.
        backend: ``str``, optional
            It can be 'auto' (default), 'direct', 'kronecker',
            'pyfaust' or 'scipy'.

            - 'auto' uses 'pyfaust' for ``N<=32768``, 'direct' otherwise.
              Of note, this condition depends on your hardware. It may change
              in the near future.
            - 'direct' uses ``N * log(N)`` algorithm and Numba jit
              to compute FWHT.
              Because of Numba jit, computation of the first ``F @ x``
              will be longer than the next one.

              - Larger the size ``N`` of the input is better
                the performances are.
              - Larger the batch is better the performances are.
            - 'kronecker' uses kron from lazylinop to compute FWHT.
            - 'pyfaust' (default) uses ``wht`` from pyfaust.
            - 'scipy' uses ``scipy.linalg.hadamard`` matrix.
              It could be memory consuming for large ``N``.
        workers: ``int``, optional
            Number of threads Numba launches.
            Default (None) is ``numba.config.NUMBA_NUM_THREADS``.
            ``workers`` has not effect if ``backend!='direct'``.
            :octicon:`alert-fill;1em;sd-text-danger` Be aware that
            input size ``N`` and batch size must be large enough
            to overload number of threads Numba launches.
            If it is not the case, please choose ``workers=1``.

    Returns:
        LazyLinOp

    Raises:
        ValueError
            The size of the signal must be a power of two,
            greater or equal to two.
        ValueError
            backend argument expects either 'auto', 'direct',
            'kronecker', 'pyfaust' or 'scipy'.
    """

    if not is_power_of_two(N) or N < 2:
        raise ValueError("The size of the signal must be a power of two," +
                         " greater or equal to two.")

    M = 32768

    new_backend = backend
    if new_backend == 'direct' or (new_backend == 'auto' and N > M):
        try:
            import numba as nb
            from numba import njit, prange
            if workers is None or type(workers) is not int:
                _T = nb.config.NUMBA_NUM_THREADS
            else:
                _T = workers
                nb.set_num_threads(_T)
            if "NUMBA_DISABLE_JIT" in os.environ.keys():
                nb.config.DISABLE_JIT = os.environ["NUMBA_DISABLE_JIT"]
            else:
                nb.config.DISABLE_JIT = 0
            nb.config.THREADING_LAYER = 'omp'
        except ImportError:
            warnings.warn("Did not find Numba, switch to 'pyfaust' backend.")
            new_backend = 'pyfaust'

    if new_backend == 'pyfaust' or (new_backend == 'auto' and N <= M):
        try:
            from pyfaust import wht
        except ImportError:
            warnings.warn("Did not find pyfaust," +
                          " switch to 'kronecker' backend.")
            new_backend = 'kronecker'

    if new_backend == 'scipy':
        return LazyLinOp(
            shape=(N, N),
            matmat=lambda x: (sp.linalg.hadamard(N) @ x) / np.sqrt(N),
            rmatmat=lambda x: (sp.linalg.hadamard(N) @ x) / np.sqrt(N),
            dtype='float'
        )
    elif new_backend == 'pyfaust' or (new_backend == 'auto' and N <= M):
        return aslazylinop(wht(N, normed=False)) / np.sqrt(N)
    elif new_backend == 'kronecker':
        H1 = np.array([[1.0, 1.0], [1.0, -1.0]])
        D = int(np.log2(N))
        if D == 1:
            return aslazylinop(H1) / np.sqrt(N)
        elif D == 2:
            return kron(H1, H1) / np.sqrt(N)
        else:
            Hd = kron(H1, H1)
            for d in range(1, D - 1):
                Hd = kron(H1, Hd)
            return Hd / np.sqrt(N)
    elif new_backend == 'direct' or (new_backend == 'auto' and N > M):

        @njit(parallel=True, cache=False)
        def _matmat(x):
            # x is always 2d
            batch_size = x.shape[1]
            _S = _T if N > 2 and nb.config.DISABLE_JIT == 0 else 1
            tmp1 = np.empty(_S, dtype=x.dtype)
            tmp2 = np.empty(_S, dtype=x.dtype)
            y = np.empty((N, batch_size), dtype=x.dtype)
            H, D = 1, int(np.floor(np.log2(N)))
            for d in range(D):
                sub = 2 * H * int(np.ceil(N / (_S * 2 * H)))
                subH = int(np.ceil(H / _S))
                if d == 0:
                    # Init y that is empty (d=0, H=1 and j=i)
                    for s in prange(_S):
                        for i in range(s * sub, min(N, (s + 1) * sub), 2 * H):
                            # NumPy uses row-major format
                            for b in range(batch_size):
                                tmp1[s] = x[i, b]
                                tmp2[s] = x[i + 1, b]
                                y[i, b] = tmp1[s] + tmp2[s]
                                y[i + 1, b] = tmp1[s] - tmp2[s]
                elif d == (D - 1):
                    # Last level
                    for i in range(0, N, 2 * H):
                        for s in prange(_S):
                            for j in range(i + s * subH,
                                           i + min(H, (s + 1) * subH), 1):
                                # NumPy uses row-major format
                                for b in range(batch_size):
                                    tmp1[s] = y[j, b]
                                    tmp2[s] = y[j + H, b]
                                    y[j, b] += tmp2[s]
                                    y[j + H, b] = tmp1[s] - tmp2[s]
                else:
                    for s in prange(_S):
                        for i in range(s * sub,
                                       min(N, (s + 1) * sub), 2 * H):
                            for j in range(i, i + H, 1):
                                # NumPy uses row-major format
                                for b in range(batch_size):
                                    tmp1[s] = y[j, b]
                                    tmp2[s] = y[j + H, b]
                                    y[j, b] += tmp2[s]
                                    y[j + H, b] = tmp1[s] - tmp2[s]
                H *= 2
            return y / np.sqrt(N)

        return LazyLinOp(
            shape=(N, N),
            matmat=lambda x: _matmat(x),
            rmatmat=lambda x: _matmat(x),
            dtype='float'
        )
    else:
        raise ValueError("backend argument expects either 'direct', \
        'kronecker', 'pyfaust' or 'scipy'.")


# if __name__ == '__main__':
#     import doctest
#     doctest.testmod()
