import gdal
import numpy as np
import sys
import argparse
from sklearn.cluster import KMeans
from matplotlib import pyplot as plt
import csv
import json
import subprocess
import statistics
# this allows GDAL to throw Python Exceptions
gdal.UseExceptions()

def input_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_DEM_file", type = str, help = "insert DEM")
    parser.add_argument("color_file", type = str, help = "insert file containing color values")
    parser.add_argument("output_color_file", type = str, help = "output color text file")
    parser.add_argument("--range", type = float, help = "range of error in formwork")
    parser.add_argument("--max_value", type = int, help = "maximum value in the range")
    parser.add_argument("--min_value", type = int, help = "minimum value in the range")
    parser.add_argument("--k", type = int, help = "number of classes")
    parser.add_argument("--flag", help = "number of classes", action = "store_true")
    return(parser.parse_args()) 

def read_raster(args):
    src_ds = gdal.Open( args.input_DEM_file )
    src_band = src_ds.GetRasterBand(1).ReadAsArray().astype(np.float).flatten()
    no_data_val = src_ds.GetRasterBand(1).GetNoDataValue()
    no_data_index = np.where(src_band==no_data_val)
    return(np.delete(src_band,no_data_index)) 

def no_of_classes(args, src_band_array):
    elevation = []
    if args.range:
        with open(args.color_file) as csvfile:
            reader = csv.reader(csvfile, delimiter=' ')
            data = len(list(reader))
        kmeans = KMeans(n_clusters = data).fit(src_band_array.reshape(-1,1))
        cluster_center = np.array([x[0] for x in kmeans.cluster_centers_])
        center_index = kmeans.predict(src_band_array.reshape(-1,1))
        floor = cluster_center[statistics.mode(center_index)]
        value = floor - args.range
        for i in range(data):
            elevation.append(value)
            value = value + (2*args.range)/data

    elif (args.max_value and args.min_value):
        value = args.min_value
        with open(args.color_file) as csvfile:
            reader = csv.reader(csvfile, delimiter=' ')
            data = len(list(reader))
        for i in range(data):
            elevation.append(value)
            value = value + ((args.max_value - args.min_value)/(data - 1))
        
    else:
        kmeans = KMeans(n_clusters = args.k).fit(src_band_array.reshape(-1,1))
        cluster_center = np.array([x[0] for x in kmeans.cluster_centers_])
        elevation.extend(sorted(cluster_center.tolist()))
    return(elevation)

def create_color_file(args, elevation):

    print(elevation)
    
    arr = []
    new_arr=[]
    with open(args.color_file) as csvfile:
        reader = csv.reader(csvfile, delimiter=' ')
        for row in reader:
            arr.append(row)

    x = len(elevation)
    y = len(arr)/x
    for i in range(x):
        j = int(y*i)
        arr[j].insert(0,elevation[i])
        new_arr.append(arr[j][:])

    new_arr.append(['nv',000,000,000])

    print(new_arr)

    with open(args.output_color_file,'w') as csvfile:
        writer = csv.writer(csvfile, delimiter =' ')
        for ar in new_arr:
            writer.writerow(ar)
    return(args.output_color_file)

args = input_arguments()
src_band_array = read_raster(args)
elevation = no_of_classes(args, src_band_array)
output_color_file = create_color_file(args, elevation) 

if args.flag:
    subprocess.call(["gdaldem", "color-relief", args.input_DEM_file , output_color_file, args.input_DEM_file.replace(".tif", "_colorised_output.tif")])        


