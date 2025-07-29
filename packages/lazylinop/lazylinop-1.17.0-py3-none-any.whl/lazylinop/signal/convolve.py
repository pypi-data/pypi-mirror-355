import numpy as np
import scipy as sp
import os
from os import environ
import sys
from lazylinop import LazyLinOp, mpad2
from lazylinop.basicops import block_diag, diag, eye
from lazylinop.signal import fft
from lazylinop.signal.utils import overlap_add
import warnings
from warnings import warn

sys.setrecursionlimit(100000)
warnings.simplefilter(action='always')


def _dims(N: int, K: int, mode: str):
    """Return length of the output as a function
    of the length of the input, of the length of kernel
    and of the convolution mode.

    Args:
        N: ``int``
            Size of the input array (if 1d, number of rows if 2d).
        K: ``int``
            Length of the kernel.
        mode: ``str``
            Convolution mode.

    Returns:
        ``int``
    """
    imode = 0 * int(mode == 'full') + 1 * int(mode == 'valid') + \
        2 * int(mode == 'same') + 3 * int(mode == 'circ')
    return np.array([N + K - 1,  # full
                     N - K + 1,  # valid
                     N,  # same
                     N  # circ
                     ],
                    dtype=np.int_)[imode]


def _rmode(mode: str):
    """Return adjoint convolution mode.

    Args:
        mode: ``str``
            Convolution mode.

    Returns:
        ``str``
    """
    return {'full': 'valid', 'valid': 'full',
            'same': 'same', 'circ': 'circ'}[mode]


def _is_cplx(t1, t2):
    return 'complex' in str(t1) or 'complex' in str(t2)


def convolve(N: int, filter: np.ndarray, mode: str = 'full',
             backend: str = 'scipy_convolve'):
    r"""
    Returns a :class:`.LazyLinOp` ``L`` for the 1d convolution of
    signal(s) of size ``N`` with a kernel ``filter``.

    Shape of ``L`` is $(M,~N)$. See ``mode`` for output size $M$.

    Args:
        N: ``int``
            Size of the signal to be convolved.

        filter: ``np.ndarray``
            Filter to be applied to the signal. ``filter`` must be a 1d-array.
        mode: ``str``, optional
            - ``'full'``: compute full convolution including at points of
              non-complete overlapping of inputs. Output size ``M`` is ``N +
              filter.size - 1``.
            - ``'valid'``: compute only fully overlapping part of the
              convolution. This is the 'full' center part of (output)
              size ``M = N - filter.size + 1`` (``filter.size <= N``
              must be satisfied).
            - ``'same'``: compute only the center part of ``'full'`` to
              obtain an output size ``M`` equal to the input size ``N``.
            - ``'circ'``: compute circular convolution (``filter.size <= N``
              must be satisfied). Output size ``M`` is ``N``.
        backend: ``str``, optional
            - ``'scipy_convolve'``: (default) encapsulate
              ``scipy.signal.convolve``.

              It uses internally the best SciPy backend between ``'fft'`` and
              ``'direct'`` (see `scipy.signal.choose_conv_method <https://
              docs.scipy.org/doc/scipy/reference/generated/scipy.signal.
              choose_conv_method.html#scipy.signal.choose_conv_method>`_).

            - ``'auto'``: use best ``backend`` available.

                - for ``mode='circ'`` use ``backend='fft'``.
                - for any other mode use ``backend='direct'``
                  if ``filter.size < log2(M)``,
                  ``backend='scipy_convolve'`` otherwise.

            - ``'direct'``: direct computation using nested for-loops with
              Numba and parallelization.
            - ``'fft'``: (only for ``mode='circ'``) compute circular
              convolution using SciPy FFT.
            - ``'toeplitz'``: encapsulate ``scipy.linalg.toeplitz`` if ``N <
              2048``, ``scipy.linalg.matmul_toeplitz`` otherwise.
            - ``'oa'``: use Lazylinop implementation of overlap-add backend.

    Returns:
        :class:`.LazyLinOp`

    Examples:
        >>> import numpy as np
        >>> import scipy.signal as sps
        >>> import lazylinop.signal as lzs
        >>> N = 1024
        >>> x = np.random.randn(N)
        >>> kernel = np.random.randn(32)
        >>> L = lzs.convolve(N, kernel)
        >>> c1 = L @ x
        >>> c2 = sps.convolve(x, kernel)
        >>> np.allclose(c1, c2)
        True
        >>> N = 32768
        >>> x = np.random.randn(N)
        >>> kernel = np.random.randn(48)
        >>> L = lzs.convolve(N, kernel, mode='circ', backend='fft')
        >>> c1 = L @ x
        >>> L = lzs.convolve(N, kernel, mode='circ', backend='direct')
        >>> c2 = L @ x
        >>> np.allclose(c1, c2)
        True

    .. seealso::
        - `SciPy convolve function <https://docs.scipy.org/doc/scipy/
          reference/generated/scipy.signal.convolve.html>`_,
        - `SciPy oaconvolve function <https://docs.scipy.org/doc/scipy/
          reference/generated/scipy.signal.oaconvolve.html>`_,
        - `Overlap-add method (wikipedia) <https://en.wikipedia.org/
          wiki/Overlap%E2%80%93add_method>`_,
        - `Circular convolution (wikipedia) <https://en.wikipedia.org/
          wiki/Circular_convolution>`_,
        - `SciPy correlate function <https://docs.scipy.org/doc/scipy/
          reference/generated/scipy.signal.correlate.html>`_,
        - `SciPy matmul_toeplitz function <https://docs.scipy.org/doc/
          scipy/reference/generated/
          scipy.linalg.matmul_toeplitz.html#scipy.linalg.matmul_toeplitz>`_.
    """
    return _convolve_helper(N, filter, mode, backend, None)


