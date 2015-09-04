import dreq, collections, string, os
import htmlTemplates as tmpl
import xml, re
import xml.dom, xml.dom.minidom

from utils_dreq import uniCleanFunc

empty=re.compile('^$')

dq = dreq.loadDreq()
inx = dq.inx
##inx.makeVarRefs()
ix_rql_uuid = {}
ix_rqvg_uuid = {}
ix_ovar_uuid = {}
ix_gpi_uuid = {}
list_gp_ovar = collections.defaultdict( list )
xr_var_ovar = collections.defaultdict( list )
xr_var_gpi = collections.defaultdict( list )
rql_by_name = collections.defaultdict( list )

def makeVarRefs(uuid, var, iref_by_uuid):
    varRefs = {}
    for thisuuid in var.uuid.keys():
      if iref_by_uuid.has_key(thisuuid):
        ee1 = collections.defaultdict( list )
        for k,i in iref_by_uuid[thisuuid]:
          sect,thisi = uuid[i]
          if sect == 'groupItem':
            ee1[sect].append( '%s.%s' % (thisi.mip, thisi.group) )
          elif sect == 'ovar':
            ee1[sect].append( thisi.mipTable )
          elif sect == 'revisedTabItem':
            ee1[sect].append( '%s.%s' % (thisi.mip, thisi.table) )
      varRefs[thisuuid] = ee1
    return varRefs

varRefs = makeVarRefs( inx.uuid, inx.var, inx.iref_by_uuid)


### check back references.
nbr = 0
lbr = []
for k in inx.iref_by_uuid.keys():
  if not inx.uuid.has_key(k):
   nbr += 1
   lbr.append(k)
print 'Missing references: ', nbr
### can now apply mappings, create updated records and write to new xml?

for i in dq.coll['requestLink'].items:
   rql_by_name[i.label].append( i.uuid )
   ix_rql_uuid[i.uuid] = i

for i in dq.coll['requestVarGroup'].items:
   ix_rqvg_uuid[i.uuid] = i


oo = open( 'uuidinsert.csv', 'w' )
for i in dq.coll['revisedTabItem'].items:
  if i.uuid == '__new__':
    if inx.var.label.has_key( i.label ):
      if len( inx.var.label[i.label] ) == 1:
        v = inx.uuid[ inx.var.label[i.label][0] ][1]
        oo.write( string.join( ['unique',i.label,v.label,v.uuid,v.prov,i.mip], '\t' ) + '\n' )
      else:
        oo.write( string.join( ['ambiguous',i.label,i.mip,str(len(inx.var.label[i.label] ) ) ], '\t' ) + '\n' )
oo.close()
    
oo = open( 'varMult.csv', 'w' )
oo2 = open( 'varDup.csv', 'w' )
oo3 = open( 'varStar.csv', 'w' )
hs = ['label','title','sn','units','description','prov','procnote','procComment','uuid']
oo.write( string.join(hs, '\t' ) + '\n' )
oo2.write( string.join(hs, '\t' ) + '\n' )
oo3.write( string.join(hs, '\t' ) + '\n' )
ks = inx.var.label.keys()
ks.sort()
for k in ks:
  if len(inx.var.label[k]) == 2:
    v1 = inx.var.uuid[inx.var.label[k][0]]
    v2 = inx.var.uuid[inx.var.label[k][1]]
    cc = map( lambda x: v1.__dict__[x] == v2.__dict__[x], ['title','sn','units','description']  )
    if all(cc):
      oo2.write( string.join(map( lambda x: v1.__dict__[x], hs) + [v2.uuid,'identical'], '\t' ) + '\n' )
    else:
      oo2.write( string.join(map( lambda x: v1.__dict__[x], hs) + ['',''], '\t' ) + '\n' )
    oo2.write( string.join(map( lambda x: v2.__dict__[x], hs) + ['',''], '\t' ) + '\n' )
      
  elif len(inx.var.label[k]) > 1:
    for i in inx.var.label[k]:
      oo.write( string.join(map( lambda x: inx.var.uuid[i].__dict__[x], hs), '\t' ) + '\n' )

  if k[-2:] == '--':
    for i in (inx.var.label[k] + inx.var.label[k[:-2]]):
      oo3.write( string.join(map( lambda x: inx.var.uuid[i].__dict__[x], hs), '\t' ) + '\n' )
oo.close()
oo2.close()
oo3.close()


