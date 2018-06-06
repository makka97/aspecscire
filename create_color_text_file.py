import gdal
import numpy as np
import sys
import argparse
import csv
import math
import logging
gdal.UseExceptions()

logging.basicConfig(filename = "loggingFile.log", level = logging.DEBUG)

def input_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("DEM_file_path", type = str, help = "insert DEM path")
    parser.add_argument("output_color_file", type = str, help = "output color text file")
    parser.add_argument("--DEM_type", type = str, help = "specify DEM type")
    parser.add_argument("--input_color_file", type = str, help = "insert file containing color values")
    parser.add_argument("--range", type = float, nargs='?', const=0.7, help = "range of error in formwork")
    parser.add_argument("--max_value", type = int, help = "maximum value in the range")
    parser.add_argument("--min_value", type = int, help = "minimum value in the range")
    logging.info("command line inputs recognised")
    return(parser.parse_args()) 

def read_raster(dem_file_path):
    src_ds = gdal.Open(dem_file_path)
    src_band = src_ds.GetRasterBand(1).ReadAsArray().astype(np.float).flatten()
    no_data_val = src_ds.GetRasterBand(1).GetNoDataValue()
    no_data_index = np.where(src_band==no_data_val)
    logging.info("elevation values from raster stored in array")
    return(np.delete(src_band,no_data_index)) 

def cluster_centroids(classes, w, clusters, k):
    results=[]
    for i in range(k):
        results.append(np.average(classes[clusters == i],weights = w[clusters ==i]))
    return results

def weighted_kmeans(classes, w, k=None, no_of_it=300):
    centroids = []
    centroids.append(np.random.choice(classes))
    cen_dists = []
    for i in range(k-1):
        dists = []
        for j in range(len(classes)):
            dists.append(abs(classes[j]-centroids[i]))
        cen_dists.append(dists)  
        min_dists = np.min(cen_dists, axis = 0)
        prob = w*np.square(min_dists)/sum((w*np.square(min_dists)))
        centroids.append(np.random.choice(classes, replace = False, p = prob))   

    for n in range(no_of_it):
        cen_dists=[]
        for i in range(len(classes)):
            dists = []
            for j in range(len(centroids)):
                dists.append(abs(classes[i] - centroids[j]))
            cen_dists.append(dists)
        
        clusters = []
        for i in range(len(cen_dists)):
            dist = cen_dists[i]
            clusters.append(dist.index(min(dist)))
        clusters = np.array(clusters)
        
        new_centroids = cluster_centroids(classes, w, clusters, k)
        if np.array_equal(new_centroids, centroids):
            break
        else:
            if(n == no_of_it):
                raise ValueError("Centroids did not converge")

        centroids = new_centroids
        
    score_list = []
    for i in range(len(cen_dists)):
        score_list.append(w[i]*(min(cen_dists[i])**2))
    score_sum = sum(score_list)
    
    return clusters, centroids, score_sum

def set_up(src_band_array, b):
    no_of_bins = int((src_band_array.max()-src_band_array.min())/b)
    weights, bin_edges = np.histogram(src_band_array, bins = no_of_bins)
    zero_index = np.where(weights==0)
    w = np.delete(weights,zero_index)
    bins = []
    value = src_band_array.min()
    for i in range(no_of_bins):
        bins.append(value)
        value = value + b
    bins = np.array(bins)
    classes = np.delete(bins,zero_index)
    return classes, w