def _convolve_helper(N: int, filter: np.ndarray, mode: str = 'full',
                     backend: str = 'scipy_convolve', workers: int = None):
    r"""
    Returns a :class:`.LazyLinOp` for the 1d convolution of
    signal(s) of size ``N`` with a kernel ``filter``.

    See below, ``N`` and ``filter`` for input sizes.
    See ``mode`` for output size.

    Args:
        workers: ``int``, optional
            The number of threads used to parallelize
            ``backend='direct', 'toeplitz', 'scipy_convolve'`` using
            respectively Numba, NumPy and SciPy capabilities.
            Default is ``os.cpu_count()`` (number of CPU threads available).

            .. admonition:: Environment override

                ``workers`` can be overridden from the environment using
                ``NUMBA_NUM_THREADS`` for ``backend='direct'`` and
                ``OMP_NUM_THREADS`` for ``backend='toeplitz'``,
                ``'scipy_convolve'``.

    Returns:
        :class:`.LazyLinOp`

    Raises:
        TypeError
            N must be an int.
        ValueError
            size N < 0
        ValueError
            mode is not valid ('full' (default), 'valid', 'same' or 'circ').
        ValueError
            filter.size > N and mode='valid'
        ValueError
            filter.size > N and mode='circ'
        Exception
            filter must be 1d array.
        ValueError
            backend is not in:
            'auto',
            'direct',
            'toeplitz',
            'scipy_convolve',
            'oa',
            'fft',
        ValueError
            backend='fft' works only with mode='circ'.

    .. seealso::
        - `SciPy convolve function <https://docs.scipy.org/doc/scipy/
          reference/generated/scipy.signal.convolve.html>`_,
        - `SciPy oaconvolve function <https://docs.scipy.org/doc/scipy/
          reference/generated/scipy.signal.oaconvolve.html>`_,
        - `Overlap-add method <https://en.wikipedia.org/wiki/
          Overlap%E2%80%93add_method>`_,
        - `Circular convolution <https://en.wikipedia.org/wiki/
          Circular_convolution>`_,
        - `SciPy correlate function <https://docs.scipy.org/doc/scipy/
          reference/generated/scipy.signal.correlate.html>`_,
        - `SciPy matmul_toeplitz function <https://docs.scipy.org/doc/
          scipy/reference/generated/
          scipy.linalg.matmul_toeplitz.html#scipy.linalg.matmul_toeplitz>`_.
    """
    # never disable JIT except if env var NUMBA_DISABLE_JIT is used
    if 'NUMBA_DISABLE_JIT' in environ:
        disable_jit = int(environ['NUMBA_DISABLE_JIT'])
    else:
        disable_jit = 0

    if workers is None:
        workers = os.cpu_count()  # default

    if mode not in ['full', 'valid', 'same', 'circ']:
        raise ValueError("mode is not valid ('full' (default), 'valid', 'same'"
                         " or 'circ').")

    all_backend = [
        'auto',
        'direct',
        'toeplitz',
        'scipy_convolve',
        'oa',
        'fft'
    ]

    circbackend = [
        'auto',
        'direct',
        'fft'
    ]

    if mode == 'circ' and backend not in circbackend:
        raise ValueError("mode 'circ' expects backend" +
                         " to be in " + str(circbackend))

    if mode != 'circ' and backend == 'fft':
        raise ValueError("backend='fft' works only with mode='circ'.")

    if type(N) is not int:
        raise TypeError("N must be an int.")

    if N <= 0:
        raise ValueError("size N < 0")

    if len(filter.shape) >= 2:
        raise Exception("filter must be 1d array.")

    K = filter.shape[0]
    if K > N and mode == 'valid':
        raise ValueError("filter.size > N and mode='valid'")
    if K > N and mode == 'circ':
        raise ValueError("filter.size > N and mode='circ'")

    if mode == 'circ':
        if backend == 'auto':
            compute = 'circ.fft'
        else:
            compute = 'circ.' + backend
    else:
        if backend == 'auto':
            if K < np.log2(_dims(N, K, mode)):
                compute = 'direct'
            else:
                compute = 'scipy_convolve'
        else:
            compute = backend

    if compute == 'direct':
        try:
            import numba  # noqa: F401
        except ImportError:
            warn("Did not find Numba, switch to 'scipy_convolve'.")
            compute = 'scipy_convolve'

    # Check which backend is asked for
    if compute == 'direct':
        C = _direct(N, filter, mode, disable_jit, workers)
    elif compute == 'toeplitz':
        C = _toeplitz(N, filter, mode, workers)
    elif compute == 'scipy_convolve':
        C = _scipy_encapsulation(N, filter, mode, workers)
    elif compute == 'oa':
        C = _oaconvolve(N, filter, mode=mode, workers=workers)
    elif 'circ.' in compute:
        C = _circconvolve(N, filter,
                          backend.replace('circ.', ''), disable_jit, workers)
    else:
        raise ValueError("backend is not in " + str(all_backend))

    L = LazyLinOp(
        shape=C.shape,
        matmat=lambda x: (
            C @ x if _is_cplx(x.dtype, filter.dtype)
            else np.real(C @ x)
        ),
        rmatmat=lambda x: (
            C.H @ x if _is_cplx(x.dtype, filter.dtype)
            else np.real(C.H @ x)
        ),
    )
    # for callee information
    L.disable_jit = disable_jit
    return L


