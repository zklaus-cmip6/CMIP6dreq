import dreq, collections, string, os
import htmlTemplates as tmpl

from dreq import inx

ix_rql_uuid = {}
ix_rqvg_uuid = {}
ix_ovar_uuid = {}
ix_gpi_uuid = {}
list_gp_ovar = collections.defaultdict( list )
xr_var_ovar = collections.defaultdict( list )
xr_var_gpi = collections.defaultdict( list )
rql_by_name = collections.defaultdict( list )


### check back references.
nbr = 0
lbr = []
for k in inx.iref_by_uuid.keys():
  if not inx.uuid.has_key(k):
   nbr += 1
   lbr.append(k)
print 'Missing references: ', nbr
### can now apply mappings, create updated records and write to new xml?

for i in dreq.c.tableItems['requestLink']:
   rql_by_name[i.label].append( i.uuid )
   ix_rql_uuid[i.uuid] = i

for i in dreq.c.tableItems['requestVarGroup']:
   ix_rqvg_uuid[i.uuid] = i



oo = open( 'uuidinsert.csv', 'w' )
for i in dreq.c.tableItems['revisedTabItem']:
  if i.uuid == '__new__':
    if inx.var_by_name.has_key( i.label ):
      if len( inx.var_by_name[i.label] ) == 1:
        v = inx.uuid[ inx.var_by_name[i.label][0] ][1]
        oo.write( string.join( ['unique',i.label,v.label,v.uuid,v.prov,i.mip], '\t' ) + '\n' )
      else:
        oo.write( string.join( ['ambiguous',i.label,i.mip,str(len(inx.var_by_name[i.label] ) ) ], '\t' ) + '\n' )
oo.close()
    
oo = open( 'varMult.csv', 'w' )
oo2 = open( 'varDup.csv', 'w' )
oo3 = open( 'varStar.csv', 'w' )
hs = ['label','title','sn','units','description','prov','procnote','procComment','uuid']
oo.write( string.join(hs, '\t' ) + '\n' )
oo2.write( string.join(hs, '\t' ) + '\n' )
oo3.write( string.join(hs, '\t' ) + '\n' )
ks = inx.var_by_name.keys()
ks.sort()
for k in ks:
  if len(inx.var_by_name[k]) == 2:
    v1 = inx.var_uuid[inx.var_by_name[k][0]]
    v2 = inx.var_uuid[inx.var_by_name[k][1]]
    cc = map( lambda x: v1.__dict__[x] == v2.__dict__[x], ['title','sn','units','description']  )
    if all(cc):
      oo2.write( string.join(map( lambda x: v1.__dict__[x], hs) + [v2.uuid,'identical'], '\t' ) + '\n' )
    else:
      oo2.write( string.join(map( lambda x: v1.__dict__[x], hs) + ['',''], '\t' ) + '\n' )
    oo2.write( string.join(map( lambda x: v2.__dict__[x], hs) + ['',''], '\t' ) + '\n' )
      
  elif len(inx.var_by_name[k]) > 1:
    for i in inx.var_by_name[k]:
      oo.write( string.join(map( lambda x: inx.var_uuid[i].__dict__[x], hs), '\t' ) + '\n' )

  if k[-2:] == '--':
    for i in (inx.var_by_name[k] + inx.var_by_name[k[:-2]]):
      oo3.write( string.join(map( lambda x: inx.var_uuid[i].__dict__[x], hs), '\t' ) + '\n' )
oo.close()
oo2.close()
oo3.close()


for i in dreq.c.tableItems['groupItem']:
   list_gp_ovar[i.gpid].append( i.uuid )

nok = 0
nerr = 0
for i in dreq.c.tableItems['ovar']:
   vid = i.vid
   ix_ovar_uuid[i.uuid] = i
   xr_var_ovar[vid].append( i.uuid )
   if not inx.var_uuid.has_key(vid):
     print 'missing key:',i.__dict__
     nerr += 1
   else:
     nok += 1

nok = 0
nerr = 0
for i in dreq.c.tableItems['groupItem']:
   vid = i.vid
   ix_gpi_uuid[i.uuid] = i
   xr_var_gpi[vid].append( i.uuid )
   if not inx.var_uuid.has_key(vid):
     nerr += 1
   else:
     nok += 1
print 'groupItem to var crossref: nok = %s, nerr = %s',nok, nerr

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
    if len( inx.var_by_name[name] ) == 1:
      self.mkVarHtml01(inx.var_by_name[name][0], name )
    else:
      self.mkVarHtmlGp(name)

  def mkVarHtmlGp(self,name):
    ee = {}
    ee['title'] = 'CMIP Variable %s (with multiple definitions)' % name
    self.pageName = 'var__%s.html' % name
    al =[]
    for i in range( len( inx.var_by_name[name] ) ):
      this = inx.var_uuid[inx.var_by_name[name][i]]
      al.append( tmpl.item % {'item':'<a href="var__%s__%s.html">[%s]</a>: %s' % (name,i,i,this.title) } )
    ee['items'] = string.join(al, '\n' )
    ee['introduction'] = ''
    ee['htmlBody'] = tmpl.indexWrapper % ee
    ee['htmlHead'] = '''<title>%(title)s</title>''' % ee
    self.pageHtml = tmpl.pageWrapper % ee
    self.write()
    for i in range( len( inx.var_by_name[name] ) ):
      self.mkVarHtml01(inx.var_by_name[name][i],i)

  def mkVarHtml01(self,id, tag):
    this = inx.var_uuid[id]
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
      assert inx.varRefs.has_key(this.uuid), 'Problem with collected references'
      ee1 = inx.varRefs[this.uuid]
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
    for k in inx.var_by_name.keys():
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
     ##print inx.var_uuid[k].label, map( lambda x: ix_ovar_uuid[x].mipTable,  xr_var_ovar[k]  )

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
for i in dreq.c.tableItems['groupItem']:
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

def dumpcsv( fn, key, atl ):
  oo = open(fn, 'w' )
  ll = dreq.c.tableItems[key][:]
  ll.sort( tcmp().cmp )
  oo.write( string.join( atl, '\t' ) + '\n' )
  for l in ll:
    oo.write( string.join( map( lambda x: l.__dict__[x], atl), '\t' ) + '\n' )
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

for k in dreq.c.tableItems.keys():
  expl = dreq.c.tableItems[k][0]
  atl = atlSort( expl.__dict__.keys() )
  dumpcsv( 'csv2/%s.csv' % k, k, atl )
  
oo = open( 'var1.csv', 'w' )
ks = ['label','title','sn','units','description','prov','procnote','procComment','uuid']
ks2 = [ 'ovar','groupItem','revisedTabItem']
oo.write( string.join(ks + ks2, '\t' ) + '\n' )
for i in dreq.c.tableItems['var']:
   if i.label[-2:] != '--':
     ee1 = inx.varRefs.get( i.uuid, {} )
     r2 = map( lambda x: string.join( ee1.get(x, [] ) ), ks2 )
     inx.var_by_sn[i.sn].append( i.uuid )
     oo.write( string.join(map( lambda x: i.__dict__[x], ks) + r2, '\t' ) + '\n' )
oo.close()
