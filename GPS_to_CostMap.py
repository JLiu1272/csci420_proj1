#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Mar 24 17:16:48 2019

@author: JenniferLiu JosephGolden
File: GPS_to_CostMap.py
"""

from os import listdir
from GPS_to_KML import *


def stops_kml(stops, filename):
    """
    Function that creates a KML File with placemarks for stops
    """

    # Open a file to write the kml file to
    kml_output = open("Kml/" + filename + ".kml", "w+")

    # Write the inital headers
    kml_output.write("<?xml version='1.0' encoding='UTF-8'?>\n")
    kml_output.write("<kml xmlns='http://www.opengis.net/kml/2.2'>\n")

    # Write the necessary tags, Document
    kml_output.write("<Document>\n")

    for stop in stops:
        # Create the placemarks
        kml_output.write("<Placemark>\n" \
                         "<name>Stop at " + str(stop["formatted"]["time"]) + "</name>\n" \
                         "<Point><coordinates>\n")

        # Write the coordinates

        lng = stop["formatted"]["lng"]
        lat = stop["formatted"]["lat"]

        kml_output.write("{},{}\n".format(str(lng), str(lat)))

            # Close coordinate
        kml_output.write("</coordinates></Point>\n")

        # Close Placemark
        kml_output.write("</Placemark>\n")

    # Document closing
    kml_output.write("</Document>\n")

    # KML Closing
    kml_output.write("</kml>")

    kml_output.close()





path = "Txt"

files = []

stops = []

# Create a file object for every file in the Txt path
for txt in listdir(path):
    raw = "Txt/" + txt

    # Initialise a file handler object
    # Passing in the txt file
    files.append(FileHandler(raw))

    # Reformat the GPS Data into easy
    # to use data points later
    files[-1].parse_data()

    # Remove Parked vehicle
    #files[-1].remove_parked_vehicle()

    # Remove redundant Data
    #files[-1].remove_redundant_data()

    # Fix GPS Hickups
    files[-1].remove_gps_burps()

    # Remove points where the vehicle is not moving
    files[-1].remove_notmoving()


    for idx in range(len(files[0].gps_data)):
        #Find stops
        if files[0].gps_data[idx]["formatted"]["delta_speed"] < 0:
            stop_time = files[0].gps_data[idx]["formatted"]["time"]
            go_time = stop_time #Default
            #Look ahead to find when we start again
            for fwd_idx in range(idx, idx + 5):
                if fwd_idx > len(files[0].gps_data) - 1 or files[0].gps_data[fwd_idx]["formatted"]["delta_speed"] <= 0.005:
                    continue
                else:
                    go_time = files[0].gps_data[fwd_idx]["formatted"]["time"]
                    break

            #Add to stops if stopped for long enough
            if go_time - stop_time > 3 and go_time - stop_time < 30:
                stops.append(files[0].gps_data[idx])


stops_kml(stops, "test_stops_kml")


