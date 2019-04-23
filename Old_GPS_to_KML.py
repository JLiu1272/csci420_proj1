#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Mar 24 11:17:31 2019

@author: JosephGolden, JenniferLiu

Objective: Convert a txt file containing GPS data into a .KML file
"""
import re
from os import listdir
import sys

class FileHandler(object):
    def __init__(self):
        self.kml_output = None
    
    def parse_data(self, raw_file):
        """
        Convert data into a dictionary form for easy cleaning
        """
        self.file = open(raw_file, "r")
        
        # Regex to check
        gprmc = re.compile(r'^\$GPRMC') # Determine whether this is a GPRMC line
        gpgga = re.compile(r'^\$GPGGA')         # Determine whether this is a GPGGA line
        parsed = re.compile(r'^lng')             # Determine whether this is an parsed data
        
        self.gps_data = []

        sub_data = {}  # Reformat the data into dictionary

        # Initialise the gprmc and gpgga as None initially
        # update if line found
        sub_data["gprmc"] = None
        sub_data["gpgga"] = None

        # Traverse through every line in a file 
        for line in self.file:
            #print(line)

            # Check what this line conveys
            if gprmc.search(line):
                sub_data["gprmc"] = line.strip("\n")

                # Check if the A field exist or not, if it
                # does not, skip this data
                tokens = sub_data["gprmc"].split(",")

                # Remove GPS Data where the A does not
                # exist in the GPRMC field
                if tokens[2] != "A":
                    # Debugging info
                    #print(tokens)
                    #print("Indicator Field: " + tokens[2])
                    #print("Error Out GPRMC!")
                    #print()
                    sub_data["gprmc"] = None

                # Create a formatted dictionary object
                # storing the necessary ingredient to
                # get the GPS working
                if "formatted" not in sub_data.keys():
                    sub_data["formatted"] = dict()
                sub_data["formatted"]["time"] = float(line.split(",")[1])

            if gpgga.search(line):
                sub_data["gpgga"] = line.strip("\n")

                gps_data = sub_data["gpgga"].split(",")

                # If the fix is not 1 , remove the data
                # If there are less than 3 satellites
                # If the Dilution of precision estimate is smaller than certain value
                # if gps_data[7] == "" or int(gps_data[7]) < 3 or \
                if gps_data[8] == "" or float(gps_data[8]) >= 6.0:
                    # Debugging Info
                    #print("Fix " + str(gps_data[6]))
                    #print("Satellites " + str(gps_data[7]))
                    #print("POC " + str(gps_data[8]))
                    #print("Error Out GPGGA!")
                    #print()
                    sub_data["gpgga"] = None

            if parsed.search(line) and sub_data["gpgga"] is not None and sub_data["gprmc"] is not None:
                tokens = line.split(", ")
                formatted = {}

                # Parse the data into separate information
                # so I can make a new dict out of it
                for token in tokens:
                    key,value = token.split("=")              # Split the data into key and value
                    formatted[key] = float(value.strip("\n")) # Strip newline and convert value to float

                if "formatted" not in sub_data.keys():
                    sub_data["formatted"] = formatted
                else:
                    sub_data["formatted"].update(formatted)

                #In case there was no gprmc to get time from, take it from gpgga instead
                if "time" not in sub_data["formatted"].keys():
                    sub_data["formatted"]["time"] = float(sub_data["gpgga"].split(",")[1])

                # Add a speed delta (acceleration) to help us identify stops
                if len(self.gps_data) == 0:
                    sub_data["formatted"]["delta_speed"] = sub_data["formatted"]["speed"]
                else:
                    delta_time = (sub_data["formatted"]["time"] - self.gps_data[-1]["formatted"]["time"])
                    delta_velocity = (sub_data["formatted"]["speed"] - self.gps_data[-1]["formatted"]["speed"])
                    if delta_time == 0:
                        sub_data["formatted"]["delta_speed"] = 0
                    else:
                        sub_data["formatted"]["delta_speed"] = delta_velocity / delta_time

                self.gps_data.append(sub_data)
                #print("Successfully Added!")
                #print(sub_data)
                #print()
                sub_data = {"gpgga": None, "gprmc": None}

            #print("Completed 1 Cycle")

    def remove_parked_vehicle(self):
        """
        If the vehicle is parked, you do not need multiple data points at that same location.
        """
        idx = 0 # Loop through entire gps_data

        # Traverse through all data points, and identify their speed
        while idx < len(self.gps_data):
            
            # If speed is 0, it means it is not moving 
            if self.gps_data[idx]["formatted"]["speed"] == 0.0:

                # For parked vehicles, ignore the angle
                # If the vehicle is stopped, we cannot rely on the angle
                # hence, put a None there
                self.gps_data[idx]["formatted"]["angle"] = None
                
            idx += 1

    def remove_notmoving(self):
        """
        When the trip first starts up, the GPS device is not moving. Do not worry about the data points when the
        vehicle has not started moving yet.
        """
        
        idx = 1 # Loop through entire gps_data
        gps_data_copy = []
        prev_lng = self.gps_data[0]["formatted"]["lng"]   # Note the first longitude in GPS 
        prev_lat = self.gps_data[0]["formatted"]["lat"]   # Note the first latitude in GPS 
        
        gps_data_copy.append(self.gps_data[0])              # Append the first point to GPS Copy  
        
        # Traverse through all data points in GPS 
        while idx < len(self.gps_data):

            # If the speed of vehicle is slower than 0.1 mph,
            # Ignore the angle
            if self.gps_data[idx]["formatted"]["speed"] == 0.00:
                self.gps_data[idx]["formatted"]["lng"] = prev_lng
                self.gps_data[idx]["formatted"]["lat"] = prev_lat

            # if the angle has not changed from new point to previous,
            # it is moving in a straight line 
            if self.gps_data[idx]["formatted"]["lng"] != prev_lng or self.gps_data[idx]["formatted"]["lat"] != prev_lat:
                prev_lng = self.gps_data[idx]["formatted"]["lng"]
                prev_lat = self.gps_data[idx]["formatted"]["lat"]
                gps_data_copy.append(self.gps_data[idx])
            
            # Update the previous angle to the current longitude
            prev_lng = self.gps_data[idx]["formatted"]["lng"]
            
            # Update the previous angle to the current latitude
            prev_lat = self.gps_data[idx]["formatted"]["lat"]
            
            idx += 1

        """
        for c in gps_data_copy:
            print(c["gprmc"])
            print(c["gpgga"])
            print(c["formatted"])
        """
        
        # Update the GPS data to the cleaned version 
        self.gps_data = gps_data_copy
    
    def remove_redundant_data(self):
        """
        If the vehicle is traveling in a straight line, you could ignore some points.If the angle
        of the vehicle never changes, we can assume that it is traveling at the same line
        """




        """
        idx = 1 # Loop through entire gps_data
        gps_data_copy = []
        prev_angle = self.gps_data[0]["formatted"]["angle"] # Note the first angle seen in GPS
        gps_data_copy.append(self.gps_data[0])              # Append the first point to GPS Copy  
        repeat_times = 0
        
        # Traverse through all data points in GPS 
        while idx < len(self.gps_data):
            # if the angle has not changed from new point to previous,
            # it is moving in a straight line 
            if self.gps_data[idx]["formatted"]["angle"] != prev_angle:
                prev_angle = self.gps_data[idx]["formatted"]["angle"]
                gps_data_copy.append(self.gps_data[idx])
            else:
                # We only sample every 4 points if they are straight
                # so it does not look too concentrated 
                repeat_times += 1
                
                # Once we reached the 4th point, we reset
                # the counter to 0 
                if repeat_times >= 4:
                    gps_data_copy.append(self.gps_data[idx])
                    repeat_times = 0
            
            # Update the previous angle to the current angle 
            prev_angle = self.gps_data[idx]["formatted"]["angle"]      
            idx += 1
        
        for c in gps_data_copy:
            print(c["gprmc"])
            print(c["gpgga"])
            print(c["formatted"])
        
        # Update the GPS data to the cleaned version 
        self.gps_data = gps_data_copy
        """
    
    
    
    def remove_gps_burps(self):
        """
        The Arduino sometimes burps, and writes two GPS sentences to the same line of the data file.
        You must detect and ignore these anomalies.
        Otherwise it looks like the car jumps from one side of the planet to the other side.
        """
        
        gps_data_copy = []
        
        # Traverse through all data points in GPS 
        for data in self.gps_data:
            
            if "gprmc" not in data or "gpgga" not in data:
                continue
            
            gprmc = data["gprmc"] # Get the GPRMC data
            gpgga = data["gpgga"] # Get the GPGGA data 
            
            
            # If found $GPRMC or $GPGGA on the same line, then do not add to data set
            if re.search(r".+\$GP(RMC|GGA)", gprmc) or re.search(r".+\$GP(RMC|GGA)", gpgga):
                continue
            
            gps_data_copy.append(data)
        
        # Update the GPS data to the cleaned version 
        self.gps_data = gps_data_copy
        
        """
        for c in gps_data_copy:
            print(c["gprmc"])
            print(c["gpgga"])
            print(c["formatted"])
        """
        
    def print_gps_data(self):
        """
        Print the GPS Data 
        """
        for data in self.gps_data:
            print(data)

    def open_kml(self, file):
        """
        Write header information for the KML file
        :return:
        """
        # Open a file to write the kml file to
        self.kml_output = open("Kml/" + file + ".kml", "w")

        # Write the inital headers
        self.kml_output.write("<?xml version='1.0' encoding='UTF-8'?>\n")
        self.kml_output.write("<kml xmlns='http://www.opengis.net/kml/2.2'>\n")

        # Write the necessary tags, Document
        self.kml_output.write("<Document>\n")

        # Customise Style of of point
        self.kml_output.write("<Style id='yellowPoly'>\n" \
                         "<LineStyle>\n" \
                         " <color>Af00ffff</color>\n" \
                         " <width>6</width>\n" \
                         "</LineStyle>\n" \
                         "<PolyStyle>\n" \
                         " <color>7f00ff00</color>\n" \
                         "</PolyStyle>\n" \
                         "</Style>\n")

    def create_kml(self, file):
        """
        Function that creates a KML File
        """
        # Open a file to write the kml file to
        #self.kml_output = open("Kml/" + file + ".kml", "a")

        # Create the placemarks
        self.kml_output.write("<Placemark><styleUrl>#yellowPoly</styleUrl>\n" \
                              "<LineString>\n" \
                              "<Description>Speed in Knots, instead of altitude.</Description>\n" \
                              " <extrude>1</extrude>\n" \
                              " <tesselate>1</tesselate>\n" \
                              "<altitudeMode>relative</altitudeMode>\n" \
                              "<coordinates>\n")

        # Write the coordinates
        for data in self.gps_data:
            lng = data["formatted"]["lng"]
            lat = data["formatted"]["lat"]
            speed = data["formatted"]["speed"]

            self.kml_output.write("{},{},{}\n".format(str(lng), str(lat), str(speed)))

        # Close coordinate
        self.kml_output.write("</coordinates>\n")

        # Close line string
        self.kml_output.write("</LineString>\n")

        # Close Placemark
        self.kml_output.write("</Placemark>\n")

    def close_kml(self, file):

        # Open a file to write the kml file to
        #kml_output = open("Kml/" + file + ".kml", "a")

        # Close coordinate
        #self.kml_output.write("</coordinates>\n")
        
        # Close line string
        #self.kml_output.write("</LineString>\n")
        
        # Close Placemark 
        #self.kml_output.write("</Placemark>\n")

        # Document closing 
        self.kml_output.write("</Document>\n")
            
        # KML Closing  
        self.kml_output.write("</kml>")

        self.kml_output.close()
        
        
def main():

    path = "Txt"

    # Check if user placed any
    # files for assimilation
    # If not, provide some default files
    if len(sys.argv) == 1:
        #file_lst = listdir("Txt")
        file_lst = [
            #'2019_03_12__1423_30.txt',
            '2019_03_13__2033_30.txt',
            #'2019_03_15__1918_14.txt',
            #'2019_03_20__2227_30.txt',
            # '.DS_Store',
            # '2019_03_16__1935_03.txt',
            # '2019_03_20__1513_06.txt',
            # '2019_03_15__2135_18.txt',
            # '2019_03_14__1429_18.txt',
            # '2019_03_15__1733_30.txt',
            # '2019_03_15__2224_04.txt',
            # '2019_03_17__2125_30.txt',
            # '2019_03_19__2134_30.txt',
            # '2019_03_19__1310_26.txt',
            # '2019_03_14__1703_19.txt'
        ]
    else:
        # User has provided a set of files
        # use these to generate a KML
        file_lst = []
        for f in sys.argv:
            file_lst.append(f)

    # Set the file name as the first file
    # seen in the file_lst
    kml_final = "merged_" + str(len(file_lst))

    # Initialise a file handler object
    # Passing in the txt file
    fileHandler = FileHandler()

    # Write header information for KML file
    fileHandler.open_kml(kml_final)

    """
    # Create a KML file for every raw txt file in 
    # the txt path 
    """
    for txt in file_lst:
        #raw = "Txt/2019_03_12__1423_30.txt"
        isFile = re.compile(r'.\.txt$')

        if isFile.search(txt) is None:
            continue

        raw = "Txt/" + txt
        #fileHandler.open_kml(txt)

        print(raw)
        # Reformat the GPS Data into easy
        # to use data points later
        fileHandler.parse_data(raw)

        # Remove Parked vehicle
        #fileHandler.remove_parked_vehicle()

        # Remove redundant Data
        #fileHandler.remove_redundant_data()

        # Fix GPS Hickups
        fileHandler.remove_gps_burps()

        # Remove points where the vehicle is not moving
        fileHandler.remove_notmoving()

        # Print Reformatted GPS Data point for
        # easier use
        #fileHandler.print_gps_data()

        # Create KML file
        fileHandler.create_kml(txt)

        #fileHandler.close_kml(txt)

    #fileHandler.create_kml()
    fileHandler.close_kml(kml_final)

    print("Num GPS Points")
    print(len(fileHandler.gps_data))

    """
    Single Test 
    raw = "Txt/2019_03_12__1423_30.txt"
        
    # Initialise a file handler object 
    # Passing in the txt file 
    fileHandler = FileHandler()
    
    # Reformat the GPS Data into easy 
    # to use data points later 
    fileHandler.parse_data(raw)
    
    # Print Reformatted GPS Data point for
    # easier use 
    #fileHandler.print_gps_data()
    
    # Remove Parked vehicle 
    fileHandler.remove_parked_vehicle()
    
    # Remove redundant Data 
    fileHandler.remove_redundant_data()
    
    # Fix GPS Hickups 
    fileHandler.remove_gps_burps()
    
    # Remove points where the vehicle is not moving 
    fileHandler.remove_notmoving()
    
    # Create KML file 
    fileHandler.create_kml(raw)
    """

if __name__ == "__main__":
    main()