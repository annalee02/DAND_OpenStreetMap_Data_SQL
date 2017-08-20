"""
- Auditing the OSMFILE and changing the variable 'mapping' to reflect the changes needed to fix
    the unexpected street types to the appropriate ones in the expected list.

- Using the update_name function, to actually fix the street name.
    The function takes a string with street name as an argument and return the fixed name.
"""
import xml.etree.cElementTree as ET
from collections import defaultdict
import re
import pprint

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

# Updating street type to a better name in the mapping list
def update_name(name, mapping, street_type_re):
    m = street_type_re.search(name)
    if m:
        st_type = m.group()
        if st_type in mapping:
            name = re.sub(street_type_re, mapping[st_type], name)
    return name


def test():
    st_types = audit(OSMFILE)
    # assert len(st_types) == 3
    #pprint.pprint(dict(st_types))

    for st_type, ways in st_types.iteritems():
        for name in ways:
            better_name = update_name(name, mapping, street_type_re)
            print name, "=>", better_name
            # if name == "West Lexington St.":
            #     assert better_name == "West Lexington Street"
            # if name == "Baldwin Rd.":
            #     assert better_name == "Baldwin Road"


if __name__ == '__main__':
    test()
