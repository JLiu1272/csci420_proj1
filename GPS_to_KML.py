#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Mar 24 11:17:31 2019

@author: JenniferLiu

Objective: Convert a txt file containing GPS data into a .KML file
"""
import re
from copy import copy 
from os import listdir
from os.path import isfile, join 


class FileHandler(object):
    def __init__(self, file):
        self.file = open(file, "r")
        self.gps_data = None
    
    def parse_data(self):
        """
        Convert data into a dictionary form for easy cleaning
        """
        hit_newline = False
        self.gps_data = []
        
        # Regex to check
        gprmc = re.compile(r'^\$GPRMC') # Determine whether this is a GPRMC line
        gpgga = re.compile(r'^\$GPGGA')         # Determine whether this is a GPGGA line
        parsed = re.compile(r'^lng')             # Determine whether this is an parsed data
        
        sub_data = {}  # Reformat the data into dictionary
        
        # Traverse through every line in a file 
        for line in self.file:
            if line == "\n":
                hit_newline = True
            
            # Do not consider the first 3 lines in the txt 
            if hit_newline:
                # Check what this line conveys
                if gprmc.search(line):
                    sub_data["gprmc"] = line.strip("\n")
                    if "formatted" not in sub_data.keys():
                        sub_data["formatted"] = dict()
                    sub_data["formatted"]["time"] = float(line.split(",")[1])
                
                if gpgga.search(line):
                    sub_data["gpgga"] = line.strip("\n") 
                
                if parsed.search(line):
                    tokens = line.split(", ")
                    formatted = {}
                    
                    # Parse the data into separate information
                    # so I can make a new dict out of it
                    for token in tokens:
                        key,value = token.split("=") # Split the data into key and value
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
                    sub_data = {}
    
    """
    The following function will be for 
    cleaning the GPS data. 
    """
    
    def remove_parked_vehicle(self):
        """
        If the vehicle is parked, you do not need multiple data points at that same location.
        """
        idx = 0 # Loop through entire gps_data
        num_times = 0
        gps_data_copy = []
        
        
        # Traverse through all data points, and identify their speed
        while idx < len(self.gps_data):
            
            # If speed is 0, it means it is not moving 
            if self.gps_data[idx]["formatted"]["speed"] == 0.0:
                
                # If it is not the first time the car has stopped
                # we do not add to the list 
                num_times += 1
            
                # If it is the first time the car has stopped
                # we add it to the list 
                if num_times == 1: 
                    gps_data_copy.append(self.gps_data[idx])
            else:
                # The speed is not 0, so we add it to the new list
                num_times = 0
                gps_data_copy.append(self.gps_data[idx])
                
                
            idx += 1
        
        # Update the new data for GPS list 
        self.gps_data = gps_data_copy
    
    def remove_notmoving(self):
        """
        When the trip first starts up, the GPS device is not moving. Do not worry about the data points when the
        vehicle has not started moving yet.
        """
        
        idx = 1 # Loop through entire gps_data
        gps_data_copy = []
        prev_lng = self.gps_data[0]["formatted"]["lng"] # Note the first longitude in GPS 
        prev_lat = self.gps_data[0]["formatted"]["lat"]   # Note the first latitude in GPS 
        
        gps_data_copy.append(self.gps_data[0])              # Append the first point to GPS Copy  
        
        # Traverse through all data points in GPS 
        while idx < len(self.gps_data):
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
        
        for c in gps_data_copy:
            print(c["gprmc"])
            print(c["gpgga"])
            print(c["formatted"])
        
        # Update the GPS data to the cleaned version 
        self.gps_data = gps_data_copy
        
        
    
    def remove_redundant_data(self):
        """
        If the vehicle is traveling in a straight line, you could ignore some points.If the angle
        of the vehicle never changes, we can assume that it is traveling at the same line
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
        
        """
        for c in gps_data_copy:
            print(c["gprmc"])
            print(c["gpgga"])
            print(c["formatted"])
        """
        
        # Update the GPS data to the cleaned version 
        self.gps_data = gps_data_copy
    
    
    
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
    
    def create_kml(self, file):
        """
        Function that creates a KML File
        """
        
        # Only get the name of the file. Not
        # the path or the file type 
        dire = file.split("/")
        file_name = dire[1].split(".")
        
        # Open a file to write the kml file to 
        kml_output = open("Kml/" + file_name[0] + ".kml", "w+")
        
        # Write the inital headers
        kml_output.write("<?xml version='1.0' encoding='UTF-8'?>\n")
        kml_output.write("<kml xmlns='http://www.opengis.net/kml/2.2'>\n")
        
        # Write the necessary tags, Document
        kml_output.write("<Document>\n")
        
        # Customise Style of of point
        kml_output.write("<Style id='yellowPoly'>\n" \
                          "<LineStyle>\n" \
                            " <color>Af00ffff</color>\n" \
                            " <width>6</width>\n" \
                          "</LineStyle>\n" \
                          "<PolyStyle>\n" \
                            " <color>7f00ff00</color>\n" \
                          "</PolyStyle>\n" \
                          "</Style>\n")
        
        # Create the placemarks 
        kml_output.write("<Placemark><styleUrl>#yellowPoly</styleUrl>\n" \
                          "<LineString>\n" \
                          "<Description>Speed in Knots, instead of altitude.</Description>\n" \
                            " <extrude>1</extrude>\n" \
                            " <tesselate>1</tesselate>\n" \
                          "<altitudeMode>absolute</altitudeMode>\n" \
                          "<coordinates>\n")
        
        # Write the coordinates 
        for data in self.gps_data:
            lng = data["formatted"]["lng"]
            lat = data["formatted"]["lat"]
            speed = data["formatted"]["speed"]
            
            kml_output.write("{},{},{}\n".format(str(lng), str(lat), str(speed)))       
        
        # Close coordinate
        kml_output.write("</coordinates>\n")
        
        # Close line string
        kml_output.write("</LineString>\n")
        
        # Close Placemark 
        kml_output.write("</Placemark>\n")

        # Document closing 
        kml_output.write("</Document>\n")
            
        # KML Closing  
        kml_output.write("</kml>")
        
        
        
        kml_output.close()
        
        
        
        
def main():    
    
    path = "Txt"
    
    # Create a KML file for every raw txt file in 
    # the txt path 
    for txt in listdir(path):
        
        raw = "Txt/" + txt
        
        # Initialise a file handler object 
        # Passing in the txt file 
        fileHandler = FileHandler(raw)
        
        # Reformat the GPS Data into easy 
        # to use data points later 
        fileHandler.parse_data()
        
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
    Single Test 
    raw = "Txt/2019_03_12__1423_30.txt"
        
    # Initialise a file handler object 
    # Passing in the txt file 
    fileHandler = FileHandler(raw)
    
    # Reformat the GPS Data into easy 
    # to use data points later 
    fileHandler.parse_data()
    
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