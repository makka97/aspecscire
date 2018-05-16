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

def input_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_DEM_file", type = str, help = "insert DEM")
    parser.add_argument("output_DEM_file", type = str, help = "output DEM file")
    parser.add_argument("color_file", type = str, help = "insert file containing color values")
    parser.add_argument("--layer_elevation_file", type = argparse.FileType('r'), help = "file which describes the layers and corresponding names of the DEM")
    parser.add_argument("--max_value", type = int, help = "maximum value in the range")
    parser.add_argument("--min_value", type = int, help = "minimum value in the range")
    parser.add_argument("--k", type = int, help = "number of classes")
    return(parser.parse_args()) 

def read_raster(args):
    src_ds = gdal.Open( args.input_DEM_file )
    src_band = src_ds.GetRasterBand(1).ReadAsArray().astype(np.float).flatten()
    no_data_val = src_ds.GetRasterBand(1).GetNoDataValue()
    no_data_index = np.where(src_band==no_data_val)
    return(np.delete(src_band,no_data_index)) 

def no_of_classes(args, src_band_array):
    elevation = []
    exp_elevation = []
    if args.layer_elevation_file:
        layer_data = json.load(args.layer_elevation_file)
        k = len(layer_data.values())
        exp_elevation.extend(sorted(list(layer_data.values())))
        kmeans = KMeans(n_clusters = k).fit(src_band_array.reshape(-1,1))
        cluster_center = np.array([x[0] for x in kmeans.cluster_centers_])
        elevation.extend(sorted(cluster_center.tolist()))

    elif (args.max_value and args.min_value):
        value = args.min_value
        with open(args.color_file) as csvfile:
            reader = csv.reader(csvfile, delimiter=' ')
            data = len(list(reader))
        for i in range(data):
            elevation.append(value)
            value = value + ((args.max_value - args.min_value)/(data - 1))
        k = data
        
    else:
        kmeans = KMeans(n_clusters = args.k).fit(src_band_array.reshape(-1,1))
        cluster_center = np.array([x[0] for x in kmeans.cluster_centers_])
        elevation.extend(sorted(cluster_center.tolist()))
        k = args.k
    return([elevation,k])

def create_color_file(args, elevation_values):

    print(elevation_values[0])
    print(elevation_values[1])

    elevation = elevation_values[0]
    k = elevation_values[1]
    arr = []
    new_arr=[]
    with open(args.color_file) as csvfile:
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

    output_color_file = args.color_file.replace('.txt','_output.txt')
    with open(output_color_file,'w') as csvfile:
        writer = csv.writer(csvfile, delimiter =' ')
        for ar in new_arr:
            writer.writerow(ar)
    return(output_color_file)

args = input_arguments()
src_band_array = read_raster(args)
elevation_values = no_of_classes(args, src_band_array)
output_color_file = create_color_file(args, elevation_values) 
subprocess.call(["gdaldem", "color-relief", args.input_DEM_file , output_color_file, args.output_DEM_file])        


