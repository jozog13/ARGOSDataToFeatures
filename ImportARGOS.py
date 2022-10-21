##---------------------------------------------------------------------
## ImportARGOS.py
##
## Description: Read in ARGOS formatted tracking data and create a line
##    feature class from the [filtered] tracking points
##
## Usage: ImportArgos <ARGOS folder> <Output feature class> 
##
## Created: Fall 2021
## Author: John.Fay@duke.edu (for ENV859)
##---------------------------------------------------------------------

# Import modules
import sys, os, arcpy

# Allow output to be overwritten
arcpy.env.overwriteOutput = True

# Set input variables
inputFolder = sys.argv[1] #'V:/ARGOSTracking/Data/ARGOSData'
outputSR = sys.argv[2] #arcpy.SpatialReference(54002)
lcFilters = sys.argv[3] #1,2,3
outputFC = sys.argv[4] #"V:/ARGOSTracking/Scratch/ARGOStrack.shp"

# create a list of files in the user provided input folder 
inputFiles = os.listdir(inputFolder)

# split multistring into list
lcValues = lcFilters.split(';')

# Create feature class to which we will add features
outPath, outFile = os.path.split(outputFC) 
arcpy.management.CreateFeatureclass(outPath,outFile,"POINT",'','','',outputSR)

# Add SourceFile, TagID, LC, IQ, and Date fields to the output feature class
arcpy.management.AddField(outputFC, "SourceFile", 'TEXT')
arcpy.management.AddField(outputFC,"TagID","LONG")
arcpy.management.AddField(outputFC,"LC","TEXT")
arcpy.management.AddField(outputFC,"Date","DATE")

# create insert cursor
cur = arcpy.da.InsertCursor(outputFC, ['SHAPE@','SourceFile','TagID','LC','Date'])

# create some counter variables 
lc_filter_count = 0
pt_error_count = 0

# Iterate through each input file 
for inputFile in inputFiles:
    # skip the README.txt file 
    if inputFile == 'README.txt': continue
    
    # give the user some status 
    arcpy.AddMessage(f'Working on file {inputFile}')
    
    # prepend input file with path
    inputFile = os.path.join(inputFolder,inputFile)
    
    #%% Construct a while loop and iterate through all lines in the data file
    # Open the ARGOS data file
    inputFileObj = open(inputFile,'r')
    
    # Get the first line of data, so we can use the while loop
    lineString = inputFileObj.readline()
    
    #Start the while loop
    while lineString:
        
        # Set code to run only if the line contains the string "Date: "
        if ("Date :" in lineString):
            
            # Parse the line into a list
            lineData = lineString.split()
            
            # Extract attributes from the datum header line
            tagID = lineData[0]
            
            # Extract location info from the next line
            line2String = inputFileObj.readline()
            
            # Parse the line into a list
            line2Data = line2String.split()
            
            # Extract the date we need to variables
            obsLat = line2Data[2]
            obsLon= line2Data[5]
                        
            # Extract the date, time, and LC values
            obsDate = lineData[3]
            obsTime = lineData[4]
            obsLC   = lineData[7]
            
            # skip record if not in LC value list
            if obsLC not in lcValues:
                # Add to the lc tally
                lc_filter_count += 1
                # move to next record
                lineString = inputFileObj.readline()
                # skip rest of code block
                continue
            
            # Print results to see how we're doing
            #print (tagID,"Lat:"+obsLat,"Long:"+obsLon, obsLC, obsDate, obsTime)
            
            # try to convert coordinates to point object
            try: 
                # Convert raw coordinate strings to numbers
                if obsLat[-1] == 'N':
                    obsLat = float(obsLat[:-1])
                else:
                    obsLat = float(obsLat[:-1]) * -1
                if obsLon[-1] == 'E':
                    obsLon = float(obsLon[:-1])
                else:
                    obsLon = float(obsLon[:-1]) * -1
                
                # create point object from lat/long coordinates
                obsPoint = arcpy.Point()
                obsPoint.X = obsLon
                obsPoint.Y = obsLat
                
                # convert point object to a geometry object 
                inputSR = arcpy.SpatialReference(4326)
                obsPointGeom = arcpy.PointGeometry(obsPoint,inputSR)
                
                # insert our feature into our feature class 
                feature = cur.insertRow((obsPointGeom,os.path.basename(inputFile),
                                         tagID,obsLC,
                                         obsDate.replace(".","/") + " " + obsTime))
            
            # handle any error
            except Exception as e:
                pt_error_count += 1
                print(f"Error adding record {tagID} to the output: {e}")
            
        # Move to the next line so the while loop progresses
        lineString = inputFileObj.readline()
        
    #Close the file object
    inputFileObj.close()

# delete the cursor
del cur

# give info to user
if lc_filter_count > 0:
    arcpy.AddWarning(f'{lc_filter_count} records not meeting LC class')
else:
    arcpy.AddMessage("No records omitted because of LC value")
    
if pt_error_count > 0:
    arcpy.AddWarning(f'{pt_error_count} record had no location data')