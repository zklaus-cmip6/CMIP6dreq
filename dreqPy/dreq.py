"""This module provides a basic python API to the Data Request.
After ingesting the XML documents (configuration and request) the module generates two python objects:
1. A collection of records
2. Index
"""
import xml, string, collections
import xml.dom
import xml.dom.minidom
import re, shelve
from __init__ import DOC_DIR

jsh='''<link type="text/css" href="/css/jquery-ui-1.8.16.custom.css" rel="Stylesheet" />
 <script src="/js/2013/jquery.min.js" type="text/javascript"></script>
 <script src="/js/2013/jquery-ui.min.js" type="text/javascript"></script>
 <script src="/js/2013/jquery.cookie.js" type="text/javascript"></script>
'''

blockSchemaFile = '%s/%s' % (DOC_DIR, 'BlockSchema.csv' )

def loadBS(bsfile):
  """Read in the 'BlockSchema' definitions of the attributes defining attributes"""
  ii = open( bsfile, 'r' ).readlines()
  ll = []
  for l in ii:
    ll.append( [x for x in l.strip().split('\t') ] )
  cc = collections.defaultdict( dict )
  
  for l in ll[3:]:
    if len(l) < len(ll[2]):
      l.append( '' )
    try:
      for i in range( len(ll[2]) ):
        cc[l[0]][ll[2][i]] = l[i]
    except:
      print (l)
      raise
  return cc

class rechecks(object):
  """Checks to be applied to strings"""
  def __init__(self):
    self.__isInt = re.compile( '-{0,1}[0-9]+' )

  def isIntStr( self, tv ):
    """Check whether a string is a valid representation of an integer."""
    if type( tv ) not in [type(''),type(u'')]:
      self.reason = 'NOT STRING'
      return False
    ok = self.__isInt.match( tv ) != None
    if not ok:
      self.reason = 'Failed to match regular expression for integers'
    else:
      self.reason = ''
    return ok

