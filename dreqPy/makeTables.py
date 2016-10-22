
import collections, os, sys
import volsum

nt__charmeEnable = collections.namedtuple( 'charme', ['id','site'] )

try:
  import dreq
  import vrev
  import misc_utils
  import rvgExtraTable
except:
  import dreqPy.dreq as dreq
  import dreqPy.vrev as vrev
  import dreqPy.misc_utils as misc_utils
  import dreqPy.rvgExtraTable as rvgExtraTable

python2 = True
if sys.version_info[0] == 3:
  python2 = False
  def cmp(x,y):
    if x == y:
      return 0
    elif x > y:
      return 1
    else:
      return -1

if sys.version_info >= (2,7):
  from functools import cmp_to_key
  oldpython = False
else:
  oldpython = True

try:
    import xlsxwriter
except:
    print ('No xlsxwrite: will not make tables ...')

##NT_txtopts = collections.namedtuple( 'txtopts', ['mode'] )

def setMlab( m ):
      if type(m) == type(''):
        if m == '_all_':
          mlab = 'TOTAL'
        else:
          mlab = m
      else:
        ll = sorted( list(m) )
        if len(ll) == 1:
          mlab = list(m)[0]
        else:
          mlab='.'.join( [ x[:2].lower() for x in m ] )
      return mlab

