import dreq, collections, string, os, utils_wb
import htmlTemplates as tmpl
import xml, re
import xml.dom, xml.dom.minidom
import sets

from utils_wb import uniCleanFunc

empty=re.compile('^$')

src1 = '../workbook/trial2_20150831.xml'

dq = dreq.loadDreq(dreqXML=src1)
inx = dq.inx
##inx.makeVarRefs()
ix_rql_uid = {}
ix_rqvg_uid = {}
ix_ovar_uid = {}
ix_gpi_uid = {}
list_gp_ovar = collections.defaultdict( list )
xr_var_ovar = collections.defaultdict( list )
xr_var_gpi = collections.defaultdict( list )
rql_by_name = collections.defaultdict( list )

def makeVarRefs(uid, var, iref_by_uid):
    varRefs = {}
    for thisuid in var.uid.keys():
      if iref_by_uid.has_key(thisuid):
        ee1 = collections.defaultdict( list )
        for k,i in iref_by_uid[thisuid]:
          thisi = uid[i]
          sect = thisi._h.label
          if sect == 'groupItem':
            ee1[sect].append( '%s.%s' % (thisi.mip, thisi.group) )
          elif sect == 'ovar':
            ee1[sect].append( thisi.mipTable )
          elif sect == 'revisedTabItem':
            ee1[sect].append( '%s.%s' % (thisi.mip, thisi.table) )
        varRefs[thisuid] = ee1
    return varRefs

varRefs = makeVarRefs( inx.uid, inx.var, inx.iref_by_uid)

class updates(object):
  delToks = sets.Set( ['inc','omit'] )
  def __init__(self,fndup,fnmult,idir='rev1'):
    assert os.path.isdir( idir ), 'Directory %s not found' % idir
    self.fdup = '%s/%s' % (idir,fndup)
    self.fmult = '%s/%s' % (idir,fnmult)
    for p in [self.fdup,self.fmult]:
      assert os.path.isfile( p ), 'File %s not found' % p
    self.repl = {}
    self.upd = {}
    self.twins = []
    self.ddel = {}

  def scandup(self):
    ii = open( self.fdup ).readlines()
    nn = (len(ii)-1)/2
    for i in range(nn):
      l1 = string.split( ii[i*2+1], '\t' )
      l2 = string.split( ii[i*2+2], '\t' )
      xx = l1[8:10]
      yy = l2[8:10]
      if xx[1] == '' and yy[1] == xx[0]:
        ths = 0
        assert not self.repl.has_key( yy[0] ), 'duplicate replacement request for %s' % yy[0]
        self.repl[ yy[0] ] = yy[1] 
      elif yy[1] == '' and xx[1] == yy[0]:
        ths = 1
        assert not self.repl.has_key( xx[0] ), 'duplicate replacement request for %s' % xx[0]
        self.repl[ xx[0] ] = xx[1] 
      elif l1[10] == 'twin' and  l2[10] == 'twin':
        ths = 2
        self.twins.append( l1[8] )
        self.twins.append( l2[8] )
      elif l1[10] in self.delToks and l2[10] in self.delToks:
        ths = 3
        self.ddel[ l1[8] ] = (l1[10],l1[11])
        self.ddel[ l2[8] ] = (l2[10],l2[11])
      elif xx[1] == '' and yy[1] == "":
        print 'WARN.087.00001: uncorrected duplication ..... %s ' %  str( l1[:5] )
      else:
        ths = -1
        print 'ERROR.xxx.0001: Match failed'
        print l1
        print l2
        assert False

  def scanmult(self):
    ii = open( self.fmult ).readlines()
    nn = (len(ii)-1)/3
    for i in range(nn):
      l1 = string.split( ii[i*3+1], '\t' )
      l2 = string.split( ii[i*3+2], '\t' )
      l3 = string.split( ii[i*3+3], '\t' )
      yy = [l1[9],l2[9],l3[9]]
      xx = [l1[8],l2[8],l3[8]]
      zz = (l1,l2,l3)
      for j in range(3):
        if yy[j] != '':
          assert yy[j] in xx, 'Invalid replacement option, %s' % yy[j]
          assert  not self.repl.has_key( xx[j] ), 'duplicate replacement request for %s' % xx[j]
          self.repl[ xx[j] ] = yy[j]
        elif zz[j][10] == 'twin':
          self.twins.append( zz[j][8] )
        elif zz[j][11] == 'update':
          tags = map( string.strip, string.split( zz[j][13], ',' ) )
          self.upd[ xx[j] ] = { 'provNote':zz[j][12], 'tags':tags, 'label':zz[j][0], 'title':zz[j][1] }

