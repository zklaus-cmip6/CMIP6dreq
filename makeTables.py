
from dreqPy import dreq
import collections, string, xlsxwriter, os
import vrev

class xlsx(object):
  def __init__(self,fn):
    self.wb = xlsxwriter.Workbook(fn)

  def newSheet(self,name):
    self.worksheet = self.wb.add_worksheet(name=name)
    return self.worksheet

  def close(self):
    self.wb.close()


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
         print 'Match failed: ', v.label
    oo.close()
      
class makeTab(object):
  def __init__(self):
    cmv = dq.coll['CMORvar'].items
    tables = sorted( list( {i.mipTable for i in cmv} ), cmp=cmpAnnex )

    addMips = True
    if addMips:
      c = vrev.checkVar(dq)

    wb = xlsx( 'tables/test.xlsx' )

    cell_format = wb.wb.add_format({'text_wrap': True})


    mode = 'c'

    for t in tables:
      oo = open( 'tables/test_%s.csv' % t, 'w' )
      sht = wb.newSheet( t )
      j = 0
      if mode == 'c':
        hrec = ['','Long name', 'units', 'description', 'label', 'CF Standard Name', 'cell_methods', 'positive', 'type', 'dimensions', 'label', 'modeling_realm', 'frequency', 'cell_measures', 'prov', 'provNote','rowIndex']
        sht.set_column(1,1,40)
        sht.set_column(3,3,50)
        sht.set_column(5,5,40)
        sht.set_column(6,6,30)
        sht.set_column(9,9,40)
      else:
        hrec = ['','Long name', 'units', 'description', '', 'label', 'CF Standard Name', '','', 'cell_methods', 'valid_min', 'valid_max', 'ok_min_mean_abs', 'ok_max_mean_abs', 'positive', 'type', 'dimensions', 'label', 'modeling_realm', 'frequency', 'cell_measures', 'flag_values', 'flag_meanings', 'prov', 'provNote','rowIndex']
      if addMips:
        hrec.append( 'MIPs' )

      for i in range(len(hrec)):
          sht.write( j,i, hrec[i] )
      thiscmv =  sorted( [v for v in cmv if v.mipTable == t], cmp=cmpdn(['prov','rowIndex','label']).cmp )
      
      for v in thiscmv:
          cv = dq.inx.uid[ v.vid ]
          strc = dq.inx.uid[ v.stid ]
          sshp = dq.inx.uid[ strc.spid ]
          tshp = dq.inx.uid[ strc.tmid ]
          ok = all( [i._h.label != 'remarks' for i in [cv,strc,sshp,tshp]] )
          #[u'shuffle', u'ok_max_mean_abs', u'vid', '_contentInitialised', u'valid_min', u'frequency', u'uid', u'title', u'rowIndex', u'positive', u'stid', u'mipTable', u'label', u'type', u'description', u'deflate_level', u'deflate', u'provNote', u'ok_min_mean_abs', u'modeling_realm', u'prov', u'valid_max']

          if not ok:
            print 'skipping %s %s' % (t,v.label)
          else:
            dims = []
            dims += string.split( sshp.dimensions, '|' )
            dims += string.split( tshp.dimensions, '|' )
            dims += string.split( strc.odims, '|' )
            dims += string.split( strc.coords, '|' )
            dims = string.join( dims )
            if mode == 'c':
              orec = ['',cv.title, cv.units, v.description, cv.label, cv.sn, strc.cell_methods, v.positive, v.type, dims, v.label, v.modeling_realm, v.frequency, strc.cell_measures, v.prov,v.provNote,str(v.rowIndex)]
            else:
              orec = ['',cv.title, cv.units, v.description, '', cv.label, cv.sn, '','', strc.cell_methods, v.valid_min, v.valid_max, v.ok_min_mean_abs, v.ok_max_mean_abs, v.positive, v.type, dims, v.label, v.modeling_realm, v.frequency, strc.cell_measures, strc.flag_values, strc.flag_meanings,v.prov,v.provNote,str(v.rowIndex)]
            if addMips:
              thismips = c.chkCmv( v.uid )
              orec.append( string.join( sorted( list( thismips) ),',') )

            oo.write( string.join(orec, '\t' ) + '\n' )
            j+=1
            for i in range(len(orec)):
              sht.write( j,i, orec[i], cell_format )
      oo.close()
    wb.close()

hdr = """
var getData  = {
cols: function() {
  var columns = [ {id:0, name:'Variable', field:0, width: 100},
              {id:1, name:'Standard name', field:1, width: 210 },
              {id:2, name:'Long name', field:2, width: 180},
              {id:3, name:'Units', field:3, width: 180},
              {id:4, name:'uid', field:4, width: 180}];
 return columns;
},
data: function() {
var data = [];
"""
ftr = """return data;
}
};
"""
rtmpl = 'data[%(n)s] = { "id":%(n)s, 0:"%(var)s",  1:"%(sn)s", 2:"%(ln)s", 3:"%(u)s", 4:"%(uid)s" };'

class makeJs(object):
  def __init__(self,dq):
    n = 0
    rl = []
    for v in dq.coll['var'].items:
      var = '%s %s' % (v.label,v.uid)
      sn = v.sn
      ln = v.title
      u = v.units
      uid = v.uid
      rr = rtmpl % locals()
      rl.append( rr )
      n += 1
    oo = open( 'data2.js', 'w' )
    oo.write( hdr )
    for r in rl:
      oo.write( r + '\n' )
    oo.write( ftr )
    oo.close()
    


class styles(object):
  def __init__(self):
    pass

  def snLink01(self,a,targ):
    if targ._h.label == 'remarks':
      return '<li>%s: Standard name under review [%s]</li>' % ( a, targ.__href__() )
    else:
      return '<li>%s [%s]: %s</li>' % ( targ._h.title, a, targ.__href__(label=targ.label)  )

styls = styles()

assert os.path.isdir( 'html' ), 'Before running this script you need to create "html", "html/index" and "html/u" sub-directories, or edit the call to dq.makeHtml'
assert os.path.isdir( 'html/u' ), 'Before running this script you need to create "html", "html/index" and "html/u" sub-directories, or edit the call to dq.makeHtml, and refernces to "u" in style lines below'
assert os.path.isdir( 'html/index' ), 'Before running this script you need to create "html", "html/index" and "html/u" sub-directories, or edit the call to dq.makeHtml, and refernces to "u" in style lines below'
assert os.path.isdir( 'tables' ), 'Before running this script you need to create a "tables" sub-directory, or edit the makeTab class'
dq = dreq.loadDreq()
##
## add special styles to dq object "itemStyle" dictionary.
##
dq.itemStyles['standardname'] = lambda i:  '<li>%s [%s]: %s</li>' % ( i.title, i.units, i.__href__(odir='../u/') )
dq.itemStyles['var'] = lambda i:  '<li>%s: %s [%s]</li>' % (  i.__href__(odir='../u/', label=i.label), i.title, i.units )
dq.coll['var'].items[0].__class__._linkAttrStyle['sn'] = styls.snLink01

dq.makeHtml()
mt = makeTab()
mp = makePurl()
mj = makeJs( dq )
