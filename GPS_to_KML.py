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

    # Stores the agglomerated paths
    # For each path, create a separate
    # list, so we do not end up with
    # lines that are on non-paths
    segments = []

    # Raw segments are the paths that
    # have no yet been clustered. The problem
    # with agglomerating paths is that
    # it does not preserve the order
    # hence when doing turns classification
    # the order would be helpful for determining
    # when car turns
    #raw_segments = []


    # Merge all of the individual dataframe
    # containing a path from each file
    # into 1 single DataFrame Object
    for index, df in enumerate(dfs):
        complete_dfs = pd.concat([complete_dfs, df], axis=0)

        """
        raw_segment = []

        # Extract the raw points, and
        # create a list out of it
        # so we can do left/right turn classification
        for i2 in range(df.shape[0]):
            raw_segment.append([df['lon'][i2],df['lat'][i2],df['speed'][i2]])
        raw_segments += raw_segment
        """

        medoids, clusters = DBScan_Cluster(df.values)
        
        # Create a placemark for every stop sign found
        for medoid_id in range(1, len(medoids)):
            #print(medoids['lon'][medoid_id])
            # Only create a stop sign if the cluster
            # is not empty
            pnt = kml.newpoint(name="Stop Light")
            pnt.coords = [(medoids['lon'][medoid_id], medoids['lat'][medoid_id], medoids['speed'][medoid_id])]
            pnt.style.labelstyle.color = simplekml.Color.yellow
            pnt.style.labelstyle.scale = 1

    # Classify the turns
    turns = classify_turn(complete_dfs)
    print("Number of turns found")
    print(len(turns))
    print(turns[:10])

    # Create a turn point
    # on the GPS Data
    for turn in turns:
        if not turn[-1]:
            pnt = kml.newpoint(name="Left Turn")
        else:
            pnt = kml.newpoint(name="Right Turn")
        pnt.coords = [[turn[0], turn[1], turn[2]]]
        pnt.style.labelstyle.color = simplekml.Color.red
        pnt.style.labelstyle.scale = 1

    """
    print("Starting K-Means")
    # Run K-Means to merge points that are
    # next to each other. This is to
    # resolve the issue with multiple GPS Data having
    # very similar paths, but due to DOS, it is slightly off
    kmeans_clusters = k_means(complete_dfs.values, 200)

    # For each medoid found, add it to the full segments
    for index in range(1, kmeans_clusters.shape[0]):
        segments.append([(kmeans_clusters['lon'][index], kmeans_clusters['lat'][index], kmeans_clusters['speed'][index])])
        #complete_dfs = pd.concat([complete_dfs, cluster], axis=0)

    print(len(segments))
    #print(segments[:10])

    # Due to issue with line string creating
    # attempting to connecting
    # every possible points. There were routes
    # that didn't make sense
    # so for every path, create a new linestring object
    for idx, segment in enumerate(segments):
        # Set Route Name
        route_name = 'Route '

        # Creates a linestring object
        # Sets it to yellow, with a size of 5
        lin = kml.newlinestring(name=route_name, coords=segment)
        lin.style.linestyle.color = simplekml.Color.yellow
        lin.style.linestyle.width = 5
        lin.altitudemode = simplekml.AltitudeMode.relativetoground
        lin.extrude = 1
    """

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