###
### varDup and varMult created in first parse ----- then editted to select options
### 2nd pass through then generates the replace and remove options -- taking into account cross references
### the results of the 2nd pass go back to ../workbook to generate a new set of inputs.
###
up = updates('varDup_20150928.csv', 'varMult_20150725.csv')
up.scandup()
up.scanmult()

urep = False
urep = True
if urep:
  oo = open( 'uuidreplace.csv', 'w' )
  oo2 = open( 'uuidremove.csv', 'w' )
  for k in up.repl.keys():
    if inx.iref_by_uid.has_key(k):
      kn = up.repl[k]
      for tag,ki  in inx.iref_by_uid[k]:
         vu = [ inx.uid.has_key(kk) for kk in [k,kn,ki] ]
         if all( vu ):
           oo.write( '%s\t%s\t%s\t%s\t%s\t%s\t%s\n' % (k,kn,tag,ki, inx.uid[k].label,  inx.uid[kn].label, inx.uid[ki].label) )
         else:
           print 'ERROR.088.0001: Bad index in replace info: %s .. %s .. %s' % ( str([k,kn,ki]), str(vu), tag )
    else:
      oo2.write( k + '\n' )
  oo.close()
  oo2.close()
  oo = open( 'uuidupdate.csv', 'w' )
  for k in up.upd.keys():
      ee = up.upd[k]
      oo.write( string.join( [k,ee['provNote'],string.join(ee['tags']),ee['label'], ee['title'] ], '\t') + '\n' )
  oo.close()
else:
  oo2 = open( 'uuidremove2.csv', 'w' )
  for i in dq.coll['var'].items:
    if not inx.iref_by_uid.has_key(i.uid):
      oo2.write( string.join( [i.uid,i.label,i.title,i.prov,i.description], '\t') + '\n' )
  oo2.close()

### check back references.
nbr = 0
lbr = []
for k in inx.iref_by_uid.keys():
  if not inx.uid.has_key(k):
   nbr += 1
   lbr.append(k)
print 'Missing references: ', nbr
### can now apply mappings, create updated records and write to new xml?

for i in dq.coll['requestLink'].items:
   rql_by_name[i.label].append( i.uid )
   ix_rql_uid[i.uid] = i

for i in dq.coll['requestVarGroup'].items:
   ix_rqvg_uid[i.uid] = i


if dq.coll.has_key( 'revisedTabItem' ):
  thisk = 'revisedTabItem'
else:
  thisk = 'requestVar'
oo = open( 'uuidinsert.csv', 'w' )
for i in dq.coll[thisk].items:
  if i.uid == '__new__':
    if inx.var.label.has_key( i.label ):
      if len( inx.var.label[i.label] ) == 1:
        v = inx.uid[ inx.var.label[i.label][0] ]
        oo.write( string.join( ['unique',i.label,v.label,v.uid,v.prov,i.mip], '\t' ) + '\n' )
      else:
        oo.write( string.join( ['ambiguous',i.label,i.mip,str(len(inx.var.label[i.label] ) ) ], '\t' ) + '\n' )
oo.close()
    
oo = open( 'varMult.csv', 'w' )
oo2 = open( 'varDup.csv', 'w' )
oo3 = open( 'varStar.csv', 'w' )
hs = ['label','title','sn','units','description','prov','procnote','procComment','uid']
oo.write( string.join(hs, '\t' ) + '\n' )
oo2.write( string.join(hs, '\t' ) + '\n' )
oo3.write( string.join(hs, '\t' ) + '\n' )
ks = inx.var.label.keys()
ks.sort()
emptySet = sets.Set( ['','unset'] )
def entryEq(a,b):
  return a == b or (a in emptySet and b in emptySet)

