import types as typelib
import datetime
import xml.etree.ElementTree as ET

def namespaces(nsmap):
    return dict(('xmlns:%s'%k,v) for k,v in nsmap.items())

def get_methods(kls):
    methods = {}
    for k, v in vars(kls).items():
        if not k.startswith('_') and isinstance(v, typelib.FunctionType):
            methods[k] = v
    return methods

def xs_type(name, sequence):
    elem = ET.Element('xs:element', name=name)
    seq = ET.SubElement(ET.SubElement(elem, 'xs:complexType'), 'xs:sequence')
    for name, typ in sequence.items():
        el = ET.SubElement(seq, 'xs:element', name=name, type='xs:string')
    return elem

def get_types(kls, methods):
    extratypes = set()
    typeselem = ET.Element('wsdl:types')
    schema = ET.SubElement(typeselem, 'xs:schema', elementFormDefault='qualified', targetNamespace=kls._target_namespace)
    built_in_types = (int, float, str, datetime.datetime, datetime.date)
    for name, method in methods.items():
        annot = method.__annotations__
        params = dict((k,v) for k,v in annot.items() if not k is 'return')
        schema.append(xs_type(name, params))
        schema.append(xs_type('%sResponse' % name, {'%sResult' % name: annot['return']}))
    return typeselem

def add_messages(defel, methods):
    for m in methods:
        msginel = ET.SubElement(defel, 'wsdl:message', name='%sIn'%m)
        partel = ET.SubElement(msginel, 'wsdl:part', name='parameters', element='tns:%s'%m)
        msgoutel = ET.SubElement(defel, 'wsdl:message', name='%sOut'%m)
        partel = ET.SubElement(msgoutel, 'wsdl:part', name='parameters', element='tns:%sResponse'%m)

def add_port(defel, kls, methods, name):
    portName = kls.__name__ + name
    portel = ET.SubElement(defel, 'wsdl:portType', name=portName)
    for m, func in methods.items():
        op = ET.SubElement(portel, 'wsdl:operation', name=m)
        ET.SubElement(op, 'wsdl:input', message='tns:%sIn'%m)
        ET.SubElement(op, 'wsdl:output', message='tns:%sOut'%m)
    return portel

def add_binding(defel, kls, methods, name, port, prefix=None):
    if prefix == None:
        prefix = name.lower()
    bindingName = kls.__name__ + name
    bindel = ET.SubElement(defel, 'wsdl:binding', name=bindingName, type='tns:%s'%port.get('name'))
    protel = ET.SubElement(bindel, '%s:binding'%prefix, transport='http://schemas.xmlsoap.org/soap/http')
    for m in methods:
        op = ET.SubElement(bindel, 'wsdl:operation', name=m)
        actionel = ET.SubElement(op, '%s:operation'%prefix, soapAction=kls._target_namespace+'/%s'%m, style='document')
        inp = ET.SubElement(op, 'wsdl:input')
        ET.SubElement(inp, '%s:body'%prefix, use='literal')
        out = ET.SubElement(op, 'wsdl:output')
        ET.SubElement(out, '%s:body'%prefix, use='literal')

def generate(kls):
    nsmap = {
        'wsdl': 'http://schemas.xmlsoap.org/wsdl/',
        'xs': 'http://www.w3.org/2001/XMLSchema',
        'soap': 'http://schemas.xmlsoap.org/wsdl/soap/',
        'soap12': 'http://schemas.xmlsoap.org/wsdl/http/',
        'tns': kls._target_namespace
    }
    defelem = ET.Element('wsdl:definitions',
                         attrib=namespaces(nsmap),
                         targetNamespace=kls._target_namespace)
    methods = get_methods(kls)
    # Create types
    typeselem = get_types(kls, methods)
    defelem.append(typeselem)
    # Create message
    add_messages(defelem, methods)
    # Create port
    port = add_port(defelem, kls, methods, 'Soap')
    add_binding(defelem, kls, methods, 'Soap', port)
    add_binding(defelem, kls, methods, 'Soap12', port)
    serviceel = ET.SubElement(defelem, 'wsdl:service', name=kls.__name__)

    for porttype in defelem.findall('wsdl:binding'):
        name = porttype.get('name')
        portel = ET.SubElement(serviceel, 'wsdl:port', name=name, binding='tns:%s'%name)
        prefix='undefined'
        for el in porttype:
            if not el.tag.startswith('wsdl:'):
                prefix = el.tag.split(':',1)[0]
                break
        ET.SubElement(portel, '%s:address'%prefix, location=kls._endpoint)
    return defelem
