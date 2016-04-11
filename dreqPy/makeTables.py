
import dreq
import collections, string, os
import vrev
try:
    import xlsxwriter
except:
    print ('No xlsxwrite: will not make tables ...')

class xlsx(object):
  def __init__(self,fn):
    self.wb = xlsxwriter.Workbook(fn)

  def newSheet(self,name):
    self.worksheet = self.wb.add_worksheet(name=name)
    return self.worksheet

  def close(self):
    self.wb.close()

def vfmt( x ):
            if x < 1.e9:
              s = '%sM' % int( x*1.e-6 )
            elif x < 1.e12:
              s = '%sG' % int( x*1.e-9 )
            elif x < 1.e13:
              s = '%3.1fT' % ( x*1.e-12 )
            elif x < 1.e15:
              s = '%3iT' % int( x*1.e-12 )
            elif x < 1.e18:
              s = '%3iP' % int( x*1.e-15 )
            else:
              s = '{:,.2f}'.format( x*1.e-9 )
            return s

#priority	long name	units 	comment 	questions & notes	output variable name 	standard name	unconfirmed or proposed standard name	unformatted units	cell_methods	valid min	valid max	mean absolute min	mean absolute max	positive	type	CMOR dimensions	CMOR variable name	realm	frequency	cell_measures	flag_values	flag_meanings

strkeys = [u'procNote', u'uid', u'odims', u'flag_meanings', u'prov', u'title', u'tmid', u'label', u'cell_methods', u'coords', u'cell_measures', u'spid', u'flag_values', u'description']

ntstr = collections.namedtuple( 'ntstr', strkeys )

class cmpd(object):
  def __init__(self,k):
    self.k = k
  def cmp(self,x,y):
    return cmp( x.__dict__[self.k], y.__dict__[self.k] )

class cmpd2(object):
  def __init__(self,k1,k2):
    self.k1 = k1
    self.k2 = k2
  def cmp(self,x,y):
    if x.__dict__[self.k1] == y.__dict__[self.k1]:
      return cmp( x.__dict__[self.k2], y.__dict__[self.k2] )
    else:
      return cmp( x.__dict__[self.k1], y.__dict__[self.k1] )

class cmpdn(object):
  def __init__(self,kl):
    self.kl = kl
  def cmp(self,x,y):
    for k in self.kl:
      if x.__dict__[k] != y.__dict__[k]:
        return cmp( x.__dict__[k], y.__dict__[k] )
    
    return cmp( 0,0 )

def cmpAnnex( x, y ):
  ax = len(x) > 2 and x[:2] == 'em'
  ay = len(y) > 2 and y[:2] == 'em'
  bx = len(x) > 5 and x[:5] in ['CMIP5','CORDE','SPECS']
  by = len(y) > 5 and y[:5] in ['CMIP5','CORDE','SPECS']
  if ax  == ay and bx == by:
    return cmp(x,y)
  elif ax:
    if by:
      return cmp(0,1)
    else:
      return cmp(1,0)
  elif ay:
    if bx:
      return cmp(1,0)
    else:
      return cmp(0,1)
  elif bx:
      return cmp(1,0)
  else:
    return cmp(0,1)

import re


class makePurl(object):
  def __init__(self):
    c1 = re.compile( '^[a-zA-Z][a-zA-Z0-9]*$' )
    mv = dq.coll['var'].items
    oo = open( 'htmlRewrite.txt', 'w' )
    for v in mv:
      if c1.match( v.label ):
         oo.write( 'RewriteRule ^%s$ http://clipc-services.ceda.ac.uk/dreq/u/%s.html\n' % (v.label,v.uid) )
      else:
         print ('Match failed: %s' % v.label )
    oo.close()
      