def _direct(N: int, filter: np.ndarray,
            mode: str = 'full', disable_jit: int = 0, workers=None):
    r"""Builds a :class:`.LazyLinOp` for the convolution of
    a signal of size ``N`` with a kernel ``filter``.
    If shape of the input array is ``(N, batch)``,
    return convolution per column.
    Function uses direct computation: nested for loops.
    You can switch on Numba jit and enable ``prange``.
    Larger the signal is better the performances are.
    Larger the batch size is better the performances are.
    Do not call ``_direct`` function outside
    of ``convolve`` function.

    Args:
        N: ``int``
            Length of the input.
        filter: ``np.ndarray``
            Kernel to convolve with the signal, shape is ``(K, )``.
        mode: ``str``, optional

            - 'full' computes convolution (input + padding).
            - 'valid' computes 'full' mode and extract centered output that
              does not depend on the padding.
            - 'same' computes 'full' mode and extract centered output that has
              the same shape that the input.
        disable_jit: ``int``, optional
            If 0 (default) enable Numba jit.
            It only matters for ``backend='direct'``.
            Be careful that ``backend='direct'`` is very slow
            when Numba jit is disabled.
            Prefix by ``NUMBA_NUM_THREADS=$t`` to launch ``t`` threads.

    Returns:
        :class:`.LazyLinOp`
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
        nb.config.THREADING_LAYER = 'omp'
        nb.config.DISABLE_JIT = disable_jit
        if workers is not None and 'NUMBA_NUM_THREADS' not in os.environ:
            nb.config.NUMBA_NUM_THREADS = workers
    except:
        pass

    K = filter.shape[0]
    M = (
        (N + K - 1) * int(mode == 'full') +
        (N - K + 1) * int(mode == 'valid') +
        N * int(mode == 'same')
    )
    P = (
        (N - K + 1) * int(mode == 'full') +
        (N + K - 1) * int(mode == 'valid') +
        N * int(mode == 'same')
    )
    start = (N + K - 1 - M) // 2
    rstart = (N + K - 1 - P) // 2

    @njit(parallel=True, cache=True)
    def _matmat(x, kernel):

        K = kernel.shape[0]
        batch_size = x.shape[1]
        y = np.full((M, batch_size),
                    0.0 * (kernel[0] * x[0, 0]))
        # y[n] = sum(h[k] * x[n - k], k, 0, K - 1)
        # n - k > 0 and n - k < len(x)
        for i in prange(start, start + M):
            # i - j >= 0
            # i - j < N
            for j in range(
                    min(max(0, i - N + 1), K),
                    min(K, i + 1)
            ):
                # NumPy (defaultly) uses row-major format
                for b in range(batch_size):
                    y[i - start, b] += kernel[j] * x[i - j, b]
        return y

    @njit(parallel=True, cache=True)
    def _rmatmat(x, kernel):

        K = kernel.shape[0]
        S, batch_size = x.shape
        y = np.full((N, batch_size), 0.0 * (kernel[0] * x[0, 0]))
        # y[n] = sum(h[k] * x[k + n], k, 0, K - 1)
        # k + n < len(x)
        for i in prange(rstart, rstart + N):
            for j in range(min(max(0, i - S + 1), K),
                           min(K, i + 1)):
                # NumPy (defaultly) uses row-major format
                for b in range(batch_size):
                    y[N + rstart - i - 1, b] += np.conjugate(
                        kernel[j]) * x[j - i + S - 1, b]
        return y

    return LazyLinOp(
        shape=(M, N),
        matmat=lambda x: _matmat(x, filter),
        rmatmat=lambda x: _rmatmat(x, filter)
    )


def _toeplitz(N: int, filter: np.ndarray, mode: str = 'full',
              workers: int = None):
    r"""Builds a :class:`.LazyLinOp` for the convolution of
    a signal of size ``N`` with a kernel ``filter``.
    If shape of the input array is ``(N, batch)``,
    return convolution per column.
    Function uses ``scipy.linalg.toeplitz`` or ``scipy.linalg.matmul_toeplitz``
    implementation to compute convolution.
    Do not call ``_toeplitz`` function outside
    of ``convolve`` function.

    Args:
        N: ``int``
            Length of the input.
        filter: ``np.ndarray``
            Kernel to convolve with the signal, shape is ``(K, )``.
        mode: ``str``, optional

            - 'full' computes convolution (input + padding).
            - 'valid' computes 'full' mode and extract centered output that
              does not depend on the padding.
            - 'same' computes 'full' mode and extract centered output that has
              the same shape that the input.
        workers:
            See convolve().
            Used only for matmul_toeplitz (if N > 2048).
            Can be overridden by OMP_NUM_THREADS environment variable.

    Returns:
        :class:`.LazyLinOp`
    """

    K = filter.shape[0]
    M = _dims(N, K, mode)
    i0 = (N + K - 1 - M) // 2

    if mode == 'full':
        # No need to slice rows
        c = np.pad(filter, (0, N - 1))
        r = np.pad([filter[0]], (0, N - 1))
    else:
        # Slice rows of the Toeplitz matrix
        if filter[i0:].shape[0] > M:
            # Handle the case such that kernel length
            # is bigger than signal length.
            c = np.copy(filter[i0:(i0 + M)])
        else:
            c = np.pad(filter[i0:], (0, M - (K - i0)))
        if filter[:(i0 + 1)].shape[0] > N:
            # Handle the case such that kernel length
            # is bigger than signal length.
            r = np.flip(filter[(i0 + 1 - N):(i0 + 1)])
        else:
            r = np.pad(np.flip(filter[:(i0 + 1)]), (0, N - (i0 + 1)))

    tmp = "OMP_NUM_THREADS"
    workers = (
        int(os.environ[tmp]) if tmp in os.environ.keys()
        else (-1 if workers is None else workers)
    )

    def _mat(c, r, x):
        if N < 2048:
            return sp.linalg.toeplitz(c, r) @ x
        else:
            return sp.linalg.matmul_toeplitz(
                (c, r), x,
                check_finite=False, workers=workers)

    # Convolution Toeplitz matrix is lower triangular,
    # therefore we have toeplitz(c, r).T = toeplitz(r, c)
    return LazyLinOp(
        shape=(_dims(N, K, mode), _dims(N, K, 'same')),
        matmat=lambda x: _mat(c, r, x),
        rmatmat=lambda x: _mat(r.conj(), c.conj(), x))


def _scipy_encapsulation(N: int, filter: np.ndarray, mode: str = 'full',
                         workers=None):
    r"""Builds a :class:`.LazyLinOp` for the convolution of
    a signal of size ``N`` with a kernel ``filter``.
    If shape of the input array is ``(N, batch)``,
    return convolution per column.
    Function uses encapsulation of ``scipy.signal.convolve``
    to compute convolution.
    Do not call ``_scipy_encapsulation`` function outside
    of ``convolve`` function.

    Args:
        N: ``int``
            Length of the input.
        filter: ``np.ndarray``
            Kernel to convolve with the signal, shape is ``(K, )``.
        mode: ``str``, optional

            - 'full' computes convolution (input + padding).
            - 'valid' computes 'full' mode and extract centered output that
              does not depend on the padding.
            - 'same' computes 'full' mode and extract centered output that has
              the same shape that the input.
        workers:
            See convolve().
            Can be overridden by OMP_NUM_THREADS environment variable.

    Returns:
        :class:`.LazyLinOp`
    """

    # Length of the output as a function of convolution mode
    K = filter.shape[0]
    tmp = "OMP_NUM_THREADS"
    workers = (
        int(os.environ[tmp]) if tmp in os.environ.keys()
        else (-1 if workers is None else workers)
    )

    # In order to avoid overhead, measure convolve duration
    # outside of `_matmat()` function.
    # It will only run during the creation of the `LazyLinOp()`.
    sp_best = sp.signal.choose_conv_method(
        np.arange(N), filter, mode=mode, measure=True)[0]

    def _matmat(x):
        # x is always 2d
        batch_size = x.shape[1]
        if batch_size > 1:
            if sp_best == 'fft':
                with sp.fft.set_workers(workers):
                    # scipy.signal.convolve does not handle batch.
                    # Therefore, we use our own fftconvolve implementation
                    # based on scipy.fft.fftn.
                    if 'complex' in str(x.dtype):
                        sp_fft = sp.fft.fftn
                        sp_ifft = sp.fft.ifftn
                    else:
                        sp_fft = sp.fft.rfftn
                        sp_ifft = sp.fft.irfftn
                    n = N + K - 1 if mode == 'full' else (
                        N if mode == 'same' else N - K + 1)
                    # Speed-up FFT using zero padding.
                    nn = sp.fft.next_fast_len(
                        N + K - 1,
                        real='complex' not in str(x.dtype))
                    x_ = sp_fft(x, s=(nn), axes=(0))
                    f_ = sp_fft(filter.reshape(-1, 1), s=(nn), axes=(0))
                    # Remove zero-padding (last elements) and
                    # extract convolution mode.
                    start = (N + K - 1 - n) // 2
                    return sp_ifft(x_ * f_, s=(nn),
                                   axes=(0))[start:(start + n), :]
            else:
                # If best is 'direct' method, we cannot
                # avoid a for loop.
                y = np.empty((_dims(N, K, mode), batch_size),
                             dtype=(x[0, 0] * filter[0]).dtype)
                for b in range(batch_size):
                    y[:, b] = sp.signal.convolve(x[:, b],
                                                 filter, mode=mode,
                                                 method='direct')
        else:
            with sp.fft.set_workers(workers):
                return sp.signal.convolve(x[:, 0],
                                          filter, mode=mode,
                                          method='auto').reshape(-1, 1)
        return y

    def _rmatmat(x):
        # x is always 2d
        batch_size = x.shape[1]
        y = np.empty((_dims(N, K, 'same'), batch_size),
                     dtype=(x[0, 0] * filter[0]).dtype)
        with sp.fft.set_workers(workers):
            for b in range(batch_size):
                y[:, b] = np.flip(
                    sp.signal.convolve(np.flip(x[:, b]),
                                       filter,
                                       mode=_rmode(mode),
                                       method='auto')
                )
        return y

    return LazyLinOp(
        shape=(_dims(N, K, mode), _dims(N, K, 'same')),
        matmat=lambda x: _matmat(x),
        rmatmat=lambda x: _rmatmat(x))


def _oaconvolve(N: int, filter: np.ndarray, mode: str = 'full',
                workers: int = None):
    """This function implements overlap-add backend for convolution.
    Builds a :class:`.LazyLinOp` for the convolution
    of a signal of length ``N`` with the kernel ``filter``.
    Do not call ``_oaconvolve`` function outside of ``convolve`` function.

    Args:
        N: ``int``
            Length of the input.
        filter: ``np.ndarray``
            Kernel to use for the convolution.
        mode: ``str``, optional

            - 'full' computes convolution (input + padding).
            - 'valid' computes 'full' mode and extract centered
              output that does not depend on the padding.
            - 'same' computes 'full' mode and extract centered
              output that has the same shape that the input.
        workers:
            see convolve().
            Can be overridden by OMP_NUM_THREADS environment variable.

    Returns:
        :class:`.LazyLinOp`
    """

    tmp = "OMP_NUM_THREADS"
    workers = (
        int(os.environ[tmp]) if tmp in os.environ.keys()
        else (os.cpu_count() if workers is None else workers)
    )

    # Size of the kernel
    K = filter.shape[0]
    # Size of the output (full mode)
    Y = N + K - 1

    # Block size B, number of blocks X = N / B
    B = K
    while B < min(N, K) or not (((B & (B - 1)) == 0) and B > 0):
        B += 1

    # Number of blocks
    step = B
    B *= 2
    R = N % step
    X = N // step + 1 if R > 0 else N // step

    # Create LazyLinOp C that will be applied to all the blocks.
    # Use mpad to pad each block.
    if N > (2 * K):
        # If the signal size is greater than twice
        # the size of the kernel use overlap-based convolution
        F = fft(B) * np.sqrt(B)
        D = diag(F @ eye(B, K, k=0) @ filter, k=0)
        G = (F.H / B) @ D @ F
        # block_diag(*[G] * X) is equivalent to kron(eye, G)
        C = overlap_add(G.shape[0] * X, B, overlap=B - step) \
            @ block_diag(*[G] * X) \
            @ mpad2(step, X, n=B - step)
        if (X * step) > N:
            C = C @ eye(X * step, N, k=0)
    else:
        # If the signal size is not greater than twice
        # the size of the kernel use FFT-based convolution
        F = fft(Y) * np.sqrt(Y)
        D = diag(F @ eye(Y, K, k=0) @ filter, k=0)
        C = (F.H / Y) @ D @ F @ eye(Y, N, k=0)

    # Convolution mode
    if mode == 'valid' or mode == 'same':
        if mode == 'valid':
            # Compute full mode, valid mode returns
            # elements that do not depend on the padding.
            extract = N - K + 1
        else:
            # Keep the middle of full mode (centered)
            # and returns the same size that the signal size.
            extract = N
        start = (Y - extract) // 2
    else:
        extract, start = Y, 0
    # Use eye operator to extract
    return eye(extract, C.shape[0], k=start) @ C


def _circconvolve(N: int, filter: np.ndarray,
                  backend: str = 'auto', disable_jit: int = 0,
                  workers: int = None):
    """Builds a :class:`.LazyLinOp` for the circular convolution.
    Do not call ``_circconvolve`` function outside of ``convolve`` function.

    Args:
        N: ``int``
            Length of the input.
        filter: ``np.ndarray``
            Kernel to use for the convolution.
        backend: ``str``, optional

            - 'auto' use best implementation.
            - 'direct' direct computation using
              nested for loops (Numba implementation).
              Larger the batch is better the performances are.
            - 'fft' use SciPy encapsulation of the FFT.
        disable_jit: int, optional
            If 0 (default) enable Numba jit.
        workers:
            see convolve().
            Used only if backend not 'direct' and filter shape smaller
            than log2(N).
            Can be overridden by OMP_NUM_THREADS environment variable.

    Returns:
        :class:`.LazyLinOp`
    """

    def njit(*args, **kwargs):
        def dummy(f):
            return f
        return dummy

    def prange(n):
        return range(n)

    tmp = backend
    try:
        import numba as nb
        from numba import njit, prange
        nb.config.THREADING_LAYER = 'omp'
        nb.config.DISABLE_JIT = disable_jit
        if workers is not None and 'NUMBA_NUM_THREADS' not in os.environ:
            nb.config.NUMBA_NUM_THREADS = workers
    except ImportError:
        if tmp == 'direct':
            warn("Did not find Numba, switch to fft.")
            tmp = 'fft'

    if tmp == 'direct' or (tmp == 'auto' and filter.shape[0] < np.log2(N)):

        @njit(parallel=True, cache=True)
        def _matmat(kernel, signal):
            K = kernel.shape[0]
            B = signal.shape[1]
            y = np.full((N, B), 0.0 * (kernel[0] * signal[0, 0]))
            # y[n] = sum(h[k] * s[n - k mod N], k, 0, K - 1)
            for i in prange(N):
                # Split the loop to avoid computation of ``np.mod``.
                for j in range(min(K, i + 1)):
                    # NumPy uses row-major format
                    for b in range(B):
                        y[i, b] += (
                            kernel[j] * signal[i - j, b]
                        )
                for j in range(i + 1, K, 1):
                    # NumPy uses row-major format
                    for b in range(B):
                        y[i, b] += (
                            kernel[j] * signal[N + i - j, b]
                        )
            return y

        @njit(parallel=True, cache=True)
        def _rmatmat(kernel, signal):
            K = kernel.shape[0]
            B = signal.shape[1]
            y = np.full((N, B), 0.0 * (kernel[0] * signal[0, 0]))
            # y[n] = sum(h[k] * s[k + n mod N], k, 0, K - 1)
            for i in prange(N):
                # Split the loop to avoid computation of ``np.mod``.
                for j in range(min(K, N - i)):
                    # NumPy uses row-major format
                    for b in range(B):
                        y[i, b] += (
                            np.conjugate(kernel[j]) * signal[i + j, b]
                        )
                for j in range(min(K, N - i), K, 1):
                    # NumPy uses row-major format
                    for b in range(B):
                        y[i, b] += (
                            np.conjugate(kernel[j]) * signal[i + j - N, b]
                        )
            return y

        return LazyLinOp(
            shape=(N, N),
            matmat=lambda x: _matmat(filter, x),
            rmatmat=lambda x: _rmatmat(filter, x)
        )
    else:
        key = "OMP_NUM_THREADS"
        workers = (
            int(os.environ[key]) if key in os.environ.keys()
            else (os.cpu_count() if workers is None else workers)
        )
        # Zero-pad the kernel
        pfilter = np.pad(filter, (0, N - filter.shape[0]),
                         mode='constant', constant_values=0.0)
        # Op = FFT^-1 @ diag(FFT(kernel)) @ FFT
        DFT = fft(N) * np.sqrt(N)
        D = diag(DFT @ pfilter, k=0)
        return (DFT / N).H @ D @ DFT


def _dsconvolve(in1: int, in2: np.ndarray, mode: str = 'full',
                offset: int = 0, every: int = 2, disable_jit: int = 0):
    """Creates convolution plus down-sampling lazy linear operator.
    If input is a 2d array shape=(in1, batch), return convolution per column.
    offset (0 or 1) argument determines the first element to compute while
    every argument determines distance between two elements (1 or 2).
    The ouput of convolution followed by down-sampling C @ x is equivalent
    to :code:`scipy.signal.convolve(x, in2, mode)[offset::every]`.

    Args:
        in1: int
            Length of the input.
        in2: np.ndarray
            1d kernel to convolve with the signal, shape is (K, ).
        mode: str, optional

            - 'full' computes convolution (input + padding).
            - 'valid' computes 'full' mode and extract centered output
              that does not depend on the padding.
            - 'same' computes 'full' mode and extract centered output
              that has the same shape that the input.
        offset: int, optional
            First element to keep (default is 0).
        every: int, optional
            Keep element every this number (default is 2).
        disable_jit: int, optional
            If 0 (default) enable Numba jit.

    Returns:
        LazyLinOp

    Examples:
        >>> import numpy as np
        >>> import scipy as sp
        >>> from lazylinop.signal.convolve import _dsconvolve
        >>> N = 1024
        >>> x = np.random.rand(N)
        >>> kernel = np.random.rand(32)
        >>> L = _dsconvolve(N, kernel, mode='same', offset=0, every=2)
        >>> c1 = L @ x
        >>> c2 = sp.signal.convolve(x, kernel, mode='same', method='auto')
        >>> np.allclose(c1, c2[0::2])
        True

    .. seealso::
        `SciPy convolve function <https://docs.scipy.org/doc/scipy/
        reference/generated/scipy.signal.convolve.html>`_,
        `SciPy correlate function <https://docs.scipy.org/doc/scipy/
        reference/generated/scipy.signal.correlate.html>`_.
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
        nb.config.THREADING_LAYER = 'omp'
        T = nb.config.NUMBA_NUM_THREADS
        nb.config.DISABLE_JIT = disable_jit
    except ImportError:
        warn("Did not find Numba.")
        T = 1

    if mode not in ['full', 'valid', 'same']:
        raise ValueError("mode is either 'full' (default), 'valid' or 'same'.")

    # Check if length of the input has been passed to the function
    if type(in1) is not int:
        raise Exception("Length of the input are expected (int).")

    if in2.ndim != 1:
        raise ValueError("Number of dimensions of the kernel must be 1.")
    if in1 <= 0:
        raise Exception("Negative input length.")

    K = in2.shape[0]

    if K > in1 and mode == 'valid':
        raise ValueError("Size of the kernel is greater than the size" +
                         " of the signal and mode is valid.")
    if offset != 0 and offset != 1:
        raise ValueError('offset must be either 0 or 1.')
    if every != 1 and every != 2:
        raise ValueError('every must be either 1 or 2.')

    # Length of the output as a function of convolution mode
    dims = np.array([in1 + K - 1, in1 - K + 1, in1, in1], dtype=np.int_)
    imode = (
        0 * int(mode == 'full') +
        1 * int(mode == 'valid') +
        2 * int(mode == 'same')
    )
    start = (dims[0] - dims[imode]) // 2 + offset
    end = min(dims[0], start + dims[imode] - offset)
    L = int(np.ceil((dims[imode] - offset) / every))
    if L <= 0:
        raise Exception("mode, offset and every are incompatibles" +
                        " with kernel and signal sizes.")

    def _matmat(x, kernel, T):
        # x is always 2d
        batch_size = x.shape[1]
        perT = int(np.ceil((dims[0] - start) / T))
        use_parallel_1d = bool((perT * K) > 100000)
        use_parallel_2d = bool((perT * K * batch_size) > 100000)

        # Because of Numba split 1d and 2d
        @njit(parallel=use_parallel_1d, cache=True)
        def _1d(x, kernel):
            _T = T
            if not use_parallel_1d:
                _T = 1
                perT = dims[0] - start
            y = np.full(L, 0.0 * (kernel[0] * x[0]))
            for t in prange(_T):
                for i in range(
                        start + t * perT,
                        min(end, start + (t + 1) * perT)):
                    # Down-sampling
                    if ((i - start) % every) == 0:
                        for j in range(max(0, i - in1 + 1), min(K, i + 1)):
                            y[(i - start) // every] += kernel[j] * x[i - j]
            return y

        @njit(parallel=use_parallel_2d, cache=True)
        def _2d(x, kernel):
            _T = T
            if not use_parallel_2d:
                _T = 1
                perT = dims[0] - start
            y = np.full((L, batch_size), 0.0 * (kernel[0] * x[0, 0]))
            for t in prange(_T):
                for i in range(
                        start + t * perT,
                        min(end, start + (t + 1) * perT)):
                    # Down-sampling
                    if ((i - start) % every) == 0:
                        for j in range(max(0, i - in1 + 1), min(K, i + 1)):
                            # NumPy uses row-major format
                            for b in range(batch_size):
                                y[(i - start) // every,
                                  b] += kernel[j] * x[i - j, b]
            return y

        return _1d(x.ravel(), kernel).reshape(-1, 1) if x.shape[1] == 1 else _2d(x, kernel)

    def _rmatmat(x, kernel, T):
        # x is always 2d
        batch_size = x.shape[1]
        rperT = int(np.ceil(dims[2] / T))
        use_rparallel_1d = bool((rperT * K) > 100000)
        use_rparallel_2d = bool((rperT * K * batch_size) > 100000)

        # Because of Numba split 1d and 2d
        @njit(parallel=use_rparallel_1d, cache=True)
        def _1d(x, kernel):
            _T = T
            if not use_rparallel_1d:
                _T = 1
                rperT = dims[2]
            a = 0 if imode == 0 and offset == 0 else 1
            y = np.full(dims[2], 0.0 * (kernel[0] * x[0]))
            for t in prange(_T):
                for i in range(t * rperT, min(dims[2], (t + 1) * rperT)):
                    if every == 2:
                        jstart = (i - a * start) - (i - a * start) // every
                    elif every == 1:
                        jstart = i - a * start
                    else:
                        pass
                    for j in range(L):
                        if j < jstart:
                            continue
                        if every == 2:
                            k = (i - a * start) % 2 + (j - jstart) * every
                        elif every == 1:
                            k = j - jstart
                        else:
                            pass
                        if k < K:
                            y[i] += kernel[k] * x[j]
            return y

        @njit(parallel=use_rparallel_2d, cache=True)
        def _2d(x, kernel):
            _T = T
            if not use_rparallel_2d:
                _T = 1
                rperT = dims[2]
            a = 0 if imode == 0 and offset == 0 else 1
            y = np.full((dims[2], batch_size), 0.0 * (kernel[0] * x[0, 0]))
            for t in prange(_T):
                for i in range(t * rperT, min(dims[2], (t + 1) * rperT)):
                    if every == 2:
                        jstart = (i - a * start) - (i - a * start) // every
                    elif every == 1:
                        jstart = i - a * start
                    else:
                        pass
                    for j in range(L):
                        if j < jstart:
                            continue
                        if every == 2:
                            k = (i - a * start) % 2 + (j - jstart) * every
                        elif every == 1:
                            k = j - jstart
                        else:
                            pass
                        if k < K:
                            # NumPy uses row-major format
                            for b in range(batch_size):
                                y[i, b] += kernel[k] * x[j, b]
            return y

        return _1d(x.ravel(), kernel).reshape(-1, 1) if x.shape[1] == 1 else _2d(x, kernel)

    return LazyLinOp(
        shape=(L, dims[2]),
        matmat=lambda x: _matmat(x, in2, T),
        rmatmat=lambda x: _rmatmat(x, in2, T)
    )


# if __name__ == '__main__':
#     import doctest
#     doctest.testmod()
