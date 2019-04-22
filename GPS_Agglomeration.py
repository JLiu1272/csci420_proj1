"""
Name: JosephGolden, JenniferLiu
File: GPS_Agglomeration.py
"""

# Dendogram
from scipy.cluster.hierarchy import dendrogram, linkage

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import math

# DBScan
from sklearn.cluster import DBSCAN
from geopy.distance import great_circle
from shapely.geometry import MultiPoint

# Cosine Similarity
from numpy import dot
from numpy.linalg import norm

from collections import Counter
from scipy.cluster import hierarchy
from sklearn.cluster import KMeans


def DBScan_Cluster(coords):
    '''
    Perform DBScanning of the GPS Location
    :param coords: A list of Coordinates [time, lon, lat, speed]
    :return: A list of medoids, and a list of points in every possible cluster
    '''

    # A list extracting only the Lon and Lat Coordinates
    lon_lat_coords = [(coord[1], coord[2]) for coord in coords]

    db = DBSCAN(eps=0.00001, min_samples=2, algorithm='auto', metric='manhattan').fit(lon_lat_coords)
    cluster_labels = db.labels_
    num_clusters = len(set(cluster_labels))

    # Put the points into respective bins, given which cluster
    # the point was classified in
    clusters = pd.Series([coords[cluster_labels == n] for n in range(num_clusters)])
    print('Number of clusters: {}'.format(num_clusters))

    total_pts = len(cluster_labels)
    print("Total points in cluster")
    print(total_pts)
    medoids = get_medoid(clusters)
    print(medoids.head(10))

    return medoids, clusters


def sort_points(coords):
    '''
    Sorts the coordinates from smallest to largest.
    It first finds the smallest longitude, if it cannot
    find the smallest longitutde, it finds the smallest
    latitude. The sorting mechanism is used to find multiple
    GPS tracks that are in similar pathways.
    :param coords:
    :return:
    '''
    return pd.DataFrame(sorted(coords, key=lambda coord: [coord[2], coord[1]]), columns=['time', 'lon', 'lat', 'speed'])

def perpendicular_dist(x1, y1, x2, y2, x3, y3):
    px = x2 - x1
    py = y2 - y1

    norm = px * px + py * py

    u = ((x3 - x1) * px + (y3 - y1) * py) / float(norm)

    if u > 1:
        u = 1
    elif u < 0:
        u = 0

    x = x1 + u * px
    y = y1 + u * py

    dx = x - x3
    dy = y - y3

    dist = (dx * dx + dy * dy) ** .5

    return dist



def get_medoid(clusters):
    '''
    For every cluster, find the medoid
    :param clusters: The clusters that DBScan found
    :return: a list of medoids for each DBScan cluster
    '''

    # For every cluster, find a real point
    # that is closest to the cluster
    # and save that
    medoids = {'time': [], 'lon': [], 'lat': [], 'speed': []}

    for cluster in clusters:

        # Only calculate the the centroid, if there are points
        # in the cluster
        if len(cluster) > 0:

            # For each cluster, get the centroid, and find the closest
            # point to the centroid, but still a point within the original
            # data
            lon_lat_clust = np.array([[coord[1], coord[2]] for coord in cluster])
            centroid = (MultiPoint(lon_lat_clust).centroid.x, MultiPoint(lon_lat_clust).centroid.y)
            medoid = find_minDist(centroid, lon_lat_clust)
            medoids['time'].append(np.mean(cluster[:,0]))
            medoids['lon'].append(medoid[0])
            medoids['lat'].append(medoid[1])
            medoids['speed'].append(np.mean(cluster[:,3]))

    # Google Earth doesn't like it when
    # there are duplicated coordinates
    # this prevents that
    medoids_df = pd.DataFrame.from_dict(medoids)
    medoids_df = medoids_df.drop_duplicates(subset=['lon', 'lat'])

    # Reset index, so that you don't see 0, 9, 10 etc...
    medoids_df = medoids_df.reset_index()

    return medoids_df

def find_minDist(centroid, cluster):
    '''
    Find the smallest distance between a real point
    in the cluster and the centroid
    :param centroid: The referenced centroid
    :param cluster: Info about the cluster
    :return:
    '''

    min_dist = float("inf")
    min_medoid = None

    # Traverse through the cluster
    # and each time it finds a distance
    # between centroid and a real point that
    # is smaller than what is available
    # save this
    for point in cluster:
        new_dist = np.linalg.norm(point - centroid)
        if new_dist < min_dist:
            min_medoid = point
            min_dist = new_dist

    # Return a true point that is closest to the
    # centroid
    return min_medoid

def convert_counter(counter):

    new_counter = {}

    for key in counter.keys():
        new_counter[key] = counter[key]

    return new_counter

def cosine_distances(a, b):
    '''
    Compute cosine similarity. Planning to
    use this for detecting turns
    :param a: Point A
    :param b: Point B
    :return: the Cosine Similarity
    '''
    return dot(a, b)/(norm(a)*norm(b))


def k_means(coords, n):
    '''
    Using K-Means the cluster the coordinates
    :param coords: The coordinates [time, lon, lat, speed]
    :param n: The number of clusters to make
    :return: A list of medoid for each cluster
    '''

    # Extract the Lon, Lat values only for K Means clustering
    lon_lat_coords = np.array([[coord[1], coord[2]] for coord in coords])
    kmeans = KMeans(n_clusters=n)
    kmeans.fit(lon_lat_coords)

    cluster_labels = kmeans.labels_
    num_clusters = len(set(cluster_labels))

    # Put the points in the respective cluster
    clusters = pd.Series([coords[cluster_labels == n] for n in range(num_clusters)])
    print('Number of clusters: {}'.format(num_clusters))

    medoids = get_medoid(clusters)

    #print(medoids.head(10))

    return medoids

# Not sure whether I will use it or not, so I will leave it here
def agglomerate(coords):
    lon_lat_coords = np.array([[coord[1], coord[2]] for coord in coords])
    Z = linkage(coords, method='single', metric=lambda u,v: cosine_distances(u,v))
    #dendrogram(Z, leaf_rotation=0, orientation='right', leaf_font_size=8)
    #plt.show()

    agg_clusters = hierarchy.fcluster(Z, 6000, criterion='distance', R=None, monocrit=None)

    print(agg_clusters)

    #freq_table = convert_counter(Counter(agg_clusters))
    agglom_points = []

    #print(freq_table)

    """
    for idx, cluster_id in enumerate(agg_clusters):
        if isinstance(freq_table[cluster_id], int):
            agglom_points.append(data[idx])
            freq_table[cluster_id] = data.iloc[idx]

    df = pd.DataFrame(agglom_points)
    df = df.reset_index(drop=True)
    print(df.head(10))

    return df

    print(data[:10])

    agglom_points = []

    print("Clusters")
    print(agg_clusters)

    freq_table = convert_counter(Counter(agg_clusters))
    print(len(freq_table.keys()))

    for idx, cluster_id in enumerate(agg_clusters):
        if isinstance(freq_table[cluster_id], int):
            agglom_points.append(data.iloc[idx])
            freq_table[cluster_id] = data.iloc[idx]

    df = pd.DataFrame(agglom_points)
    df = df.reset_index(drop=True)
    print(df.head(10))


    #dendrogram(Z, leaf_rotation=0, orientation='right', leaf_font_size=8, labels=np.array([i for i in range(data.shape[0])]))
    #plt.show()
    """