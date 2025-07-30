#!/use/bin/env python
# coding=utf-8
# @Author  : Shuhao Liu
# @Time    : 2025/6/13 12:53 
# @File    : testSHC.py
import pathlib

import sagea

sagea.set_auxiliary_data_path("sagea_data/")

from scripts.PlotGrids import plot_grids


def demo():
    lmax = 60

    l2_dir = pathlib.Path("data/L2_SH_products/GSM/CSR/RL06/BA01/2002")
    l2_path_list = list(l2_dir.iterdir())
    l2_path_list.sort()

    l2_low_deg_path_list = [
        pathlib.Path("data/L2_low_degrees/TN-13_GEOC_CSR_RL06.txt"),
        pathlib.Path("data/L2_low_degrees/TN-14_C30_C20_SLR_GSFC.txt"),
    ]

    gif_48_sh_path = "data/auxiliary/GIF48.gfc"

    gia_sh_path = "data/GIA/GIA.ICE-6G_D.txt"

    basin_sh_path = "data/auxiliary/BASIN.ICE-6G_D.txt"

    shc, dates_begin, dates_end = sagea.load_SHC(l2_path_list, key="GRCOF2", lmax=lmax, get_dates=True)

    shc_gif48 = sagea.load_SHC(gif_48_sh_path, key="gfc", lmax=lmax, get_dates=False)
    shc_gia_trend = sagea.load_SHC(gia_sh_path, key=None, lmax=lmax, get_dates=False)

    sh_low_degs = sagea.load_SHLow(l2_low_deg_path_list)

    shc.replace_low_degs(
        dates_begin=dates_begin, dates_end=dates_end, low_deg=sh_low_degs,
        c10=True, c11=True, s11=True,
    )

    for i in range(len(shc)):
        print(l2_path_list[i].name, dates_begin[i], dates_end[i])

    dates_ave = sagea.TimeTool.get_average_dates(dates_begin, dates_end)
    shc_gia_monthly = shc_gia_trend.linear_expand(dates_ave)
    shc_gia_monthly.de_background()

    shc -= shc_gia_monthly

    shc.de_background(shc_gif48)

    # shc.geometric(assumption=sagea.Preference.GeometricCorrectionAssumption.Ellipsoid,log=True)

    shc.filter(method=sagea.Preference.SHCFilterType.DDK, param=(4,))
    # shc.filter(method=sagea.Preference.SHCFilterType.Gaussian, param=(300,))
    # shc.filter(method=sagea.Preference.SHCFilterType.Fan, param=(300, 500,))
    # shc.filter(method=sagea.Preference.SHCFilterType.AnisotropicGaussianHan, param=(300, 500, 30))

    shc.convert_type(to_type=sagea.Preference.PhysicalDimension.EWH)
    print(shc.get_normalization())
    print(shc.get_physical_dimension())

    grd = shc.to_GRD(grid_space=1)

    plot_grids(
        grd.value[:3] * 100, grd.lat, grd.lon,
        vmin=-20, vmax=20
    )


if __name__ == "__main__":
    demo()