for i in dq.coll['groupItem'].items:
   list_gp_ovar[i.gpid].append( i.uuid )

vns = inx.var.label.keys()
vns.sort()
for v in vns:
  if len( inx.var.label[v] ) > 1:
     print 'INFO.001.0001:',v, string.join( map( lambda x: inx.var.uuid[x].sn, inx.var.label[v] ), ';' )

nok = 0
nerr = 0
for i in dq.coll['ovar'].items:
   vid = i.vid
   ix_ovar_uuid[i.uuid] = i
   xr_var_ovar[vid].append( i.uuid )
   if not inx.var.uuid.has_key(vid):
     print 'missing key:',i.__dict__
     nerr += 1
   else:
     nok += 1

nok = 0
nerr = 0
for i in dq.coll['groupItem'].items:
   vid = i.vid
   ix_gpi_uuid[i.uuid] = i
   xr_var_gpi[vid].append( i.uuid )
   if not inx.var.uuid.has_key(vid):
     nerr += 1
   else:
     nok += 1
print 'groupItem to var crossref: nok = %s, nerr = %s' % (nok, nerr)

class rqHtml(object):

  def __init__(self,odir='./html/'):
    self.odir = odir
    if not os.path.isdir(odir):
      os.mkdir(odir)

  def mkRqlHtml(self,name):
     ## [u'comment', u'uuid', u'tab', u'title', u'label', u'grid', 'defaults', u'objective', u'mip', 'globalDefault', u'gridreq']
    if len( rql_by_name[name] ) == 1:
      self.mkRqlHtml01(rql_by_name[name][0], name )
    else:
      self.mkRqlHtmlGp(name)

  def mkRqlHtmlGp(self,name):
    ee = {}
    ee['title'] = 'CMIP Request Link %s (with multiple definitions)' % name
    self.pageName = 'rql__%s.html' % name
    al =[]
    for i in range( len( rql_by_name[name] ) ):
      this = ix_rql_uuid[rql_by_name[name][i]]
      al.append( tmpl.item % {'item':'<a href="rql__%s__%s.html">[%s]</a>: %s' % (name,i,i,this.title) } )
    ee['items'] = string.join(al, '\n' )
    ee['introduction'] = ''
    ee['htmlBody'] = tmpl.indexWrapper % ee
    ee['htmlHead'] = '''<title>%(title)s</title>''' % ee
    self.pageHtml = tmpl.pageWrapper % ee
    self.write()
    for i in range( len( rql_by_name[name] ) ):
      self.mkRqlHtml01(rql_by_name[name][i],i)

  def mkRqlHtml01(self,id, tag):
    this = ix_rql_uuid[id]
    ee = {}
    if this.label == tag:
      ee['title'] = 'CMIP Request Link %s' % tag
      self.pageName = 'rql__%s.html' % tag
    else:
      ee['title'] = 'CMIP Request Link %s[%s]' % (this.label,tag)
      self.pageName = 'rql__%s__%s.html' % (this.label,tag)
    atts = this.__dict__.keys()
    atts.sort()
    al =[]
    for a in atts:
      if a not in ['defaults','globalDefault']:
        al.append( tmpl.item % {'item':'<b>%s</b>: %s' % (a,this.__dict__.get(a,'-- Not Set --')) } )
    ee['items'] = string.join(al, '\n' )
    ee['introduction'] = ''
    ee['htmlBody'] = tmpl.indexWrapper % ee
    ee['htmlHead'] = '''<title>%(title)s</title>''' % ee
    self.pageHtml = tmpl.pageWrapper % ee
    self.write()
     
  def mkVarHtml(self,name):
    if len( inx.var.label[name] ) == 1:
      self.mkVarHtml01(inx.var.label[name][0], name )
    else:
      self.mkVarHtmlGp(name)

  def mkVarHtmlGp(self,name):
    ee = {}
    ee['title'] = 'CMIP Variable %s (with multiple definitions)' % name
    self.pageName = 'var__%s.html' % name
    al =[]
    for i in range( len( inx.var.label[name] ) ):
      this = inx.var.uuid[inx.var.label[name][i]]
      al.append( tmpl.item % {'item':'<a href="var__%s__%s.html">[%s]</a>: %s' % (name,i,i,this.title) } )
    ee['items'] = string.join(al, '\n' )
    ee['introduction'] = ''
    ee['htmlBody'] = tmpl.indexWrapper % ee
    ee['htmlHead'] = '''<title>%(title)s</title>''' % ee
    self.pageHtml = tmpl.pageWrapper % ee
    self.write()
    ##print 'Multi var: %s' % name
    for i in range( len( inx.var.label[name] ) ):
      self.mkVarHtml01(inx.var.label[name][i],i)

  def mkVarHtml01(self,id, tag):
    this = inx.var.uuid[id]
    ee = {}
    if this.label == tag:
      ee['title'] = 'CMIP Variable %s' % tag
      self.pageName = 'var__%s.html' % tag
    else:
      ee['title'] = 'CMIP Variable %s[%s]' % (this.label,tag)
      self.pageName = 'var__%s__%s.html' % (this.label,tag)
    atts = this.__dict__.keys()
    atts.sort()
    al =[]
    for a in atts:
      if a not in ['defaults','globalDefault']:
        al.append( tmpl.item % {'item':'<b>%s</b>: %s' % (a,this.__dict__.get(a,'-- Not Set --')) } )

    if inx.iref_by_uuid.has_key(this.uuid):
      assert varRefs.has_key(this.uuid), 'Problem with collected references'
      ee1 = varRefs[this.uuid]
      ks = ee1.keys()
      ks.sort()
      for k in ks:
        al.append( tmpl.item % {'item':'<b>%s</b>: %s' % (k,string.join(ee1[k])) } )
    ee['items'] = string.join(al, '\n' )
    ee['introduction'] = ''
    ee['htmlBody'] = tmpl.indexWrapper % ee
    ee['htmlHead'] = '''<title>%(title)s</title>''' % ee
    self.pageHtml = tmpl.pageWrapper % ee
    self.write()

  def varHtml(self):
    for k in inx.var.label.keys():
      self.mkVarHtml(k)
  
  def rqlHtml(self):
    for k in rql_by_name.keys():
      self.mkRqlHtml(k)
  
  def write(self):
    oo = open( '%s/%s' % (self.odir,self.pageName), 'w' )
    oo.write( self.pageHtml )
    oo.close()

    
