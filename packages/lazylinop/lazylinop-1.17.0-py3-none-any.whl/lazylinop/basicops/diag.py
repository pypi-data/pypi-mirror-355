from lazylinop import LazyLinOp, sanitize_op, aslazylinop
import numpy as np
from scipy.sparse import issparse, spdiags


def diag(v, k=0, extract_meth='canonical_vectors', extract_batch=1):
    r"""
    Extracts a diagonal or constructs a diagonal :py:class:`LazyLinOp`.

    Args:
        v: (compatible linear operator,  1D ``numpy.ndarray``)
            - If ``v`` is a :py:class:`LazyLinOp` or an array-like compatible
              object, returns a copy of its k-th diagonal.
            - If ``v`` is a 1D numpy array, returns a :py:class:`LazyLinOp`
              with ``v`` on the k-th diagonal.
        k: (``int``)
             The index of diagonal, ``0`` for the main diagonal,
             ``k > 0`` for diagonals above,
             ``k < 0`` for diagonals below (see :py:func:`eye`).
        extract_meth: (``str``)
            The method used to extract the diagonal vector. The interest to
            have several methods resides in their difference of memory and
            execution time costs but also on the operator capabilities (e.g.
            not all of them support a CSC matrix as multiplication operand).

            - ``'canonical_vectors'``: use canonical basis vectors $e_i$
              to extract each diagonal element of the operator. It takes an
              operator-vector multiplication to extract each diagonal element.
            - ``'canonical_vectors_csc'``: The same as above but using scipy
              `CSC matrices
              <https://docs.scipy.org/doc/scipy/reference/generated/
              scipy.sparse.csc_matrix.html#scipy.sparse.csc_matrix>`_
              to encode the canonical vectors. The memory cost is
              even smaller than that of ``'canonical_vectors'``.
              However ``v`` must be compatible to CSC matrices multiplication.
            - ``'slicing'``: extract diagonal elements by slicing rows and
              columns by blocks of shape ``(extract_batch, extract_batch)``.
            - ``'toarray'``: use :func:`LazyLinOp.toarray` to extract
              the diagonal after a conversion to a whole numpy array.
        extract_batch: (``int``)
            - The size of the batch used for partial diagonal extraction in
              ``'canonical_vectors'``, ``'canonical_vectors_csc'`` and
              ``'slicing '`` methods.
               This argument is ignored for ``'toarray'`` method.


        .. admonition:: Diagonal extraction cost
            :class: admonition warning

            Even though the ``'toarray'`` method is generally faster if the
            operator is not extremely large it has an important memory cost
            ($O(v.shape[0] \times v.shape[1])$) .
            Hence the default method is ``canonical_vectors`` in order to
            avoid memory consumption.
            However note that this method allows to define a memory-time
            trade-off with the ``extract_batch`` argument. The larger is the
            batch, the faster should be the execution (provided enough memory
            is available).

    Returns:
        The extracted diagonal numpy vector or
        the constructed diagonal :py:class:`LazyLinOp`.

    Example: (diagonal :py:class:`LazyLinOp`)
        >>> import lazylinop as lz
        >>> import numpy as np
        >>> v = np.arange(1, 6)
        >>> v
        array([1, 2, 3, 4, 5])
        >>> ld1 = lz.diag(v)
        >>> ld1
        <5x5 LazyLinOp with unspecified dtype>
        >>> ld1.toarray('int')
        array([[1, 0, 0, 0, 0],
               [0, 2, 0, 0, 0],
               [0, 0, 3, 0, 0],
               [0, 0, 0, 4, 0],
               [0, 0, 0, 0, 5]])
        >>> ld2 = lz.diag(v, -2)
        >>> ld2
        <7x7 LazyLinOp with unspecified dtype>
        >>> ld2.toarray('int')
        array([[0, 0, 0, 0, 0, 0, 0],
               [0, 0, 0, 0, 0, 0, 0],
               [1, 0, 0, 0, 0, 0, 0],
               [0, 2, 0, 0, 0, 0, 0],
               [0, 0, 3, 0, 0, 0, 0],
               [0, 0, 0, 4, 0, 0, 0],
               [0, 0, 0, 0, 5, 0, 0]])
        >>> ld3 = lz.diag(v, 2)
        >>> ld3
        <7x7 LazyLinOp with unspecified dtype>
        >>> ld3.toarray('int')
        array([[0, 0, 1, 0, 0, 0, 0],
               [0, 0, 0, 2, 0, 0, 0],
               [0, 0, 0, 0, 3, 0, 0],
               [0, 0, 0, 0, 0, 4, 0],
               [0, 0, 0, 0, 0, 0, 5],
               [0, 0, 0, 0, 0, 0, 0],
               [0, 0, 0, 0, 0, 0, 0]])

    Example: (diagonal extraction)
        >>> import lazylinop as lz
        >>> from lazylinop import aslazylinop
        >>> import numpy as np
        >>> lD = aslazylinop(np.random.rand(10, 12))
        >>> d = lz.diag(lD, -2)
        >>> # verify d is really the diagonal of index -2
        >>> d_ = np.array([lD[i, i-2] for i in range(abs(-2), lD.shape[0])])
        >>> np.allclose(d, d_)
        True


    .. seealso::
        `numpy.diag
        <https://numpy.org/doc/stable/reference/generated/numpy.diag.html>`_
        :func:`.aslazylinop`
    """
    if np.isscalar(extract_batch):
        extract_batch = int(extract_batch)
    if not isinstance(extract_batch, int) or extract_batch < 1:
        raise TypeError('extract_batch must be a strictly positive int')
    te = TypeError("v must be a 1-dim vector (np.ndarray) or a 2d "
                   "array/LinearOperator.")
    if isinstance(v, np.ndarray) and v.ndim == 1:

        ne = v.size
        m = ne + abs(k)

        # spd is just in case x is sparse in matmat.
        if k > 0:
            spd = spdiags([np.hstack((np.zeros(k), v))], k, m=m, n=m)
        else:
            spd = spdiags([v], k, m=m, n=m)

        def matmat(x, v, k):
            if issparse(x):
                # Because elementwise mul for scipy sparse
                # matrix is not immediate.
                return spd @ x
            v = v.reshape(ne, 1)
            # x is always 2d
            if k > 0:
                y = np.zeros((m, x.shape[1]), dtype=(x[0, 0] * v[0]).dtype)
                y[:ne] = v * x[k:(k + ne)]
            elif k < 0:
                y = np.zeros((m, x.shape[1]), dtype=(x[0, 0] * v[0]).dtype)
                y[abs(k):] = v * x[:ne]
            else:  # k == 0
                y = v * x
            return y
        return LazyLinOp(shape=(m, m),
                         matmat=lambda x: matmat(x, v, k),
                         rmatmat=lambda x: matmat(x, np.conj(v), -k))
    elif v.ndim == 2:
        # extraction of op diagonal
        op = v
        sanitize_op(op)
        op = aslazylinop(op)

        if extract_meth == 'toarray' or isinstance(op, np.ndarray):
            return _extract_by_toarray(op, k, te)
        elif extract_meth == 'slicing':
            return _extract_by_slicing(op, *_prepare_extract(op, k),
                                       extract_batch)
        elif extract_meth == 'canonical_vectors':
            return _extract_by_canonical_vecs(op, *_prepare_extract(op, k),
                                              extract_batch)
        elif extract_meth == 'canonical_vectors_csc':
            return _extract_by_canonical_csc_vecs(op, *_prepare_extract(op, k),
                                                  extract_batch)
        elif extract_meth == 'canonical_vectors_csr':
            return _extract_by_canonical_csr_vecs(op, *_prepare_extract(op, k),
                                                  extract_batch)
        else:
            raise ValueError('Extraction method '+str(extract_meth)+' is'
                             ' unknown.')
    else:  # v is 1-dim but not a numpy array or more than 2-dim
        raise te


