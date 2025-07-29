from lazylinop.basicops import diag, eye, kron
from lazylinop.basicops import hstack, vstack
from lazylinop.basicops import anti_eye
from lazylinop.signal import dct
from lazylinop.signal.utils import chunk
import numpy as np
import scipy as sp
import sys
sys.setrecursionlimit(100000)


def _helper(N, backend: str = 'scipy'):

    if (N % 4) != 0:
        raise Exception("N must be a multiple of 4.")

    H = N // 2
    Q = H // 2

    # Extract first sequence (see References [1]).
    V = -vstack(
        (
            anti_eye(Q, Q) @ eye(Q, N, k=H),
            eye(Q, N, k=3 * Q)
        )
    )
    # Compute the sum of the first half with the second one.
    H1 = hstack((eye(Q, Q), eye(Q, Q))) @ V
    # Extract second sequence (see References [1]).
    H2 = vstack(
        (
            eye(Q, N),
            -anti_eye(Q, Q) @ eye(Q, N, k=Q)
        )
    )
    # Compute the sum of the first half with the second one.
    H2 = hstack((eye(Q, Q), eye(Q, Q))) @ H2
    # Compute two DCT IV and subtract the two results (see Ref [1]).
    return dct(H, 4, backend=backend) @ vstack((H1, H2))  # / np.sqrt(2.0)