deferredRecs = []
for k in ks:
  if len(inx.var.label[k]) == 2:
    v1 = inx.var.uid[inx.var.label[k][0]]
    v2 = inx.var.uid[inx.var.label[k][1]]
    cc = map( lambda x: entryEq( v1.__dict__[x], v2.__dict__[x]), ['title','sn','units','description']  )
    if all(cc):
### where duplicates are identical , collect and output at end of file.
      pv1 = string.find( v1.__dict__['prov'], 'OMIP.' ) != -1
      pv2 = string.find( v2.__dict__['prov'], 'OMIP.' ) != -1
      if pv2:
        vp = v2
        vo = v1
      else:
        if not pv1:
          print 'WARN.088.00002: no preference: %s, %s, %s' % (v1.__dict__['label'],v1.__dict__['prov'],v2.__dict__['prov'])
        vp = v1
        vo = v2
      deferredRecs.append( string.join(map( lambda x: vo.__dict__[x], hs) + [vp.uid,'identical'], '\t' ) + '\n' )
      deferredRecs.append( string.join(map( lambda x: vp.__dict__[x], hs) + ['',''], '\t' ) + '\n' )
    else:
      oo2.write( string.join(map( lambda x: v1.__dict__[x], hs) + ['',''], '\t' ) + '\n' )
      oo2.write( string.join(map( lambda x: v2.__dict__[x], hs) + ['',''], '\t' ) + '\n' )
      
  elif len(inx.var.label[k]) > 1:
    for i in inx.var.label[k]:
      oo.write( string.join(map( lambda x: inx.var.uid[i].__dict__[x], hs), '\t' ) + '\n' )

  if k[-2:] == '--':
    for i in (inx.var.label[k] + inx.var.label[k[:-2]]):
      oo3.write( string.join(map( lambda x: inx.var.uid[i].__dict__[x], hs), '\t' ) + '\n' )

## output auto-filled records for identical duplicates at end of varDup file.
for r in deferredRecs:
  oo2.write( r )
oo.close()
oo2.close()
oo3.close()



vns = inx.var.label.keys()
vns.sort()
for v in vns:
  if len( inx.var.label[v] ) > 1:
     print 'INFO.001.0001:',v, string.join( map( lambda x: inx.var.uid[x].sn, inx.var.label[v] ), ';' )

nok = 0
nerr = 0
if dq.coll.has_key( 'ovar' ):
  thisk = 'ovar'
else:
  thisk = 'CMORvar'
for i in dq.coll[thisk].items:
   vid = i.vid
   ix_ovar_uid[i.uid] = i
   xr_var_ovar[vid].append( i.uid )
   if not inx.var.uid.has_key(vid):
     print 'missing key:',i.label, i.prov
     nerr += 1
   else:
     nok += 1

class rqHtml(object):

  def __init__(self,odir='./html/'):
    self.odir = odir
    if not os.path.isdir(odir):
      os.mkdir(odir)

  def mkRqlHtml(self,name):
     ## [u'comment', u'uid', u'tab', u'title', u'label', u'grid', 'defaults', u'objective', u'mip', 'globalDefault', u'gridreq']
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
      this = ix_rql_uid[rql_by_name[name][i]]
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
    this = ix_rql_uid[id]
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
      this = inx.var.uid[inx.var.label[name][i]]
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
    this = inx.var.uid[id]
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

    if inx.iref_by_uid.has_key(this.uid):
      assert varRefs.has_key(this.uid), 'Problem with collected references'
      ee1 = varRefs[this.uid]
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
     ##print inx.var.uid[k].label, map( lambda x: ix_ovar_uid[x].mipTable,  xr_var_ovar[k]  )

