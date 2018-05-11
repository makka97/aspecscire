import gdal
import numpy as np
import sys
import argparse
import matplotlib
# this allows GDAL to throw Python Exceptions
gdal.UseExceptions()

def make_histogram(arr,bin):
    hist = np.histogram(arr,bins = bin)
    matplotlib.pyplot.hist(arr,bin)
    return hist

try:
    src_ds = gdal.Open( "/home/makka/16june2017-planer-dem.tif" )
except RuntimeError as e:
    print ('Unable to open')
    print (e)
    sys.exit(1)

try:
    src_band = src_ds.GetRasterBand(1).ReadAsArray().astype(np.float).flatten()
    no_data_val = src_ds.GetRasterBand(1).GetNoDataValue()
    no_data_index = np.where(src_band==no_data_val)
    #print(nodataval)
    #print(nodataindex)
    src_band_array = np.delete(src_band,no_data_index)
    #print (srcbandarray)
    parser = argparse.ArgumentParser()
    parser.add_argument("no_of_bins",type=int,help = "to add the no of bins")
    args = parser.parse_args()
    bins = args.no_of_bins
    histogram = make_histogram(src_band_array,bins)
    print (histogram)
except RuntimeError as e:
    # for example, try GetRasterBand(10)
    print ('Band not found')
    print (e)
    sys.exit(1)