class dreqItemBase(object):
       __doc__ = """A base class used in the definition of records. Designed to be used via a class factory which sets "itemLabelMode" and "attributes" before the class is instantiated: attempting to instantiate the class before setting these will trigger an exception."""
       _indexInitialised = False
       _inx = None
       _urlBase = ''
       _htmlStyle = {}
       _linkAttrStyle = {}

       def __init__(self,idict=None,xmlMiniDom=None,id='defaultId',etree=False):
         dictMode = idict != None
         mdMode = xmlMiniDom != None
         self._htmlTtl = None
         assert not( dictMode and mdMode), 'Mode must be either dictionary of minidom: both assigned'
         assert dictMode or mdMode, 'Mode must be either dictionary of minidom: neither assigned'
         ##self._defaults = { }
         ##self._globalDefault = '__unset__'
         self._contentInitialised = False
         self._greenIcon = '<img height="12pt" src="/images/154g.png" alt="[i]"/>'
         if dictMode:
           self.dictInit( idict )
         elif mdMode:
           self.mdInit( xmlMiniDom, etree=etree )

       def __repr__(self):
         """Provide a one line summary of identifying the object."""
         if self._contentInitialised:
           return 'Item <%s>: [%s] %s' % (self._h.title,self.label,self.title)
         else:
           return 'Item <%s>: uninitialised' % self._h.title

       def __info__(self,full=False):
         """Print a summary of the data held in the object as a list of key/value pairs"""
         if self._contentInitialised:
           print ( 'Item <%s>: [%s] %s' % (self._h.title,self.label,self.title) )
           for a in self.__dict__.keys():
             if a[0] != '_' or full:
               if hasattr( self._a[a], 'useClass') and self._a[a].useClass == 'internalLink' and self._base._indexInitialised:
                 if self.__dict__[a] in self._base._inx.uid:
                   targ = self._base._inx.uid[ self.__dict__[a] ]
                   print ( '   %s: [%s]%s [%s]' % ( a, targ._h.label, targ.label, self.__dict__[a] ) )
                 else:
                   print ( '   %s: [ERROR: key not found] [%s]' % ( a, self.__dict__[a] ) )
               else:
                 print ( '    %s: %s' % ( a, self.__dict__[a] ) )
         else:
           print ( 'Item <%s>: uninitialised' % self.sectionLabel )

       def __href__(self,odir="",label=None):
         """Generate html text for a link to this item."""
         igns =  ['','__unset__']
         if self._htmlTtl == None:
           if 'description' in self.__dict__ and self.description != None and string.strip( self.description ) not in igns:
             ttl = self.description
           elif 'title' in self.__dict__ and self.title != None and string.strip( self.title ) not in igns:
             ttl = self.title
           else:
             ttl = self.label
           ttl = string.replace( ttl,'"', '&quot;' )
           ttl = string.replace( ttl,'<', '&lt;' )
           self._htmlTtl = string.replace( ttl,'>', '&gt;' )
         if label == None:
             label = self.uid

         return '<span title="%s"><a href="%s%s.html">%s</a></span>' % (self._htmlTtl,odir,self.uid,label)

       def getHtmlLinkAttrStyle(self,a):
         """Return a string containing a html fragment for a link to an attribute."""
         if a in self.__class__._linkAttrStyle:
           return self.__class__._linkAttrStyle[a]
         else:
           return lambda a,targ, frm='': '<li>%s: [%s] %s [%s]</li>' % ( a, targ._h.label, targ.label, targ.__href__() )

       def __html__(self,ghis=None):
         """Create html view"""
         msg = []
         if self._contentInitialised:
           sect = self._h.label
           msg.append( '<h1>%s: [%s] %s</h1>' % (self._h.title,self.label,self.title) )
           msg.append( '<a href="../index.html">Home</a> &rarr; <a href="../index/%s.html">%s section index</a><br/>\n' % (sect, self._h.title) )
           msg.append( '<ul>' )
           for a in self.__dict__.keys():
             if a[0] != '_':
               app = '%s%s' % (a, self.__class__.__dict__[a].__href__(label=self._greenIcon) )
               if hasattr( self._a[a], 'useClass') and self._a[a].useClass == 'internalLink' and self._base._indexInitialised:
                 if self.__dict__[a] == '__unset__':
                   m = '<li>%s: %s [missing link]</li>' % ( app, self.__dict__[a] )
                 else:
                   try:
                     targ = self._base._inx.uid[ self.__dict__[a] ]
                     lst = self.getHtmlLinkAttrStyle(a)
                     m = lst( app, targ, frm=sect )
                   except:
                     print ( a, self.__dict__[a], sect )
                     m = '<li>%s: %s .... broken link</li>' % ( app, self.__dict__[a] )
                     ##raise
                   ##m = '<li>%s, %s: [%s] %s [%s]</li>' % ( a, self.__class__.__dict__[a].__href__(label=self._greenIcon), targ._h.label, targ.label, targ.__href__() )
               elif hasattr( self._a[a], 'useClass') and self._a[a].useClass == 'externalUrl':
                 m = '<li>%s: <a href="%s" title="%s">%s</a></li>' % ( app, self.__dict__[a], self._a[a].description, self._a[a].title )
               else:
                 m = '<li>%s: %s</li>' % ( app, self.__dict__[a] )
               msg.append( m )
           msg.append( '</ul>' )
