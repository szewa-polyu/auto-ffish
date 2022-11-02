import numpy as np


# constants

cardinal_names = np.array(["S", "SW", "W", "NW", "N", "NE", "E", "SE"])
# cardinal_names_rep = np.array(["S", "SW", "W", "NW", "N", "NE", "E", "SE", "S"])
cardinal_deg = np.array(range(-180, 180, 45))

# end of constants


def get_region(areas_paths, areas_names, lat, lon):
    region = "Outside"
    lon = float(lon)
    lat = float(lat)
    for i in range(len(areas_paths)):
        if areas_paths[i].contains_point((lon, lat)):
            region = areas_names[i]
            break
    return region


def get_cardinal(dir_deg):
    # https://stackoverflow.com/questions/1878907/how-can-i-find-the-difference-between-two-angles
    anglediff = np.abs((dir_deg - cardinal_deg + 180) % 360 - 180)
    cardinal = cardinal_names[anglediff == anglediff.min()]
    if len(cardinal) == 2:
        if len(cardinal[0]) == 1:
            cardinal = cardinal[0]
        else:
            cardinal = cardinal[1]
    else:
        cardinal = cardinal[0]
    # for i in range(len(cardinal_names_rep)):
    #     if i % 2 == 0:
    #         if dir_deg < 22.5 - 180 + i*45:
    #             cardinal = cardinal_names_rep[i]
    #             break
    #     else:
    #         if dir_deg <= 22.5 - 180 + i*45:
    #             cardinal = cardinal_names_rep[i]
    #            break
    return cardinal


def get_forecast(df, region, time_period):
    # input: dataframe, region, time_period(array)
    # Filter
    df_filter = df.loc[(df.region == region) & (
        df.fchour >= time_period[0]) & (df.fchour <= time_period[1])]
    # Force
    # Rule: if Prob(maxforce) < 0.05 -> occasional
    # if Prob(maxforce) > 0.5 -> give one force level
    maxforce = max(df_filter.force)
    maxforcepercent = df_filter.force.loc[df_filter.force == maxforce].count(
    ) / df_filter.force.count()
    if maxforcepercent > 0.5:
        forcestr = str(maxforce)
    else:
        if maxforcepercent < 0.05:
            forcestr = str(maxforce - 2) + "-" + str(maxforce -
                                                     1) + ", occasionally " + str(maxforce)
        else:
            forcestr = str(maxforce - 1) + "-" + str(maxforce)

    # Wind Dir
    modewind = df_filter.cardinal.value_counts().reset_index()["index"][0]
    modewindpercent = df_filter.cardinal.value_counts(
    )[0] / sum(df_filter.cardinal.value_counts())
    modewindindex = int(np.where(cardinal_names == modewind)[0])
    if modewindpercent > 0.8:
        dirstr = modewind
    else:
        findmodewind2 = True
        moderank = 1  # Search the rank of wind dataframe
        modewind2A = cardinal_names[(modewindindex + 1) % 8]
        modewind2B = cardinal_names[(modewindindex - 1) % 8]
        while findmodewind2:
            modewind2_temp = df_filter.cardinal.value_counts().reset_index()[
                "index"][moderank]
            if modewind2_temp == modewind2A:
                modewind2 = modewind2A
                findmodewind2 = False
            elif modewind2_temp == modewind2B:
                modewind2 = modewind2B
                findmodewind2 = False
            else:
                moderank = moderank + 1
        if len(modewind) == 1:
            dirstr = modewind + "-" + modewind2
        else:
            dirstr = modewind2 + "-" + modewind
    return dirstr, forcestr
