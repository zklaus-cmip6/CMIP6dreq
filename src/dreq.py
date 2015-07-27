""" Module to read in the data request and make some cross-reference tables to facilitate use.
----------------------------------------------------------------------------------------------
The data request is stored in a flattened format, which nevertheless requires 7 interlinking sections.
"""

import xml, string, collections
import xml.dom
import xml.dom.minidom
class dreqItemBase(object):
       def __init__(self,dict=None,xmlMiniDom=None,id='defaultId'):
         dictMode = dict != None
         mdMode = xmlMiniDom != None
         assert not( dictMode and mdMode), 'Mode must be either dictionary of minidom: both assigned'
         assert dictMode or mdMode, 'Mode must be either dictionary of minidom: neither assigned'
         self.defaults = {}
         self.globalDefault = '__unset__'
         if dictMode:
           self.dictInit( dict )
         elif mdMode:
           self.mdInit( xmlMiniDom )

       def dictInit( self, dict ):
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

  def __init__(self):
    self.vdef = '../docs/parVocabDefn.xml' 
    self.vsamp = '../docs/CMIP6DataRequest_v0_01.xml'
    self.nts = collections.namedtuple( 'sectdef', ['tag','label','title','id','itemLabelMode'] )
    self.nti = collections.namedtuple( 'itemdef', ['tag','label','title','type'] )
    self.ntt = collections.namedtuple( 'sect', ['header','attributes'] )

    doc = xml.dom.minidom.parse( self.vdef  )
    self.contentDoc = xml.dom.minidom.parse( self.vsamp )
##<vocab label="institute" title="Institute" id="cmip.drv.001" itemLabelMode="def">
##  <itemAttribute label="label"/>
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

    for k in tables.keys():
      vl = self.contentDoc.getElementsByTagName( k )
      if len(vl) == 1:
        v = vl[0]
        t = v.getAttribute( 'title' )
        i = v.getAttribute( 'id' )
        il = v.getElementsByTagName( 'item' )
        print k, t, i, len(il)
        self.tables[k] = (i,t,len(il))
        
        for i in il:
          ii = self.tableClasses[k](xmlMiniDom=i)
          self.tableItems[k].append( ii )
      elif len(vl) > 1:
        l1 = []
        l2 = []
        print '#### %s: %s' % (k,len(vl) )
        for v in vl:
          t = v.getAttribute( 'title' )
          i = v.getAttribute( 'id' )
          il = v.getElementsByTagName( 'item' )
          print k, t, i, len(il)
          l1.append( (i,t,len(il)) )
          
          l2i = []
          for i in il:
            ii = self.tableClasses[k](xmlMiniDom=i)
            l2i.append( ii )
          l2.append( l2i )
        self.tables[k] = l1
        self.tableItems[k] = l2

  def itemClassFact(self,itemLabelMode,attributes):
     class dreqItem(dreqItemBase):
       """Inherits all methods from dreqItemBase"""
       
     dreqItem.itemLabelMode = itemLabelMode
     dreqItem.attributes = attributes
     return dreqItem
         
  def parsevcfg(self,v):
      l = v.getAttribute( 'label' )
      t = v.getAttribute( 'title' )
      i = v.getAttribute( 'id' )
      ilm = v.getAttribute( 'itemLabelMode' )
      il = v.getElementsByTagName( 'rowAttribute' )
      vtt = self.nts( v.nodeName, l,t,i,ilm )
      ll = []
      idict = {}
      for i in il:
        tt = self.parseicfg(i)
        idict[tt.label] = tt
        ll.append(tt)
      return self.ntt( vtt, idict )

  def parseicfg(self,i):
      l = i.getAttribute( 'label' )
      if i.hasAttribute( 'title' ):
        t = i.getAttribute( 'title' )
        self.lastTitle = t
      else:
        t = None
      if i.hasAttribute( 'type' ):
        ty = i.getAttribute( 'type' )
      else:
        ty = "xs:string"
      return self.nti( i.nodeName, l,t,ty )

c = config()

class index(object):
  def __init__(self, dreq):
    self.uuid = {}
    self.var_uuid = {}
    self.var_by_name = collections.defaultdict( list )
    self.var_by_sn = collections.defaultdict( list )
    self.iref_by_uuid = collections.defaultdict( list )
    irefdict = {'ovar':['vid'], 'groupItem':['gpid','vid'], 'requestLink':['refid'], 'requestItem':['rlid'], 'revisedTabItem':['vid']}
    for k in dreq.tableItems.keys():
        for i in dreq.tableItems[k]:
          self.uuid[i.uuid] = (k,i)
        for k2 in irefdict.get( k, [] ):
          for i in dreq.tableItems[k]:
            self.iref_by_uuid[ i.__dict__.get( k2 ) ].append( (k2,i.uuid) )   

    for i in dreq.tableItems['var']:
       self.var_uuid[i.uuid] = i
       self.var_by_name[i.label].append( i.uuid )
       self.var_by_sn[i.sn].append( i.uuid )

  def makeVarRefs(self):
    self.varRefs = {}
    for thisuuid in self.var_uuid.keys():
      if self.iref_by_uuid.has_key(thisuuid):
        ee1 = collections.defaultdict( list )
        for k,i in self.iref_by_uuid[thisuuid]:
          sect,thisi = self.uuid[i]
### irefdict = {'ovar':['vid'], 'groupItem':['gpid','vid'], 'requestLink':['refid'], 'requestItem':['rlid'], 'revisedTabItem':['vid']}
          if sect == 'groupItem':
            ee1[sect].append( '%s.%s' % (thisi.mip, thisi.group) )
          elif sect == 'ovar':
            ee1[sect].append( thisi.mipTable )
          elif sect == 'revisedTabItem':
            ee1[sect].append( '%s.%s' % (thisi.mip, thisi.table) )
        self.varRefs[thisuuid] = ee1

inx = index( c )
inx.makeVarRefs()