##
## add list of inward references
##
           if self._base._indexInitialised:
             f1 = self._htmlStyle.get( sect, {} ).get( 'getIrefs', None ) != None
             if f1:
               tl = []
               if f1:
                 tl = self._htmlStyle[sect]['getIrefs']
               doall = '__all__' in tl
               if doall:
                 tl = self._inx.iref_by_sect[self.uid].a.keys()
               tl1 = []
               for t in tl:
                 if t in self._inx.iref_by_sect[self.uid].a and len( self._inx.iref_by_sect[self.uid].a[t] ) > 0:
                   tl1.append( t )
               am = []
               if len(tl1) > 0:
                 am.append( '''<div class="demo">\n<div id="tabs">\n<ul>''' )
                 for t in tl1:
                   u0 = self._inx.iref_by_sect[self.uid].a[t][0]
                   this1 = '<li><a href="#tabs-%s">%s</a></li>' % (t,self._inx.uid[u0]._h.title )
                   am.append( this1 )
                 am.append( '</ul>' )
               for t in tl1:
                   u0 = self._inx.iref_by_sect[self.uid].a[t][0]
                   am.append( '<div id="tabs-%s">' % t )
                   am.append( '<h3>%s</h3>' % self._inx.uid[u0]._h.title )
                   am.append( '<ul>' )
                   items = [self._inx.uid[u] for  u in self._inx.iref_by_sect[self.uid].a[t] ]
                   items.sort( ds('label').cmp )
                   for targ in items:
                     if ghis == None:
                       m = '<li>%s:%s [%s]</li>' % ( targ._h.label, targ.label, targ.__href__() )
                     else:
                       lst = ghis( targ._h.label )
                       m = lst( targ, frm=sect )
                     am.append( m )
                   am.append( '</ul>' )
                   am.append( '</div>' )
               if len(am) > 0:
                 am.append( '</div>' )
                 msg.append( '<h2>Links from other sections</h2>' )
                 msg.append( ''' <script>
        $(function() {
                $( "#tabs" ).tabs({cookie: { expires: 1 } });
        });
 </script>
<!-- how to make tab selection stick: http://stackoverflow.com/questions/5066581/jquery-ui-tabs-wont-save-selected-tab-index-upon-page-reload  expiry time in days-->''' )
                 for m in am:
                    msg.append(m)
               
         else:
           msg.append( '<b>Item %s: uninitialised</b>' % self.sectionLabel )
         return msg


       def dictInit( self, idict ):
         __doc__ = """Initialise from a dictionary."""
         for a in self._a.keys():
           if a in idict:
             val = idict[a]
           else:
             val = self._d.defaults.get( a, self._d.glob )
           setattr( self, a, val )
         self._contentInitialised = True

       def mdInit( self, el, etree=False ):
         __doc__ = """Initialisation from a mindom XML element. The list of attributes must be set by the class factory before the class is initialised"""
         deferredHandling=False
         nw1 = 0
         tvtl = []
         if etree:
           ks = set( el.keys() )
           for a in self._a.keys():
             if a in ks:
               aa = '%s%s' % (self.ns,a)
               tvtl.append( (a,True, str( el.get( a ) ) ) )
             else:
               tvtl.append( (a,False,None) )
         else:
           for a in self._a.keys():
             if el.hasAttribute( a ):
               tvtl.append( (a,True, str( el.getAttribute( a ) ) ) )
             else:
               tvtl.append( (a,False,None) )
       
         for a,tv,v in tvtl:
           if tv:
             if self._a[a].type == u'xs:float':
               try:
                 v = float(v)
               except:
                 print ( 'Failed to convert real number: %s' % v )
                 raise
             elif self._a[a].type == u'xs:integer':
               if self._rc.isIntStr( v ):
                 v = int(v)
               else:
                 v = string.strip(v)
                 thissect = '%s [%s]' % (self._h.title,self._h.label)
                 if v in [ '',u'',' ', u' ']:
                   if nw1 < 20:
                     print ( 'WARN.050.0001: input integer non-compliant: %s: %s: "%s" -- set to zero' % (thissect,a,v) )
                     nw1 += 1
                   v = 0
                 else:
                   try:
                     v = int(float(v))
                     print ( 'WARN: input integer non-compliant: %s: %s: %s' % (thissect,a,v) )
                   except:
                     msg = 'ERROR: failed to convert integer: %s: %s: %s' % (thissect,a,v)
                     deferredHandling=True
             elif self._a[a].type == u'xs:boolean':
               v = v in ['true','1']
             self.__dict__[a] = v
           else:
             if a in ['uid',]:
               thissect = '%s [%s]' % (self._h.title,self._h.tag)
               print ( 'ERROR.020.0001: missing uid: %s' % thissect )
               if etree:
                 print ( ks )
                 import sys
                 sys.exit(0)
             self.__dict__[a] = self._d.defaults.get( a, self._d.glob )

           ##if type( self.__dict__.get( 'rowIndex', 0 ) ) != type(0):
             ##print 'Bad row index ', el.hasAttribute( 'rowIndex' )
             ##raise
           if deferredHandling:
             print ( msg )

         self._contentInitialised = True

    