def _batched_extract_inds_iterator(op, start_i, start_j, dlen, batch_sz):
    i, j = start_i, start_j
    for di in range(0, dlen, batch_sz):
        next_di = min(dlen, di + batch_sz)
        next_j = min(op.shape[1], j + batch_sz)
        next_i = min(op.shape[0], i + batch_sz)
        # e_batch_sz <= batch_sz
        # is the effective batch size (because batch_sz might not divide
        # op.shape[1] evenly, then e_batch_sz == op.shape[1] % batch_sz
        e_batch_sz = next_j - j
        yield (di, i, j, next_di, next_i, next_j, e_batch_sz)
        i = next_i
        j = next_j


def _extract_by_slicing(op, d, start_i, start_j, dlen, batch_sz):
    for di, i, j, next_di, next_i, next_j, _ in _batched_extract_inds_iterator(
            op, start_i,
            start_j, dlen,
            batch_sz):
        d[di:next_di] = np.diag(op[i:next_i, j:next_j].toarray())
    return d


def _extract_by_canonical_vecs(op, d, start_i, start_j, dlen, batch_sz):
    ej = np.zeros((op.shape[1], batch_sz))
    for di, i, j, next_di, next_i, next_j, e_batch_sz in (
        _batched_extract_inds_iterator(
            op, start_i,
            start_j, dlen,
            batch_sz)):
        # use batch_sz canonical vectors for batch columns extraction
        for jj in range(j, next_j):
            ej[jj, jj-j] = 1
        # extract blocks (columns then rows)
        # and finally the diagonal of the block
        # (ej[:, :e_batch_sz] is a group of e_batch_sz canonical vectors)
        d[di:next_di] = np.diag((op @ ej[:, :e_batch_sz])[i:next_i])
        if next_di != dlen:
            # erase ones for next batch
            for jj in range(j, next_j):
                ej[jj, jj-j] = 0
    return d


