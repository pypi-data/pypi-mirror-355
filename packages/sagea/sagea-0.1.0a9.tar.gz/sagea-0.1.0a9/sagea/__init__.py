#!/use/bin/env python
# coding=utf-8
# @Author  : Shuhao Liu
# @Time    : 2025/6/13 10:28 
# @File    : __init__.py.py
import pathlib

import sagea
from sagea.pysrc.data_class.__SHC__ import SHC
from sagea.pysrc.data_class.__GRD__ import GRD

from sagea.pysrc.load_file.LoadL2SH import load_SHC as load_SHC
from sagea.pysrc.load_file.LoadL2LowDeg import load_low_degs as load_SHLow
from sagea.pysrc.load_file.LoadNoah import load_GLDAS_TWS
from sagea.pysrc.load_file.LoadShp import LoadShp

from sagea.pysrc.auxiliary.MathTool import MathTool
from sagea.pysrc.auxiliary.TimeTool import TimeTool
from sagea.pysrc.auxiliary.FileTool import FileTool
import sagea.pysrc.auxiliary.Preference as Preference

from sagea.pysrc.data_collection.collect_auxiliary import collect_auxiliary as collect_auxiliary_data


def set_auxiliary_data_path(path):
    path = pathlib.Path(path)
    assert path.exists(), f"Path {path} does not exist."

    sagea.pysrc.auxiliary.Preference.Config.aux_data_dir = pathlib.Path(path)