vh = rqHtml()
vh.varHtml()
vh.rqlHtml()

if nerr == 0:
  print 'CHECK 001: %s records checked, no missing references' % nok

##for k in xr_var_ovar.keys():
  ##if len( xr_var_ovar[k] ) > 1:
     ##print inx.var.uuid[k].label, map( lambda x: ix_ovar_uuid[x].mipTable,  xr_var_ovar[k]  )

shps = {'': 64, 'XYZKT': 13, '4-element vector': 2, 'XYT': 476, '2D vector field ': 2, 'KZT': 4, '2D vector field': 2, 'XYZ': 27, 'XYZT': 204, '2D': 83, 'scalar': 14, 'XY': 88, '?': 21, '2D ': 1, 'XYKT': 3, 'YZT': 16, 'ZST1': 15, 'XKT': 2, 'BasinYT': 1}
vshpchkMap = {'':'', u'all model levels above 400hPa':'alevStrat', u'all':'Xlev', 3.0:'plev3', '4.0':'plev4', \
            36.0:'plev36', u'soil levels':'sdepth', \
            1.0:'sfc?', \
           16.0:'plev16', 7.0:'plev7', 40.0:'plev40', u'all*':'Xlev', 14.0:'plev14', u'Model levels or 27Plevs':'alev|plev27', \
           27.0:'plev27', 17.0:'plev17', u'17 (or23)':'plev17|plev23', 8.0:'plev8', u'all model levels':'alev', 5.0:'plev5'}
ks = vshpchkMap.keys()
for k in ks:
  if type(k) == type(0.):
     vshpchkMap[str(k)] = vshpchkMap[k]

print vshpchkMap.keys()

tsmap = { 'mean':[u'daily mean', u'time mean', u'time: day',
                u'Cumulative annual fraction', u'Time mean', u'weighted time mean', u'time: mean', u'mean', u'Mean'],
          '__unknown__':[''],
          'point':[ u'Instantaneous (end of year)', u'point', u'Synoptic', u'instantaneous', u'time: point', u'synoptic'] }
tsmap2 = {}
for k in tsmap.keys():
  for i in tsmap[k]:
    tsmap2[i] = k