class makeTab(object):
  def __init__(self, dq, subset=None, dest='tables/test.xlsx', skipped=set(), collected=None):
    if subset != None:
      cmv = [x for x in dq.coll['CMORvar'].items if x.uid in subset]
    else:
      cmv = dq.coll['CMORvar'].items
    tables = sorted( list( set( [i.mipTable for i in cmv] ) ), cmp=cmpAnnex )

    addMips = True
    if addMips:
      c = vrev.checkVar(dq)

    wb = xlsx( dest )

    hdr_cell_format = wb.wb.add_format({'text_wrap': True, 'font_size': 14, 'font_color':'#0000ff', 'bold':1, 'fg_color':'#aaaacc'})
    hdr_cell_format.set_text_wrap()
    sect_cell_format = wb.wb.add_format({'text_wrap': True, 'font_size': 14, 'font_color':'#0000ff', 'bold':1, 'fg_color':'#ccccbb'})
    sect_cell_format.set_text_wrap()
    cell_format = wb.wb.add_format({'text_wrap': True, 'font_size': 11})
    cell_format.set_text_wrap()

    mode = 'c'
    sht = wb.newSheet( 'Notes' )
    tableNotes = [('MIPs (...)','The last two columns in each row list MIPs associated with each variable. The first column in this pair lists the MIPs which are requesting the variable in one or more experiments. The second column lists the MIPs proposing experiments in which this variable is requested. E.g. If a variable is requested in a DECK experiment by HighResMIP, then HighResMIP appears in the first column and DECK in the second')]
    sht.write( 0,0, '', hdr_cell_format )
    sht.write( 0,1, 'Notes on tables', hdr_cell_format )
    ri = 0
    sht.set_column(0,0,30)
    sht.set_column(1,1,60)
    for t in tableNotes:
      ri += 1
      for i in range(2):
          sht.write( ri,i, t[i], cell_format )

    if collected != None:
      ri += 2
      sht.write( ri, 0, 'Table', sect_cell_format )
      sht.write( ri, 1, 'Reference Volume (1 deg. atmosphere, 0.5 deg. ocean)', sect_cell_format )
      for k in sorted( collected.keys() ):
        ri += 1
        sht.write( ri, 0, k )
        sht.write( ri, 1, vfmt( collected[k]*2. ) )

    ncga = 'NetCDF Global Attribute'
    withoo = False
    for t in tables:
      if withoo:
        oo = open( 'tables/test_%s.csv' % t, 'w' )
      sht = wb.newSheet( t )
      j = 0
      if mode == 'c':
        hrec = ['Priority','Long name', 'units', 'description', 'comment', 'Variable Name', 'CF Standard Name', 'cell_methods', 'positive', 'type', 'dimensions', 'CMOR Name', 'modeling_realm', 'frequency', 'cell_measures', 'prov', 'provNote','rowIndex']
        hcmt = ['Default priority (generally overridden by settings in "requestVar" record)',ncga,'','','Name of variable in file','','','CMOR directive','','','CMOR name, unique within table','','','','','','','','','']
        sht.set_column(1,1,40)
        sht.set_column(1,3,50)
        sht.set_column(1,4,30)
        sht.set_column(1,5,50)
        sht.set_column(1,6,30)
        sht.set_column(1,9,40)
        sht.set_column(1,18,40)
        sht.set_column(1,19,40)
      else:
        hrec = ['','Long name', 'units', 'description', '', 'Variable Name', 'CF Standard Name', '','', 'cell_methods', 'valid_min', 'valid_max', 'ok_min_mean_abs', 'ok_max_mean_abs', 'positive', 'type', 'dimensions', 'CMOR name', 'modeling_realm', 'frequency', 'cell_measures', 'flag_values', 'flag_meanings', 'prov', 'provNote','rowIndex']
      if addMips:
        hrec.append( 'MIPs (requesting)' )
        hrec.append( 'MIPs (by experiment)' )

      ##sht.set_row(0,40)
      for i in range(len(hrec)):
          sht.write( j,i, hrec[i], hdr_cell_format )
          if hcmt[i] != '':
            sht.write_comment( j,i,hcmt[i])
      thiscmv =  sorted( [v for v in cmv if v.mipTable == t], cmp=cmpdn(['prov','rowIndex','label']).cmp )
      ##print 'INFO.001: Table %s, rows: %s' % (t,len(thiscmv) )
      
      for v in thiscmv:
          cv = dq.inx.uid[ v.vid ]
          strc = dq.inx.uid[ v.stid ]
          if strc._h.label == 'remarks':
            print ( 'ERROR: structure not found for %s: %s .. %s (%s)' % (v.uid,v.label,v.title,v.mipTable) )
            ok = False
          else:
            sshp = dq.inx.uid[ strc.spid ]
            tshp = dq.inx.uid[ strc.tmid ]
            ok = all( [i._h.label != 'remarks' for i in [cv,strc,sshp,tshp]] )
          #[u'shuffle', u'ok_max_mean_abs', u'vid', '_contentInitialised', u'valid_min', u'frequency', u'uid', u'title', u'rowIndex', u'positive', u'stid', u'mipTable', u'label', u'type', u'description', u'deflate_level', u'deflate', u'provNote', u'ok_min_mean_abs', u'modeling_realm', u'prov', u'valid_max']

          if not ok:
            if (t,v.label) not in skipped:
              print ( 'makeTables: skipping %s %s' % (t,v.label) )
              skipped.add( (t,v.label) )
          else:
            dims = []
            dims += string.split( sshp.dimensions, '|' )
            dims += string.split( tshp.dimensions, '|' )
            dims += string.split( strc.odims, '|' )
            dims += string.split( strc.coords, '|' )
            dims = string.join( dims )
            if mode == 'c':
              orec = [str(v.defaultPriority),cv.title, cv.units, cv.description, v.description, cv.label, cv.sn, strc.cell_methods, v.positive, v.type, dims, v.label, v.modeling_realm, v.frequency, strc.cell_measures, v.prov,v.provNote,str(v.rowIndex),cv.uid]
            else:
              orec = ['',cv.title, cv.units, v.description, '', cv.label, cv.sn, '','', strc.cell_methods, v.valid_min, v.valid_max, v.ok_min_mean_abs, v.ok_max_mean_abs, v.positive, v.type, dims, v.label, v.modeling_realm, v.frequency, strc.cell_measures, strc.flag_values, strc.flag_meanings,v.prov,v.provNote,str(v.rowIndex),cv.uid]
            if addMips:
              thismips = c.chkCmv( v.uid )
              thismips2 = c.chkCmv( v.uid, byExpt=True )
              orec.append( string.join( sorted( list( thismips) ),',') )
              orec.append( string.join( sorted( list( thismips2) ),',') )

            if withoo:
              oo.write( string.join(orec, '\t' ) + '\n' )
            j+=1
            for i in range(len(orec)):
              sht.write( j,i, orec[i], cell_format )
      if withoo:
        oo.close()
    wb.close()