def mdct(N, window=('vorbis', 128),
         backend: str = 'scipy'):
    r"""
    Returns a :class:`.LazyLinOp` ``L`` for the
    Modified Direct Cosine Transform (MDCT).

    Shape of ``L`` is $(M,~N)$ with $M=n\frac{W}{2}$.

    $n$ is the number of chunks and $W$ is the window size.

    Our implementation matches the one from TensorFlow,
    ``L @ x`` where ``L = mdct(N, window=('vorbis', 128))``
    is equivalent to:

    .. code-block:: python3

        import tensorflow as tf
        tf.signal.mdct(x,
                       frame_length=128,
                       window_fn=tf.signal.vorbis_window,
                       norm='ortho')

    If we consider MDCT using a rectangular window with
    a scale $\frac{1}{\sqrt{2}}$, ``L = mdct(N, window=('None', N))``,
    ``X = L @ x`` yiels a vector ``X`` of size $H=\frac{N}{2}$ such that:

    .. math::

        \begin{equation}
        X_k=\frac{1}{\sqrt{H}}\sum_{n=0}^{N-1}x_n\cos\left(\frac{\pi}{H}\left(n+\frac{1}{2}+\frac{H}{2}\right)\left(k+\frac{1}{2}\right)\right)
        \end{equation}

    ``y = L.T @ X`` yields a vector ``y`` of size $N$ such that:

    .. math::

        \begin{equation}
        y_n=\frac{1}{\sqrt{H}}\sum_{k=0}^{H-1}X_k\cos\left(\frac{\pi}{H}\left(n+\frac{1}{2}+\frac{H}{2}\right)\left(k+\frac{1}{2}\right)\right)
        \end{equation}

    The operator ``L`` is rectangular and is not left invertible.
    It is however right-invertible as ``L @ L.T = Id``.
    Thus, ``L.T`` can be used as a right-inverse.

    After removing some details the code looks like:

    .. code-block:: python3

        # Consecutive windows are slided by hop samples.
        hop = win_size // 2
        # Number of chunks.
        n = 1 + (N - win_size) // hop
        # Lazy linear operator that extracts and
        # concatenates chunks from a signal of length N.
        G = chunk(N, win_size, hop)

    and using the `mixed Kronecker product property <https://en.wikipedia.org/
    wiki/Kronecker_product>`_
    $(I^T\otimes A)\mathtt{vec}(X)=\mathtt{vec}(AXI)=\mathtt{vec}(AX)$:

    .. code-block:: python3

        K = kron(eye(n), _helper(win_size, backend) @ diag(win))
        L = K @ G

    where ``_helper(...)`` encapsulates underlying implementation
    using DCT of type IV (see Ref [1] for more details).

    The function provides two backends: SciPy and Lazylinop for
    the underlying computation of the DCT of type IV.

    Args:
        N: ``int``
            Length of the input array.
        window: ``(str, int)`` or ``(str, int, float)``, optional
            Window, a tuple ``(name: str, win_size: int)``
            or ``(name: str, win_size: int, beta: float)``.
            Window size must be a mutliple of 4.
            Default is ``('vorbis', 128)``.
            ``beta`` has no effect excepts
            for ``'kaiser_bessel_derived'`` window.
            Possible windows are:

            - ``'None'`` corresponds to a rectangular window
              with a scale $\frac{1}{\sqrt{2}}$.
            - ``'kaiser_bessel_derived'``
              see `scipy.signal.window.kaiser_bessel_derived <https://
              docs.scipy.org/doc/scipy/reference/generated/
              scipy.signal.windows.kaiser_bessel_derived.html>`_
              for more details.
            - ``'vorbis'`` (default) or ``'sin'``
              see `<https://en.wikipedia.org/wiki/
              Modified_discrete_cosine_transform>`_ for more details.
        backend: str, optional
            - ``'scipy'`` (default) uses ``scipy.fft.dct`` encapsulation
              for the underlying computation of the DCT of type IV.
            - ``'lazylinop'`` uses pre-built Lazylinop operators
              (Lazylinop :func:`.dct`, :func:`eye`, :func:`kron`,
              :func:`.vstack` etc.) to build the pipeline
              that will compute the MDCT and the underlying
              DCT of type IV.

    Returns:
        :class:`.LazyLinOp`

    Example:
        >>> from lazylinop.signal import mdct
        >>> import numpy as np
        >>> x = np.random.randn(64)
        >>> # MDCT with a rectangular window
        >>> # of size equal to the size of the input.
        >>> L = mdct(64, ('None', 64))
        >>> y = L @ x
        >>> y.shape[0] == 32
        True
        >>> x_ = L.T @ y
        >>> x_.shape[0] == 64
        True

    References:
        - [1] Xuancheng Shao, Steven G. Johnson, Type-IV DCT, DST, and MDCT
          algorithms with reduced numbers of arithmetic operations,
          Signal Processing, Volume 88, Issue 6, 2008, Pages 1313-1326,
          ISSN 0165-1684, https://doi.org/10.1016/j.sigpro.2007.11.024.

    .. seealso::
        - `MDCT (Wikipedia) <https://en.wikipedia.org/wiki/
          Modified_discrete_cosine_transform>`_,
        - `Type-IV DCT, DST, and MDCT algorithms with reduced
          numbers of arithmetic operations <https://www.sciencedirect.com/
          science/article/pii/S0165168407003829?via%3Dihub>`_,
        - `SMAGT/MDCT <https://github.com/smagt/mdct>`_,
        - `MDCT.jl <https://github.com/stevengj/
          MDCT.jl/blob/master/src/MDCT.jl>`_,
        - `Nils Werner <https://github.com/nils-werner/mdct/blob/
          master/mdct/fast/transforms.py>`_,
        - `TensorFlow MDCT <https://www.tensorflow.org/api_docs/
          python/tf/signal/mdct>`_,
        - :func:`dct`,
        - :func:`imdct`.
    """

    msg = "window must be a tuple (str, int) or (str, int, float)."
    if isinstance(window, tuple):
        if not (isinstance(window[0], str) and
                isinstance(window[1], int)):
            raise Exception(msg)
        if window[0] == 'kaiser_bessel_derived':
            if not (len(window) == 3 and isinstance(window[2], float)):
                raise Exception(msg)
            win = sp.signal.windows.kaiser_bessel_derived(
                window[1], window[2])
        elif window[0] == 'vorbis':
            win = np.sin(
                0.5 * np.pi * np.sin(
                    (np.pi / window[1]) * (np.arange(window[1]) + 0.5)) ** 2)
        elif window[0] == 'sin':
            win = np.sin((np.pi / window[1]) * (np.arange(window[1]) + 0.5))
        elif window[0] == 'None':
            win = np.full(window[1], 1.0 / np.sqrt(2.0))
        else:
            raise ValueError("window name must be either" +
                             " kaiser_bessel_derived," +
                             " vorbis, sin or None.")
        win_size = win.shape[0]
    else:
        raise Exception(msg)

    if win_size < 1:
        raise ValueError("win_size expects value greater than 0.")
    if win_size > N:
        raise ValueError(f"win_size={win_size} is greater than"
                         + f" input length N={N}.")
    if (win_size % 4) != 0:
        raise ValueError(f"win_size={win_size} is not a multiple of 4.")

    if N == win_size:
        return _helper(N, backend) @ diag(win)
    else:
        # Consecutive windows are slided by hop samples.
        hop = win_size // 2
        # Number of chunks.
        n = 1 + (N - win_size) // hop
        # Lazy linear operator that extracts and
        # concatenates chunks from a signal of length N.
        G = chunk(N, win_size, hop)
        # Apply windowing and MDCT per chunk.
        S = kron(eye(n), _helper(win_size, backend) @ diag(win))
        return S @ G
