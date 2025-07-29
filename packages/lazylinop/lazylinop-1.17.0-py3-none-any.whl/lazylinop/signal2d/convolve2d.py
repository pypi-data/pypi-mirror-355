import numpy as np
import scipy as sp
from lazylinop import LazyLinOp
from lazylinop.basicops import add, eye, kron
from lazylinop.signal import convolve
from lazylinop.signal.utils import chunk
from lazylinop.signal2d import padder2d, colvec, uncolvec
import sys
sys.setrecursionlimit(100000)


def convolve2d(in_shape: tuple, filter: np.ndarray,
               mode: str = 'full', boundary: str = 'fill',
               backend: str = 'auto'):
    r"""
    Returns a :class:`.LazyLinOp` ``L`` for the 2D convolution of
    a 2D signal of shape ``in_shape=(M, N)``
    (provided in flattened version) with a 2D ``filter``.

    Shape of ``L`` is $(M'N',~MN)$ where ``(M, N)=in_shape`` and
    ``out_shape=(M', N')`` depends on ``mode``.
    After applying the operator as ``y = L @ colvec(X)``, a 2D output
    can be obtained via ``uncolvec(y, out_shape)``.

    Args:
        in_shape: ``tuple``,
            Shape $(M,~N)$ of the signal to convolve with kernel.
        filter: ``np.ndarray``
            Kernel to use for the convolution, shape is $(K,~L)$.
        mode: ``str``, optional
            - ``'full'``: compute full convolution including at points of
              non-complete overlapping of inputs (default).
              Yields ``out_shape=(M', N')`` with ``M'=M + K - 1`` and
              ``N'=N + L - 1``.
            - ``'valid'``: compute only fully overlapping part of the
              convolution. This is the 'full' center part of (output) shape
              ``(M - K + 1, N - L + 1)``
              (``K <= M`` and ``L <= N`` must be satisfied).
              Yields ``out_shape=(M', N')`` with ``M' = M - K + 1`` and
              ``N' = N - L + 1``.
            - ``'same'``: compute only the center part of ``'full'`` to
              obtain an output size ``M`` equal to the input size ``N``.
              Yields ``out_shape=(M', N')`` with ``M' = M`` and ``N' = N``.
        boundary: ``str``, optional
            - ``'fill'`` pads input array with zeros (default).
            - ``'wrap'`` periodic boundary conditions.
            - ``'symm'`` symmetrical boundary conditions.
        backend: ``str``, optional
            - ``'auto'`` to use the best backend according to the kernel and
              input array dimensions.
            - ``'scipy encapsulation'`` use scipy.signal.convolve2d as a
              lazy linear operator.
            - ``'lazylinop'`` use the fact that 2d convolution can be written
              as a sum of Kronecker product between :class:`.LazyLinOp` ``eye``
              and :class:`.LazyLinOp` ``convolve``.
            - ``'scipy toeplitz'`` to use lazy encapsulation of Scipy
              implementation of Toeplitz matrix.
            - ``'scipy fft'`` to use Fast-Fourier-Transform
              to compute convolution.

    Returns:
        :class:`.LazyLinOp`

    Examples:
        >>> from lazylinop.signal2d import convolve2d, colvec, uncolvec
        >>> import scipy as sp
        >>> X = np.random.randn(6, 6)
        >>> H = np.random.randn(3, 3)
        >>> L = convolve2d(X.shape, H, mode='same')
        >>> y1 = uncolvec(L @ colvec(X), X.shape)
        >>> y2 = sp.signal.convolve2d(X, H, mode='same')
        >>> np.allclose(y1, y2)
        True

    .. seealso::
        `SciPy convolve2d function <https://docs.scipy.org/doc/scipy/
        reference/generated/scipy.signal.convolve2d.html>`_
    """
    if boundary not in ['fill', 'wrap', 'symm']:
        raise ValueError("boundary is either 'fill' (default) " +
                         ", 'wrap' or 'symm'")

    if type(in_shape) is tuple:
        if len(in_shape) != 2:
            raise Exception("in_shape expects tuple (M, N).")
        M, N = in_shape[0], in_shape[1]
    else:
        raise Exception("in_shape expects tuple (M, N).")

    if M <= 0 or N <= 0:
        raise ValueError("zero or negative dimension is not allowed.")
    K, L = filter.shape
    if (K > M or L > N) and mode == 'valid':
        raise Exception("Size of the kernel is greater than the size" +
                        " of the image (mode is valid).")
    if K <= 0 or L <= 0:
        raise ValueError("Negative dimension value is not allowed.")

    if backend == 'auto':
        compute = 'scipy fft' if max(K, L) >= 32 else 'lazylinop'
    else:
        compute = backend

    if compute == 'scipy encapsulation' and (boundary == 'wrap'
                                             or boundary == 'symm'):
        raise Exception("scipy encapsulation backend has no" +
                        " implementation of wrap and symm boundaries.")

    # boundary conditions
    if boundary == 'fill' or compute == 'scipy encapsulation':
        # SciPy encapsulation uses boundary argument of SciPy function.
        B = 1
    else:
        if K > M or L > N:
            B = 1 + 2 * 2 * max(max(0, int(np.ceil((K - M) / M))),
                                int(np.ceil((L - N) / N)))
        else:
            # Add one input on both side of each axis.
            B = 3
    hB = (B - 1) // 2
    # hB = B - 1

    # shape of the output image (full mode)
    # it takes into account the boundary conditions
    P, Q = B * M + K - 1, B * N + L - 1

    # length of the output as a function of convolution mode
    xdim = {}
    xdim['full'] = B * M + K - 1
    xdim['valid'] = B * M - K + 1
    xdim['same'] = B * M
    ydim = {}
    ydim['full'] = B * N + L - 1
    ydim['valid'] = B * N - L + 1
    ydim['same'] = B * N

    imode = (
        0 * int(mode == 'full') + 1 * int(mode == 'valid') +
        2 * int(mode == 'same') + 3 * int(mode == 'circ')
    )
    rmode = {}
    rmode['full'] = 'valid'
    rmode['valid'] = 'full'
    rmode['same'] = 'same'
    xy = {}
    xy['full'] = (M + K - 1) * (N + L - 1)
    xy['valid'] = (M - K + 1) * (N - L + 1)
    xy['same'] = M * N

    if mode != 'full' and mode != 'valid' and mode != 'same':
        raise ValueError("mode is either 'full' (default), 'valid' or 'same'.")

    if compute == 'scipy encapsulation':
        # correlate2d is the adjoint operator of convolve2d
        def _matmat(x):
            # x is always 2d
            batch_size = x.shape[1]
            # use Dask ?
            y = np.empty((xdim[mode] * ydim[mode], batch_size),
                         dtype=(x[0, 0] * filter[0, 0]).dtype)
            for b in range(batch_size):
                y[:, b] = colvec(sp.signal.convolve2d(
                    uncolvec(x[:, b], (xdim['same'], ydim['same'])),
                    filter, mode=mode, boundary=boundary))
            return y

        def _rmatmat(x):
            # x is always 2d
            batch_size = x.shape[1]
            # use Dask ?
            y = np.empty((xdim['same'] * ydim['same'], batch_size),
                         dtype=(x[0, 0] * filter[0, 0]).dtype)
            for b in range(batch_size):
                y[:, b] = colvec(sp.signal.correlate2d(
                    uncolvec(x[:, b], (xdim[mode], ydim[mode])),
                    filter, mode=rmode[mode], boundary=boundary))
            return y
        C = LazyLinOp(
            shape=(xdim[mode] * ydim[mode], xdim['same'] * ydim['same']),
            matmat=lambda x: _matmat(x),
            rmatmat=lambda x: _rmatmat(x)
        )
    elif compute == 'scipy toeplitz' or compute == 'lazylinop' or \
         compute == 'scipy fft' or compute == 'auto':
        if compute == 'scipy fft' or compute == 'auto':
            tmp = 'scipy_convolve'
        elif compute == 'scipy toeplitz':
            tmp = 'toeplitz'
        else:
            tmp = 'direct'
        # Write 2d convolution as a sum of Kronecker products:
        # input * kernel = sum(kron(convolve_i, E_i), i, 1, K) where
        # E_i is an eye matrix eye(P, M, k=-i).
        # Kronecker product trick: vec(A @ X @ B) = kron(B^T, A) @ vec(X).
        Ops = [None] * K
        for i in range(K):
            Ops[i] = kron(
                convolve(B * N, filter[i, :], backend=tmp, mode='full'),
                eye(xdim['full'], xdim['same'], k=-i)
            )
        C = add(*Ops)
        # Add boundary conditions.
        C = C @ padder2d((M, N),
                         ((M * hB, M * hB), (N * hB, N * hB)),
                         mode=boundary)
        # Extract center of the output.
        if mode == 'full':
            r, c = M + K - 1, N + L - 1
        elif mode == 'same':
            # keep middle of the full mode
            # number of rows to extract is M (centered)
            # number of columns to extract is N (centered)
            # if boundary conditions extract image from the center
            r, c = M, N
        else:
            # compute full mode and extract what we need
            # number of rows to extract is M - K + 1 (centered)
            # number of columns to extract is N - L + 1 (centered)
            # if boundary conditions extract image from the center
            r, c = M - K + 1, N - L + 1
        if P > r or Q > c:
            C = chunk(C.shape[0], r, hop=P,
                      start=P * ((Q - c) // 2) + (P - r) // 2,
                      stop=P * ((Q - c) // 2) + P * c - P + (P - r) // 2 + r + 1) @ C
    else:
        raise ValueError('Unknown backend.')

    # return lazy linear operator
    ckernel = 'complex' in str(filter.dtype)
    # Because of LazyLinOp dft we have to use np.real().
    return LazyLinOp(
        shape=C.shape,
        matmat=lambda x: (
            C @ x if ckernel or 'complex' in str(x.dtype)
            else np.real(C @ x)
        ),
        rmatmat=lambda x: (
            C.H @ x if ckernel or 'complex' in str(x.dtype)
            else np.real(C.H @ x)
        )
    )


# if __name__ == '__main__':
#     import doctest
#     doctest.testmod()