def _extract_by_canonical_csc_vecs(op, d, start_i, start_j, dlen, batch_sz):
    return _extract_by_canonical_sparse_vecs(op, d, start_i, start_j, dlen,
                                             batch_sz, 'csc')


def _extract_by_canonical_sparse_vecs(op, d, start_i, start_j, dlen, batch_sz,
                                      scipy_format='csc'):
    from scipy.sparse import csc_matrix, csr_matrix

    def init_scipy_mat(fmt, *args, **kwargs):
        assert fmt.lower() in ['csc', 'csr']
        if fmt.lower() == 'csc':
            return csc_matrix(*args, **kwargs)
        else:  # fmt.lower() == 'csr':
            return csr_matrix(*args, **kwargs)
    ones = [1 for j in range(batch_sz)]
    for di, i, j, next_di, next_i, next_j, e_batch_sz in (
        _batched_extract_inds_iterator(
            op, start_i,
            start_j, dlen,
            batch_sz)):
        ej_ones_rows = np.arange(j, next_j)
        ej_ones_cols = np.arange(0, e_batch_sz)
        ej_data = ones[:e_batch_sz]
        # ej is a group of e_batch_sz canonical vectors
        ej = init_scipy_mat(scipy_format, (ej_data,
                                           (ej_ones_rows,
                                            ej_ones_cols)),
                            shape=(op.shape[1], e_batch_sz))
        res = (op @ ej)[i:next_i]
        d[di:next_di] = (np.diag(res.toarray()) if issparse(res) else
                         np.diag(res))
    return d


def _extract_by_canonical_csr_vecs(op, d, start_i, start_j, dlen, batch_sz):

    return _extract_by_canonical_sparse_vecs(op, d, start_i, start_j, dlen,
                                             batch_sz, 'csr')


def _extract_by_toarray(op, k, te):
    # op is a LazyLinOp because aslazylinop
    # was called in diag
    return np.diag(op.toarray(), k)


def _start_row_col(k):
    if k >= 0:
        return 0, k
    else:
        return -k, 0


def _prepare_extract(op, k):
    if k >= op.shape[1] or k <= - op.shape[0]:
        raise ValueError('k is out of bounds.')
    i, j = _start_row_col(k)
    dlen = min(op.shape[0] - i, op.shape[1] - j)
    d = np.empty(dlen, dtype=op.dtype)
    return d, i, j, dlen
