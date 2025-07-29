from warnings import warn

try:
    import torch

    found_pytorch = True
except ImportError:
    warn("Did not find PyTorch, therefore use NumPy/SciPy.")
    found_pytorch = False
try:
    from einops import rearrange

    found_einops = True
except ImportError:
    warn("Did not find einops, therefore use NumPy.")
    found_einops = False
from lazylinop.butterfly.GB_utils import (
    partial_prod_deformable_butterfly_params, Factor)
import numpy as np
from scipy.sparse.linalg import svds
import os


if "GB_DISABLE_EINOPS" in dict(os.environ).keys():
    found_einops = os.environ["GB_DISABLE_EINOPS"] == 0
    if not found_einops:
        print("Disable einops.")


def low_rank_project(M, rank: int = 1, backend: str = 'scipy'):
    """Return low rank approximation by batch SVD.

    Args:
        M:
            A tensor of order 4, performing svd on the two last axis.
        rank: ``int``, optional
            Desired rank (default is 1).
        backend: ``str``, optional
            Use numpy, pytorch or scipy (default) to compute
            SVD and QR decompositions.
            Of note, ``backend='scipy'`` uses partial SVD
            ``scipy.sparse.linalg.svds``.

    Returns:
        U and Vh (``tuple``).

    References:
        - `NumPy SVD <https://numpy.org/doc/stable/reference/
          generated/numpy.linalg.svd.html>`_,
        - `PyTorch SVD <https://pytorch.org/docs/stable/
          generated/torch.linalg.svd.html>`_.
    """
    if backend == 'pytorch' and found_pytorch:
        U, S, Vh = torch.linalg.svd(M, full_matrices=False)
        S_sqrt = S[..., :rank].sqrt()
        shape = S_sqrt.size()
        if found_einops:
            U = U[..., :rank] * rearrange(S_sqrt, "... rank -> ... 1 rank")
            Vh = rearrange(
                S_sqrt, "... rank -> ... rank 1") * Vh[..., :rank, :]
        else:
            U = U[..., :rank] * S_sqrt.reshape(shape[0], shape[1], 1, shape[2])
            Vh = (
                S_sqrt.reshape(shape[0], shape[1], shape[2], 1)
                * Vh[..., :rank, :]
            )
    else:
        if backend == 'numpy':
            U, S, Vh = np.linalg.svd(M, full_matrices=False)
            # print('here', M.shape)
            # print('    ', U.shape, U[..., :rank].shape)
            # print('    ', S.shape, np.sqrt(S[..., :rank]).shape)
            # print('    ', Vh.shape, Vh[..., :rank, :].shape)
        elif backend == 'scipy':
            a, b, m, n = M.shape
            for i in range(a):
                for j in range(b):
                    if rank >= (min(m, n) - 1):
                        # According to
                        # https://docs.scipy.org/doc/scipy/reference/sparse.linalg.svds-propack.html
                        # we must have 1 <= k <= min(M, N) for solver='propack',
                        # min(M, N) - 1 otherwize.
                        u, s, vh = np.linalg.svd(M[i, j, :, :], full_matrices=False)
                        # u, s, vh = svds(M[i, j, :, :], k=rank, solver='arpack')
                        # u, s, vh = svds(M[i, j, :, :], k=rank, solver='lobpcg')
                        # u, s, vh = svds(M[i, j, :, :], k=rank, solver='propack')
                    else:
                        u, s, vh = svds(M[i, j, :, :], k=rank)
                    if i == 0 and j == 0:
                        U = np.empty((a, b, *u.shape), dtype=u.dtype)
                        S = np.empty((a, b, s.shape[0]), dtype=s.dtype)
                        Vh = np.empty((a, b, *vh.shape), dtype=vh.dtype)
                        # print('sub ', M[i, j, :, :].shape)
                        # print('    ', u.shape, U.shape)
                        # print('    ', s.shape, S.shape)
                        # print('    ', vh.shape, Vh.shape)
                    np.copyto(U[i, j, :, :], u[..., :rank])
                    np.copyto(S[i, j, :], s[..., :rank])
                    np.copyto(Vh[i, j, :, :], vh[..., :rank, :])
        else:
            raise Exception("backend must be either 'numpy', 'pytorch' or 'scipy'.")
        S_sqrt = np.sqrt(S[..., :rank])
        shape = S_sqrt.shape
        if found_einops:
            U = U[..., :rank] * rearrange(S_sqrt, "... rank -> ... 1 rank")
            Vh = rearrange(S_sqrt, "... rank -> ... rank 1") * Vh[..., :rank, :]
        else:
            U = U[..., :rank] * S_sqrt.reshape(shape[0], shape[1], 1, shape[2])
            Vh = S_sqrt.reshape(shape[0], shape[1], shape[2], 1) * Vh[..., :rank, :]
    return U, Vh


