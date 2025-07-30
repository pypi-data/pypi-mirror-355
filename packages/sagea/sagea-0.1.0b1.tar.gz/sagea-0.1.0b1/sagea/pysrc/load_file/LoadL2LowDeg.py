import datetime
import pathlib
import re

import numpy as np

import sagea.pysrc.auxiliary.Preference as Enums
from sagea.pysrc.auxiliary.FileTool import FileTool
from sagea.pysrc.auxiliary.TimeTool import TimeTool


def load_TN11(filepath):
    with open(filepath) as f:
        txt = f.read()

    dates_c20 = []
    values_c20 = []
    values_c20_dev = []

    pat_data = r'\s*^\d{5}.*'
    data = re.findall(pat_data, txt, re.M)
    for i in data:
        line = i.split()

        ave_dates = TimeTool.convert_date_format(
            (float(line[0]) + float(line[5])) / 2,
            input_type=TimeTool.DateFormat.MJD,
            output_type=TimeTool.DateFormat.ClassDate
        )

        dates_c20.append(ave_dates)
        values_c20.append(float(line[2]))
        values_c20_dev.append(float(line[4]) * 1e-10)

    c20 = [dates_c20, np.array(values_c20)]
    c20_dev = [dates_c20, np.array(values_c20_dev)]

    result = dict(
        c20=c20,
        c20_dev=c20_dev
    )
    return result


def load_TN13(filepath):
    with open(filepath) as f:
        txt = f.read()

    times_c10 = []
    values_c10 = []
    values_c10_dev = []

    times_c11 = []
    values_c11 = []
    values_c11_dev = []

    times_s11 = []
    values_s11 = []
    values_s11_dev = []

    pat_data = r'^GRCOF2.*\w'
    data = re.findall(pat_data, txt, re.M)
    for i in data:
        line = i.split()
        m = int(line[2])
        ymd_begin = line[7][:8]
        date_begin = datetime.date(int(ymd_begin[:4]), int(ymd_begin[4:6]), int(ymd_begin[6:]))
        mjd_begin = TimeTool.convert_date_format(
            date_begin,
            input_type=TimeTool.DateFormat.ClassDate,
            output_type=TimeTool.DateFormat.MJD,
        )

        ymd_end = line[8][:8]
        date_end = datetime.date(int(ymd_end[:4]), int(ymd_end[4:6]), int(ymd_end[6:]))
        mjd_end = TimeTool.convert_date_format(
            date_end,
            input_type=TimeTool.DateFormat.ClassDate,
            output_type=TimeTool.DateFormat.MJD,
        )

        ave_dates = TimeTool.convert_date_format(
            (mjd_begin + mjd_end) / 2,
            input_type=TimeTool.DateFormat.MJD,
            output_type=TimeTool.DateFormat.ClassDate,
        )

        if m == 0:
            times_c10.append(ave_dates)
            values_c10.append(float(line[3]))
            values_c10_dev.append(float(line[5]))

        elif m == 1:
            times_c11.append(ave_dates)
            values_c11.append(float(line[3]))
            values_c11_dev.append(float(line[5]))

            times_s11.append(ave_dates)
            values_s11.append(float(line[4]))
            values_s11_dev.append(float(line[6]))

    c10 = [times_c10, np.array(values_c10)]
    c11 = [times_c11, np.array(values_c11)]
    s11 = [times_s11, np.array(values_s11)]

    c10_dev = [times_c10, np.array(values_c10_dev)]
    c11_dev = [times_c11, np.array(values_c11_dev)]
    s11_dev = [times_s11, np.array(values_s11_dev)]

    result = dict(
        c10=c10, c11=c11, s11=s11,
        c10_dev=c10_dev, c11_dev=c11_dev, s11_dev=s11_dev
    )
    return result


def load_TN14(filepath):
    with open(filepath) as f:
        txt = f.read()

    dates_c20 = []
    values_c20 = []
    values_c20_dev = []

    dates_c30 = []
    values_c30 = []
    values_c30_dev = []

    pat_data = r'\s*^\d{5}.*'
    data = re.findall(pat_data, txt, re.M)
    for i in data:
        line = i.split()
        ave_dates = TimeTool.convert_date_format(
            (float(line[0]) + float(line[8])) / 2,
            input_type=TimeTool.DateFormat.MJD,
            output_type=TimeTool.DateFormat.ClassDate,
        )

        if line[2] != 'NaN':
            dates_c20.append(ave_dates)
            values_c20.append(float(line[2]))
            values_c20_dev.append(float(line[4]) * 1e-10)

        if line[5] != 'NaN':
            dates_c30.append(ave_dates)
            values_c30.append(float(line[5]))
            values_c30_dev.append(float(line[7]) * 1e-10)

    c20 = [dates_c20, np.array(values_c20)]
    c30 = [dates_c30, np.array(values_c30)]
    c20_dev = [dates_c20, np.array(values_c20_dev)]
    c30_dev = [dates_c30, np.array(values_c30_dev)]

    result = dict(
        c20=c20, c30=c30,
        c20_dev=c20_dev, c30_dev=c30_dev
    )
    return result


def load_low_degs(filepath):
    if FileTool.is_iterable(filepath) and (type(filepath) is not str):
        filepath_to_load = list(filepath)
    else:
        filepath_to_load = [pathlib.Path(filepath)]

    if len(filepath_to_load) == 1:
        this_filepath = filepath_to_load[0]

        if this_filepath.is_file():
            check_ids = ("TN-11", "TN-13", "TN-14")
            check_pattern = "(" + ")|(".join(check_ids) + ")"  # r"(TN-11)|(TN-13)|(TN-14)"
            checked = re.search(check_pattern, this_filepath.name) is not None
            if not checked:
                assert False, f"file name should include one of ids: {check_pattern}"

            if "TN-11" in this_filepath.name:
                return load_TN11(this_filepath)
            elif "TN-13" in this_filepath.name:
                return load_TN13(this_filepath)
            elif "TN-14" in this_filepath.name:
                return load_TN14(this_filepath)
            else:
                assert False

        elif this_filepath.is_dir():

            filepath_to_load = FileTool.get_l2_low_deg_path(this_filepath)

            return load_low_degs(filepath_to_load)

    else:
        result = {}
        for i in range(len(filepath_to_load)):
            this_result = load_low_degs(filepath_to_load[i])
            result.update(this_result)

        return result

    pass