hdr = """
var getData  = {
cols: function() {
  var columns = [ {id:0, name:'Variable', field:0, width: 100},
              {id:1, name:'Standard name', field:1, width: 210 },
              {id:2, name:'Long name', field:2, width: 180},
              {id:3, name:'Units', field:3, width: 180},
              {id:4, name:'Description', field:4, width: 180},
              {id:5, name:'uid', field:5, width: 180}];
              #{id:4, name:'uid', field:4, width: 180}];
 return columns;
},
data: function() {
var data = [];
"""
ftr = """return data;
}
};
"""
##rtmpl = 'data[%(n)s] = { "id":%(n)s, 0:"%(var)s",  1:"%(sn)s", 2:"%(ln)s", 3:"%(u)s", 4:"%(uid)s" };'
rtmpl = 'data[%(n)s] = { "id":%(n)s, 0:"%(var)s",  1:"%(sn)s", 2:"%(ln)s", 3:"%(u)s", 4:"%(d)s", 5:"%(uid)s" };'

class htmlTrees(object):
  def __init__(self,dq,odir='html/t/'):
    self.dq = dq
    self.odir = odir
    self.c = vrev.checkVar( dq )
    self.anno = {}
    for v in dq.coll['var'].items:
      self.makeTree( v )
    
  def makeTree( self, v ):
    ee = self.c.chk2( v.label )
    if len(ee.keys()) > 0:
      title = 'Usage tree for %s' % v.label
      bdy = ['<h1>%s</h1>' % title, ]
      bdy.append( '<html><head></head><body>\n' )
      bdy.append( '<ul>\n' )
      for k in sorted( ee.keys() ):
        l1, xx = ee[k]
        lx = list( xx )
        if len( lx ) == 0:
          bdy.append( '<li>%s: Empty</li>\n' % l1 )
        else:
          bdy.append( '<li>%s:\n<ul>' % l1 )
          for x in lx:
            bdy.append( '<li>%s</li>\n' % x )
          bdy.append( '</ul></li>\n' )
      bdy.append( '</ul></body></html>\n' )
      oo = open( '%s/%s.html' % (self.odir,v.label), 'w' )
      oo.write( dq.pageTmpl % ( title, '', '../', '../index.html', string.join( bdy, '\n' ) ) )
      oo.close()
      self.anno[v.label] = '<a href="../t/%s.html">Usage</a>' % v.label
    else:
      self.anno[v.label] = 'Unused'
        