ee = collections.defaultdict( int )
for i in dq.coll['groupItem'].items:
  tst = tsmap2[ i.tstyle ]
  dd = ''
  if 'X' in i.shape:
    dd += 'latitude '
  if 'Y' in i.shape:
    dd += 'longitude '
  if 'Z' in i.shape:
    if i.levels == '':
      print 'ERROR.001.0001: no levels specified', i.label, i.title
    else:
      zdim = vshpchkMap[i.levels]
      dd +=  zdim 
  ## print '%s::%s::%s|%s' % (i.shape, i.levels, i.tstyle, dd)

class tcmp(object):
  def __init__(self):
    pass
  def cmp(self,x,y):
    return cmp(x.title,y.title)

def atRepr(l,x):
  v = l.__dict__[x]
  if v == '__unset__':
    return ''
  else:
    return v
  
def dumpcsv( fn, key, atl ):
  oo = open(fn, 'w' )
  ll = dq.coll[key].items[:]
  ll.sort( tcmp().cmp )
  oo.write( string.join( atl, '\t' ) + '\n' )
  for l in ll:
    oo.write( string.join( map( lambda x: atRepr(l,x), atl), '\t' ) + '\n' )
  oo.close()

def atlSort( ll ):
  oo = []
  l1 = ['label','title']
  l2 = ['uuid','defaults','globalDefault']
  for i in l1:
    if i in ll:
      oo.append(i)
  ll.sort()
  for i in ll:
    if i not in l1 + l2:
      oo.append(i)
  if 'uuid' in ll:
    oo.append( 'uuid' )
  return oo

for k in dq.coll.keys():
  if len( dq.coll[k].items ) > 0:
    expl = dq.coll[k].items[0]
    atl = atlSort( expl.__dict__.keys() )
    print k, atl
    dumpcsv( 'csv2/%s.csv' % k, k, atl )
  
oo = open( 'var1.csv', 'w' )
ks = ['label','title','sn','units','description','prov','procnote','procComment','uuid']
ks2 = [ 'ovar','groupItem','revisedTabItem']
oo.write( string.join(ks + ks2, '\t' ) + '\n' )
for i in dq.coll['var'].items:
   if i.label[-2:] != '--':
     ee1 = varRefs.get( i.uuid, {} )
     r2 = map( lambda x: string.join( ee1.get(x, [] ) ), ks2 )
     oo.write( string.join(map( lambda x: i.__dict__[x], ks) + r2, '\t' ) + '\n' )
oo.close()

class annotate(object):
  def __init__(self,src,dreq):
    assert os.path.isfile( src), '%s not found' % src 
    self.doc = xml.dom.minidom.parse( src  )
    self.dreq = dreq

  def missingRefs(self,mrefs,clear=True):
    this = self.doc.getElementsByTagName('remarks')[0]
    if clear:
      dil = this.getElementsByTagName('item')
      for d in dil:
        this.removeChild(d)
    for k in mrefs.keys():
      if len(  mrefs[k] ) == 1:
        tid = mrefs[k][0][2]
        tattr = mrefs[k][0][1]
        tn = None
      else:
        tid = None
        ee = collections.defaultdict(int)
        tn = str( len( mrefs[k] ) )
        for t in mrefs[k]:
          s = self.dreq.inx.uuid[t[2]][0]
          ee['%s.%s' % (s,t[1])] += 1
        if len( ee.keys() ) == 1:
          tattr = ee.keys()[0]
        else:
          tattr = '__multiple__'
      item = self.doc.createElement( 'item' )
      item.setAttribute( 'uuid', k )  
      item.setAttribute( 'tattr', tattr )  
      if tn != None:
        item.setAttribute( 'techNote', tn )  
      if tid != None:
        item.setAttribute( 'tid', tid )  
      item.setAttribute( 'class', 'missingLink' )  
      item.setAttribute( 'description', 'Missing links detected and marked for fixing' )  
      item.setAttribute( 'prov', 'scanDreq.py:annotate' )  
      this.appendChild( item )
  
    txt = self.doc.toprettyxml(indent='\t', newl='\n', encoding=None)
    oo = open( 'annotated_20150731.xml', 'w' )
    lines = string.split( txt, '\n' )
    for line in lines:
      l = uniCleanFunc( string.strip(line) )
      if empty.match(l):
        continue
      else:
        oo.write(l + '\n')
    oo.close()

doAnno = True
if doAnno:
  an = annotate( dq.c.vsamp, dq )
  an.missingRefs( dq.inx.missingIds )