shps = {'': 64, 'XYZKT': 13, '4-element vector': 2, 'XYT': 476, '2D vector field ': 2, 'KZT': 4, '2D vector field': 2, 'XYZ': 27, 'XYZT': 204, '2D': 83, 'scalar': 14, 'XY': 88, '?': 21, '2D ': 1, 'XYKT': 3, 'YZT': 16, 'ZST1': 15, 'XKT': 2, 'BasinYT': 1}
vshpchkMap = {'':'', u'all model levels above 400hPa':'alevStrat', u'all':'Xlev', 3.0:'plev3', '4.0':'plev4', \
            36.0:'plev36', u'soil levels':'sdepth', \
            1.0:'sfc?', \
           16.0:'plev16', 7.0:'plev7', 40.0:'plev40', u'all*':'Xlev', 14.0:'plev14', u'Model levels or 27Plevs':'alev|plev27', \
           u'17 (or 23 )':'plev17|plev23', u'17 (or 23)':'plev17|plev23', \
           27.0:'plev27', 17.0:'plev17', u'17 (or23)':'plev17|plev23', 8.0:'plev8', u'all model levels':'alev', 5.0:'plev5'}
ks = vshpchkMap.keys()
for k in ks:
  if type(k) == type(0.):
     vshpchkMap[str(k)] = vshpchkMap[k]

print vshpchkMap.keys()

tsmap = { 'mean':[u'daily mean', u'time mean', u'time: day',
                u'Cumulative annual fraction', u'Time mean', u'weighted time mean', u'time: mean', u'mean', u'Mean'],
          '__unknown__':['','dummyAt'],
          'point':[ u'Instantaneous (end of year)', u'point', u'Synoptic', u'instantaneous', u'time: point', u'synoptic'] }
tsmap2 = {}
for k in tsmap.keys():
  for i in tsmap[k]:
    tsmap2[i] = k

if dq.coll.has_key( 'groupItem' ):
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
  for i in dq.coll['groupItem'].items:
     list_gp_ovar[i.gpid].append( i.uid )

  nok = 0
  nerr = 0
  for i in dq.coll['groupItem'].items:
     vid = i.vid
     ix_gpi_uid[i.uid] = i
     xr_var_gpi[vid].append( i.uid )
     if not inx.var.uid.has_key(vid):
       nerr += 1
     else:
       nok += 1
  print 'groupItem to var crossref: nok = %s, nerr = %s' % (nok, nerr)


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
    try:
      oo.write( string.join( map( lambda x: str(atRepr(l,x)), atl), '\t' ) + '\n' )
    except:
      print 'SEVERE.090.0001: print %s' % str(atl)
      print l
      raise
  oo.close()

def atlSort( ll ):
  oo = []
  l1 = ['label','title']
  l2 = ['uid','defaults','globalDefault']
  for i in l1:
    if i in ll:
      oo.append(i)
  ll.sort()
  for i in ll:
    if i not in l1 + l2:
      oo.append(i)
  if 'uid' in ll:
    oo.append( 'uid' )
  return oo

for k in dq.coll.keys():
  if len( dq.coll[k].items ) > 0:
    expl = dq.coll[k].items[0]
    atl = atlSort( expl.__dict__.keys() )
    if 'parent' in atl:
      atl.pop( atl.index('parent') )
    dumpcsv( 'csv2/%s.csv' % k, k, atl )
  
oo = open( 'var1.csv', 'w' )
ks = ['label','title','sn','units','description','prov','procnote','procComment','uid']
ks2 = [ 'ovar','groupItem','revisedTabItem']
oo.write( string.join(ks + ks2, '\t' ) + '\n' )
for i in dq.coll['var'].items:
   if i.label[-2:] != '--':
     ee1 = varRefs.get( i.uid, {} )
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
          s = self.dreq.inx.uid[t[2]]._h.label
          ee['%s.%s' % (s,t[1])] += 1
        if len( ee.keys() ) == 1:
          tattr = ee.keys()[0]
        else:
          tattr = '__multiple__'
      item = self.doc.createElement( 'item' )
      item.setAttribute( 'uid', k )  
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
      l = utils_wb.uniCleanFunc( string.strip(line) )
      if empty.match(l):
        continue
      else:
        oo.write(l + '\n')
    oo.close()

doAnno = True
if doAnno:
  an = annotate( dq.c.vsamp, dq )
  an.missingRefs( dq.inx.missingIds )
