from lazylinop import LazyLinOp, sanitize_op, aslazylinop
import numpy as np
from scipy.sparse import issparse


def anti_diag(v, k=0, extract_meth='canonical_vectors', extract_batch=1):
    r"""
    Returns a :py:class:`LazyLinOp` ``L`` that extracts an antidiagonal
    or builds an antidiagonal .

    The shape of ``L`` is square and depends on the size of ``v``.

    Args:
        v: (compatible linear operator,  1D ``numpy.ndarray``)
            - If ``v`` is a :py:class:`LazyLinOp` or an array-like compatible
              object, returns a copy of its k-th antidiagonal.
            - If ``v`` is a 1D numpy array, returns a :py:class:`LazyLinOp`
              with ``v`` on the k-th antidiagonal.
        k: ``int``, optional
             The index of antidiagonal, ``0`` (default) for the main
             antidiagonal (the one starting from the upper right corner),
             ``k > 0`` for upper antidiagonals,
             ``k < 0`` for lower antidiagonals below
             (see :py:func:`.anti_eye`).
        extract_meth: ``str``, optional
            The method used to extract the antidiagonal vector. The interest to
            have several methods resides in their difference of memory and
            execution time costs but also on the operator capabilities (e.g.
            not all of them support a CSC matrix as multiplication operand).

            - ``'canonical_vectors'``: use canonical basis vectors $e_i$
              to extract each antidiagonal element of the operator. It takes an
              operator-vector multiplication to extract each antidiagonal
              element.
            - ``'canonical_vectors_csc'``: The same as above but using scipy
              `CSC matrices
              <https://docs.scipy.org/doc/scipy/reference/generated/
              scipy.sparse.csc_matrix.html#scipy.sparse.csc_matrix>`_
              to encode the canonical vectors. The memory cost is
              even smaller than that of ``'canonical_vectors'``.
              However ``v`` must be compatible with CSC
              matrix-vector multiplication.
            - ``'slicing'``: extract antidiagonal elements by slicing rows and
              columns by blocks of shape ``(extract_batch, extract_batch)``.
            - ``'toarray'``: use :func:`LazyLinOp.toarray` to extract
              the antidiagonal after a conversion to a whole numpy array.
        extract_batch: ``int``, optional
            - The size of the batch used for partial antidiagonal extraction in
              ``'canonical_vectors'``, ``'canonical_vectors_csc'`` and
              ``'slicing '`` methods.
               This argument is ignored for ``'toarray'`` method.


        .. admonition:: Antidiagonal extraction cost
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
        The extracted antidiagonal numpy vector or
        the constructed antidiagonal :py:class:`LazyLinOp`.

    Example: (antidiagonal :py:class:`LazyLinOp`)
        >>> import lazylinop.basicops as lz
        >>> import numpy as np
        >>> v = np.arange(1, 6)
        >>> v
        array([1, 2, 3, 4, 5])
        >>> ld1 = lz.anti_diag(v)
        >>> ld1
        <5x5 LazyLinOp with unspecified dtype>
        >>> ld1.toarray('int')
        array([[0, 0, 0, 0, 1],
               [0, 0, 0, 2, 0],
               [0, 0, 3, 0, 0],
               [0, 4, 0, 0, 0],
               [5, 0, 0, 0, 0]])
        >>> ld2 = lz.anti_diag(v, -2)
        >>> ld2
        <7x7 LazyLinOp with unspecified dtype>
        >>> ld2.toarray('int')
        array([[0, 0, 0, 0, 0, 0, 0],
               [0, 0, 0, 0, 0, 0, 0],
               [0, 0, 0, 0, 0, 0, 1],
               [0, 0, 0, 0, 0, 2, 0],
               [0, 0, 0, 0, 3, 0, 0],
               [0, 0, 0, 4, 0, 0, 0],
               [0, 0, 5, 0, 0, 0, 0]])
        >>> ld3 = lz.anti_diag(v, 2)
        >>> ld3
        <7x7 LazyLinOp with unspecified dtype>
        >>> ld3.toarray('int')
        array([[0, 0, 0, 0, 1, 0, 0],
               [0, 0, 0, 2, 0, 0, 0],
               [0, 0, 3, 0, 0, 0, 0],
               [0, 4, 0, 0, 0, 0, 0],
               [5, 0, 0, 0, 0, 0, 0],
               [0, 0, 0, 0, 0, 0, 0],
               [0, 0, 0, 0, 0, 0, 0]])

    Example: (antidiagonal extraction)
        >>> import lazylinop.basicops as lz
        >>> import numpy as np
        >>> lD = aslazylinop(np.random.rand(10, 12))
        >>> d = lz.anti_diag(lD, -2, extract_meth='toarray', extract_batch=3)
        >>> # verify d is really the antidiagonal of index -2
        >>> d_ = np.diag(np.fliplr(lD.toarray()), -2)
        >>> np.allclose(d, d_)
        True


    .. seealso::
        :py:func:`.diag`
        `numpy.diag
        <https://numpy.org/doc/stable/reference/generated/numpy.diag.html>`_
        `numpy.fliplr
        <https://numpy.org/doc/stable/reference/generated/numpy.fliplr.html>`_
        :func:`.aslazylinop`
    """
    if np.isscalar(extract_batch):
        extract_batch = int(extract_batch)
    if not isinstance(extract_batch, int) or extract_batch < 1:
        raise TypeError('extract_batch must be a strictly positive int')
    te = TypeError("v must be a 1-dim vector (np.ndarray) or a 2d "
                   "array/LinearOperator.")
    if isinstance(v, np.ndarray) and v.ndim == 1:
        # building antidiagonal op
        m = v.size + abs(k)
        # spd is just in case x is sparse in matmat
        spd = [None]  # lazy instantiation

        def matmat(x, v, k):
            # x is always 2d
            if issparse(x):
                # because elementwise mul for scipy sparse
                # matrix is not immediate

                if spd[0] is None:
                    spd[0] = _sp_anti_diag(v, k)
                return spd[0] @ x

            v = v.reshape(v.size, 1)
            if k > 0:
                y = v * x[- 1 - k:-1 - k - v.size:-1]
                y = np.vstack((y, np.zeros((k, x.shape[1]), dtype=v.dtype)))
            elif k < 0:
                y = v * x[-1:-1 - v.size:-1]
                y = np.vstack((np.zeros((abs(k), x.shape[1]), dtype=v.dtype),
                               y))
            else:  # k == 0
                y = v * x[-1:-1 - v.size:-1]
            return y
        return LazyLinOp((m, m), matmat=lambda x: matmat(x, v, k),
                         rmatmat=lambda x: matmat(x, np.conj(v[::-1]), k))
    elif v.ndim == 2:
        # extraction of op antidiagonal
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
    i, prev_j = start_i, start_j + 1
    for di in range(0, dlen, batch_sz):
        next_di = min(dlen, di + batch_sz)
        j = max(0, prev_j - batch_sz)
        next_i = min(op.shape[0], i + batch_sz)
        # e_batch_sz <= batch_sz
        # is the effective batch size (because batch_sz might not divide
        # op.shape[1] evenly, then e_batch_sz == op.shape[1] % batch_sz
        e_batch_sz = prev_j - j
        yield (di, i, j, next_di, next_i, prev_j, e_batch_sz)
        i = next_i
        prev_j = j