class config(object):
  """Read in a vocabulary collection configuration document and a vocabulary document"""

  def __init__(self, configdoc='out/dreqDefn.xml', thisdoc='../workbook/trial_20150724.xml', useShelve=False):
    self.rc = rechecks()
    self.silent = True
    self.vdef = configdoc
    self.vsamp = thisdoc

    self.nts = collections.namedtuple( 'sectdef', ['tag','label','title','id','itemLabelMode','level','maxOccurs','labUnique','uid'] )
    self.nti = collections.namedtuple( 'itemdef', ['tag','label','title','type','useClass','techNote'] )
    self.ntt = collections.namedtuple( 'sectinit', ['header','attributes','defaults'] )
    self.nt__default = collections.namedtuple( 'deflt', ['defaults','glob'] )
    self.ntf = collections.namedtuple( 'sect', ['header','attDefn','items'] )
    self.bscc = loadBS(blockSchemaFile)

    self.coll = {}
    doc = xml.dom.minidom.parse( self.vdef  )
##
## elementTree parsing implemented for main document
##
    self.etree = False
    self.etree = True
    if self.etree:
      import xml.etree.cElementTree as cel

      self.contentDoc = cel.parse( self.vsamp )
      root = self.contentDoc.getroot()
      ##bs = string.split( root.tag, '}' )
      bs = root.tag.split( '}' )
      if len( bs ) > 1:
        self.ns = bs[0] + '}'
      else:
        self.ns = None
    else:
      self.contentDoc = xml.dom.minidom.parse( self.vsamp )
      self.ns = None

    vl = doc.getElementsByTagName( 'table' )
    self.tables = {}
    tables = {}
    self.tableClasses = {}
    self.tableItems = collections.defaultdict( list )
##
## this loads in some metadata, but not yet in a useful way.
##
    self._t0 = self.parsevcfg(None)
    self._tableClass0 = self.itemClassFact( self._t0, ns=self.ns )
##
## define a class for the section heading records.
##
    self._t1 = self.parsevcfg('__sect__')
    self._t2 = self.parsevcfg('__main__')
    self._sectClass0 = self.itemClassFact( self._t1, ns=self.ns )

    self.tt0 = {}
    for k in self.bscc:
      self.tt0[k] = self._tableClass0(idict=self.bscc[k])
      if k in self._t0.attributes:
        setattr( self._tableClass0, '%s' % k, self.tt0[k] )
      if k in self._t1.attributes:
        setattr( self._sectClass0, '%s' % k, self.tt0[k] )

##
## save header information, as for recordAttributeDefn below
##
    self._recAtDef = {'__core__':self._t0, '__sect__':self._t1}
