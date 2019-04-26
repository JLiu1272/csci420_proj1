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

    db = DBSCAN(eps=0.0001, min_samples=15, algorithm='auto', metric='manhattan').fit(lon_lat_coords)
    cluster_labels = db.labels_
    num_clusters = len(set(cluster_labels))

    # Put the points into respective bins, given which cluster
    # the point was classified in
    clusters = pd.Series([coords[cluster_labels == n] for n in range(num_clusters)])
    print('Number of clusters: {}'.format(num_clusters))

    total_pts = len(cluster_labels)
    print("Total points in cluster")
    print(total_pts)

    print("Medoid from DBScan")
    medoids = get_medoid(clusters)
    print(medoids.head(10))

    return medoids, clusters

# Another garbage function...
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
    agglom_coords = [coord[0] for coord in coords]
    #print(agglom_coords)
    #return sorted(agglom_coords, key=lambda coord: [coord[0], coord[1]]), columns=['lon', 'lat', 'speed'])
    return sorted(agglom_coords, key=lambda coord: [coord[0], coord[1]])

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

            # Find a real point that is closest to the centroid
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
    # Also a garbage function
    # An auxilary used
    # for agglomeration. Will soon
    # be removed. But keeping it here
    # just in case agglomeration
    # is useful
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

    # Cluster using K-Mean down to n clusters
    kmeans = KMeans(n_clusters=n)
    kmeans.fit(lon_lat_coords)

    # Creates a unique set for the cluster points
    cluster_labels = kmeans.labels_
    num_clusters = len(set(cluster_labels))

    # Put the points in the respective cluster
    clusters = pd.Series([coords[cluster_labels == n] for n in range(num_clusters)])
    print('Number of clusters: {}'.format(num_clusters))

    medoids = get_medoid(clusters)

    #print(medoids.head(10))

    return medoids

def get_bearing(x_lon, x_lat, y_lon, y_lat):
    '''
    Given two GPS points, find the angle
    between them using the Bearings formula
    :param x_lon: longitude of point 1
    :param x_lat: latitude of point 1
    :param y_lon: longitude of point 2
    :param y_lat: latitude of point 2
    :return: The angle in Degree rounded to 2 decimal place
    '''
    dy = y_lat - x_lat
    dx = math.cos(math.pi/180*x_lat)*(y_lon - x_lon)

    return round(math.degrees(math.atan2(dy, dx)),2)

def find_angle_between_pts(coords, n_space):
    '''
    Traverse through the coordinates and
    compute the bearings between two points
    :param coords:
    :return:
    '''

    for idx in range(n_space, len(coords), n_space):

        # Compute the cosine between
        # between previous point and correct point

        # X Coordinates
        x_lon = coords[idx-n_space][0]
        x_lat = coords[idx-n_space][1]
        x_speed = coords[idx-n_space][2]


        # Y Coordinates
        y_lon = coords[idx][0]
        y_lat = coords[idx][1]
        y_speed = coords[idx][2]

        angle = get_bearing(x_lon, x_lat, y_lon, y_lat)
        delta_speed = abs(y_speed - x_speed)

        # The speed direction tells me whether
        # the vehicle is speeding up or slowing down
        if y_speed < x_speed:
            # If recent speed is slower
            # then previous speed, it is
            # decelerating
            speed_dir = "d"
        elif y_speed > x_speed:
            # If recent speed is faster
            # then previous speed, it is
            # accelerating
            speed_dir = "a"
        else:
            # If recent speed does not
            # change, it is neutral
            speed_dir = "n"

        print("Delta Speed")
        print(delta_speed)
        print("Angle")
        print(angle)
        print("Speed Direction")
        print(speed_dir)

        # If bearing information exist,
        # take the most updated one
        if len(coords[idx]) >= 6:
            coords[idx][3] = angle
            coords[idx][4] = delta_speed
            coords[idx][5] = speed_dir
        else:
            # No bearing found yet, create a
            # new bearing field
            coords[idx].append(angle)
            coords[idx].append(delta_speed)
            coords[idx].append(speed_dir)

        print(coords[idx - n_space])
        print(coords[idx])
        print()

    return coords

def turn_classifier(coord):
    '''
    If the angle is greater than or equal to 100, and
    the speed is slower than 15, and it is
    deccelarting, it is considered a turn
    :param coord:
    :return:
    '''

    # Grab the respective components from the coordinate
    lon, lat, speed, angle, delta_speed, speed_dir = coord[0], \
                                                     coord[1], \
                                                     coord[2], coord[3], coord[4], coord[5]

    # If the angle is within the range of 100 and 60 inclusive
    if angle >= 100:
        # Is the change in speed from previous
        # point to current point slower than 15 mph
        if delta_speed <= 15:
            # Is the vehicle deccelarting
            if speed_dir == "d":
                return True
            else:
                return False

