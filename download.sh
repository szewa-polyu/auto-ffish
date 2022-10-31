#!/bin/sh

# Download GFS data

if [ $# -ne 1 ]; then
  echo "./download.sh [ymdh]"
  exit 1
fi

ymdh=$1

mkdir ${ymdh}
cd ./${ymdh}
for tfc in `seq -f "%03g" 0 3 96`; do
  # wget -c  https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/gfs.${ymdh:0:8}/${ymdh:8:2}/atmos/gfs.t${ymdh:8:2}z.pgrb2.0p25.f${tfc}
  outputgrb=gfs.t${ymdh:8:2}z.pgrb2.0p25.f${tfc}
  wget -O ${outputgrb} "https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl?file=gfs.t${ymdh:8:2}z.pgrb2.0p25.f${tfc}&var_UGRD=on&var_VGRD=on&var_LAND=on&subregion=&leftlon=100&rightlon=125&toplat=30&bottomlat=10&dir=%2Fgfs.${ymdh:0:8}%2F${ymdh:8:2}%2Fatmos"
  ncl_convert2nc ${outputgrb} -e grb -L
  sleep 15
done
