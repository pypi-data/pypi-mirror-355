#!/use/bin/env python
# coding=utf-8
# @Author  : Shuhao Liu
# @Time    : 2025/6/13 10:34 
# @File    : __SHC__.py
import copy

import numpy as np

from sagea.pysrc.auxiliary.Preference import GeoConstants, SHNormalization, PhysicalDimension
from sagea.pysrc.auxiliary.TimeTool import TimeTool
from sagea.pysrc.auxiliary.MathTool import MathTool
from sagea.pysrc.post_processing.filter.GetSHCFilter import get_filter
from sagea.pysrc.auxiliary import Preference
from sagea.pysrc.auxiliary.LoveNumber import LoveNumber
from sagea.pysrc.post_processing.convert_field_physical_quantity.ConvertSHC import ConvertSHC
from sagea.pysrc.post_processing.geometric_correction.GeometricalCorrection import GeometricalCorrection
from sagea.pysrc.post_processing.harmonic.Harmonic import Harmonic
from sagea.pysrc.post_processing.replace_low_deg.ReplaceLowDegree import ReplaceLowDegree


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

    Attribute self.normalization indicates the normalization of the SHCs (in EnumClasses.SHNormalization), for example,
    EnumClasses.SHNormalization.full.

    Attribute self.physical_dimension indicates the physical dimension of the SHCs (in EnumClasses.PhysicalDimensions).
    """

    def __init__(self, c, s=None, normalization=None, physical_dimension=None):
        """

        :param c:
                if s is not None:
                    harmonic coefficients c in 2-dimension (l,m), or a series (q,l,m);
                else:
                    1-dimension array sorted by degree [c00, s11, c10, c11, s22, s21, ...]
                    or 1-dimension array sorted by degree [[c00, s11, c10, c11, s22, s21, ...],[...]]

        :param s: harmonic coefficients s in 2-dimension (l,m), or a series (q,l,m),
                or None.

        :param normalization: in preference.SHNormalization, defaults to .full.

        :param physical_dimension: in preference.PhysicalDimensions, defaults to .Dimensionless.
        """
        if s is None:
            self.value = np.array(c)
            if len(self.value.shape) == 1:
                self.value = np.array([self.value])

        else:
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

        if normalization is None:
            normalization = Preference.SHNormalization.full
        assert normalization in Preference.SHNormalization
        self.__normalization = normalization

        if physical_dimension is None:
            physical_dimension = Preference.PhysicalDimension.Dimensionless
        assert physical_dimension in Preference.PhysicalDimension
        self.__physical_dimension = physical_dimension

    def append(self, *params):
        """

        :param params: One parameter of instantiated SHC,
         or two parameters of c and s with the same input requirement as SHC.
        :param date_begin: datetime.date, necessary is self.is_with_date() is True.
        :param date_end: datetime.date, necessary is self.is_with_date() is True.
        :return: self
        """
        assert len(params) in (1, 2)

        if len(params) == 1:
            if issubclass(type(params[0]), SHC):
                shc = params[0]
            else:
                shc = SHC(params[0])

        else:
            shc = SHC(*params)

        assert np.shape(shc.value)[-1] == np.shape(self.value)[-1]

        self.value = np.concatenate([self.value, shc.value])

        return self

    def is_series(self):
        """
        To determine whether the spherical harmonic coefficients stored in this class are one group or multiple groups.
        :return: bool, True if it stores multiple groups, False if it stores only one group.
        """
        return self.get_length() != 1

    def get_length(self):
        """
        To get the number of sets.
        """
        return np.shape(self.value)[0]

    def __len__(self):
        return self.get_length()

    def get_lmax(self):
        """

        :return: int, max degree/order of the spherical harmonic coefficients stored in this class.
        """
        length_of_cs1d = np.shape(self.value)[-1]
        lmax = int(np.sqrt(length_of_cs1d) - 1)

        return lmax

    def get_physical_dimension(self):
        """

        :return:
        """

        return self.__physical_dimension

    def set_physical_dimension(self, physical_dimension: PhysicalDimension):
        self.__physical_dimension = physical_dimension

        return self

    def get_normalization(self):
        """

        :return:
        """

        return self.__normalization

    def set_normalization(self, normalization: SHNormalization):
        self.__normalization = normalization
        return self

    def get_cs2d(self, fill_value=0):
        """
        return: cqlm, sqlm. Both cqlm and sqlm are 3-dimension, EVEN IF NOT self.is_series()
        """
        lmax = self.get_lmax()

        num_of_series = np.shape(self.value)[0]

        cqlm = np.zeros((num_of_series, lmax + 1, lmax + 1))
        sqlm = np.zeros((num_of_series, lmax + 1, lmax + 1))

        for i in range(num_of_series):
            this_cs = self.value[i]
            this_clm, this_slm = MathTool.cs_decompose_triangle1d_to_cs2d(this_cs)
            cqlm[i, :, :] = this_clm
            sqlm[i, :, :] = this_slm

        return cqlm, sqlm

    def __de_average(self):
        if self.is_series():
            self.value -= np.mean(self.value, axis=0)
        else:
            raise Exception

    def get_average(self):
        return SHC(np.mean(self.value, axis=0))

    def de_background(self, background=None):
        """
        if background is None, de average
        """
        if background is None:
            self.__de_average()

        else:
            assert isinstance(background, SHC)
            assert not background.is_series()

            self.value -= background.value

    @staticmethod
    def identity(lmax: int):
        basis_num = (lmax + 1) ** 2
        cs = np.eye(basis_num)

        return SHC(cs)

    def __add__(self, other):
        assert isinstance(other, SHC)
        assert self.get_lmax() == other.get_lmax()

        return SHC(self.value + other.value)

    def __sub__(self, other):
        assert isinstance(other, SHC)
        assert self.get_lmax() == other.get_lmax()

        return SHC(self.value - other.value)

    def add(self, shc, lbegin=None, lend=None):
        if (lend is None) and (lbegin is None):
            self.value += shc.value
            return self

        else:
            assert (lend is None) or (0 <= lend <= self.get_lmax())
            assert (lbegin is None) or (0 <= lbegin <= self.get_lmax())

            shc_copy = copy.deepcopy(shc)

            if lend is not None:
                shc_copy.value[:, (lend + 1) ** 2:] = 0
            if lbegin is not None:
                shc_copy.value[:, :lbegin ** 2] = 0

            return self.add(shc_copy)

    def subtract(self, shc, lbegin=None, lend=None):
        if (lend is None) and (lbegin is None):
            self.value -= shc.value
            return self

        else:
            assert (lend is None) or (0 <= lend <= self.get_lmax())
            assert (lbegin is None) or (0 <= lbegin <= self.get_lmax())

            shc_copy = copy.deepcopy(shc)

            if lend is not None:
                shc_copy.value[:, (lend + 1) ** 2:] = 0
            if lbegin is not None:
                shc_copy.value[:, :lbegin ** 2] = 0

            return self.subtract(shc_copy)

    def get_degree_rms(self):
        cqlm, sqlm = self.get_cs2d()
        return MathTool.cs_get_degree_rms(cqlm, sqlm)

    def get_degree_rss(self):
        cqlm, sqlm = self.get_cs2d()
        return MathTool.cs_get_degree_rss(cqlm, sqlm)

    def get_cumulative_degree_rss(self):
        cqlm, sqlm = self.get_cs2d()
        return MathTool.cs_get_cumulative_degree_rss(cqlm, sqlm)

    def get_std(self):
        cs_std = np.std(self.value, axis=0)
        return SHC(cs_std)

    def convert_type(self, to_type: Preference.PhysicalDimension):
        from_type = self.__physical_dimension

        assert from_type in Preference.PhysicalDimension
        assert to_type in Preference.PhysicalDimension

        lmax = self.get_lmax()
        LN = LoveNumber()
        LN.configuration.set_lmax(lmax)

        ln = LN.get_Love_number()

        convert = ConvertSHC()
        convert.configuration.set_Love_number(ln).set_input_type(from_type).set_output_type(to_type)

        self.value = convert.apply_to(self.value)
        self.__physical_dimension = to_type
        return self

    def filter(self, method: Preference.SHCFilterType or Preference.SHCDecorrelationType, param: tuple = None):
        cqlm, sqlm = self.get_cs2d()
        filtering = get_filter(method, param, lmax=self.get_lmax())
        cqlm_f, sqlm_f = filtering.apply_to(cqlm, sqlm)
        self.value = MathTool.cs_combine_to_triangle_1d(cqlm_f, sqlm_f)

        return self

    def to_GRD(self, grid_space=None):
        from sagea.pysrc.data_class.__GRD__ import GRD

        """pure synthesis"""

        if grid_space is None:
            grid_space = int(180 / self.get_lmax())

        lat, lon = MathTool.get_global_lat_lon_range(grid_space)

        lmax = self.get_lmax()
        har = Harmonic(lat, lon, lmax, option=1)

        cqlm, sqlm = self.get_cs2d()

        if self.__physical_dimension in (Preference.PhysicalDimension.HorizontalDisplacementEast,
                                         Preference.PhysicalDimension.HorizontalDisplacementNorth):
            grid_data = har.synthesis(cqlm, sqlm, special_type=self.__physical_dimension)

        else:
            grid_data = har.synthesis(cqlm, sqlm)

        grid = GRD(grid_data, lat, lon, option=1)

        return grid

    def geometric(self, assumption: Preference.GeometricCorrectionAssumption, log=False):
        gc = GeometricalCorrection()
        cqlm, sqlm = self.get_cs2d()
        cqlm_new, sqlm_new = gc.apply_to(cqlm, sqlm, assumption=assumption, log=log)
        self.value = MathTool.cs_combine_to_triangle_1d(cqlm_new, sqlm_new)

        return self

    def replace_low_degs(self, dates_begin, dates_end, low_deg: dict,
                         c10=False, c11=False, s11=False, c20=False, c30=False):
        assert len(dates_begin) == len(dates_end) == len(self.value)

        replace_or_not = (c10, c11, s11, c20, c30)
        low_ids = ("c10", "c11", "s11", "c20", "c30")
        for i in range(len(low_ids)):
            if replace_or_not[i]:
                assert low_ids[i] in low_deg.keys(), f"input low_deg should include key {low_ids[i]}"

        replace_low_degs = ReplaceLowDegree()
        replace_low_degs.configuration.set_replace_c10(c10).set_replace_c11(c11).set_replace_s11(s11)
        replace_low_degs.configuration.set_replace_c20(c20).set_replace_c30(c30)

        replace_low_degs.set_low_degrees(low_deg)
        cqlm, sqlm = replace_low_degs.apply_to(*self.get_cs2d(), begin_dates=dates_begin, end_dates=dates_end)
        self.value = MathTool.cs_combine_to_triangle_1d(cqlm, sqlm)

        return self

    def linear_expand(self, time):
        assert not self.is_series()

        year_frac = TimeTool.convert_date_format(time,
                                                 input_type=TimeTool.DateFormat.ClassDate,
                                                 output_type=TimeTool.DateFormat.YearFraction)

        year_frac = np.array(year_frac)

        trend = self.value[0]
        value = year_frac[:, None] @ trend[None, :]
        return SHC(value)

    def regional_extraction(self, shc_region, average=True):
        assert isinstance(shc_region, SHC)

        extraction = (shc_region.value @ self.value.T) * (GeoConstants.radius_earth ** 2)

        if average:
            extraction /= (shc_region.value[:, None, 0] * (GeoConstants.radius_earth ** 2))

        else:
            if self.__normalization == SHNormalization.full:
                extraction *= (4 * np.pi)
            else:
                assert False

        return extraction


if __name__ == "__main__":
    pass
