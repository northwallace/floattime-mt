"""Reproduce manually reviewed planning mileage from an archived public KML line.

This measures a published map, not a surveyed route or a published numeric trip
length. It grants no access, course-display, navigation or timing approval.
"""
import hashlib
import math
from pathlib import Path
import re
import xml.etree.ElementTree as ET

METHOD = 'mapped-course-length'
ALGORITHM = 'haversine-6371008.8m'
NS = {'k': 'http://www.opengis.net/kml/2.2'}

def require(ok, message):
    if not ok: raise ValueError(message)

def distance(a, b):
    x, y = math.radians(a[1]), math.radians(b[1])
    dl = math.radians(b[0]-a[0])
    return 12742017.6 * math.asin(min(1, math.sqrt(math.sin((y-x)/2)**2 + math.cos(x)*math.cos(y)*math.sin(dl/2)**2)))

def read_line(root, measurement):
    require(isinstance(measurement, dict), 'Mapped distance measurement required')
    require(measurement.get('format') == 'kml' and measurement.get('algorithm') == ALGORITHM, 'Unsupported mapped distance format or algorithm')
    relative = measurement.get('evidenceFile')
    require(isinstance(relative, str) and relative.startswith('research/') and not Path(relative).is_absolute(), 'Mapped distance evidence must be under research/')
    folder = (root/'research').resolve(); path = (root/relative).resolve()
    require(folder in path.parents and path.is_file(), 'Mapped distance evidence path is missing or outside research/')
    require(path.stat().st_size <= 20000000, 'Mapped distance evidence file is too large')
    raw = path.read_bytes()
    require(isinstance(measurement.get('sha256'), str) and re.fullmatch('[a-f0-9]{64}', measurement['sha256']), 'Mapped distance evidence hash required')
    require(hashlib.sha256(raw).hexdigest() == measurement['sha256'], 'Mapped distance evidence changed; re-review required')
    require(b'<!DOCTYPE' not in raw.upper() and b'<!ENTITY' not in raw.upper(), 'KML declarations are not supported')
    try: document = ET.fromstring(raw)
    except ET.ParseError as e: raise ValueError('Invalid mapped distance KML') from e
    name = measurement.get('featureName')
    require(isinstance(name, str) and name.strip(), 'Mapped distance feature name required')
    matches = [p for p in document.findall('.//k:Placemark', NS) if p.findtext('k:name', namespaces=NS) == name]
    require(len(matches) == 1, 'Mapped distance feature must be unique')
    lines = matches[0].findall('./k:LineString', NS)
    require(len(lines) == 1 and len(matches[0].findall('.//k:LineString', NS)) == 1, 'Mapped distance requires one unambiguous LineString')
    text = lines[0].findtext('k:coordinates', namespaces=NS) or ''
    points = []
    for item in text.split():
        parts = item.split(',')
        require(len(parts) in (2,3), 'Invalid mapped distance coordinate')
        try: lon,lat = float(parts[0]),float(parts[1])
        except ValueError as e: raise ValueError('Invalid mapped distance coordinate') from e
        require(math.isfinite(lat) and math.isfinite(lon) and -90<=lat<=90 and -180<=lon<=180, 'Invalid mapped distance coordinate')
        points.append([lon,lat])
    require(2<=len(points)<=100000, 'Mapped distance needs a bounded line with at least two vertices')
    miles = sum(distance(a,b) for a,b in zip(points,points[1:])) / 1609.344
    require(miles > 0, 'Mapped distance line has zero length')
    return points, miles

def validate(section, root):
    evidence = section['distanceEvidence'];measurement=evidence.get('measurement')
    points,miles = read_line(root, measurement)
    measured = measurement.get('measuredMiles')
    require(type(measured) in (int,float) and math.isfinite(measured) and abs(measured-miles)<.000001, 'Mapped distance measurement is not reproducible')
    require(abs(section['miles']-round(miles,1))<.000001, 'Mileage disagrees with the reviewed map line')
    require(isinstance(measurement.get('reviewNote'),str) and measurement['reviewNote'].strip(), 'Mapped distance review note required')
    for endpoint,point in [('putIn',points[0]),('takeOut',points[-1])]:
        record=evidence.get(endpoint);coords=section.get(endpoint+'Coords')
        require(isinstance(record,dict) and record.get('name')==section[endpoint], 'Mapped distance endpoint name changed')
        require(isinstance(record.get('sourceLocation'),str) and record['sourceLocation'].strip(), 'Mapped distance endpoint source location required')
        require(isinstance(coords,dict), 'Mapped distance requires reviewed access coordinates')
        for axis,lo,hi in [('lat',-90,90),('lon',-180,180)]:
            value=record.get(axis)
            require(type(value) in (int,float) and math.isfinite(value) and lo<=value<=hi, 'Invalid mapped distance endpoint coordinate')
            require(abs(value-coords[axis])<.000001, 'Mapped distance access coordinates changed; re-review required')
        require(distance(point,[record['lon'],record['lat']])<=250, 'Mapped line does not match the named endpoint or downstream order')
