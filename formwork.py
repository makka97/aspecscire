import gdal
import numpy as np
import sys
import argparse
from sklearn.cluster import KMeans
from matplotlib import pyplot as plt
import csv
import json
import subprocess
# this allows GDAL to throw Python Exceptions
gdal.UseExceptions()

parser = argparse.ArgumentParser()
parser.add_argument("input_DEM_file", type = str, help = "insert DEM")
parser.add_argument("output_DEM_file", type = str, help = "output DEM file")
parser.add_argument("--layer_elevation_file", type = argparse.FileType('r'), help = "file which describes the layers and corresponding names of the DEM")
parser.add_argument("--max_value", type = int, help = "maximum value in the range")
parser.add_argument("--min_value", type = int, help = "minimum value in the range")
parser.add_argument("--k", nargs = '?', const = 11, type = int, help = "number of classes")

args = parser.parse_args()
src_ds = gdal.Open( args.input_DEM_file )
src_band = src_ds.GetRasterBand(1).ReadAsArray().astype(np.float).flatten()
no_data_val = src_ds.GetRasterBand(1).GetNoDataValue()
no_data_index = np.where(src_band==no_data_val)
src_band_array = np.delete(src_band,no_data_index)


elevation = []
exp_elevation = []
if args.layer_elevation_file:
    layer_data = json.load(args.layer_elevation_file)
    k = len(layer_data.values())
    exp_elevation.extend(sorted(list(layer_data.values())))
    kmeans = KMeans(n_clusters = k).fit(src_band_array.reshape(-1,1))
    cluster_center = np.array([x[0] for x in kmeans.cluster_centers_])
    elevation.extend(sorted(cluster_center.tolist()))
    

elif (args.max_value and args.min_value and args.k):
    value = args.min_value
    for i in range(0,11):
        elevation.append(value)
        value = value + ((args.max_value - args.min_value)/10)
        k = args.k
    
else:
    kmeans = KMeans(n_clusters = args.k).fit(src_band_array.reshape(-1,1))
    cluster_center = np.array([x[0] for x in kmeans.cluster_centers_])
    elevation.extend(sorted(cluster_center.tolist()))
    k = args.k

print(elevation)

arr = []
new_arr=[]
with open("/home/malavika/clrTxtFile.txt") as csvfile:
    reader = csv.reader(csvfile, delimiter=' ')
    for row in reader:
        arr.append(row)

i = 0
j = 0
while(j<k*int(11/k)):
    arr[j].insert(0,elevation[i])
    new_arr.append(arr[j][:])
    j = j + int(11/k)
    i = i + 1
new_arr.append(['nv',000,000,000])

print(new_arr)

with open("/home/malavika/clr_file.txt",'w') as csvfile:
    writer = csv.writer(csvfile, delimiter =' ')
    for ar in new_arr:
        writer.writerow(ar)


subprocess.call(["gdaldem", "color-relief", args.input_DEM_file ,"/home/malavika/clr_file.txt",args.output_DEM_file])        


