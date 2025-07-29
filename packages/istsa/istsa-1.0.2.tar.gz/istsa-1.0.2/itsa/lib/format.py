#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May 21 11:02:37 2025

@author: tsaponga
"""

from itsa.lib.midas import midas
from datetime import datetime
from time_series import read_time_series

#read_time_series(time_series_path: Path, forma: str = "pbo")
# def midas(dates, disp, steps=None, tolerance=0.001, print_msg=False, display=False):

def get(folder, ref_frame="IGS14"):
    
    """get and validate station time series"""

    from pathlib import Path
    # from glob import glob

    pos_files = list(Path(folder).glob("????.txt")) + list(Path(folder).glob("?????????.txt"))
    pos_files = [file for file in pos_files if verify_file_structure(file, "pos")]
    if pos_files:
        for file in pos_files:
            code = (file.name).split(".")[0]
            write_PBO(file, code, ref_frame)
            
    pbo_files = list(Path(folder).glob("????.pos")) + list(Path(folder).glob("?????????.pos"))
    pbo_files = [str(file) for file in pbo_files if verify_file_structure(file, "pbo")]

    if pbo_files:
        
        for file in pbo_files:
            
            marker=((Path(file).name).split(".")[0]).upper()
            weight = 1.0
            
            link = file
            
            with open(file) as f:
                line = f.readline()
                
                if not line.startswith("*YYYYMMDD"):
                    
                    if line.startswith("AnalysisCentre"):
                        center = line.strip().split()[-1]
                    elif line.startswith("Software"):
                        Software= line.strip().split()[-1]
                    elif "Reference Frame" in line:
                        frame = line.strip().split()[-1]
                    elif line.startswith("First Epoch"):
                        start_date = datetime.strptime(line.strip().split()[3],"%Y%m%d")
                    elif line.startswith("Last Epoch"):
                        end_date   = datetime.strptime(line.strip().split()[3],"%Y%m%d")

                    elif line.startswith("XYZ Reference"):
                        X, Y, Z = line.strip().split()[4:7]
                        # start_date = datetime.strptime(line.strip().split()[3],"%Y%m%d")
                    elif line.startswith("NEU Reference"):
                        latitude, longitude, hgt = line.strip().split()[4:7]


      
# ln="NEU Reference position :  -20.5462104079  -70.1776554161   90.0338068400 (ITRF2014/WGS84)"

# AnalysisCentre: UGA-CNRS
# Software      : GipsyX
# DOI           : 10.5072/GNSS.products.SouthAmerica_GIPSYX.daily
# SamplingPeriod: daily
# PBO Station Position Time Series. Reference Frame : ITRF2014
# Format Version: 1.1.0
# 4-character ID: AEDA
# Processing    : GipsyX
# First Epoch   : 20031208 120000
# Last Epoch    : 20200212 120000
# Release Date  : 20250507 135536
# XYZ Reference position :  2026140.579270 -5620943.021640 -2224451.884010 (ITRF2014)
# NEU Reference position :  -20.5462104079  -70.1776554161   90.0338068400 (ITRF2014/WGS84)
# Start Field Description
# YYYYMMDD      Year, month, day for the given position epoch
# HHMMSS        Hour, minute, second for the given position epoch
# JJJJJ.JJJJJ   Modified Julian day for the given position epoch
# X             X coordinate, Specified Reference Frame, meters
# Y             Y coordinate, Specified Reference Frame, meters
# Z             Z coordinate, Specified Reference Frame, meters
# Sx            Standard deviation of the X position, meters
# Sy            Standard deviation of the Y position, meters
# Sz            Standard deviation of the Z position, meters
# Rxy           Correlation of the X and Y position
# Rxz           Correlation of the X and Z position
# Ryz           Correlation of the Y and Z position
# Nlat          North latitude, WGS-84 ellipsoid, decimal degrees
# Elong         East longitude, WGS-84 ellipsoid, decimal degrees
# Height (Up)   Height relative to WGS-84 ellipsoid, m
# dN            Difference in North component from NEU reference position, meters
# dE            Difference in East component from NEU reference position, meters
# dU            Difference in vertical component from NEU reference position, meters
# Sn            Standard deviation of dN, meters
# Se            Standard deviation of dE, meters
# Su            Standard deviation of dU, meters
# Rne           Correlation of dN and dE
# Rnu           Correlation of dN and dU
# Reu           Correlation of dE and dU
# Soln
# End Field Description
# *YYYYMMDD HHMMSS JJJJJ.JJJJ         X             Y             Z            Sx        Sy       Sz     Rxy   Rxz    Ryz            NLat         Elong          Height        dN        dE        dU         Sn       Se       Su      Rne    Rnu    Reu  Soln
#  20031209 120000 52982.5000  2026140.57927 -5620943.02164 -2224451.88401  0.00175  0.00418  0.00188 -0.751 -0.647  0.827     -20.5462104079  -70.1776554161   90.03381     0.00000   0.00000   0.00000    0.00099  0.00110  0.00468  0.055  0.008 -0.080 itsa
 



# {
#   "bounding_box": {
#     "min_lon": -5.0,
#     "max_lon":  8.0,
#     "min_lat": 41.0,
#     "max_lat": 51.0
#   },
#   "stations": [
#     {
#       "id":        "STN001",
#       "latitude":  45.123,
#       "longitude":  1.234,
#       "marker":     "o",
#       "center":     "France",
#       "plate":      "EURA",
#       "frame":      "ITRF2014",
#       "x":         4451234.56,
#       "y":         1234567.89,
#       "z":         4321000.00,
#       "hgt":       350.5,
#       "modif":      null,
#       "ve":        2.3,
#       "vn":       -1.1,
#       "vu":        0.5,
#       "se":        0.1,
#       "sn":        0.1,
#       "su":        0.2,
#       "nbr_days": 365,
#       "nbr_insar":  12,
#       "start_date": "2020-01-01",
#       "end_date":   "2021-01-01",
#       "link":       "http://...",
#       "gps_vel":   2.4,
#       "gps_sig":   0.3,
#       "weight":     1.0,
#       "insar_vel": 1.8
#     },
#     {
#       "id": "...",
#       ...
#     }
#   ]
# }



def write_PBO(pos_file, code, ref_frame, outdir=None):
    """
    Write PBO pos file from Geodetic time series (Gts)

    Parameters
    ----------
    outdir : str, optional
        Output directory.
        The default is '.'.

    warn : bool, optional
        Print warning if true.
        The default is True.
        
    Raises
    ------
    TypeError
        If any parameter does not have the right type.
    OSError
        If output file name is already taken and |replace| is false.
    WARNING
        If |replace| is not bool: |replace| set to False.

    """
    
    import numpy as np
    from pathlib import Path
    from datetime import datetime
    from itsa.lib.coordinates import xyz2geo
    from itsa.lib.astrotime import mjd2cal, ut2hms
    from itsa.gts.lib.format.PBOpos import _print_header
    
    # read data
    time, XYZ0, NEU0, data_xyz, data_neu, process = read_POS(pos_file, ref_frame=ref_frame, process='GX', neu=True)
    
    # Make dN, dE, dU data array
    data = XYZ2DNUE(XYZ0, data_xyz, corr=True, warn=True)
    
    if not outdir or not Path(outdir).is_dir():
        # construct pbo file
        pbo_file = Path(pos_file).with_suffix('.pos')
    else:
        Path(outdir) / (Path(pos_file).stem + ".pos")
        
    # Open pos file
    with open(pbo_file, 'w+') as f_pos:
        
        # Header
        def format_epoch(Y, M, D, h, m, s):
            return '%04d%02d%02d %02d%02d%02d' % (Y, M, D, h, m, s)
        # First epoch
        (fday, fmonth, fyear, fut) = mjd2cal(time[0, 1])
        (fhour, fminute, fsecond) = ut2hms(fut)
        first_epoch = format_epoch(fyear, fmonth, fday, fhour, fminute,
                                   fsecond)
        # Last epoch
        (lday, lmonth, lyear, lut) = mjd2cal(time[-1, 1])
        (lhour, lminute, lsecond) = ut2hms(lut)
        last_epoch = format_epoch(lyear, lmonth, lday, lhour, lminute, lsecond)
        # Current epoch
        current_epoch = datetime.today()
        release_epoch = format_epoch(current_epoch.year, current_epoch.month,
                                     current_epoch.day, current_epoch.hour,
                                     current_epoch.minute,
                                     current_epoch.second)
        # XYZ reference position
        XYZ0 = '%15.6lf %15.6lf %15.6lf' % tuple(XYZ0)
        # NEU reference position
        NEU0 = '%15.10lf %15.10lf %15.10lf' % tuple(NEU0)
        # Print header
        _print_header(f_pos, code, process, first_epoch, last_epoch,
                      release_epoch, XYZ0, NEU0, ref_frame)

        # Populate |data_neu|
        if data_neu is None:
            (E, N, U) = xyz2geo(data_xyz[:, 0], data_xyz[:, 1],
                                data_xyz[:, 2])
            data_neu = np.c_[N, E, U]

        # Calendar date and time (hour, minute, second)
        (day, month, year, ut) = mjd2cal(time[:, 1])
        (hour, minute, second) = ut2hms(ut)
        cal = list(map(format_epoch, year, month, day, hour, minute, second))
        # XYZ coordinates
        XYZ = list(map(lambda x: ('%14.5lf %14.5lf %14.5lf %8.5lf %8.5lf '
                                  '%8.5lf %6.3lf %6.3lf %6.3lf') % tuple(x), data_xyz))
        # NEU coordinates
        NEU = list(map(lambda x: '%14.10lf  %14.10lf %10.5lf' % tuple(x), data_neu))
        # dNEU coordinates
        data[:, :3] = data[:, :3]*1e-3
        dNEU = list(map(lambda x: ('%10.5lf%10.5lf%10.5lf   %8.5lf %8.5lf '
                                   '%8.5lf %6.3lf %6.3lf %6.3lf') % tuple(x), data))
        
        for k in range(time.shape[0]):
            f_pos.write(' %s %10.4lf %s     %s  %s itsa \n'
                        % (cal[k], time[k, 1], XYZ[k], NEU[k], dNEU[k]))

def read_POS(pos_file, ref_frame='Unknown',
               process='GX', neu=False, warn=True):
    """
    Read GipsyX pos file and load the time series into Gts object

    Parameters
    ----------

    pos_file : str, optional
        Pos file from GipysX processing to be readed.
        The default is None: |read_POS| look for '|self.code|*.pos' file.
    ref_frame : str, optional
        Reference frame of GipsyX processing.
        The default is 'Unknown'.
    process : str, optional
        Processing used to get the solution.
        The default is 'GX'.
    neu : bool, optional
        Populate |data_neu| if true.
        The default is False.
    warn : bool, optional
        Print warning if true.
        The default is True.
        
    Note
    ----
    With this function the information of |code|, |time|, |data|, |t0|, |XYZ0|,
    |NEU0|, |ref_frame|, |data_xyz| and |in_file| will be populated in |ts|
    (and |data_neu| if asked)
    
    """
    
    import numpy as np
    from itsa.lib.astrotime import cal2decyear, cal2mjd
    from itsa.lib.coordinates import xyz2geo
    
    # Read data
    data = np.genfromtxt(pos_file, skip_header=1)
    # Ensure 2D array
    if data.ndim == 1:
        data = np.array([data])
    # Change type
    d_date = data[:, :3].astype(int)
    
    # Populate
    # Make time array
    time = np.c_[cal2decyear(d_date[:, 2], d_date[:, 1], d_date[:, 0]), 
                      cal2mjd(d_date[:, 2], d_date[:, 1], d_date[:, 0])]
    # Make XYZ data array
    data_xyz = data[:, 3:12]
    # Reference variables
    # t0 = time[0, :]
    XYZ0 = data_xyz[0, :3]
    (E0, N0, U0) = xyz2geo(XYZ0[0], XYZ0[1], XYZ0[2])
    NEU0 = np.array([N0, E0, U0])
    ref_frame = ref_frame
    process = process

    # Populate if asked
    if neu:
        from itsa.lib.coordinates import xyz2geo
        (lon, lat, h) = xyz2geo(
            data_xyz[:, 0], data_xyz[:, 1], data_xyz[:, 2])
        data_neu = np.c_[lat, lon, h]
    
    return time, XYZ0, NEU0, data_xyz, data_neu, process

def XYZ2DNUE(XYZ0, data_xyz, corr=False, warn=True): #XYZ2DNUE
    """
    Populate dN, dE, dU (|data|) using XYZ (|data_xyz|)
    |XYZ0| and |NEU0| will also be set
    
    Parameters
    ----------
    corr : bool, optional
        Compute NEU STD and CORR (and populate |data|) if true.
        The default is False.
    warn : bool, optional
        Print warning if true.
        The default is True.
        
    Raise
    -----
    WARNING
        If |corr| is not bool: |corr| set to False.
        If NEU STD and CORR are set to np.nan: XYZ STD and CORR are not
                                               computed                       
    """
    
    import numpy as np
    from itsa.lib.coordinates import xyz2geo, mat_rot_general_to_local
    import warnings
    warnings.filterwarnings("error")
    
    # Compute rotation matrix
    (lon, lat, _) = xyz2geo(XYZ0[0], XYZ0[1], XYZ0[2])
    R = mat_rot_general_to_local(lon, lat)
    
    # Compute and populate dN, dE, dU coordinates
    # DXYZ
    DXYZ = data_xyz[:, :3]-XYZ0
    # DENU
    DENU = np.dot(R, DXYZ.T).T
    # Populate
    data = np.zeros(data_xyz.shape)*np.nan
    data[:, :3] = DENU[:, [1, 0, 2]]*1e3
    
    # Compute and populate NEU STD and CORR
    if corr:
        if not np.isnan(data_xyz[:, 3:]).all():
            # Import
            from itsa.lib.Glinalg import corr2cov, cov2corr

            for k in np.arange(data_xyz.shape[0]):
                # Read STD and CORR values for XYZ
                (_, _, _, Sx, Sy, Sz, Rxy, Rxz, Ryz) = data_xyz[k, :]
                # Create STD and CORR matrix for XYZ
                STD_XYZ = np.array([Sx, Sy, Sz])
                CORR_XYZ = np.array([[+1,  Rxy, Rxz],
                                     [Rxy,  1,  Ryz],
                                     [Rxz, Ryz, 1]])
                try:
                    # Compute COV for XYZ and ENU
                    COV_XYZ = corr2cov(CORR_XYZ, STD_XYZ)
                    COV_ENU = np.dot(np.dot(R, COV_XYZ), R.T)
                    # Compute CORR and STD for ENU
                    (CORR_ENU, STD_ENU) = cov2corr(COV_ENU)
                except:
                    pass
                else:
                    # Populate
                    data[k, 3:6] = STD_ENU[[1, 0, 2]]
                    data[k, 6:9] = CORR_ENU[[0, 1, 0], [1, 2, 2]]
    return data



def is_line_valid(line: str, forma: str) -> bool:
    """
    Check whether a single line conforms to the expected format:
    
        YYYY MM DD  X[m] Y[m] Z[m] Sx[m] Sy[m] Sz[m] Rxy Rxz Ryz
    
    - The line can contain any amount of whitespace (spaces or tabs) between fields.
    - After stripping leading/trailing whitespace, split() is used to separate fields.
    - We expect exactly 12 fields:
        indices 0–2: integers (year, month, day)
        indices 3–11: floats (X, Y, Z, Sx, Sy, Sz, Rxy, Rxz, Ryz)
    
    Returns True if the line matches exactly this pattern; False otherwise.
    """
    # Strip leading/trailing whitespace and split on any whitespace
    fields = line.strip().split()
    
    if forma == "pos":
        nbr_lines = 12
        int_number= 3
    elif forma == "pbo":
        nbr_lines = 25
        int_number=2
    
    # Immediately reject if field count is not exactly 12
    if len(fields) != nbr_lines:
        return False
    # print(len(fields), nbr_lines)
    
    try:
        # Attempt to parse the first three fields as integers
        for idx in range(int_number):
            _ = int(fields[idx])
        
        # Attempt to parse the remaining nine fields as floats
        for idx in range(int_number, nbr_lines-1):
            _ = float(fields[idx])
        
        return True
    except ValueError:
        # If any conversion fails, the format is invalid
        return False

def verify_file_structure(file_path: str, forma: str) -> bool:
    """
    Open and verify that every non-empty line in the file at `file_path` 
    matches the expected structure (see is_line_valid).
    
    - Empty lines (those containing only whitespace) are ignored.
    - On finding the first invalid line, prints its number and content, then returns False.
    - If all non-empty lines pass, prints a confirmation message and returns True.
    
    Example usage:
        python check_structure.py /path/to/your_file.txt
    """
    
    if forma == "pos":
        pattern = "YYYY MM"
    elif forma == "pbo":
        pattern = "*YYYYMMDD"
    
    try:
        with open(file_path, 'r') as f:
            header=True
            for lineno, raw_line in enumerate(f, start=1):
                # If the line is blank or contains only whitespace, skip it
                
                if header:
                    if (raw_line.strip()).startswith(pattern):
                        header=False
                    continue
                    
                if not raw_line.strip():
                    continue
                
                if not is_line_valid(raw_line, forma):
                    print(f"Invalid format detected on line {lineno}:")
                    print(f"    {raw_line.rstrip()}")
                    return False
        
        if header:
            print("Invalid format detected")
            return False
        
        # If we reach here, every non-empty line was valid
        print("All non-empty lines conform to the expected structure.")
        return True
    
    except FileNotFoundError:
        print(f"Error: File not found: {file_path}")
        return False
    except PermissionError:
        print(f"Error: Permission denied when trying to read: {file_path}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False



# if __name__ == "__main__":
    
#     pos_file  = "/Users/tsaponga/Desktop/Insar/old-rringg/AEDA.txt"
#     code      = "AEDA"
#     ref_frame = "IGS14"
#     outdir    = "/Users/tsaponga/Desktop/Insar"
    
#     data = write_PBO(pos_file, code, ref_frame)