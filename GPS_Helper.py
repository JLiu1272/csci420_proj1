"""
File: Helper functions for GPS Data
"""

import pandas as pd
import math

class Point:
    """
    Class to store one single GPS Data point
    """
    def __init__(self, time, lat, lon, speed, angle):
        self.time = time
        self.lat = round(lat, 5)
        self.lon = round(lon, 5)
        self.speed = round(speed, 5)
        self.angle = angle

    def get_time(self):
        return self.time

    def get_lat(self):
        return self.lat

    def get_lon(self):
        return self.lon

    def get_speed(self):
        return self.speed

    def __repr__(self):
        return str(self.lat) + ", " + str(self.lon)

def dms_to_dd(dms):
    """
    Converts degrees, minutes, seconds to decimal degress
    :param dms: degrees, minute, seconds
    :return: decimal degress that we can use to plot
    """
    if dms[0] == '0':
        dms = dms[1:]
        degrees = float(dms[:2])
        minutes = float(dms[2:])
        return -(degrees + (minutes / 60))
    else:
        degrees = float(dms[:2])
        minutes = float(dms[2:])
        return degrees + (minutes / 60)

def haversine(coord1, coord2):
    """
    Compute the haversine distance between
    coord1 and coord2
    """

    # Coordinates in decimal degrees (e.g. 2.89078, 12.79797)
    lon1, lat1 = coord1[0], coord1[1]
    lon2, lat2 = coord2[0], coord2[1]

    R = 6371000  # radius of Earth in meters
    phi_1 = math.radians(lat1)
    phi_2 = math.radians(lat2)

    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi_1) * math.cos(phi_2) * math.sin(delta_lambda / 2.0) ** 2

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    meters = R * c  # output distance in meters
    km = meters / 1000.0  # output distance in kilometers
    # km = round(km, 3)

    return meters

def load_file(file):
    """
    Takes a GPS File and create a Pandas DataFrame
    :param file: The GPS trace file
    :return: DataFrame containing the parsed GPS Trace
    """
    entry = {'time': [], 'lon': [], 'lat': [], 'speed': []}

    stops = {'time': [], 'lon': [], 'lat': [], 'speed': []}

    # Keeps a record of 1 previous entry
    # Initially, it is None
    prev_entry = None

    print('Loading ' + file + "")
    with open(file) as f:
        bad = False
        skipCount = 0
        for line in f:
            # $GPRMC,183410.001,A,4305.1494,N,07740.8738,W,0.02,342.94,030319,,,A*7A
            # $GPGGA,183410.200,4305.1494,N,07740.8738,W,1,08,1.03,154.2,M,-34.4,M,,*5F
            # lng=-77.681236, lat=43.085823, altitude=154.20, speed=0.02, satellites=8, angle=342.9400, fixquality=1
            split = line.split(",")

            try:
                if line.startswith('$GPRMC'):
                    # Skip garbage GPS entries
                    if split[3] == '' or split[5] == '' or split[7] == '$PGACK':
                        bad = True
                        skipCount += 1
                        continue

                    time = float(split[1])
                    lat = dms_to_dd(split[3])
                    lon = dms_to_dd(split[5])
                    speed = round(float(split[7]) * 1.151,3)

                    # If the speed is slower than a certain threshold,
                    # we might have to do some agglomeration
                    # We ignore this stop point
                    # The speed is still rather slow and the time
                    # hasn't changed much and the distance between
                    # previous point and current point is smaller than 10 m

                    if speed <= 0.5:
                        if prev_entry is None:
                            prev_entry = {'time': time, 'lon': lon, 'lat': lat, 'speed': speed}
                            #print({'time': time, 'lon': lon, 'lat': lat, 'speed': speed})
                            #print()
                        elif haversine((lon, lat), (prev_entry['lon'], prev_entry['lat'])) <= 10:
                            stops['time'].append(time)
                            stops['lat'].append(lat)
                            stops['lon'].append(lon)
                            stops['speed'].append(speed)
                            #print("Found a stop")
                            #print({'time': time, 'lon': lon, 'lat': lat, 'speed': speed})
                            #print()
                            continue
                        else:
                            prev_entry = {'time': time, 'lon': lon, 'lat': lat, 'speed': speed}

                    
                    entry['time'].append(time)
                    entry['lat'].append(lat)
                    entry['lon'].append(lon)
                    entry['speed'].append(speed)


                elif not bad and line.startswith("$GPGGA"):
                    # Do not add point, if the essential
                    # data are empty
                    if split[8] == '' or split[9] == '':
                        continue

                    sats = int(split[7])
                    dil = round(float(split[8]), 4)
                    alt = round(float(split[9]), 1)

                    # Check for Dilution of Precision
                    # If not satisified, pop it off the list
                    if alt < 100 or dil > 9 or sats < 3:
                        entry['time'].pop()
                        entry['lat'].pop()
                        entry['lon'].pop()
                        entry['speed'].pop()
                        skipCount += 1
                elif bad:
                    bad = False

            except IndexError as ie:
                print(ie, split)
            except ValueError as ve:
                print(ve, split)

    df = None
    try:
        df = pd.DataFrame.from_dict(entry)
    except ValueError:
        # Print the lengths of the dictionary lists. Note: They must be the same length to work!
        # If we get this error, we didn't clean the input data properly
        for key, value in entry.items():
            print(key, len(value))

    print('Loaded ' + str(len(df) + skipCount) + " total GPS data points.")
    print('Dropped ' + str(skipCount) + " anomalous GPS data points.")
    df = df.drop_duplicates(subset=['lat', 'lon'])

    # Reset index so that it is in sequential order
    df = df.reset_index(drop=True)

    print('Dropped Duplicate Points.')
    print('Considering ' + str(len(df)) + " total GPS data points.")
    return df



