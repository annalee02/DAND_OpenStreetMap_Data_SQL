#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
After auditing is complete the next step is to prepare the data to be inserted into a SQL database.
To do so I parse the elements in the OSM XML file, transforming them from document format to
tabular format, thus making it possible to write to .csv files.  These csv files can then easily be
imported to a SQL database as tables.

The process for this transformation is as follows:
- Use iterparse to iteratively step through each top level element in the XML
- Shape each element into several data structures using a custom function
- Utilize a schema and validation library to ensure the transformed data is in the correct format
- Write each data structure to the appropriate .csv files

## Shape Element Function
The function takes an iterparse Element object as input and return a dictionary.

### The final return value for a "node" element look something like:

{'node': {'id': 757860928,
          'user': 'uboot',
          'uid': 26299,
          'version': '2',
          'lat': 41.9747374,
          'lon': -87.6920102,
          'timestamp': '2010-07-22T16:16:51Z',
          'changeset': 5288876},
 'node_tags': [{'id': 757860928,
                'key': 'amenity',
                'value': 'fast_food',
                'type': 'regular'},
               {'id': 757860928,
                'key': 'cuisine',
                'value': 'sausage',
                'type': 'regular'},
               {'id': 757860928,
                'key': 'name',
                'value': "Shelly's Tasty Freeze",
                'type': 'regular'}]}

### The final return value for a "way" element look something like:

{'way': {'id': 209809850,
         'user': 'chicago-buildings',
         'uid': 674454,
         'version': '1',
         'timestamp': '2013-03-13T15:58:04Z',
         'changeset': 15353317},
 'way_nodes': [{'id': 209809850, 'node_id': 2199822281, 'position': 0},
               {'id': 209809850, 'node_id': 2199822390, 'position': 1},
               {'id': 209809850, 'node_id': 2199822392, 'position': 2},
               {'id': 209809850, 'node_id': 2199822369, 'position': 3},
               {'id': 209809850, 'node_id': 2199822370, 'position': 4},
               {'id': 209809850, 'node_id': 2199822284, 'position': 5},
               {'id': 209809850, 'node_id': 2199822281, 'position': 6}],
 'way_tags': [{'id': 209809850,
               'key': 'housenumber',
               'type': 'addr',
               'value': '1412'},
              {'id': 209809850,
               'key': 'street',
               'type': 'addr',
               'value': 'West Lexington St.'},
              {'id': 209809850,
               'key': 'street:name',
               'type': 'addr',
               'value': 'Lexington'},
              {'id': '209809850',
               'key': 'street:prefix',
               'type': 'addr',
               'value': 'West'},
              {'id': 209809850,
               'key': 'street:type',
               'type': 'addr',
               'value': 'Street'},
              {'id': 209809850,
               'key': 'building',
               'type': 'regular',
               'value': 'yes'},
              {'id': 209809850,
               'key': 'levels',
               'type': 'building',
               'value': '1'},
              {'id': 209809850,
               'key': 'building_id',
               'type': 'chicago',
               'value': '366409'}]}
