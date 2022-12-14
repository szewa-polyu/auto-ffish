import xarray as xr
import numpy as np
from matplotlib import path
import pandas as pd
from datetime import datetime, timedelta
import os
import sys

import utils


# constants

# Setting for constants
input_dir = "/Users/perryma/Documents/GFS_WIND"
speed_lvl = np.array([0, .6, 2., 3.7, 5.6, 8.7, 11.4,
                     14.5, 17.5, 21.1, 24.5, 28.9, 32.8, 999])

# Setting for SCCW
areas_names = ["NanAo", "Shanwei", "South of HK",
               "ShangChuan Dao", "SE of Hainan", "South of BBW"]
time_periodsA = np.array([[0, 24], [0, 12], [13, 24]])
time_periodsB = np.array([[25, 72], [25, 48], [49, 72]])

# Corners must be set in anticlockwise sense
areas_corners = np.array([[[118.56, 24.51], [116.75, 23.34], [116.75, 20.63], [118.56, 21.2], [118.56, 24.51]],
                          [[116.75, 23.34], [115, 22.7], [115, 20.09],
                              [116.75, 20.63], [116.75, 23.34]],
                          [[115, 22.7], [113.26, 22.03], [
                              113.26, 19.52], [115, 20.09], [115, 22.7]],
                          [[113.26, 22.03], [111.67, 21.53], [111.67, 18.43],
                              [113.26, 19.52], [113.26, 22.03]],
                          [[111.67, 20.45], [110.94, 20.02], [109.6, 18.17],
                              [109.6, 17], [111.67, 18.43], [111.67, 20.45]],
                          [[109.6, 18.17], [108.64, 19.0], [105.62, 19.0], [107.11, 17], [109.6, 17], [109.6, 18.17]]], dtype="object")

for areanum in range(len(areas_names)):
    if areanum == 0:
        areas_paths = path.Path(areas_corners[areanum])
    else:
        areas_paths = np.append(areas_paths, path.Path(areas_corners[areanum]))

hkscorners = np.array([[115, 22.7], [113.26, 22.03], [
                      113.26, 19.52], [115, 20.09], [115, 22.7]])
hkspath = path.Path(hkscorners)

# end of constants


# Forecast start
fcstart = os.environ.get("issue_ymdh")
fcstart_datetime = datetime.strptime(
    fcstart, "%Y%m%d%H") - timedelta(hours=8)  # Correct to UTC

# Search initial:
searchinitial = True
gotinitial = False
for hourbefore in range(25):  # Use model data no earlier than 24 hours.
    initial_datetime = fcstart_datetime - timedelta(hours=hourbefore)
    initial = initial_datetime.strftime("%Y%m%d%H")
    if os.path.exists(input_dir + "/" + initial[0:10]):
        gotinitial = True
        break

if not gotinitial:
    sys.exit('No available model data within 24 hours.. Abort.')

# Check exists df
file_df = "GFS_fcst" + str(fcstart) + "_init" + str(initial) + ".pkl"

if os.path.exists(input_dir + "/" + file_df):
    df = pd.read_pickle(input_dir + "/" + file_df)
else:
    df = pd.DataFrame()
    firstfile = True
    # Turn data into dataframe
    for fchour in range(73):  # 0-72
        hourfrominitial = fchour + hourbefore
        hourfrominit_str = str(hourfrominitial).zfill(3)
        targetfile = input_dir + "/" + \
            initial[0:10] + "/gfs.t" + initial[8:10] + \
            "z.pgrb2.0p25.f" + hourfrominit_str + ".nc"
        if not os.path.exists(targetfile):
            continue
        dat = xr.load_dataset(targetfile)
        if firstfile:
            lon = dat["lon_0"]
            lat = dat["lat_0"]
            land = dat["LAND_P0_L1_GLL0"]
            firstfile = False

        u = dat["UGRD_P0_L103_GLL0"].loc[10, :, :].values
        v = dat["VGRD_P0_L103_GLL0"].loc[10, :, :].values
        lon2d, lat2d = np.meshgrid(lon.values, lat.values)

        SCCW = np.logical_and.reduce(
            (lon2d > 100, lon2d < 130, lat2d > 10, lat2d < 30, land == 0))
        u_SCCW = u[SCCW].flatten()
        v_SCCW = v[SCCW].flatten()
        lon_SCCW = lon2d[SCCW].flatten()
        lat_SCCW = lat2d[SCCW].flatten()

        df_temp = pd.DataFrame(
            {"lon": lon_SCCW, "lat": lat_SCCW, "u": u_SCCW, "v": v_SCCW})
        df_temp["fchour"] = fchour
        df = pd.concat([df, df_temp], ignore_index=True)
        df.to_pickle(input_dir + "/" + file_df)
df["region"] = df.apply(lambda x: utils.get_region(
    areas_paths, areas_names, x.lat, x.lon), axis=1)
df["spd"] = np.sqrt(df["u"]*df["u"]+df["v"]*df["v"])
# Note for the convention (N'ly = 0deg)
df["dir"] = np.arctan2(-1*df["u"], -1*df["v"])*180/np.pi
df["force"] = pd.cut(df.spd, speed_lvl, right=False, labels=range(13))
df["cardinal"] = df.apply(lambda x: utils.get_cardinal(x.dir), axis=1)

with open(input_dir + "/SCCW_GFS_fcst" + str(fcstart) + "_init" + str(initial) + ".txt", 'w') as f:
    currenttime = datetime.now().strftime("%Y%m%d%H%M")
    # print("********************** AUTO-SCCW ***********************", file=f)
    # print("*** Careful interpretation by meteorologist required ***", file=f)
    # print("************ Generated at " + currenttime[0:8] + " " + currenttime[8:12] + "HKT *************", file=f)
    # print("********************************************************", file=f)
    print("AUTO-SCCW", file=f)
    print("Careful interpretation by meteorologist required", file=f)
    print("Generated at " + currenttime[0:8] +
          " " + currenttime[8:12] + "HKT", file=f)
    print("================================================", file=f)
    print("For forecast from: " +
          fcstart[0:8] + " " + fcstart[8:10] + "HKT", file=f)
    print("Based on NCEP model run: " +
          initial[0:8] + " " + initial[8:10] + "UTC", file=f)
    print("For First 24 Hours", file=f)
    for area_ind in range(len(areas_names)):
        area = areas_names[area_ind]
        print(area + ":", file=f)
        for timeperiod_ind in range(len(time_periodsA)):
            time_period = time_periodsA[timeperiod_ind]
            dirstr, forcestr = utils.get_forecast(df, area, time_period)
            print(str(time_period[0]) + "-" + str(time_period[1]
                                                  ) + " hours: " + dirstr + " " + forcestr, file=f)

    print("For next 48 Hours:", file=f)
    for area_ind in range(len(areas_names)):
        area = areas_names[area_ind]
        print(area + ":", file=f)
        for timeperiod_ind in range(len(time_periodsB)):
            time_period = time_periodsB[timeperiod_ind]
            dirstr, forcestr = utils.get_forecast(df, area, time_period)
            print(str(time_period[0]) + "-" + str(time_period[1]
                                                  ) + " hours: " + dirstr + " " + forcestr, file=f)