class xlsx(object):
  def __init__(self,fn,xls=True,txt=False,txtOpts=None):
    self.xls=xls
    self.txt=txt
    self.txtOpts = txtOpts
    self.mcfgNote = 'Reference Volume (1 deg. atmosphere, 0.5 deg. ocean)'
    if xls:
      self.wb = xlsxwriter.Workbook('%s.xlsx' % fn)
      self.hdr_cell_format = self.wb.add_format({'text_wrap': True, 'font_size': 14, 'font_color':'#0000ff', 'bold':1, 'fg_color':'#aaaacc'})
      self.hdr_cell_format.set_text_wrap()
      self.sect_cell_format = self.wb.add_format({'text_wrap': True, 'font_size': 14, 'font_color':'#0000ff', 'bold':1, 'fg_color':'#ccccbb'})
      self.sect_cell_format.set_text_wrap()
      self.cell_format = self.wb.add_format({'text_wrap': True, 'font_size': 11})
      self.cell_format.set_text_wrap()

    if txt:
      self.oo = open( '%s.csv' % fn, 'w' )

  def header(self,tableNotes,collected):
    if self.xls:
      sht = self.newSheet( 'Notes' )
      sht.write( 0,0, '', self.hdr_cell_format )
      sht.write( 0,1, 'Notes on tables', self.hdr_cell_format )
      ri = 0
      sht.set_column(0,0,30)
      sht.set_column(1,1,60)
      self.sht = sht
      for t in tableNotes:
        ri += 1
        for i in range(2):
          sht.write( ri,i, t[i], self.cell_format )

      if collected != None:
        ri += 2
        sht.write( ri, 0, 'Table', self.sect_cell_format )
        sht.write( ri, 1, self.mcfgNote, self.sect_cell_format )
        ttl = 0.
        for k in sorted( collected.keys() ):
          ri += 1
          sht.write( ri, 0, k )
          sht.write( ri, 1, vfmt( collected[k]*2. ) )
          ttl += collected[k]

        ri += 1
        sht.write( ri, 0, 'TOTAL' )
        sht.write( ri, 1, vfmt( ttl*2. ) )

    if self.txt:
      self.oo.write( '\t'.join( ['Notes','','Notes on tables']) + '\n' )
      for t in tableNotes:
        self.oo.write( '\t'.join( ['Notes',] + list(t)) + '\n' )

      if collected != None:
        self.oo.write( '\t'.join( ['Notes','Table','Reference Volume (1 deg. atmosphere, 0.5 deg. ocean)']) + '\n')
        for k in sorted( collected.keys() ):
          self.oo.write( '\t'.join( ['Notes',k,vfmt( collected[k]*2. )]) + '\n' )

  def cmvtabrec(self,j,t,orec):
     if self.xls:
        for i in range(len(orec)):
           self.sht.write( j,i, orec[i], self.cell_format )

     if self.txt:
        self.oo.write( '\t'.join( [t,] + orec) + '\n' )

  def varrec(self,j,orec):
     if self.xls:
        for i in range(len(orec)):
           self.sht.write( j,i, orec[i], self.cell_format )

     if self.txt:
        self.oo.write( '\t'.join( orec, '\t') + '\n' )

  def var(self):
      if self.xls:
        self.sht = self.newSheet( 'var' )
      j = 0
      hrec = ['Long name', 'units', 'description', 'Variable Name', 'CF Standard Name' ]
      if self.xls:
          self.sht.set_column(1,1,40)
          self.sht.set_column(1,2,30)
          self.sht.set_column(1,3,60)
          self.sht.set_column(1,4,40)
          self.sht.set_column(1,5,40)

      if self.xls:
        for i in range(len(hrec)):
          self.sht.write( j,i, hrec[i], self.hdr_cell_format )

      if self.txt:
        for i in range(len(hrec)):
          self.oo.write( hrec[i] + '\t' )
        self.oo.write( '\n' )

  def cmvtab(self,t,addMips,mode='c'):
      if self.xls:
        self.sht = self.newSheet( t )
      j = 0
      ncga = 'NetCDF Global Attribute'
      if mode == 'c':
        hrec = ['Priority','Long name', 'units', 'description', 'comment', 'Variable Name', 'CF Standard Name', 'cell_methods', 'positive', 'type', 'dimensions', 'CMOR Name', 'modeling_realm', 'frequency', 'cell_measures', 'prov', 'provNote','rowIndex','UID','vid','stid','Structure Title']
        hcmt = ['Default priority (generally overridden by settings in "requestVar" record)',ncga,'','','Name of variable in file','','','CMOR directive','','','CMOR name, unique within table','','','','','','','','','','CMOR variable identifier','MIP variable identifier','Structure identifier','']
        if self.xls:
          self.sht.set_column(1,1,40)
          self.sht.set_column(1,3,50)
          self.sht.set_column(1,4,30)
          self.sht.set_column(1,5,50)
          self.sht.set_column(1,6,30)
          self.sht.set_column(1,9,40)
          self.sht.set_column(1,18,40)
          self.sht.set_column(1,19,40)
      else:
        hrec = ['','Long name', 'units', 'description', '', 'Variable Name', 'CF Standard Name', '','', 'cell_methods', 'valid_min', 'valid_max', 'ok_min_mean_abs', 'ok_max_mean_abs', 'positive', 'type', 'dimensions', 'CMOR name', 'modeling_realm', 'frequency', 'cell_measures', 'flag_values', 'flag_meanings', 'prov', 'provNote','rowIndex','UID']

      if addMips:
        hrec.append( 'MIPs (requesting)' )
        hrec.append( 'MIPs (by experiment)' )

      if self.xls:
        for i in range(len(hrec)):
          self.sht.write( j,i, hrec[i], self.hdr_cell_format )
          if hcmt[i] != '':
            self.sht.write_comment( j,i,hcmt[i])

      if self.txt:
        self.oo.write( 'MIP table\t' )
        for i in range(len(hrec)):
          self.oo.write( hrec[i] + '\t' )
        self.oo.write( '\n' )
        self.oo.write( t + '\t' )
        for i in range(len(hrec)):
          if hcmt[i] != '':
            self.oo.write( hcmt[i] + '\t')
          else:
            self.oo.write( '\t')
        self.oo.write( '\n' )

  def newSheet(self,name):
    self.worksheet = self.wb.add_worksheet(name=name)
    return self.worksheet

  def close(self):
    if self.xls:
      self.wb.close()
    if self.txt:
      self.oo.close()

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