# def torch_svd(A, rank):
#     """
#     Return low rank approximation by finding eigenvalues
#     of a symmetric matrix.
#     Good when one size of a matrix is small.
#     Input:
#     A: a tensor of order 4, performing svd on the two last axis
#     rank: desired rank
#     """
#     if A.dtype == torch.complex64 or A.dtype == torch.complex128:
#         B = torch.matmul(A, A.mH)
#     else:
#         B = torch.matmul(A, A.transpose(-1, -2))

#     sq_S, U = torch.linalg.eigh(B)
#     # print(sq_S[..., -(rank+1):])
#     U = U[..., -rank:]
#     if A.dtype == torch.complex64 or A.dtype == torch.complex128:
#         Vh = torch.matmul(U.mH, A)
#     else:
#         Vh = torch.matmul(U.transpose(-1, -2), A)

#     # print(torch.linalg.norm(torch.matmul(U, Vh) - A))
#     return U, Vh


def dense_to_pre_low_rank_projection(matrix, b2, c1, backend: str = 'numpy'):
    """Reshape a twiddle to be ready to factorized.

    Args:
        matrix: ``np.ndarray`` or ``torch.tensor``.
            Twiddle.
        b2: ``int``
            Decomposition of the third dimension.
        c1: ``int``
            Decomposition of the fourth dimension.
        backend: ``str``, optional
            Use numpy (default) or pytorch to compute
            SVD and QR decompositions.

    Returns:
        Reshaped twiddle (``np.ndarray`` or ``torch.tensor``).
    """
    if found_einops:
        return rearrange(
            matrix, "a d (b1 b2) (c1 c2) -> (a c1) (b2 d) b1 c2", b2=b2, c1=c1
        )
    else:
        if backend == 'pytorch' and found_pytorch:
            a, d, b, c = matrix.size()
        else:
            a, d, b, c = matrix.shape
        b1 = b // b2
        c2 = c // c1
        return (
            matrix.reshape(a, d, b1, b2, c)
            .reshape(a, d, b1, b2, c1, c2)
            .swapaxes(2, 4)
            .swapaxes(1, 2)
            .swapaxes(2, 3)
            .reshape(a * c1, b2, d, b1, c2)
            .reshape(a * c1, b2 * d, b1, c2)
        )


def left_to_twiddle(left, c1):
    """Reshape left twiddle.

    Args:
        left: ``np.ndarray`` or ``torch.tensor``.
            Left twiddle.
        c1: ``int``
            Decomposition of the first dimension.

    Returns:
        Reshaped left twiddle (``np.ndarray`` or ``torch.tensor``).
    """
    if found_einops:
        return rearrange(left, "(a c1) d b q -> a d b (c1 q)", c1=c1)
    else:
        tmp, d, b, q = left.shape
        a = tmp // c1
        return (
            left.reshape(a, c1, d, b, q)
            .swapaxes(1, 2)
            .swapaxes(2, 3)
            .reshape(a, d, b, c1 * q)
        )


