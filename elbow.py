import gdal
import numpy as np
import sys
import argparse
from sklearn.cluster import KMeans
from matplotlib import pyplot as plt
# this allows GDAL to throw Python Exceptions
gdal.UseExceptions()

parser = argparse.ArgumentParser()
parser.add_argument("input_DEM_file", type = str, help = "insert DEM")
args = parser.parse_args()

src_ds = gdal.Open( args.input_DEM_file )
src_band = src_ds.GetRasterBand(1).ReadAsArray().astype(np.float).flatten()
no_data_val = src_ds.GetRasterBand(1).GetNoDataValue()
no_data_index = np.where(src_band==no_data_val)
src_band_array = np.delete(src_band,no_data_index)

kmeans = KMeans(n_clusters = 11).fit(src_band_array.reshape(-1,1))
cluster_center = np.array(kmeans.cluster_centers_)

scores = []
for i in range(1,20):
    scores.append(KMeans(n_clusters = i).fit(src_band_array.reshape(-1,1)).score(src_band_array.reshape(-1,1)))
plt.clf()
plt.plot(range(1,20),scores)
plt.show()