def no_of_classes( 
        data,
        src_band_array,
        dem_type,
        floor_height_deviation_m, 
        min_height_m,
        max_height_m):
    elevation = []
    if dem_type == 'formwork':
        logging.debug(floor_height_deviation_m)
        b = 0.001
        classes, w = set_up(src_band_array, b)
        cluster, cen, score = weighted_kmeans(classes, w, data)
        while((b/math.sqrt(score/len(classes))>=0.01)):
            b = 0.1*b
            classes, w = set_up(src_band_array, b)
            cluster, cen, score = weighted_kmeans(classes, w, data)
        mode = []
        for i in range(len(cen)):
            index = np.where(cluster == i)
            mode.append(np.sum(w[index]))
        floor = cen[mode.index(max(mode))]
        logging.debug(floor)
        range_array = src_band_array[(src_band_array<=floor+floor_height_deviation_m) & (src_band_array>=floor-floor_height_deviation_m)]
        b = 0.001
        classes, w = set_up(range_array, b)
        cluster, cen, score = weighted_kmeans(classes, w, data-2)
        while((b/math.sqrt(score/len(classes))>=0.01)):
            b = 0.1*b
            classes, w = set_up(range_array, b)
            cluster, cen, score = weighted_kmeans(classes, w, data-2)
        elevation.extend(sorted(cen))
        elevation.insert(0,floor-floor_height_deviation_m)
        elevation.append(floor+floor_height_deviation_m)
        
    elif dem_type == 'time-series':
        value = min_height_m
        for i in range(data-2):
            elevation.append(value)
            value = value + ((max_height_m - min_height_m)/(data - 3))
        elevation.insert(0,src_band_array.min())
        elevation.append(src_band_array.max())        
        
    else:
        b = 0.001
        classes, w = set_up(src_band_array, b)
        cluster, cen, score = weighted_kmeans(classes, w, data-2)
        while((b/math.sqrt(score/len(classes))>=0.01)):
            b = 0.1*b
            classes, w = set_up(src_band_array, b)
            cluster, cen, score = weighted_kmeans(classes, w, data-2)
        elevation.extend(sorted(cen))
        elevation.insert(0,src_band_array.min())
        elevation.append(src_band_array.max())
    return(elevation)

def create_color_file(
        dem_file_path, 
        output_color_file, 
        dem_type='single', 
        floor_height_deviation_m=0.7, 
        min_height_m=0,
        max_height_m=100,
        input_color_file=None):
    
    types = ['single', 'formwork', 'time-series']
    if dem_type not in types:
        raise ValueError("specify dem type")

    if input_color_file != None:
        arr = []
        with open(input_color_file) as csvfile:
            reader = csv.reader(csvfile, delimiter=' ')
            for row in reader:
                arr.append(row)
    else :
        if dem_type == 'formwork':
            arr = [['0', '0', '0'], ['128', '0', '0'], ['160', '82', '45'], ['255', '0', '0'], ['255', '160', '122'], ['255', '140', '0'], ['218', '165', '32'], ['255', '255', '0'], ['154', '205', '50'], ['0', '255', '0'], ['0', '128', '0'], ['60', '179', '113'], ['102', '205', '170'], ['0', '255', '255'], ['0', '139', '139'], ['0', '0', '255'], ['0', '0', '128'], ['128', '0', '128'], ['199', '21', '133'], ['255', '0', '255'], ['0', '0', '0']]
        else:
            arr = [['0', '0', '0'], ['255', '0', '0'], ['204', '51', '0'], ['255', '166', '77'], ['255', '210', '77'], ['153', '255', '153'], ['51', '204', '51'], ['0', '153', '51'], ['204', '203', '255'], ['128', '179', '255'], ['179', '128', '255'], ['255', '102', '255'], ['0', '0', '0']]
    data_length = len(arr)

    src_band_array = read_raster(dem_file_path)

    elevation = no_of_classes(data_length, src_band_array, dem_type, floor_height_deviation_m, min_height_m, max_height_m)
    logging.debug(elevation)

    x = len(elevation)
    y = len(arr)/x
    new_arr=[]
    for i in range(x):
        j = int(y*i)
        arr[j].insert(0,elevation[i])
        new_arr.append(arr[j][:])
    new_arr.append(['nv',000,000,000])

    with open(output_color_file,'w') as csvfile:
        writer = csv.writer(csvfile, delimiter =' ')
        for ar in new_arr:
            writer.writerow(ar)
    logging.debug(new_arr)
    logging.info("output color text file created")
    return(output_color_file)

if __name__ == "__main__":
    args = input_arguments()
    src_band_array = read_raster(args.DEM_file_path)
    output_color_file = create_color_file(args.DEM_file_path, args.output_color_file, dem_type = args.DEM_type, floor_height_deviation_m = args.range, min_height_m = args.min_value, max_height_m = args.max_value, input_color_file = args.input_color_file)