if not oldpython:
  kAnnex = cmp_to_key( cmpAnnex )

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
  def __init__(self, dq, subset=None, mcfgNote=None, dest='tables/test', skipped=set(), collected=None,xls=True,txt=False,txtOpts=None):
    """txtOpts: gives option to list MIP variables instead of CMOR variables"""
    if subset != None:
      cmv = [x for x in dq.coll['CMORvar'].items if x.uid in subset]
    else:
      cmv = dq.coll['CMORvar'].items

    if oldpython:
      tables = sorted( list( set( [i.mipTable for i in cmv] ) ), cmp=cmpAnnex )
    else:
      tables = sorted( list( set( [i.mipTable for i in cmv] ) ), key=kAnnex )

    addMips = True
    if addMips:
      c = vrev.checkVar(dq)
    mode = 'c'
    tableNotes = [
       ('Request Version',str(dq.version)),
       ('MIPs (...)','The last two columns in each row list MIPs associated with each variable. The first column in this pair lists the MIPs which are requesting the variable in one or more experiments. The second column lists the MIPs proposing experiments in which this variable is requested. E.g. If a variable is requested in a DECK experiment by HighResMIP, then HighResMIP appears in the first column and DECK in the second')]

    wb = xlsx( dest, xls=xls, txt=txt )
    if mcfgNote != None:
      wb.mcfgNote = mcfgNote
    wb.header( tableNotes, collected)

    if txtOpts != None and txtOpts.mode == 'var':
      vl =  list( set( [v.vid for v in cmv] )  )
      vli = [dq.inx.uid[i] for i in vl]
      thisvli =  sorted( vli, cmp=cmpdn(['sn','label']).cmp )
      wb.var()
      
      j = 0
      for v in thisvli:
      ###hrec = ['Long name', 'units', 'description', 'Variable Name', 'CF Standard Name' ]
         orec = [v.title, v.units, v.description, v.label, v.sn]
         j += 1
         wb.varrec( j,orec )
    else:
      withoo = False
      for t in tables:
        if withoo:
          oo = open( 'tables/test_%s.csv' % t, 'w' )
        wb.cmvtab(t,addMips,mode='c')

        j = 0
        thiscmv =  sorted( [v for v in cmv if v.mipTable == t], cmp=cmpdn(['prov','rowIndex','label']).cmp )

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
              ml = []
              for i in range(4):
                 ii = [cv,strc,sshp,tshp][i]
                 if ii._h.label == 'remarks':
                   ml.append( ['var','struct','time','spatial'][i] )
              print ( 'makeTables: skipping %s %s: %s' % (t,v.label,','.join( ml)) )
              skipped.add( (t,v.label) )
          else:
            dims = []
            dims +=  sshp.dimensions.split( '|' )
            dims +=  tshp.dimensions.split( '|' )
            dims +=  strc.odims.split( '|' )
            dims +=  strc.coords.split( '|' )
            dims = ' '.join( dims )
            if mode == 'c':
              orec = [str(v.defaultPriority),cv.title, cv.units, cv.description, v.description, cv.label, cv.sn, strc.cell_methods, v.positive, v.type, dims, v.label, v.modeling_realm, v.frequency, strc.cell_measures, v.prov,v.provNote,str(v.rowIndex),v.uid,v.vid,v.stid,strc.title]
            else:
              orec = ['',cv.title, cv.units, v.description, '', cv.label, cv.sn, '','', strc.cell_methods, v.valid_min, v.valid_max, v.ok_min_mean_abs, v.ok_max_mean_abs, v.positive, v.type, dims, v.label, v.modeling_realm, v.frequency, strc.cell_measures, strc.flag_values, strc.flag_meanings,v.prov,v.provNote,str(v.rowIndex),cv.uid]
            if addMips:
              thismips = c.chkCmv( v.uid )
              thismips2 = c.chkCmv( v.uid, byExpt=True )
              orec.append( ','.join( sorted( list( thismips) ) ) )
              orec.append( ','.join( sorted( list( thismips2) ) ) )

            if withoo:
              oo.write( '\t'.join(orec ) + '\n' )
            j+=1
            wb.cmvtabrec( j,t,orec )

        if withoo:
          oo.close()
    wb.close()

