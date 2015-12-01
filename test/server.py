import sys
sys.path.append('.')

import datetime as dt
import paxws.server.wsdlgenerator as wsdlgen
import xml.etree.ElementTree as ET
from paxws.server import decorator
from xml.dom import minidom

def pretty_print(etree):
    s = minidom.parseString(ET.tostring(etree)).toprettyxml(indent='  ')
    print(s)

class Foo:
    x = str
    y = dt.datetime

@decorator.service('http://www.test.com/hello', 'http://localhost:8001')
class MyService:
    def sayHello(name: str, datetime: dt.datetime) -> str:
        return "Yo %s, now is %s" % (name, datetime)