def right_to_twiddle(right, b2):
    """Reshape right twiddle.

    Args:
        right: ``np.ndarray`` or ``torch.tensor``.
            Left twiddle.
        b2: ``int``
            Decomposition of the second dimension.

    Returns:
        Reshaped right twiddle (``np.ndarray`` or ``torch.tensor``).
    """
    if found_einops:
        return rearrange(right, "a (b2 d) b c -> a d (b b2) c", b2=b2)
    else:
        a, tmp, b, c = right.shape
        d = tmp // b2
        return (
            right.reshape(a, b2, d, b, c)
            .swapaxes(1, 2)
            .swapaxes(2, 3)
            .reshape(a, d, b * b2, c)
        )


def gbf_normalization(l_twiddle, r_twiddle, l_param, r_param,
                      type: str = 'left', backend: str = 'numpy'):
    """Performing pairwise normalization using QR factorization.

    Args:
        l_twiddle: ``np.ndarray`` or ``torch.tensor``
            Left factor.
        r_twiddle: ``np.ndarray`` or ``torch.tensor``
            Right factor.
        l_param: ``tuple``
            Left GB parameter.
        r_twiddle: ``tuple``
            Right GB parameter.
        type: ``str``, optional
            - left -> normalized column left factor (default),
            - right -> normalized row right factor.
        backend: ``str``, optional
            Use ``'numpy'`` (default) or ``'pytorch'``
            to compute SVD and QR decompositions.

    Returns:
        Two new factors with one of them being
        column (row) normalized (``tuple``).
    """
    a1, b1, c1, d1, p1, q1 = l_param
    a2, b2, c2, d2, p2, q2 = r_param
    if found_einops:
        l_twiddle = rearrange(
            l_twiddle, "a1 d1 b1 (c1 q1) -> (a1 c1) d1 b1 q1", c1=c1
        )
        r_twiddle = rearrange(
            r_twiddle, "a2 d2 (p2 b2) c2 -> a2 (b2 d2) p2 c2", b2=b2
        )
    else:
        a1, d1, b1, tmp = l_twiddle.shape
        q1 = tmp // c1
        l_twiddle = (
            l_twiddle.reshape(a1, d1, b1, c1, q1)
            .swapaxes(2, 3)
            .swapaxes(1, 2)
            .reshape(a1 * c1, d1, b1, q1)
        )
        a2, d2, tmp, c2 = r_twiddle.shape
        p2 = tmp // b2
        r_twiddle = (
            r_twiddle.reshape(a2, d2, p2, b2, c2)
            .swapaxes(2, 3)
            .swapaxes(1, 2)
            .reshape(a2, b2 * d2, p2, c2)
        )
    if type == "left":
        if backend == 'pytorch' and found_pytorch:
            l_twiddle, m_twiddle = torch.linalg.qr(l_twiddle)
            r_twiddle = torch.matmul(m_twiddle, r_twiddle)
        else:
            l_twiddle, m_twiddle = np.linalg.qr(l_twiddle)
            r_twiddle = m_twiddle @ r_twiddle
        if found_einops:
            l_twiddle = rearrange(
                l_twiddle, "(a1 c1) d1 b1 q1 -> a1 d1 b1 (c1 q1)", c1=c1
            )
            r_twiddle = rearrange(
                r_twiddle, "a2 (b2 d2) p2 c2 -> a2 d2 (p2 b2) c2", b2=b2
            )
        else:
            tmp, d1, b1, q1 = l_twiddle.shape
            a1 = tmp // c1
            l_twiddle = (
                l_twiddle.reshape(a1, c1, d1, b1, q1)
                .swapaxes(1, 2)
                .swapaxes(2, 3)
                .reshape(a1, d1, b1, c1 * q1)
            )
            a2, tmp, p2, c2 = r_twiddle.shape
            d2 = tmp // b2
            r_twiddle = (
                r_twiddle.reshape(a2, b2, d2, p2, c2)
                .swapaxes(1, 2)
                .swapaxes(2, 3)
                .reshape(a2, d2, p2 * b2, c2)
            )
    else:
        if backend == 'pytorch' and found_pytorch:
            l_twiddle_tp = r_twiddle.permute(0, 1, 3, 2)
            r_twiddle_tp = l_twiddle.permute(0, 1, 3, 2)
            l_twiddle_tp, m_twiddle_tp = torch.linalg.qr(l_twiddle_tp)
            r_twiddle_tp = torch.matmul(m_twiddle_tp, r_twiddle_tp)
        else:
            l_twiddle_tp = r_twiddle.swapaxes(3, 2)
            r_twiddle_tp = l_twiddle.swapaxes(3, 2)
            l_twiddle_tp, m_twiddle_tp = np.linalg.qr(l_twiddle_tp)
            r_twiddle_tp = m_twiddle_tp @ r_twiddle_tp
        if found_einops:
            l_twiddle = rearrange(
                r_twiddle_tp, "(a1 c1) d1 q1 b1 -> a1 d1 b1 (c1 q1)", c1=c1
            )
            r_twiddle = rearrange(
                l_twiddle_tp, "a2 (b2 d2) c2 p2 -> a2 d2 (p2 b2) c2", b2=b2
            )
        else:
            tmp, d1, q1, b1 = r_twiddle_tp.shape
            a1 = tmp // c1
            l_twiddle = (
                r_twiddle_tp.reshape(a1, c1, d1, q1, b1)
                .swapaxes(1, 4)
                .swapaxes(1, 2)
                .swapaxes(3, 4)
                .reshape(a1, d1, b1, c1 * q1)
            )
            a2, tmp, c2, p2 = l_twiddle_tp.shape
            d2 = tmp // b2
            r_twiddle = (
                l_twiddle_tp.reshape(a2, b2, d2, c2, p2)
                .swapaxes(1, 2)
                .swapaxes(3, 4)
                .swapaxes(2, 3)
                .reshape(a2, d2, p2 * b2, c2)
            )
    return l_twiddle, r_twiddle


