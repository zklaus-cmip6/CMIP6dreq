"""This module provides a basic python API to the Data Request.
After ingesting the XML documents (configuration and request) the module generates two python objects:
1. A collection of records
2. Index
"""
import xml, string, collections
import xml.dom
import xml.dom.minidom

class dreqItemBase(object):
       __doc__ = """A base class used in the definition of records. Designed to be used via a class factory which sets "itemLabelMode" and "attributes" before the class is instantiated: attempting to instantiate the class before setting these will trigger an exception."""
       def __init__(self,dict=None,xmlMiniDom=None,id='defaultId'):
         dictMode = dict != None
         mdMode = xmlMiniDom != None
         assert not( dictMode and mdMode), 'Mode must be either dictionary of minidom: both assigned'
         assert dictMode or mdMode, 'Mode must be either dictionary of minidom: neither assigned'
         self.defaults = { }
         self.globalDefault = '__unset__'
         if dictMode:
           self.dictInit( dict )
         elif mdMode:
           self.mdInit( xmlMiniDom )

       def dictInit( self, dict ):
         __doc__ = """Initialise from a dictionary."""
         for a in self.attributes:
           if dict.has_key(a):
             self.__dict__[a] = dict[a]
           else:
             self.__dict__[a] = self.defaults.get( a, self.globalDefault )

       def mdInit( self, el ):
         __doc__ = """Initialisation from a mindom XML element. The list of attributes must be set by the class factory before the class is initialised"""
         for a in self.attributes:
           if el.hasAttribute( a ):
             v = el.getAttribute( a )
             self.__dict__[a] = v
           else:
             self.__dict__[a] = self.defaults.get( a, self.globalDefault )

    
class config(object):
  """Read in a vocabulary collection configuration document and a vocabulary document"""

  def __init__(self, configdoc='out/dreqDefn.xml', thisdoc='../workbook/trial_20150724.xml',silent=True):
    self.silent = silent
    self.vdef = configdoc
    self.vsamp = thisdoc
    self.nts = collections.namedtuple( 'sectdef', ['tag','label','title','id','itemLabelMode','level'] )
    self.nti = collections.namedtuple( 'itemdef', ['tag','label','title','type','rClass','techNote'] )
    self.ntt = collections.namedtuple( 'sectinit', ['header','attributes'] )
    self.ntf = collections.namedtuple( 'sect', ['header','attDefn','items'] )

    self.coll = {}
    doc = xml.dom.minidom.parse( self.vdef  )
    self.contentDoc = xml.dom.minidom.parse( self.vsamp )
    vl = doc.getElementsByTagName( 'table' )
    self.slist = []
    self.tables = {}
    tables = {}
    self.tableClasses = {}
    self.tableItems = collections.defaultdict( list )
    for v in vl:
      t = self.parsevcfg(v)
      tables[t[0].label] = t
      self.tableClasses[t[0].label] = self.itemClassFact( t.header.itemLabelMode, t.attributes.keys() )
      self.slist.append( t )

    self.recordAttributeDefn = tables
    for k in tables.keys():
      vl = self.contentDoc.getElementsByTagName( k )
      if len(vl) == 1:
        v = vl[0]
        t = v.getAttribute( 'title' )
        i = v.getAttribute( 'id' )
        il = v.getElementsByTagName( 'item' )
        self.info( '%s, %s, %s, %s' % ( k, t, i, len(il) ) )
 
        self.tables[k] = (i,t,len(il))
        
        for i in il:
          ii = self.tableClasses[k](xmlMiniDom=i)
          self.tableItems[k].append( ii )
      elif len(vl) > 1:
        l1 = []
        l2 = []
        for v in vl:
          t = v.getAttribute( 'title' )
          i = v.getAttribute( 'id' )
          il = v.getElementsByTagName( 'item' )
          self.info( '%s, %s, %s, %s' % ( k, t, i, len(il) ) )
          l1.append( (i,t,len(il)) )
          
          l2i = []
          for i in il:
            ii = self.tableClasses[k](xmlMiniDom=i)
            l2i.append( ii )
          l2.append( l2i )
        self.tables[k] = l1
        self.tableItems[k] = l2
      self.coll[k] = self.ntf( self.recordAttributeDefn[k].header, self.recordAttributeDefn[k].attributes, self.tableItems[k] )
 
  def info(self,ss):
    if not self.silent:
      print ss

  def get(self):
    return self.coll

  def itemClassFact(self,itemLabelMode,attributes):
     class dreqItem(dreqItemBase):
       """Inherits all methods from dreqItemBase"""
       
     dreqItem.itemLabelMode = itemLabelMode
     dreqItem.attributes = attributes
     return dreqItem
         
  def parsevcfg(self,v):
      """Parse a section definition element, including all the record attributes. The results are returned as a namedtuple of attributes for the section and a dictionary of record attribute specifications."""
      l = v.getAttribute( 'label' )
      t = v.getAttribute( 'title' )
      i = v.getAttribute( 'id' )
      ilm = v.getAttribute( 'itemLabelMode' )
      lev = v.getAttribute( 'level' )
      il = v.getElementsByTagName( 'rowAttribute' )
      vtt = self.nts( v.nodeName, l,t,i,ilm,lev )
      idict = {}
      for i in il:
        tt = self.parseicfg(i)
        idict[tt.label] = tt
      return self.ntt( vtt, idict )

  def parseicfg(self,i):
      """Parse a record attribute specification"""
      defs = {'type':"xs:string"}
      ll = []
      for k in ['label','title','type','class','techNote']:
        if i.hasAttribute( k ):
          ll.append( i.getAttribute( k ) )
        else:
          ll.append( defs.get( k, None ) )
      l, t, ty, cls, tn = ll
      self.lastTitle = t
      return self.nti( i.nodeName, l,t,ty,cls,tn )