##
## experimental addition of __core__ to coll dictionary ..
##
    self.coll['__core__'] = self.ntf( self._t0.header, self._t0.attributes, [self.tt0[k] for k in self.tt0] )
      ##self.coll[k] = self.ntf( self.recordAttributeDefn[k].header, self.recordAttributeDefn[k].attributes, self.tableItems[k] )

    self.tt1 = {}
    self.ttl2 = []
    for v in vl:
      t = self.parsevcfg(v)
      tables[t[0].label] = t
      self.tableClasses[t[0].label] = self.itemClassFact( t, ns=self.ns )
      thisc = self.tableClasses[t[0].label]
      self.tt1[t[0].label] = self._sectClass0( idict=t.header._asdict() )
      self.tt1[t[0].label].maxOccurs = t.header.maxOccurs
      self.tt1[t[0].label].labUnique = t.header.labUnique
      self.tt1[t[0].label].level = t.header.level
      self.tt1[t[0].label].itemLabelMode = t.header.itemLabelMode
      self.ttl2 += [thisc.__dict__[a] for a in t.attributes]
    self.coll['__main__'] = self.ntf( self._t2.header, self._t2.attributes, self.ttl2 )

    self.coll['__sect__'] = self.ntf( self._t1.header, self._t1.attributes, [self.tt1[k] for k in self.tt1] )

    self.recordAttributeDefn = tables
    for k in tables.keys():
      if self.etree:
        vl = root.findall( './/%s%s' % (self.ns,k) )
        if len(vl) == 1:
          v = vl[0]
          t = v.get( 'title' )
          i = v.get( 'id' )
          uid = v.get( 'uid' )
          useclass = v.get( 'useClass' )

          self.tt1[k].label = k
          self.tt1[k].title = t
          self.tt1[k].id = i
          self.tt1[k].uid = uid
          self.tt1[k].useClass = useclass
          self.tableClasses[k]._h = self.tt1[k]
          il = v.findall( '%sitem' % self.ns )
          self.info( '%s, %s, %s, %s' % ( k, t, i, len(il) ) )
 
          self.tables[k] = (i,t,len(il))
        
          for i in il:
            ii = self.tableClasses[k](xmlMiniDom=i, etree=True)
            self.tableItems[k].append( ii )
        elif len(vl) > 1:
          assert False, 'not able to handle repeat sections with etree yet'
      else:
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
    """Switchable print function ... switch off by setting self.silent=True"""
    if not self.silent:
      print ( ss )

  ###def get(self):
    ###return self.coll

  def itemClassFact(self, sectionInfo,ns=None):
     class dreqItem(dreqItemBase):
       """Inherits all methods from dreqItemBase.

USAGE
-----
The instanstiated object contains a single data record. The "_h" attribute links to information about the record and the section it belongs to. 

object._a: a python dictionary defining the attributes in each record. The keys in the dictionary correspond to the attribute names and the values are python "named tuples" (from the "collections" module). E.g. object._a['priority'].type contains the type of the 'priority' attribute. Type is expressed using XSD schema language, so "xs:integer" implies integer.  The "useClass" attribute carries information about usage. If object._a['xxx'].useClass = u'internalLink' then the record attribute provides a link to another element and object.xxx is the unique identifier of that element.

object._h: a python named tuple describing the section. E.g. object._h.title is the section title (E.g. "CMOR Variables")
"""
       _base=dreqItemBase
       
     dreqItem.__name__ = 'dreqItem_%s' % str( sectionInfo.header.label )
     dreqItem._h = sectionInfo.header
     dreqItem._a = sectionInfo.attributes
     dreqItem._d = sectionInfo.defaults
     if sectionInfo.attributes != None:
        self.addAttributes(dreqItem, sectionInfo.attributes )
     ##dreqItem.itemLabelMode = itemLabelMode
     ##dreqItem.attributes = attributes
     dreqItem._rc = self.rc
     dreqItem.ns = ns
     return dreqItem

  def addAttributes( self, thisClass, attrDict ):
    """Add a set of attributes, from a dictionary, to a class"""
    for k in attrDict:
      setattr( thisClass, '%s' % k , attrDict[k] )
         
  def parsevcfg(self,v):
      """Parse a section definition element, including all the record attributes. The results are returned as a namedtuple of attributes for the section and a dictionary of record attribute specifications."""
      if v in [ None,'__main__']:
        idict = {'description':'An extended description of the object', 'title':'Record Description', \
         'techNote':'', 'useClass':'__core__', 'superclass':'rdf:property',\
         'type':'xs:string', 'uid':'__core__:description', 'label':'label' }
        if v == None:
          vtt = self.nts( '__core__', 'CoreAttributes', 'X.1 Core Attributes', '00000000', 'def', '0', '0', 'false', '__core__' )
        else:
          vtt = self.nts( '__main__', 'DataRequestAttributes', 'X.2 Data Request Attributes', '00000001', 'def', '0', '0', 'false', '__main__' )
      elif v == '__sect__':
        idict = {'title':'Record Description', \
         'uid':'__core__:description', 'label':'label', 'useClass':'text', 'id':'id', 'maxOccurs':'', 'itemLabelMode':'', 'level':'', 'labUnique':'' }
        vtt = self.nts( '__sect__', 'sectionAttributes', 'X.3 Section Attributes', '00000000', 'def', '0', '0', 'false', '__sect__' )