hdr = """
function f000(value) { return (value + "").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;") };

function formatter00(row, cell, value, columnDef, dataContext) {
        var vv = value.split(" ");
        return '<b><a href="u/' + vv[1] + '.html">' + (vv[0] + " ").replace(/&/g,"&amp;") + '</a></b>, ';
    };
function formatter01(row, cell, value, columnDef, dataContext) { return '<i>' + f000(value) + '</i> ' };
function formatter02(row, cell, value, columnDef, dataContext) { return '[' + f000(value) + '] ' };
function formatter03(row, cell, value, columnDef, dataContext) { if (value != "'unset'"  ) { return '(' + f000(value) + ') ' } else {return ''} };
function formatter04(row, cell, value, columnDef, dataContext) { return '{' + f000(value) + '} ' };
function formatter05(row, cell, value, columnDef, dataContext) { return '&lt;' + f000(value) + '&gt; ' };

var getData  = {
cols: function() {
  var columns = [ {id:0, name:'Variable', field:0, width: 100, formatter:formatter00 },
              {id:1, name:'Standard name', field:1, width: 210, formatter:formatter01 },
              {id:2, name:'Long name', field:2, width: 180, formatter:formatter02},
              {id:3, name:'Units', field:3, width: 180, formatter:formatter03},
              {id:4, name:'Description', field:4, width: 180, formatter:formatter04},
              {id:5, name:'uid', field:5, width: 180, formatter:formatter05}];
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
      oo.write( dq.pageTmpl % ( title, '', '../', '../index.html', '\n'.join( bdy ) ) )
      oo.close()
      self.anno[v.label] = '<a href="../t/%s.html">Usage</a>' % v.label
    else:
      self.anno[v.label] = 'Unused'
        

class makeJs(object):
  def __init__(self,dq):
    n = 0
    rl = []
    for v in dq.coll['var'].items:
      if 'CMORvar' in dq.inx.iref_by_sect[v.uid].a and len(dq.inx.iref_by_sect[v.uid].a['CMORvar'] ) > 0:
        var = '%s %s' % (v.label,v.uid)
        sn = v.sn
        ln = v.title
        u = v.units
        d = v.description
        uid = v.uid
        d = locals()
        for k in ['sn','ln','u','var','d']:
    
          if  d[k].find( '"' ) != -1:
            print ( "WARNING ... quote in %s .. %s [%s]" % (k,var,d[k]) )
            d[k] =  d[k].replace( '"', "'" )
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

  def stidLink01(self,a,targ,frm='',ann=''):
    if targ._h.label == 'remarks':
      return '<li>%s: Broken link to structure  [%s]</li>' % ( a, targ.__href__() )
    else:
      return '<li>%s [%s]: %s [%s]</li>' % ( targ._h.title, a, targ.__href__(label=targ.title), targ.label  )

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
    if 'requestVar' in targ._inx.iref_by_sect[targ.uid].a:
      nrq = len( targ._inx.iref_by_sect[targ.uid].a['requestVar'] )
    else:
      nrq = 'unused'
    return '<li>%s {%s}: %s [%s: %s] (%s)</li>' % (  targ.__href__(odir='../u/', label=targ.label), targ.mipTable, targ.title, targ.frequency, t2.title, nrq )

  def objLink(self,targ,frm='',ann=''):
    return '<li>%s: %s</li>' % (  targ.label, targ.__href__(odir='../u/', label=targ.title,title=targ.description) )

  def unitLink(self,targ,frm='',ann=''):
    return '<li>%s [%s]: %s</li>' % (  targ.text, targ.label, targ.__href__(odir='../u/', label=targ.title) )

  def strLink(self,targ,frm='',ann=''):
    return '<li>%s: %s</li>' % (  targ.label, targ.__href__(odir='../u/', label=targ.title) )

  def cmLink(self,targ,frm='',ann=''):
    return '<li>%s [%s]: %s</li>' % (  targ.cell_methods,targ.label, targ.__href__(odir='../u/', label=targ.title) )

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
  def __init__(self,sc, odir='xls',xls=True,txt=False,txtOpts=None):
      self.sc = sc
      self.dq = sc.dq
      ##self.mips = mips
      self.odir = odir
      self.accReset()
      self.doXls = xls
      self.doTxt = txt
      self.txtOpts = txtOpts
      self.odir = 'vs-xls'

  def accReset(self):
    self.acc = [0.,collections.defaultdict(int),collections.defaultdict( float ) ]

  def accAdd(self,x):
    self.acc[0] += x[0]
    for k in x[2]:
       self.acc[2][k] += x[2][k]


  def getTable(self,m,m2,pmax,odsz,npy):
     vs = volsum.vsum( self.sc, odsz, npy )
     mlab = setMlab( m )
     vs.run( m, 'requestVol_%s_%s_%s' % (mlab,self.sc.tierMax,pmax), pmax=pmax )


## collected=summed volumes by table for first page.
     makeTab( self.sc.dq, subset=vs.thiscmvset, dest='%s/%s-%s_%s_%s' % (self.odir,mlab,mlab2,self.sc.tierMax,pmax), collected=collector[kkc].a,
              mcfgNote=self.sc.mcfgNote,
              txt=self.doTxt, xls=self.doXls, txtOpts=self.txtOpts )
  def doTable(self,m,l1,m2,pmax,collector,acc=True, mlab=None,exptids=None,cc=None):
      """*acc* allows accumulation of values to be switched off when called in single expt mode"""
      
      self.verbose = False
      if mlab == None:
        mlab = setMlab( m )

      cc0 = misc_utils.getExptSum( self.dq, mlab, l1 )
      ks = sorted( list( cc0.keys() ) )
      if self.verbose:
        print ('Experiment summary: %s %s' % (mlab,', '.join( ['%s: %s' % (k,len(cc0[k])) for k in ks] ) ) )

      if m2 in [None, 'TOTAL']:
        x = self.acc
      else:
        x = self.sc.volByExpt( l1, m2, pmax=pmax )

##self.volByExpt( l1, e, pmax=pmax, cc=cc, retainRedundantRank=retainRedundantRank, intersection=intersection, adsCount=adsCount )
        v0 = self.sc.volByMip( m, pmax=pmax,  exptid=m2 )
####
        if cc==None:
          cc = collections.defaultdict( int )
        for e in self.sc.volByE:
          if self.verbose:
             print ('INFO.mlab.... %s: %s: %s' % ( mlab, e, len( self.sc.volByE[e][2] ) ) )
          for v in self.sc.volByE[e][2]:
             cc[v] += self.sc.volByE[e][2][v]
        xxx = 0
        for v in cc:
          xxx += cc[v]
####
        if acc:
          for e in self.sc.volByE:
            self.accAdd(self.sc.volByE[e])

      if m2 not in [ None, 'TOTAL']:
          im2 = self.dq.inx.uid[m2]
          ismip = im2._h.label == 'mip'
          mlab2 = im2.label

          x0 = 0
          for e in self.sc.volByE:
            if exptids == None or e in exptids:
              x = self.sc.volByE[e]
              if x[0] > 0:
                collector[mlab].a[mlab2] += x[0]
                x0 += x[0]
      else:
          ismip = False
          mlab2 = 'TOTAL'
          x0 = x[0]

      if mlab2 == 'TOTAL' and x0 == 0:
        print ( 'no data detected for %s' % mlab )

      if x0 > 0:
#
# create sum for each table
#
        xs = 0
        kkc = '_%s_%s' % (mlab,mlab2)
        kkct = '_%s_%s' % (mlab,'TOTAL')
        if m2 in [None, 'TOTAL']:
          x = self.acc
          x2 = set(x[2].keys() )
          for k in x[2].keys():
           i = self.dq.inx.uid[k]
           xxx =  x[2][k]
           xs += xxx
        else:
          x2 = set()
          for e in self.sc.volByE:
            if exptids == None or e in exptids:
              x = self.sc.volByE[e]
              x2 = x2.union( set( x[2].keys() ) )
              for k in x[2].keys():
               i = self.dq.inx.uid[k]
               xxx =  x[2][k]
               xs += xxx
               if xxx > 0:
                collector[kkc].a[i.mipTable] += xxx
                if ismip:
                  collector[kkct].a[i.mipTable] += xxx

##
## One user was getting false error message here, with ('%s' % x0) == ('%s' % xs)
##
        if abs(x0 -xs) > 1.e-8*( abs(x0) + abs(xs) ):
          print ( 'ERROR.0088: consistency problem %s  %s %s %s' % (m,m2,x0,xs) )
        if x0 == 0:
          print ( 'Zero size: %s, %s' % (m,m2) )
          if len( x[2].keys() ) > 0:
             print ( 'ERROR:zero: %s, %s: %s' % (m,m2,str(x[2].keys()) ) )

        if acc and m2 not in [ None, 'TOTAL']:
          collector[mlab].a['TOTAL'] += x0

        dd = collections.defaultdict( list )
        lll = set()
        for v in x2:
          vi = self.sc.dq.inx.uid[v]
          if vi._h.label != 'remarks':
            f,t,l,tt,d,u = (vi.frequency,vi.mipTable,vi.label,vi.title,vi.description,vi.uid)
            lll.add(u)
            dd[t].append( (f,t,l,tt,d,u) )

        if len( dd.keys() ) > 0:
          collector[mlab].dd[mlab2] = dd
          if m2 not in [ None, 'TOTAL']:
            if im2._h.label == 'experiment':
              dothis = self.sc.tierMax >= min( im2.tier )
###
### BUT ... there is a treset in the request item .... it may be that some variables are excluded ...
###         need the variable list itself .....
###
          makeTab( self.sc.dq, subset=lll, dest='%s/%s-%s_%s_%s' % (self.odir,mlab,mlab2,self.sc.tierMax,pmax), collected=collector[kkc].a,
              mcfgNote=self.sc.mcfgNote,
              txt=self.doTxt, xls=self.doXls, txtOpts=self.txtOpts )

styls = styles()

htmlStyle = {}
htmlStyle['CMORvar'] = {'getIrefs':['__all__']}
htmlStyle['requestVarGroup'] = {'getIrefs':['requestVar','requestLink']}
htmlStyle['var'] = {'getIrefs':['CMORvar']}
htmlStyle['objective'] = {'getIrefs':['objectiveLink']}
htmlStyle['requestLink'] = {'getIrefs':['objectiveLink','requestItem']}
htmlStyle['exptgroup'] = {'getIrefs':['__all__']}
htmlStyle['requestItem'] = {'getIrefs':['__all__']}
htmlStyle['experiment'] = {'getIrefs':['__all__']}
htmlStyle['mip'] = {'getIrefs':['__all__']}
htmlStyle['miptable'] = {'getIrefs':['__all__']}
htmlStyle['remarks'] = {'getIrefs':['__all__']}
htmlStyle['grids'] = {'getIrefs':['__all__']}
htmlStyle['varChoice'] = {'getIrefs':['__all__']}
htmlStyle['spatialShape'] = {'getIrefs':['__all__']}
htmlStyle['temporalShape'] = {'getIrefs':['__all__']}
htmlStyle['structure']    = {'getIrefs':['__all__']}
htmlStyle['cellMethods']  = {'getIrefs':['__all__']}
htmlStyle['standardname'] = {'getIrefs':['__all__']}
htmlStyle['varRelations'] = {'getIrefs':['__all__']}
htmlStyle['varRelLnk']    = {'getIrefs':['__all__']}
htmlStyle['units']        = {'getIrefs':['__all__']}
htmlStyle['timeSlice']    = {'getIrefs':['__all__']}

if __name__ == "__main__":
  assert os.path.isdir( 'html' ), 'Before running this script you need to create "html", "html/index" and "html/u" sub-directories, or edit the call to dq.makeHtml'
  assert os.path.isdir( 'html/u' ), 'Before running this script you need to create "html", "html/index" and "html/u" sub-directories, or edit the call to dq.makeHtml, and refernces to "u" in style lines below'
  assert os.path.isdir( 'html/index' ), 'Before running this script you need to create "html", "html/index" and "html/u" sub-directories, or edit the call to dq.makeHtml, and refernces to "u" in style lines below'
  assert os.path.isdir( 'tables' ), 'Before running this script you need to create a "tables" sub-directory, or edit the makeTab class'

  dq = dreq.loadDreq( htmlStyles=htmlStyle, manifest='out/dreqManifest.txt' )
##
## add special styles to dq object "itemStyle" dictionary.
##

  dq.itemStyles['standardname'] = styls.snLink
  dq.itemStyles['var'] = styls.varLink
  dq.itemStyles['mip'] = styls.mipLink
  dq.itemStyles['CMORvar'] = styls.cmvLink
  dq.itemStyles['objective'] = styls.objLink
  dq.itemStyles['units'] = styls.unitLink
  dq.itemStyles['structure'] = styls.strLink
  dq.itemStyles['cellMethods'] = styls.cmLink
  dq.itemStyles['objectiveLink'] = styls.objLnkLink
  dq.itemStyles['requestVarGroup'] = styls.vgrpLink
  dq.itemStyles['requestLink'] = styls.rqlLink02
  dq.itemStyles['requestItem'] = styls.rqiLink02
  dq.itemStyles['spatialShape'] = styls.labTtl
  dq.coll['var'].items[0].__class__._linkAttrStyle['sn'] = styls.snLink01
  dq.coll['CMORvar'].items[0].__class__._linkAttrStyle['stid'] = styls.stidLink01
##dq.coll['requestVarGroup'].items[0].__class__._linkAttrStyle['requestVar'] = styls.rqvLink01
  dq.itemStyles['requestVar'] = styls.rqvLink01

  dreq.dreqItemBase._extraHtml['requestVarGroup'] = rvgExtraTable.vgx1(dq).mxoGet
  dreq.dreqItemBase.__charmeEnable__['var'] = nt__charmeEnable( 'test','http://clipc-services.ceda.ac.uk/dreq' )

  ht = htmlTrees(dq)
  dq.makeHtml( annotations={'var':ht.anno}, ttl0='Data Request [%s]' % dreq.version )
  try:
    import xlsxwriter
    mt = makeTab( dq)
  except:
    print ('Could not make tables ...')
    raise
  mp = makePurl()
  mj = makeJs( dq )