class makeJs(object):
  def __init__(self,dq):
    n = 0
    rl = []
    for v in dq.coll['var'].items:
      var = '%s %s' % (v.label,v.uid)
      sn = v.sn
      ln = v.title
      u = v.units
      d = v.description
      uid = v.uid
      d = locals()
      for k in ['sn','ln','u','var','d']:
    
        if string.find( d[k], '"' ) != -1:
          print ( "WARNING ... quote in %s .. %s [%s]" % (k,var,d[k]) )
          d[k] = string.replace( d[k], '"', "'" )
          print ( d[k] )
        
      rr = rtmpl % d
      rl.append( rr )
      n += 1
    oo = open( 'data3.js', 'w' )
    oo.write( hdr )
    for r in rl:
      oo.write( r + '\n' )
    oo.write( ftr )
    oo.close()
    


class styles(object):
  def __init__(self):
    pass

  def rqvLink01(self,targ,frm='',ann=''):
    if targ._h.label == 'remarks':
      return '<li>%s: %s</li>' % ( targ.__href__(odir='../u/', label=targ.title), "Link to request variable broken"  )
    elif frm != "CMORvar":
      cmv = targ._inx.uid[ targ.vid ]
      if targ._h.label == 'remarks':
        return '<li>%s [%s]: %s</li>' % ( cmv.label, targ.__href__(odir='../u/',label=targ.priority) , 'Variable not defined or not found'  )
      else:
        return '<li>%s [%s]: %s</li>' % ( cmv.label, targ.__href__(odir='../u/',label=targ.priority) , cmv.__href__(odir='../u/',label=cmv.title)  )
    else:
      rg = targ._inx.uid[ targ.vgid ]
      if targ._h.label == 'remarks':
        return '<li>%s [%s]: %s</li>' % ( targ.label, targ.__href__(label=targ.priority) , 'Link not defined or not found'  )
      elif rg._h.label == 'remarks':
        return '<li>%s [%s]: %s</li>' % ( rg.label, targ.__href__(label=targ.priority) , 'Group not defined or not found'  )
      else:
        return '<li>%s [%s]: %s</li>' % ( rg.label, targ.__href__(label=targ.priority) , rg.__href__(label=rg.mip)  )

  def snLink01(self,a,targ,frm='',ann=''):
    if targ._h.label == 'remarks':
      return '<li>%s: Standard name under review [%s]</li>' % ( a, targ.__href__() )
    else:
      return '<li>%s [%s]: %s</li>' % ( targ._h.title, a, targ.__href__(label=targ.label)  )

  def rqlLink02(self,targ,frm='',ann=''):
    t2 = targ._inx.uid[targ.refid]
    if t2._h.label == 'remarks':
      return '<li>%s: %s</li>' % ( targ.__href__(odir='../u/', label=targ.title), "Link to variable group broken"  )
    elif frm == "requestVarGroup":
      return '<li>%s: %s [%s]</li>' % ( targ.__href__(odir='../u/', label=targ.mip), targ.title, targ.objective  )
    else:
      gpsz = len(t2._inx.iref_by_sect[t2.uid].a['requestVar'])
      return '<li>%s: Link to group: %s [%s]</li>' % ( targ.__href__(odir='../u/', label='%s:%s' % (targ.mip,targ.title)), t2.__href__(odir='../u/', label=t2.title), gpsz  )

  def rqiLink02(self,targ,frm='',ann=''):
    t2 = targ._inx.uid[targ.rlid]
    if t2._h.label == 'remarks':
      return '<li>%s: %s</li>' % ( targ.__href__(odir='../u/', label=targ.title), "Link to request link broken"  )
    else:
      t3 = t2._inx.uid[t2.refid]
      if t3._h.label == 'remarks':
        return '<li>%s [%s]: %s</li>' % ( targ.__href__(odir='../u/', label=targ.title), t2.__href__(odir='../u/', label=t2.title),"Link to request group broken"  )
      else:
        nv = len( t3._inx.iref_by_sect[t3.uid].a['requestVar'] )
        return '<li>%s [%s]: %s (%s variables)</li>' % ( targ.__href__(odir='../u/', label=targ.title), t2.__href__(odir='../u/', label=t2.title), t3.__href__(odir='../u/', label=t3.title), nv )

  def snLink(self,targ,frm='',ann=''):
    return '<li>%s [%s]: %s</li>' % ( targ.title, targ.units, targ.__href__(odir='../u/') )

  def varLink(self,targ,frm='',ann=''):
    return '<li>%s: %s [%s]%s</li>' % (  targ.__href__(odir='../u/', label=targ.label), targ.title, targ.units, ann )

  def mipLink(self,targ,frm='',ann=''):
    if targ.url != '':
      return '<li>%s: %s <a href="%s">[project site]</a></li>' % (  targ.__href__(odir='../u/', label=targ.label), targ.title, targ.url )
    else:
      return '<li>%s: %s</li>' % (  targ.__href__(odir='../u/', label=targ.label), targ.title )

  def cmvLink(self,targ,frm='',ann=''):
    t2 = targ._inx.uid[targ.stid]
    return '<li>%s {%s}: %s [%s: %s]</li>' % (  targ.__href__(odir='../u/', label=targ.label), targ.mipTable, targ.title, targ.frequency, t2.title )

  def objLink(self,targ,frm='',ann=''):
    return '<li>%s: %s</li>' % (  targ.label, targ.__href__(odir='../u/', label=targ.title,title=targ.description) )

  def strLink(self,targ,frm='',ann=''):
    return '<li>%s: %s</li>' % (  targ.label, targ.__href__(odir='../u/', label=targ.title) )

  def objLnkLink(self,targ,frm='',ann=''):
    if frm == 'objective':
      t2 = targ._inx.uid[targ.rid]
      t3 = targ._inx.uid[t2.refid]
      thislab = '%s (%s)' % (t2.mip,t3.label)
      return '<li>%s: %s</li>' % (  t2.title, t2.__href__(odir='../u/',label=thislab) )
    else:
      t2 = targ._inx.uid[targ.oid]
      return '<li>%s: %s</li>' % (  t2.label, t2.__href__(odir='../u/',label=t2.title) )

  def labTtl(self,targ,frm='',ann=''):
    return '<li>%s: %s</li>' % (  targ.__href__(odir='../u/', label=targ.label), targ.title )

  def vgrpLink(self,targ,frm='',ann=''):
    gpsz = len(targ._inx.iref_by_sect[targ.uid].a['requestVar'])
    nlnk = len(targ._inx.iref_by_sect[targ.uid].a['requestLink'])
    return '<li>%s {%s}: %s variables, %s request links</li>' % (  targ.__href__(odir='../u/', label=targ.label), targ.mip, gpsz, nlnk )

