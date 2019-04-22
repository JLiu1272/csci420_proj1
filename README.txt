When running this program, you should do the following:

1) Create a Kml directory and a Txt directory
2) The Txt directory should contain all the GPS .txt files provided by professor

Recommendation:
1) I recommend that you create your own branch, so that you can check for merge conflicts before commiting to the master branch
2) The .gitignore file should ignore Kml and Txt directory when you commit to this branch.

Running the folder:
1) When you run this program, it should start putting all the parsed Kml files into the Kml directory


Preliminary Installations:
If you are using Conda, you need to install some additional packages
that you may not have. 
I have created a req.txt file that contains all of the requirements

You can install the environment using
$ conda create -n new environment --file req.txt

If you don't have conda, i believe you can do it with pip too, but I do not remember

How to Run: 

The main function for converting a raw data into KML file 
is in GPS_to_KML.py 

You have 2 options when running this file. You can either
generate one KML for one GPS text raw file. Or you can
generate one KML for a list of GPS text raw files. This
function will merge all of these file into one, and clean
out any duplicate paths. 

Example Command:
# For directory 
python GPS_to_KML.py -d <Directory where all the .txt files are>

# If you have a Txt Directory. Run this.  
python GPS_to_KML.py -d Txt

# For single file
python GPS_to_KML.py -f <The path of file>

This command will create a resulting KML called assimilated_.kml inside the KML directory 

