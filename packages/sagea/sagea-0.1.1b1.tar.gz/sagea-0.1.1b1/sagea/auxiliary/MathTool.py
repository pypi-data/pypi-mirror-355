import numpy as np


class MathTool:
    @staticmethod
    def cs_combine_to_triangle_1d(c: np.ndarray, s: np.ndarray):
        """
        combine the SHC C or S in 2-dimensional matrix to 1-dimension vector,
        or SHC C or S in 3-dimensional matrix to 2-dimension vector.
        Example:

        input
        00
        10 11
        20 21 22
        30 31 32 33

        return cs 1d-array which is formed as
        [c(0,0); s(1,1), c(1,0), c(1,1); s(2,2), s(2,1), c(2,0), c(2,1), c(2,2); s(3,3), s(3,2), s(3,1), c(3,0), ...].
        """
        assert np.shape(c) == np.shape(s)
        lmax = np.shape(c)[-1] - 1

        ones_tril = np.tril(np.ones((lmax + 1, lmax + 1)))
        ones_tri = np.concatenate([ones_tril[:, -1:0:-1], ones_tril], axis=1)
        index_tri = np.where(ones_tri == 1)

        cs_tri = MathTool.cs_combine_to_triangle(c, s)

        if cs_tri.ndim == 2:
            return cs_tri[index_tri]

        elif cs_tri.ndim == 3:
            return np.array([cs_tri[i][index_tri] for i in range(np.shape(cs_tri)[0])])

        else:
            raise Exception

    @staticmethod
    def cs_combine_to_triangle(c: np.ndarray, s: np.ndarray):
        """
        :param c: 2- or 3-d array clm or cqlm
        :param s: 2- or 3-d array slm or sqlm
        return: 2d-array like /s|c\, for example,
        [[0,   ...,   0, c00,   0,  ...,    0],
         [0,   ..., s11, c10, c11,  ...,    0],
         [0,   ..., s21, c20, c21,  ...,    0],
         [...  ...,      ...,       ...,  ...],
         [sii, ..., si1, ci0, ci1,  ...,  cii]]

        or 3d-array with the last two dimensions representing format as above if input are 3-d array.
        """

        assert np.shape(c) == np.shape(s)

        if c.ndim == 2:
            return np.concatenate([s[:, -1:0:-1], c], axis=1)

        elif c.ndim == 3:
            return np.array([np.concatenate([s[i, :, -1:0:-1], c[i]], axis=1) for i in range(np.shape(c)[0])])

        else:
            raise Exception

    @staticmethod
    def cs_decompose_triangle1d_to_cs2d(cs: np.ndarray, fill=0.):
        """
        :param cs: 1d-array sorted as
        [c(0,0); s(1,1), c(1,0), c(1,1); s(2,2), s(2,1), c(2,0), c(2,1), c(2,2); s(3,3), s(3,2), s(3,1), c(3,0), ...],
        or 2d-array as
        [
        [c1(0,0); s1(1,1), ...],
        [c2(0,0); s2(1,1), ...],
        ...
        ]

        :param fill: filled value, defaults to 0.
        return: 3d-array c_qlm, 3-array s_qlm
        """
        assert cs.ndim in (1, 2)

        if cs.ndim == 1:
            length_cs1d = len(cs)
            lmax = int(np.sqrt(length_cs1d) - 1)
            shape2d = (lmax + 1, lmax + 1)

            clm, slm = np.full(shape2d, fill, dtype=np.float32), np.full(shape2d, fill, dtype=np.float32)

            for l in range(lmax + 1):
                for m in range(l + 1):
                    c_index_tri1d = int(l ** 2 + l + m)
                    clm[l, m] = cs[c_index_tri1d]

                    if m > 0:
                        s_index_tri1d = int(l ** 2 + l - m)
                        slm[l, m] = cs[s_index_tri1d]

            return np.array([clm]), np.array([slm])

        else:
            cqlm, sqlm = [], []
            for i in range(np.shape(cs)[0]):
                clm, slm = MathTool.cs_decompose_triangle1d_to_cs2d(cs[i])
                cqlm.append(clm)
                sqlm.append(slm)

            return np.array(cqlm), np.array(sqlm)

    @staticmethod
    def cs_get_degree_rms(cqlm, sqlm):
        assert np.shape(cqlm) == np.shape(sqlm)
        if len(np.shape(cqlm)) == 2:
            cqlm = np.array([cqlm])
            sqlm = np.array([sqlm])

        shape = np.shape(cqlm)
        lmax = np.shape(cqlm)[1] - 1

        rms = np.zeros((shape[0], lmax + 1))

        for i in range(lmax + 1):
            rms_this_degree = np.sum(cqlm[:, i, :i + 1] ** 2 + sqlm[:, i, :i + 1] ** 2, axis=1)
            rms_this_degree = np.sqrt(rms_this_degree / ((i + 1) ** 2))
            rms[:, i] = rms_this_degree

        return rms

    @staticmethod
    def cs_get_degree_rss(cqlm, sqlm):
        assert np.shape(cqlm) == np.shape(sqlm)
        if len(np.shape(cqlm)) == 2:
            cqlm = np.array([cqlm])
            sqlm = np.array([sqlm])

        shape = np.shape(cqlm)
        lmax = np.shape(cqlm)[1] - 1

        rss = np.zeros((shape[0], lmax + 1))

        for i in range(lmax + 1):
            rss_this_degree = np.sum(cqlm[:, i, :i + 1] ** 2 + sqlm[:, i, :i + 1] ** 2, axis=1)
            rss_this_degree = np.sqrt(rss_this_degree)
            rss[:, i] = rss_this_degree

        return rss

    @staticmethod
    def get_cumulative_rss(cqlm, sqlm):
        assert np.shape(cqlm) == np.shape(sqlm)
        rss = MathTool.cs_get_degree_rss(cqlm, sqlm)
        crss = np.zeros_like(rss)
        for i in range(rss.shape[1]):
            crss[:, i] = np.sqrt(np.sum(rss[:, :i + 1] ** 2, axis=1))

        return crss
