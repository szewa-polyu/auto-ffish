#!/bin/sh

# Convert GFS data

if [ $# -ne 1 ]; then
  echo "./convert.sh [ymdh]"
  exit 1
fi

ymdh=$1

mkdir ${ymdh}
cd ./${ymdh}
for tfc in `seq -f "%03g" 63 3 96`; do
  ncl_convert2nc gfs.t${ymdh:8:2}z.pgrb2.0p25.f${tfc} -e grb -L
done