##<var label="var" uid="SECTION:var" useClass="vocab" title="MIP Variable" id="cmip.drv.001">
      else:
        l = v.getAttribute( 'label' )
        t = v.getAttribute( 'title' )
        i = v.getAttribute( 'id' )
        ilm = v.getAttribute( 'itemLabelMode' )
        lev = v.getAttribute( 'level' )
        maxo = v.getAttribute( 'maxOccurs' )
        labu = v.getAttribute( 'labUnique' )
        il = v.getElementsByTagName( 'rowAttribute' )
        vtt = self.nts( v.nodeName, l,t,i,ilm,lev, maxo, labu, 's__%s' % v.nodeName )
        idict = {}
        for i in il:
          tt = self.parseicfg(i)
          idict[tt.label] = tt
      deflt = self.nt__default( {}, '__unset__' )
      return self.ntt( vtt, idict, deflt )

  def parseicfg(self,i):
      """Parse a record attribute specification"""
      defs = {'type':"xs:string"}
      ll = []
      ee = {}
      for k in ['label','title','type','useClass','techNote','description','uid']:
        if i.hasAttribute( k ):
          ll.append( i.getAttribute( k ) )
        else:
          ll.append( defs.get( k, None ) )
        ee[k] = ll[-1]
      l, t, ty, cls, tn, desc, uid = ll
      self.lastTitle = t

      returnClass = True
      if returnClass:
        return self._tableClass0( idict=ee )
      else:
        return self.nti( i.nodeName, l,t,ty,cls,tn )

class container(object):
  """Simple container class, to hold a set of dictionaries of lists."""
  def __init__(self, atl ):
    self.uid = {}
    for a in atl:
      self.__dict__[a] =  collections.defaultdict( list )

class c1(object):
  def __init__(self):
    self.a = collections.defaultdict( list )

class index(object):
  """Create an index of the document. Cross-references are generated from attributes with class 'internalLink'. 
This version assumes that each record is identified by an "uid" attribute and that there is a "var" section. 
Invalid internal links are recorded in tme "missingIds" dictionary. 
For any record, with identifier u, iref_by_uid[u] gives a list of the section and identifier of records linking to that record.
"""

  def __init__(self, dreq):
    self.silent = True
    self.uid = {}
    self.uid2 = collections.defaultdict( list )
    nativeAtts = ['uid','iref_by_uid','iref_by_sect','missingIds']
    naok = map( lambda x: not x in dreq, nativeAtts )
    assert all(naok), 'This version cannot index collections containing sections with names: %s' % str( nativeAtts )
    self.var_uid = {}
    self.var_by_name = collections.defaultdict( list )
    self.var_by_sn = collections.defaultdict( list )
    self.iref_by_uid = collections.defaultdict( list )
    irefdict = collections.defaultdict( list )
    for k in dreq.keys():
      if 'sn' in dreq[k].attDefn:
         self.__dict__[k] =  container( ['label','sn'] )
      else:
         self.__dict__[k] =  container( ['label'] )
    ##
    ## collected names of attributes which carry internal links
    ##
      for ka in dreq[k].attDefn.keys():
        if hasattr( dreq[k].attDefn[ka], 'useClass') and dreq[k].attDefn[ka].useClass == 'internalLink':
           irefdict[k].append( ka )

    for k in dreq.keys():
        for i in dreq[k].items:
          assert 'uid' in i.__dict__, 'uid not found::\n%s\n%s' % (str(i._h),str(i.__dict__) )
          if 'uid' in self.uid:
            print ( 'ERROR.100.0001: Duplicate uid: %s [%s]' % (i.uid,i._h.title) )
            self.uid2[i.uid].append( (k,i) )
          else:
