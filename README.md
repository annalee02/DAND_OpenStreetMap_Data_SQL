# About 
This repository contains the Udacity's Data Analysis Nanodegree project connected to the Data Wrangling course. 
### OpenStreetMap Data Wrangling with SQL 
- The map area selected for this project: Las Vegas, Nevada, USA
- The data is available at: [OpenStreetMap_URL](https://www.openstreetmap.org/relation/170117#map=10/36.1462/-115.0818) and [Mapzen_URL](https://mapzen.com/data/metro-extracts/metro/las-vegas_nevada/)

# Files
* `src/`: a set of python files and an OSM XML file
* `audit_street_name.py`: auditing the OSM file to fix the unexpected street types
* `audit_postal_code.py`: auditing the OSM file to fix the unexpected postal codes
* `data.py`: parsing and transforming elements to write to .csv files
* `project_report.pdf`: a project report document
* `mapparser.py`: finding out what tags are there and how many of them
* `sample.osm`: a small part of the map region data
* `sample.py`: writing to sample.osm (1-10MB)
* `schema.py`: storing data as serialized format 
* `tags.py`: Counting each of 4 tag categories in a dictionary
* `users.py`: finding out unique users