def intermediate_factorization(
    start,
    middle,
    end,
    gb_params,
    target,
    normalized_type: str = "L",
    track_epsilon: bool = False,
    backend: str = 'numpy'
):
    """ Performing one level of hierarchical factorization.

    Args:
        start: ``int``
            Start of the initial interval.
        end: ``int``
            End of the initial interval.
        middle: ``int``
            The separation of the interval start - end.
        gb_params: ``tuple``
            Parameters for butterfly factorizations
        target:
            The target factors.
        normalized_type: ``str``, optional
            Not important for now.
        track_epsilon: ``bool``, optional
            Defaut is False: do not track epsilon.
        backend: ``str``, optional
            Use numpy (default) or pytorch to compute
            SVD and QR decompositions.

    Returns:
        Two factors (start - mid) and (mid + 1 - end) respecting
        the supports, epsilon (``tuple``).
    """
    param = partial_prod_deformable_butterfly_params(gb_params, start, end)
    param_left = partial_prod_deformable_butterfly_params(
        gb_params, start, middle
    )
    param_right = partial_prod_deformable_butterfly_params(
        gb_params, middle + 1, end
    )
    if backend == 'pytorch' and found_pytorch:
        assert target.size() == (
            param[0],
            param[3],
            param[1] * param[4],
            param[2] * param[5],
        )
    else:
        assert target.shape == (
            param[0],
            param[3],
            param[1] * param[4],
            param[2] * param[5],
        )

    # Reshape the target twiddle
    target = dense_to_pre_low_rank_projection(
        target, param_right[1], param_left[2], backend=backend
    )

    # Compute batch SVD
    l_factor, r_factor = low_rank_project(
        target, rank=param_left[-1], backend=backend
    )
    if track_epsilon:
        # ...
        if backend == 'pytorch' and found_pytorch:
            low_rank_errors = torch.linalg.norm(
                target - torch.matmul(l_factor, r_factor), dim=(-1, -2)
            )
            norms = torch.linalg.norm(target, dim=(-1, -2))
        else:
            low_rank_errors = np.linalg.norm(
                target - l_factor @ r_factor, axis=(-1, -2)
            )
            norms = np.linalg.norm(target, axis=(-1, -2))
        relative_error = low_rank_errors / norms
        if backend == 'pytorch' and found_pytorch:
            epsilon = torch.max(relative_error)
        else:
            epsilon = np.max(relative_error)
    else:
        epsilon = None

        # return l_factor, r_factor, low_rank_errors
    # l_factor, r_factor = torch_svd(target, rank = param_left[-1])

    # print("Size l_factor: ", l_factor.size())
    # print("Size r_factor: ", r_factor.size())
    # Reshape the factor twiddle
    l_factor = left_to_twiddle(l_factor, param_left[2])

    # print(r_factor.size())
    r_factor = right_to_twiddle(r_factor, param_right[1])

    # if not track_epsilon:
    #     return l_factor, r_factor
    return l_factor, r_factor, epsilon