### create index bx uid.
            self.uid[i.uid] = i

    self.missingIds = collections.defaultdict( list )
    self.iref_by_sect = collections.defaultdict( c1 )
    for k in dreq.keys():
        for k2 in irefdict.get( k, [] ):
          n1 = 0
          n2 = 0
          for i in dreq[k].items:
            id2 = i.__dict__.get( k2 )
            if id2 != '__unset__':
              sect = i._h.label
## append attribute name and target  -- item i.uid, attribute k2 reference item id2
              self.iref_by_uid[ id2 ].append( (k2,i.uid) )
              self.iref_by_sect[ id2 ].a[sect].append( i.uid )
              if id2 in self.uid:
                n1 += 1
              else:
                n2 += 1
                self.missingIds[id2].append( (k,k2,i.uid) )
          self.info(  'INFO:: %s, %s:  %s (%s)' % (k,k2,n1,n2) )

    for k in dreq.keys():
      for i in dreq[k].items:
        self.__dict__[k].uid[i.uid] = i
        self.__dict__[k].label[i.label].append( i.uid )
        if 'sn' in dreq[k].attDefn:
          self.__dict__[k].sn[i.sn].append( i.uid )

  def info(self,ss):
    if not self.silent:
      print ( ss )

class ds(object):
  """Comparison object to assist sorting of lists of dictionaries"""
  def __init__(self,k):
    self.k = k
  def cmp(self,x,y):
    return cmp( x.__dict__[self.k], y.__dict__[self.k] )

class kscl(object):
  """Comparison object to assist sorting of dictionaries of class instances"""
  def __init__(self,idict,k):
    self.k = k
    self.idict = idict
  def cmp(self,x,y):
    return cmp( self.idict[x].__dict__[self.k], self.idict[y].__dict__[self.k] )

src1 = '../workbook/trial_20150831.xml'

#DEFAULT LOCATION -- changed automatically when building distribution
defaultDreq = 'dreq.xml'
#DEFAULT CONFIG
defaultConfig = 'dreq2Defn.xml'

defaultDreqPath = '%s/%s' % (DOC_DIR, defaultDreq )
defaultConfigPath = '%s/%s' % (DOC_DIR, defaultConfig )

class loadDreq(object):
  """Load in a vocabulary document.
  dreqXML: full path to the XML document
  configdoc: full path to associated configuration document
  useShelve: flag to specify whether to retrieve data from cache (not implemented)
  htmlStyles: dictionary of styling directives which influence structure of html page generates by the "makeHtml" method
"""

  def __init__(self,dreqXML=defaultDreqPath, configdoc=defaultConfigPath, useShelve=False, htmlStyles=None ):
    self.c = config( thisdoc=dreqXML, configdoc=configdoc, useShelve=useShelve)
    self.coll = self.c.coll
    self.inx = index(self.coll)
    self.itemStyles = {}
    self.defaultItemLineStyle = lambda i, frm='', ann='': '<li>%s: %s</li>' % ( i.label, i.__href__(odir='../u/') )