"""

# Importing libraries
import xml.etree.cElementTree as ET
from collections import defaultdict
import re
import pprint
import csv
import codecs
import cerberus
import schema

# ================================================== #
#                  Data Cleaning                     #
# ================================================== #

#######   Functions from audit_street_name.py  #######

# osm file
OSMFILE = "las-vegas_nevada.osm"
# Checking tag to get the last word as a street type
street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)

# Expected street type list
expected = ["Street", "Avenue", "Boulevard", "Drive", "Court", "Place", "Square", "Lane", "Road",
            "Trail", "Parkway", "Commons", "Circle", "Drive", "Highway", "Way"]

# How unexpected street types should be changed
mapping = { "St": "Street",
            "St.": "Street",
            "street":"Street",
            "Ave": "Avenue",
            "AVE": "Avenue",
            "Ave.": "Avenue",
            "ave": "Avenue",
            "Blvd": "Boulevard",
            "Blvd.": "Boulevard",
            "blvd": "Boulevard",
            "Cir": "Circle",
            "Dr": "Drive",
            "drive": "Drive",
            "Ln":"Lane",
            "Ln.": "Lane",
            "Pkwy": "Parkway",
            "parkway": "Parkway",
            "Rd": "Road",
            "Rd.": "Road",
            "Rd5": "Road",
            "raod":"road"
            }

# Adding street types into dictionary
def audit_street_type(street_types, street_name):
    m = street_type_re.search(street_name)
    if m:
        street_type = m.group()
        if street_type not in expected:
            street_types[street_type].add(street_name)

# Finding street name in the ['k']'s value
def is_street_name(elem):
    return (elem.attrib['k'] == "addr:street")

# Returning dictionary of uncleaned street names and their values
def audit(osmfile):
    osm_file = open(osmfile, "r")
    street_types = defaultdict(set)
    for event, elem in ET.iterparse(osm_file, events=("start",)):

        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_street_name(tag):
                    audit_street_type(street_types, tag.attrib['v'])
    osm_file.close()
    return street_types

cleaned = "cleaned.osm"

# Updating street type to a better name in the mapping list
def update_name(name, mapping, street_type_re):
    m = street_type_re.search(name)
    if m:
        st_type = m.group()
        if st_type in mapping:
            name = re.sub(street_type_re, mapping[st_type], name)
    return name

#######   Helper function  #######
# Getting elements from OSM file
def get_element(osm_file, tags=('node', 'way', 'relation')):
    """Yield element if it is the right type of tag"""

    context = ET.iterparse(osm_file, events=('start', 'end'))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()
##################################

# Replacing abbreviations of street types and saving the changes in a new file
def modify_street(old_file, new_file):
    with open(new_file, 'wb') as output:
        output.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        output.write('<osm>\n  ')
        for i, element in enumerate(get_element(old_file)):
            for tag in element.iter("tag"):
                if is_street_name(tag):
                    tag.set('v',update_name(tag.attrib['v'], mapping, street_type_re))
            output.write(ET.tostring(element, encoding='utf-8'))
        output.write('</osm>')

# Modifying osm file
modify_street(OSMFILE, cleaned)

#######   Functions from audit_postal_code.py  #######

# Checking tag to get 5 digits of postal code
zip_type_re = re.compile(r'\d{5}-??')

# Grouping postcodes and saving them to dictionary
def audit_zip_type(zip_types, zip):
    m = zip_type_re.search(zip)
    if m:
        zip_type = m.group()
        if zip_type not in zip_types:
            zip_types[zip_type].add(zip)
    else:
        zip_types['unknown'].add(zip)

# Finding postcode in the ['k']'s value
def is_zip(elem):
    return (elem.attrib['k'] == "addr:postcode")

# Returning 5 digits of postcode as a key and their values in dictionary
def zip_audit(osmfile):
    osm_file = open(osmfile, "r")
    zip_types = defaultdict(set)
    for event, elem in ET.iterparse(osm_file, events=("start",)):
        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_zip(tag):
                    audit_zip_type(zip_types, tag.attrib['v'])
    osm_file.close()
    return zip_types

# Updating each postal code to a better form
def update_zip(zip):
    m = zip_type_re.search(zip)
    if m:
        return m.group()
    else:
        return "unknown"

cleaned2 = "cleaned2.osm"

# This function replace wrong postcode in osm file
def modify_zip(old_file, new_file):
    with open(new_file, 'wb') as output:
        output.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        output.write('<osm>\n  ')
        for i, element in enumerate(get_element(old_file)):
            for tag in element.iter("tag"):
                if is_zip(tag):
                    tag.set('v',update_zip(tag.attrib['v']))
            output.write(ET.tostring(element, encoding='utf-8'))
        output.write('</osm>')

# Modifying osm file
modify_zip(cleaned, cleaned2)

# ================================================== #
#           Transforming to Tabular format           #
# ================================================== #

OSM_PATH = "cleaned2.osm"

NODES_PATH = "nodes.csv"
NODE_TAGS_PATH = "nodes_tags.csv"
WAYS_PATH = "ways.csv"
WAY_NODES_PATH = "ways_nodes.csv"
WAY_TAGS_PATH = "ways_tags.csv"

LOWER_COLON = re.compile(r'^([a-z]|_)+:([a-z]|_)+')
PROBLEMCHARS = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

SCHEMA = schema.schema

# Make sure the fields order in the csvs matches the column order in the sql table schema
NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']

# The function takes an iterparse Element object as input and return a dictionary.
def shape_element(element, node_attr_fields=NODE_FIELDS, way_attr_fields=WAY_FIELDS,
                  problem_chars=PROBLEMCHARS, default_tag_type='regular'):
    """Clean and shape node or way XML element to Python dict"""

    node_attribs = {}
    way_attribs = {}
    way_nodes = []
    tags = []  # Handle secondary tags the same way for both node and way elements

    way_tags = []

    if element.tag == "node":
        # Node attributes
        for i in element.attrib:
            if i in node_attr_fields:
                node_attribs[i]=element.attrib[i]

        # Node's tags
        for i in element:
            temp = {}
            temp["id"] = element.attrib["id"]
            temp["value"] = i.attrib["v"]
            k = i.attrib["k"].split(":")
            if len(k)>1:
                temp["type"] = k[0]
                temp["key"] = k[1]
            else:
                temp["type"] = "regular"
                temp["key"] = i.attrib["k"]

            tags.append(temp)



    if element.tag == "way":
        # Way attributes
        for i in element.attrib:
            if i in way_attr_fields:
                way_attribs[i]=element.attrib[i]

        # Way's nodes(nd) and tags
        num = 0
        for i in element:
            # way_nodes
            if i.tag == "nd":
                temp1 = {}
                temp1["id"] = element.attrib["id"]
                temp1["node_id"] = i.attrib["ref"]
                temp1["position"] = num
                num = num+1
                way_nodes.append(temp1)

            # way_tags
            if i.tag == "tag":
                temp2 = {}
                temp2["id"] = element.attrib["id"]
                temp2["value"] = i.attrib["v"]
                k = i.attrib["k"].split(":")
                if len(k)>1:
                    temp2["type"] = k[0]
                    if len(k)>2:
                        temp2["key"] = k[1]+':'+k[2]
                    else: temp2["key"] = k[1]
                else:
                    temp2["type"] = "regular"
                    temp2["key"] = i.attrib["k"]
                way_tags.append(temp2)


    if element.tag == 'node':
        return {'node': node_attribs, 'node_tags': tags}
    elif element.tag == 'way':
        return {'way': way_attribs, 'way_nodes': way_nodes, 'way_tags': way_tags}


# ================================================== #
#               Helper Functions                     #
# ================================================== #

def validate_element(element, validator, schema=SCHEMA):
    """Raise ValidationError if element does not match schema"""
    if validator.validate(element, schema) is not True:
        field, errors = next(validator.errors.iteritems())
        message_string = "\nElement of type '{0}' has the following errors:\n{1}"
        error_string = pprint.pformat(errors)

        raise Exception(message_string.format(field, error_string))


class UnicodeDictWriter(csv.DictWriter, object):
    """Extend csv.DictWriter to handle Unicode input"""

    def writerow(self, row):
        super(UnicodeDictWriter, self).writerow({
            k: (v.encode('utf-8') if isinstance(v, unicode) else v) for k, v in row.iteritems()
        })

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


# ================================================== #
#               Main Function                        #
# ================================================== #
def process_map(file_in, validate):
    """Iteratively process each XML element and write to csv(s)"""

    with codecs.open(NODES_PATH, 'w') as nodes_file, \
         codecs.open(NODE_TAGS_PATH, 'w') as nodes_tags_file, \
         codecs.open(WAYS_PATH, 'w') as ways_file, \
         codecs.open(WAY_NODES_PATH, 'w') as way_nodes_file, \
         codecs.open(WAY_TAGS_PATH, 'w') as way_tags_file:

        nodes_writer = UnicodeDictWriter(nodes_file, NODE_FIELDS)
        node_tags_writer = UnicodeDictWriter(nodes_tags_file, NODE_TAGS_FIELDS)
        ways_writer = UnicodeDictWriter(ways_file, WAY_FIELDS)
        way_nodes_writer = UnicodeDictWriter(way_nodes_file, WAY_NODES_FIELDS)
        way_tags_writer = UnicodeDictWriter(way_tags_file, WAY_TAGS_FIELDS)

        nodes_writer.writeheader()
        node_tags_writer.writeheader()
        ways_writer.writeheader()
        way_nodes_writer.writeheader()
        way_tags_writer.writeheader()

        validator = cerberus.Validator()

        for element in get_element(file_in, tags=('node', 'way')):
            el = shape_element(element)
            if el:
                if validate is True:
                    validate_element(el, validator)

                if element.tag == 'node':
                    nodes_writer.writerow(el['node'])
                    node_tags_writer.writerows(el['node_tags'])
                elif element.tag == 'way':
                    ways_writer.writerow(el['way'])
                    way_nodes_writer.writerows(el['way_nodes'])
                    way_tags_writer.writerows(el['way_tags'])


if __name__ == '__main__':
    # Note: Validation is ~ 10X slower. For the project consider using a small
    # sample of the map when validating.
    process_map(OSM_PATH, validate=True)
