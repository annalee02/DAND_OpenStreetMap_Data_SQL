"""
- Auditing the OSMFILE and changing the unexpected postal code types to the appropriate ones.
- The update_zip function actually fixes the postal codes.
"""

import xml.etree.cElementTree as ET
from collections import defaultdict
import re
import pprint

# osm file
OSMFILE = "las-vegas_nevada.osm"

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

def test():
    # Auditing our osm file
    zp_types = zip_audit(OSMFILE)

    # Printing results
    #pprint.pprint(dict(zp_types))

    for zip_type, ways in zp_types.iteritems():
        for name in ways:
            better_name = update_zip(name)
            print name, "=>", better_name

if __name__ == '__main__':
    test()