##
## add index to Item base class .. so that it can be accessed by item instances
##
    dreqItemBase._inx = self.inx
    dreqItemBase._indexInitialised = True
##
## load in additional styling directives
##
    if htmlStyles != None:
      for k in htmlStyles:
        dreqItemBase._htmlStyle[k] = htmlStyles[k]

##    dreqItemBase._htmlStyle['__general__'] = {'addRemarks':True}

    self.pageTmpl = """<html><head><title>%s</title>
%s
<link rel="stylesheet" type="text/css" href="%scss/dreq.css">
</head><body>
<div id="top">CMIP6 Data Request</div>
%s</body></html>"""

  def getHtmlItemStyle(self, sect):
    """Get the styling method associated with a given section."""
    if sect in self.itemStyles:
      return self.itemStyles[sect]
    return self.defaultItemLineStyle


  def _sectionSortHelper(self,title):
    ab = string.split( string.split(title)[0], '.' )
    if len( ab ) == 2:
      a,b = ab
    ##sorter =  lambda x: [int(y) for y in string.split( string.split(x,':')[0], '.' )]
      if self.c.rc.isIntStr(a):
        a = int(a)
      if self.c.rc.isIntStr(b):
        b = int(b)
      rv = (a,b)
    elif len(ab) == 1:
      rv = (ab[0],0)
    else:
      rv = ab 
    return rv

  def makeHtml(self,odir='./html', ttl0 = 'Data Request Index', annotations=None):
    """Generate a html view of the vocabularies, using the "__html__" method of the vocabulary item class to generate a
page for each item and also generating index pages.
    odir: directory for html files;
    ttl0: Title for main index (in odir/index.html)"""

    ks = self.inx.uid.keys()
    ks.sort( kscl( self.inx.uid, 'title' ).cmp )
    for k in ks:
      i = self.inx.uid[k]
      ttl = 'Data Request Record: [%s]%s' % (i._h.label,i.label)
      bdy = string.join( i.__html__( ghis=self.getHtmlItemStyle ), '\n' )
      oo = open( '%s/u/%s.html' % (odir,i.uid), 'w' )
      oo.write( self.pageTmpl % (ttl, jsh, '../', bdy ) )
      oo.close()

    msg0 = ['<h1>%s</h1>' % ttl0, '<ul>',]
    ks = sorted( self.coll.keys() )
    ee = {}
    for k in ks:
      ee[self.coll[k].header.title] = k
    kks = sorted( ee.keys(),  key = self._sectionSortHelper )
    for kt in kks:
      k = ee[kt]
##
## sort on item label
##
      if annotations != None and k in annotations:
        ann = annotations[k]
      else:
        ann = {}

      self.coll[k].items.sort( ds('label').cmp )
      ttl = 'Data Request Section: %s' % k
      msg0.append( '<li><a href="index/%s.html">%s [%s]</a></li>\n' % (k,self.coll[k].header.title,k) )
      msg = ['<h1>%s</h1>\n' % ttl, '<ul>',]
      msg.append( '<a href="../index.html">Home</a><br/>\n' )
      lst = self.getHtmlItemStyle(k)
      
      for i in self.coll[k].items:
        ##m = '<li>%s: %s</li>' % ( i.label, i.__href__(odir='../u/') )
       
        m = lst( i, ann=ann.get( i.label ) )
        msg.append( m )
      msg.append( '</ul>' )
      bdy = string.join( msg, '\n' )
      oo = open( '%s/index/%s.html' % (odir,k), 'w' )
      oo.write( self.pageTmpl % (ttl, '', '../', bdy ) )
      oo.close()
    msg0.append( '</ul>' )
    bdy = string.join( msg0, '\n' )
    oo = open( '%s/index.html' % odir, 'w' )
    oo.write( self.pageTmpl % (ttl0, '', '', bdy ) )
    oo.close()
    
if __name__ == '__main__':
  dreq = loadDreq( )