class container(object):
  """Simple container class, to hold a set of dictionaries of lists."""
  def __init__(self, atl ):
    self.uuid = {}
    for a in atl:
      self.__dict__[a] =  collections.defaultdict( list )

class c1(object):
  def __init__(self):
    self.a = collections.defaultdict( list )
class index(object):
  """Create an index of the document. Cross-references are generated from attributes with class 'internalLink'. 
This version assumes that each record is identified by an "uuid" attribute and that there is a "var" section. 
Invalid internal links are recorded in tme "missingIds" dictionary. 
For any record, with identifier u, iref_by_uuid[u] gives a list of the section and identifier of records linking to that record.
"""

  def __init__(self, dreq):
    self.silent = True
    self.uuid = {}
    nativeAtts = ['uuid','iref_by_uuid','iref_by_sect','missingIds']
    naok = map( lambda x: not dreq.has_key(x), nativeAtts )
    assert all(naok), 'This version cannot index collections containing sections with names: %s' % str( nativeAtts )
    self.var_uuid = {}
    self.var_by_name = collections.defaultdict( list )
    self.var_by_sn = collections.defaultdict( list )
    self.iref_by_uuid = collections.defaultdict( list )
    irefdict = collections.defaultdict( list )
    for k in dreq.keys():
      if dreq[k].attDefn.has_key('sn'):
         self.__dict__[k] =  container( ['label','sn'] )
      else:
         self.__dict__[k] =  container( ['label'] )
    ##
    ## collected names of attributes which carry internal links
    ##
      for ka in dreq[k].attDefn.keys():
        if dreq[k].attDefn[ka].rClass == 'internalLink':
           irefdict[k].append( ka )

    for k in dreq.keys():
        for i in dreq[k].items:
          self.uuid[i.uuid] = (k,i)

    self.missingIds = collections.defaultdict( list )
    self.iref_by_sect = collections.defaultdict( c1 )
    for k in dreq.keys():
        for k2 in irefdict.get( k, [] ):
          n1 = 0
          n2 = 0
          for i in dreq[k].items:
            id2 = i.__dict__.get( k2 )
            if id2 != '__unset__':
              self.iref_by_uuid[ id2 ].append( (k2,i.uuid) )
              self.iref_by_sect[ id2 ].a[k2].append( i.uuid )
              if self.uuid.has_key( id2 ):
                n1 += 1
              else:
                n2 += 1
                self.missingIds[id2].append( (k,k2,i.uuid) )
          self.info(  'INFO:: %s, %s:  %s (%s)' % (k,k2,n1,n2) )

    for k in dreq.keys():
      for i in dreq[k].items:
        self.__dict__[k].uuid[i.uuid] = i
        self.__dict__[k].label[i.label].append( i.uuid )
        if dreq[k].attDefn.has_key('sn'):
          self.__dict__[k].sn[i.sn].append( i.uuid )

  def info(self,ss):
    if not self.silent:
      print ss


class loadDreq(object):
  def __init__(self,dreqXML='../docs/dreq.xml',configdoc='../docs/dreqDefn.xml' ):
    self.c = config( thisdoc=dreqXML, configdoc=configdoc,silent=False)
    self.coll = self.c.get()
    self.inx = index(self.coll)

if __name__ == '__main__':
  dreq = loadDreq()