class tables(object):
  def __init__(self,sc, mips, odir='xls'):
      self.sc = sc
      self.dq = sc.dq
      self.mips = mips
      self.odir = odir

  def setMlab( self, m ):
      if type(m) == type(''):
        mlab = m
      else:
        ll = sorted( list(m) )
        if len(ll) == 1:
          mlab = list(m)[0]
        else:
          mlab=string.join( [ x[:2].lower() for x in m ], '.' )
      return mlab

  def doTable(self,m,l1,m2,pmax,collector,acc=True, mlab=None):
      """*acc* allows accumulation of values to be switched off when called in single expt mode"""

      if mlab == None:
        mlab = self.setMlab( m )
        

      x = self.sc.volByExpt( l1, m2, expFullEx=(m2 in self.mips), pmax=pmax )
      if x[0] > 0:
        if m2 != None:
          im2 = self.dq.inx.uid[m2]
          mlab2 = im2.label
        else:
          mlab2 = 'all'
        collector[mlab].a[mlab2] += x[0]
#
# create sum for each table
#
        xs = 0
        kkc = '_%s_%s' % (mlab,mlab2)
        for k in x[2].keys():
          i = self.dq.inx.uid[k]
          xxx =  x[2][k]
          xs += xxx
          if xxx > 0:
            collector[kkc].a[i.mipTable] += xxx
        assert x[0] == xs, 'ERROR.0088: consistency problem %s  %s %s %s' % (m,m2,x[0],xs)
        if x[0] == 0:
          print ( 'Zero size: %s, %s' % (m,m2) )
          if len( x[2].keys() ) > 0:
             print ( 'ERROR:zero: %s, %s: %s' % (m,m2,str(x[2].keys()) ) )

        if acc:
          collector[mlab].a['TOTAL'] += x[0]

        dd = collections.defaultdict( list )
        lll = set()
        for v in x[2].keys():
          vi = self.sc.dq.inx.uid[v]
          if vi._h.label != 'remarks':
            f,t,l,tt,d,u = (vi.frequency,vi.mipTable,vi.label,vi.title,vi.description,vi.uid)
            lll.add(u)
            dd[t].append( (f,t,l,tt,d,u) )
        if len( dd.keys() ) > 0:
          collector[mlab].dd[mlab2] = dd
          if m2 != None:
            if im2._h.label == 'experiment':
              dothis = self.sc.tierMax >= im2.tier