def _extract_by_slicing(op, d, start_i, start_j, dlen, batch_sz):
    for di, i, j, next_di, next_i, prev_j, _ in _batched_extract_inds_iterator(
            op, start_i,
            start_j, dlen,
            batch_sz):
        if j > 0:
            d[di:next_di] = np.diag(
                op[i:next_i, prev_j - 1:j - 1:-1].toarray())
        else:
            d[di:next_di] = np.diag(op[i:next_i, prev_j - 1::-1].toarray())
    return d


def _extract_by_canonical_vecs(op, d, start_i, start_j, dlen, batch_sz):
    ej = np.zeros((op.shape[1], batch_sz))
    for di, i, j, next_di, next_i, prev_j, e_batch_sz in (
        _batched_extract_inds_iterator(
            op, start_i,
            start_j, dlen,
            batch_sz)):
        # use batch_sz canonical vectors for batch columns extraction
        for jj in range(prev_j - 1, max(j - 1, -1), -1):
            ej[jj, prev_j - 1 - jj] = 1
        # extract blocks (columns then rows)
        # and finally the antidiagonal of the block
        # (ej[:, :e_batch_sz] is a group of e_batch_sz canonical vectors)
        d[di:next_di] = np.diag((op @ ej[:, :e_batch_sz])[i:next_i])
        if next_di != dlen:
            # erase ones for next batch
            for jj in range(prev_j - 1, max(j - 1, -1), -1):
                ej[jj, prev_j - jj - 1] = 0
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
    for di, i, j, next_di, next_i, prev_j, e_batch_sz in (
        _batched_extract_inds_iterator(
            op, start_i,
            start_j, dlen,
            batch_sz)):
        ej_ones_rows = np.arange(prev_j - 1, max(j - 1, -1), -1)
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
    # was called in anti_diag
    return np.diag(op.toarray()[:, -1::-1], k)


def _start_row_col(k, op):
    n = op.shape[1]
    if k >= 0:
        return 0, n - k - 1
    else:
        return - k, n - 1


def _prepare_extract(op, k):
    if k >= op.shape[1] or k <= - op.shape[0]:
        raise ValueError('k is out of bounds.')
    i, j = _start_row_col(k, op)
    dlen = min(op.shape[0] - i, j + 1)
    d = np.empty(dlen, dtype=op.dtype)
    return d, i, j, dlen


def _sp_anti_diag(v, k):
    from scipy.sparse import csr_matrix
    if k >= 0:
        m = v.size + k  # mat m x m
        rows = np.arange(v.size)
        cols = np.arange(m - 1 - k, m - 1 - k - v.size, -1)
    else:
        m = v.size - k
        rows = np.arange(-k, v.size - k)
        cols = np.arange(m - 1, m - 1 - v.size, -1)
    return csr_matrix((v, (rows, cols)), shape=(m, m))