def GBfactorize(
    matrix,
    gb_params,
    orders,
    normalize: bool = True,
    normalized_type: str = "L",
    track_epsilon: bool = False,
    backend: str = 'numpy',
):
    """Return list of factors corresponding to the
    factorization of the matrix.

    Args:
        matrix: ``np.ndarray`` or ``torch.tensor``
            Target matrix that will be factorized.
        gb_params: ``tuple``
            The set of parameters describing the
            parameterization of GB factors.
        orders:
            A permutation describing the order of factorization
        normalize: ``bool``, optional
            Normalize (default).
        normalized_type: ``str``, optional
            L is default.
        track_epsilon: ``bool``, optional
            Do not return epsilon (default).
        backend: ``str``, optional
            Use numpy (default) or pytorch to compute
            SVD and QR decompositions.

    Returns:
        A list of GB factors approximating the target
        matrix (list, epsilon if ``track_epsilon == True``).
    """
    result = [Factor(0, len(gb_params) - 1, matrix)]
    max_epsilon = 0
    for i in orders:
        # Search for the corresponding intermediate factors
        if normalize:
            for index in range(len(result)):
                f = result[index]
                if i > f.end:
                    l_factor, r_factor = gbf_normalization(
                        result[index].factor,
                        result[index + 1].factor,
                        result[index].param_cal(gb_params),
                        result[index + 1].param_cal(gb_params),
                        "left",
                        backend=backend,
                    )
                    result[index].factor = l_factor
                    result[index + 1].factor = r_factor
                    continue
                break
            for index in range(len(result))[::-1]:
                f = result[index]
                if i < f.start:
                    l_factor, r_factor = gbf_normalization(
                        result[index - 1].factor,
                        result[index].factor,
                        result[index - 1].param_cal(gb_params),
                        result[index].param_cal(gb_params),
                        "right",
                        backend=backend,
                    )
                    result[index - 1].factor = l_factor
                    result[index].factor = r_factor
                    continue
                break
        for index in range(len(result)):
            f = result[index]
            if f.start <= i and i < f.end:
                l_factor, r_factor, epsilon = intermediate_factorization(
                    f.start,
                    i,
                    f.end,
                    gb_params,
                    f.factor,
                    normalized_type=normalized_type,
                    track_epsilon=track_epsilon,
                    backend=backend,
                )
                if track_epsilon and epsilon.item() > max_epsilon:
                    max_epsilon = epsilon.item()
                l_element = Factor(f.start, i, l_factor)
                r_element = Factor(i + 1, f.end, r_factor)
                del result[index]
                result.insert(index, l_element)
                result.insert(index + 1, r_element)
                break
    if track_epsilon:
        return result, max_epsilon
    else:
        return result