###
### BUT ... there is a treset in the request item .... it may be that some variables are excluded ...
###         need the variable list itself .....
###
          makeTab( self.sc.dq, subset=lll, dest='%s/%s-%s_%s_%s.xlsx' % (self.odir,mlab,mlab2,self.sc.tierMax,pmax), collected=collector[kkc].a )

styls = styles()

htmlStyle = {}
htmlStyle['CMORvar'] = {'getIrefs':['requestVar']}
htmlStyle['requestVarGroup'] = {'getIrefs':['requestVar','requestLink']}
htmlStyle['var'] = {'getIrefs':['CMORvar']}
htmlStyle['objective'] = {'getIrefs':['objectiveLink']}
htmlStyle['requestLink'] = {'getIrefs':['objectiveLink','requestItem']}
htmlStyle['exptgroup'] = {'getIrefs':['__all__']}
htmlStyle['requestItem'] = {'getIrefs':['__all__']}
htmlStyle['experiment'] = {'getIrefs':['__all__']}
htmlStyle['mip'] = {'getIrefs':['__all__']}
htmlStyle['remarks'] = {'getIrefs':['__all__']}
htmlStyle['varChoice'] = {'getIrefs':['__all__']}
htmlStyle['spatialShape'] = {'getIrefs':['__all__']}
htmlStyle['temporalShape'] = {'getIrefs':['__all__']}
htmlStyle['structure'] = {'getIrefs':['__all__']}
htmlStyle['standardname'] = {'getIrefs':['__all__']}

if __name__ == "__main__":
  assert os.path.isdir( 'html' ), 'Before running this script you need to create "html", "html/index" and "html/u" sub-directories, or edit the call to dq.makeHtml'
  assert os.path.isdir( 'html/u' ), 'Before running this script you need to create "html", "html/index" and "html/u" sub-directories, or edit the call to dq.makeHtml, and refernces to "u" in style lines below'
  assert os.path.isdir( 'html/index' ), 'Before running this script you need to create "html", "html/index" and "html/u" sub-directories, or edit the call to dq.makeHtml, and refernces to "u" in style lines below'
  assert os.path.isdir( 'tables' ), 'Before running this script you need to create a "tables" sub-directory, or edit the makeTab class'

  dq = dreq.loadDreq( htmlStyles=htmlStyle)
##
## add special styles to dq object "itemStyle" dictionary.
##

  dq.itemStyles['standardname'] = styls.snLink
  dq.itemStyles['var'] = styls.varLink
  dq.itemStyles['mip'] = styls.mipLink
  dq.itemStyles['CMORvar'] = styls.cmvLink
  dq.itemStyles['objective'] = styls.objLink
  dq.itemStyles['structure'] = styls.strLink
  dq.itemStyles['objectiveLink'] = styls.objLnkLink
  dq.itemStyles['requestVarGroup'] = styls.vgrpLink
  dq.itemStyles['requestLink'] = styls.rqlLink02
  dq.itemStyles['requestItem'] = styls.rqiLink02
  dq.itemStyles['spatialShape'] = styls.labTtl
  dq.coll['var'].items[0].__class__._linkAttrStyle['sn'] = styls.snLink01
##dq.coll['requestVarGroup'].items[0].__class__._linkAttrStyle['requestVar'] = styls.rqvLink01
  dq.itemStyles['requestVar'] = styls.rqvLink01

  ht = htmlTrees(dq)
  dq.makeHtml( annotations={'var':ht.anno} )
  try:
    import xlsxwriter
    mt = makeTab( dq)
  except:
    print ('Could not make tables ...')
    raise
  mp = makePurl()
  mj = makeJs( dq )
