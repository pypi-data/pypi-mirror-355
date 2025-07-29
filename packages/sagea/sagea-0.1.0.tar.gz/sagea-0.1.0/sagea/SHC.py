#!/use/bin/env python
# coding=utf-8
# @Author  : Shuhao Liu
# @Time    : 2025/6/13 10:34 
# @File    : SHC.py

import numpy as np

from sagea.auxiliary.MathTool import MathTool


class SHC:
    """
    This class is to store the spherical harmonic coefficients (SHCs) for the use in necessary data processing.

    Attribute self.value stores the coefficients in 2d-array (in numpy.ndarray) combined with c and s.
    which are sorted by degree, for example,
    numpy.ndarray: [[c1[0,0]; s1[1,1], c1[1,0], c1[1,1]; s1[2,2], s1[2,1], c1[2,0], c1[2,1], c1[2,2]; ...],
     [c2[0,0]; s2[1,1], c2[1,0], c2[1,1]; s2[2,2], s2[2,1], c2[2,0], c2[2,1], c2[2,2]; ...],
     [                                        ...                                         ]].
    Note that even it stores only one set of SHCs, the array is still 2-dimension, i.e.,
    [[c1[0,0]; s1[1,1], c1[1,0], c1[1,1]; s1[2,2], s1[2,1], c1[2,0], c1[2,1], c1[2,2]; ...]].

    Attribute self.dates stores beginning and ending dates (in datetime.date) in list as
        list: [
            [begin_1: datetime,date, begin_2: datetime,date, ...],
            [end_1: datetime,date, end_2: datetime,date, ...],
        ] if needed, else None.

    Attribute self.normalization indicates the normalization of the SHCs (in EnumClasses.SHNormalization), for example,
    EnumClasses.SHNormalization.full.

    Attribute self.physical_dimension indicates the physical dimension of the SHCs (in EnumClasses.PhysicalDimensions).
    """

    def __init__(self, c, s, normalization=None, physical_dimension=None, perference=None):
        """

        :param c: harmonic coefficients c in 2-dimension (l,m), or a series (q,l,m);
        :param s: harmonic coefficients s in 2-dimension (l,m), or a series (q,l,m),
        :param normalization: in Preference.SHNormalization, default Preference.SHNormalization.full.
        :param physical_dimension: in Preference.PhysicalDimensions, default Preference.PhysicalDimensions.Dimensionless.
        """

        assert np.shape(c) == np.shape(s)

        if len(np.shape(c)) == 2:
            self.value = MathTool.cs_combine_to_triangle_1d(c, s)

        elif len(np.shape(c)) == 3:
            cs = []
            for i in range(np.shape(c)[0]):
                this_cs = MathTool.cs_combine_to_triangle_1d(c[i], s[i])
                cs.append(this_cs)
            self.value = np.array(cs)

        if len(np.shape(self.value)) == 1:
            self.value = self.value[None, :]

        assert len(np.shape(self.value)) == 2

        self.dates = None

        if normalization is None:
            normalization = perference.SHNormalization.full

        assert normalization in perference.SHNormalization
        self.normalization = normalization

        if physical_dimension is None:
            physical_dimension = perference.PhysicalDimensions.Dimensionless

        assert physical_dimension in perference.PhysicalDimensions
        self.physical_dimension = physical_dimension


if __name__ == "__main__":
    pass
