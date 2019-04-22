"""
Created on Sun Mar 24 11:17:31 2019

@author: JosephGolden, JenniferLiu

Objective: Convert a txt file containing GPS data into a .KML file
"""

import argparse
from os.path import join
import os

# KML Utilities
import simplekml

# Aux Lib
import pandas as pd
from scipy.cluster.hierarchy import dendrogram, linkage
import numpy as np


# Own code
from GPS_Helper import load_file
from GPS_Agglomeration import *

def convert_to_kml(file_name, dfs, route_files):
    """
    Create a KML file from the input data. This
    is also the main function that calls
    the classifiers
    :param name: Output file name
    :param df: The data to parse into a KML file
    """
    # All of the points in all of the various paths
    kml = simplekml.Kml()

    complete_dfs = pd.DataFrame()
    segments = []

    # Merge all of the individual dataframe
    # containing a path from each file
    # into 1 single DataFrame Object
    for index, df in enumerate(dfs):
        complete_dfs = pd.concat([complete_dfs, df], axis=0)

    # Use DBScan to find potential stopping
    # points
    medoid, clusters = DBScan_Cluster(dfs[0].values)

    # Create a placemark for every stop sign found
    for cluster in clusters:
        # Only create a stop sign if the cluster
        # is not empty
        if len(cluster) > 0:
            pnt = kml.newpoint(name="Stop Light")
            pnt.coords = [(cluster[-1][1], cluster[-1][2], cluster[-1][3])]
            pnt.style.labelstyle.color = simplekml.Color.yellow
            pnt.style.labelstyle.scale = 1

    # Run K-Means to merge points that are
    # next to each other. This is to
    # resolve the issue with multiple GPS Data having
    # very similar paths, but due to DOS, it is slightly off
    kmeans_clusters = k_means(complete_dfs.values, 1500)

    # For each medoid found, add it to the full segments
    for index in range(1, kmeans_clusters.shape[0]):
        segments.append([(kmeans_clusters['lon'][index], kmeans_clusters['lat'][index], kmeans_clusters['speed'][index])])
        #complete_dfs = pd.concat([complete_dfs, cluster], axis=0)

    print(len(segments))
    print(segments[:10])

    # Due to issue with line string creating
    # attempting to connecting
    # every possible points. There were routes
    # that didn't make sense
    # so for every path, create a new linestring object
    for idx, segment in enumerate(segments):
        # Set Route Name
        route_name = 'Route '

        lin = kml.newlinestring(name=route_name, coords=segment)
        lin.style.linestyle.color = simplekml.Color.yellow
        lin.style.linestyle.width = 3
        lin.altitudemode = simplekml.AltitudeMode.relativetoground
        lin.extrude = 1

    # Save the final KML File
    if file_name.__contains__('/'):
        kml.save('kml/' + str(file_name).split("/")[1].split(".")[0] + ".kml")
    else:
        kml.save('kml/' + str(file_name).split(".")[0] + ".kml")


if __name__=="__main__":
    """
    Read the files that user specified for turning it into 
    KML files 
    """
    parser = argparse.ArgumentParser(usage='Parse GPS data and create 1 single KML file')
    parser.add_argument('-f', '--file', type=str, help='File to parse')
    parser.add_argument('-d', '--dir', type=str, help='Directory to parse')
    args = parser.parse_args()

    # Parsing single file
    if args.file is not None:
        df = load_file(args.file)
        convert_to_kml(args.file, [df], [args.file])
    elif args.dir is not None:
        files = [f for f in os.listdir(args.dir) if os.path.isfile(join(args.dir, f))]

        # Name of destination path
        des_path = 'Kml/assimilated_'

        # Merge all df into 1 single df
        all_dfs = []

        # Route Files
        route_files = []

        for file in files:
            filename = str(os.fsdecode(file))

            # The real path, with necessary appending
            realPath = 'Txt/' + filename

            # If the file ends with .txt, it is a permissible file
            if filename.lower().endswith('.txt'):
                # Append route file
                route_files.append(filename)

                # Convert a GPS file into DataFrame object
                df = load_file(realPath)

                # Create a list of dataframes object for
                # each path
                all_dfs.append(df)

                # Concatenate all of the individual df from each
                # file into one big one
                print("File: " + filename)

        convert_to_kml(des_path, all_dfs, route_files)