def classify_turn(coords):
    #unit_vector = lambda vector : vector / np.linalg.norm(vector)
    #angle_between = lambda v1, v2: np.arccos(np.clip(np.dot(unit_vector(v1), unit_vector(v2)), -1.0, 1.0))
    coords = coords.values.tolist()

    #Have to fix lat and lon mixup here...
    for idx in range(len(coords)):
        lat = coords[idx][1]
        lon = coords[idx][0]
        coords[idx][0] = lat
        coords[idx][1] = lon

    angle_between = lambda v1_lat, v1_lon, v2_lat, v2_lon: round(math.degrees(math.atan2(v2_lat - v1_lat, math.cos(math.pi / 180 * v1_lat) * (v2_lon - v1_lon))), 2)

    # Get acceleration between this point and last
    for idx in range(1, len(coords)):
        if idx == 1: coords[idx][3] = 0; continue
        coords[idx][3] = coords[idx][2] - coords[idx - 1][2]

    #Get angle between this point and last
    for idx in range(1, len(coords)):
        if idx == 1: coords[idx].append(0); continue
        coords[idx].append(angle_between(coords[idx - 1][0], coords[idx - 1][1], coords[idx][0], coords[idx][1]))

    #Get change (delta) of angle between this point and next
    #Average with change between the last angle to try to weed out anomalies
    for idx in range(1, len(coords) -1):
        if idx == 1 or idx == 2:
            coords[idx].append(coords[idx][4]); continue

        delta1 = (coords[idx + 1][4] - coords[idx][4])
        delta2 = (coords[idx + 1][4] - coords[idx - 1][4])
        #Sometimes these are really weird and anomalous - even when taking the average of two of them
        #We're just going to completely cut out massive weird numbers
        if abs(delta1) > 150: delta1 = 0
        if abs(delta2) > 150: delta2 = 0

        coords[idx].append((delta1 + delta2) / 2)

    #[coord[3] for coord in coords[3:] if abs(coord[5]) > 2 and coord[3] < -1]
    turns = []
    for idx in range(1, len(coords) - 1):
        if abs(coords[idx][5]) > 20 and abs(coords[idx][5]) < 170:
            turns.append(coords[idx] + [abs(coords[idx][5]) == coords[idx][5]])

    #plt.scatter([coord[0] for coord in coords[1:-1]], [coord[1] for coord in coords[1:-1]],
    #            c=KMeans(n_clusters=2, random_state=1).fit(np.array(coords[1:-1])).labels_)
    plt.scatter([coord[0] for coord in coords[1:-1]], [coord[1] for coord in coords[1:-1]], s= 3, c = [coord[3] for coord in coords[1:-1]], alpha=.8 )
    plt.scatter([coord[0] for coord in turns], [coord[1] for coord in turns], color="r")
    plt.show()

    return turns

def main():
    '''
    Test individual functions.
    I recommend using this to test the
    turn classifier. 
    :return:
    '''

    coords = [[-77.437765, 43.13831666666667, 0.0], [-77.43776166666666, 43.13832333333333, 0.529],
              [-77.43776166666666, 43.138326666666664, 0.99], [-77.43776, 43.13833, 1.703],
              [-77.43775833333333, 43.13833666666667, 2.532], [-77.43775333333333, 43.138345, 3.004],
              [-77.43775, 43.138353333333335, 3.534], [-77.43774833333333, 43.13836333333333, 3.821],
              [-77.43774666666667, 43.138371666666664, 4.109], [-77.43774666666667, 43.13838166666667, 4.408], [-77.43774833333333, 43.13839, 4.88], [-77.43774666666667, 43.138398333333335, 4.892], [-77.437745, 43.13840666666667, 4.938], [-77.43774333333333, 43.138416666666664, 5.03], [-77.43774333333333, 43.138425, 5.548], [-77.43774166666667, 43.138435, 5.997], [-77.43774, 43.13844666666667, 6.296], [-77.43774, 43.13845666666667, 6.791], [-77.43773833333333, 43.138468333333336, 6.929], [-77.43773666666667, 43.13848, 6.779], [-77.437735, 43.13849166666667, 6.791], [-77.437735, 43.13850333333333, 6.549], [-77.43773333333333, 43.138515, 6.319], [-77.43773166666666, 43.138526666666664, 5.836], [-77.43773, 43.13853666666667, 5.778], [-77.43773, 43.13854666666667, 5.352], [-77.43772833333334, 43.138555, 4.477], [-77.43772833333334, 43.13856166666667, 3.787], [-77.43772666666666, 43.13856833333333, 3.384], [-77.43772333333334, 43.13857333333333, 2.97], [-77.43772166666666, 43.138578333333335, 2.993], [-77.43771833333334, 43.13858333333334, 3.062], [-77.437715, 43.13858666666667, 3.349], [-77.43771, 43.13859, 3.718], [-77.43770333333333, 43.13859333333333, 3.557], [-77.43769833333333, 43.138598333333334, 3.488], [-77.43769166666667, 43.1386, 3.407], [-77.43768666666666, 43.1386, 3.338], [-77.43768, 43.138601666666666, 3.338], [-77.43767166666666, 43.138603333333336, 3.407], [-77.437665, 43.138603333333336, 2.843], [-77.43765833333333, 43.138603333333336, 2.049], [-77.43765666666667, 43.138603333333336, 1.105], [-77.43765833333333, 43.138601666666666, 1.911], [-77.43766333333333, 43.138601666666666, 3.718], [-77.43767333333334, 43.138601666666666, 5.974], [-77.43768833333333, 43.138601666666666, 8.092], [-77.43771, 43.138601666666666, 10.301], [-77.43773333333333, 43.138603333333336, 12.304], [-77.43776333333334, 43.138605, 14.468], [-77.43779666666667, 43.13860666666667, 16.333], [-77.43783333333333, 43.13861, 17.771], [-77.43787166666667, 43.138616666666664, 19.176],
              [-77.43791333333333, 43.138623333333335, 20.223], [-77.437955, 43.13863, 21.363],
              [-77.43800166666666, 43.13863833333333, 22.583], [-77.43805, 43.13865, 22.916],
              [-77.43809833333333, 43.138661666666664, 23.975], [-77.43814833333333, 43.138675, 24.654],
              [-77.43819666666667, 43.138691666666666, 24.758], [-77.43824666666667, 43.13871, 25.598],
              [-77.438295, 43.13873, 26.197], [-77.438345, 43.13875, 26.738],
              [-77.43839666666666, 43.13877333333333, 27.233],
              [-77.43844666666666, 43.138796666666664, 27.808]]

    print(find_angle_between_pts(coords, 10)[:40])

main()