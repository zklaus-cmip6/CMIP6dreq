import string, itertools
from fcc_utils2 import snlist
import xlrd, string, shelve, os, re, sys
import collections
import xlutils, xlwt
import xlutils.copy
import xlutils.styles
import copy
####
import dreq_cfg

nt__deckrq = collections.namedtuple( 'dckrq', ['control','AMIP','abrupt4xCO2','rq_1pctCO2','historical'] )
dd_rq = collections.defaultdict( dict )
dd_tbl = collections.defaultdict( int )
def uniCleanFunc(ss,jsFilt=False):
      if type(ss) in [type('x'),type(u'x')]:
          ss = string.replace( ss, u'\u2013', '-' )
          ss = string.replace( ss, u'\u2014', '-' )
          ss = string.replace( ss, u'\u201c', '"' )
          ss = string.replace( ss, u'\u201d', '"' )
          ss = string.replace( ss, u'\u2018', "'" )
          ss = string.replace( ss, u'\u2019', "'" )
          ss = string.replace( ss, u'\u2026', '...' )
          ss = string.replace( ss, u'\u25e6', 'o' )
          ss = string.replace( ss, u'\xb2', '2' )
          ss = string.replace( ss, u'\xb3', '3' )
          if jsFilt:
            ss = string.replace( ss, '"', "'" )
            ss = string.replace( ss, '\n', ";;" )
          return ss
      else:
          return ss
    

class wbcp(object):
  def __init__( self, inbook=dreq_cfg.rqcfg.tmpl ):
    self.book = xlrd.open_workbook(inbook,formatting_info=True)
    self.sns = self.book.sheet_names()
    self.wb = xlutils.copy.copy(self.book)
    ##self.book = xlrd.open_workbook(inbook,formatting_info=True)
    self.plain = xlwt.easyxf('')
    self.styles = xlutils.styles.Styles(self.book)


  def styleUpdate(self,other):
    self.styles.cell_styles.update( other.styles.cell_styles )
  def _getOutCell(self, rowIndex, colIndex,stbk=None):
    """ HACK: Extract the internal xlwt cell representation. """
   
    if stbk == None:
      this = self
    else:
      this = stbk
    row = this.currentSo._Worksheet__rows.get(rowIndex)

    if not row: return None

    cell = row._Row__cells.get(colIndex)
    return cell

  def rowValues(self, i, f=None, uniClean=False, jsFilt=False ):
    if f == None:
      v1 = map( lambda x: x.value, self.currentSi.row(i) )
    else:
      v1 = map( lambda x: f(x.value), self.currentSi.row(i) )
    if not uniClean:
      return v1
    else:
      return map( lambda x: uniCleanFunc(x,jsFilt=jsFilt), v1 )

  def putValue2(self, row, col, value,sti=None,stj=None,stbk=None,style=0):
    """ Change cell value without changing formatting. """
    # HACK to retain cell style.
    if sti == None:
      sti = col
    if stj == None:
      stj = row
    self.previousCell = self._getOutCell( stj,sti,stbk=stbk )
    # END HACK, PART I

    if style==0:
      self.currentSo.write(row, col, value)
    else:
      self.currentSo.write(row, col, value,style=style)

    # HACK, PART II

    do_style = False
    if self.previousCell and style==0 and do_style:
        self.newCell = self._getOutCell( row, col)
        if self.newCell:
          if stbk == None:
            self.newCell.xf_idx = self.previousCell.xf_idx
          else:
            self.newCell.xf_idx = self.previousCell.xf_idx
            ##nn = len( self.styles.cell_styles.keys() )
            ##print stj,sti,self.previousCell.xf_idx, nn
            ##self.styles.cell_styles[nn] = stbk.styles.cell_styles.items()[self.previousCell.xf_idx]
            ##self.newCell.xf_idx = nn
    # END HACK

  def focus( self, name, old=None ):
    if old == None:
      oname = name
      new=False
    else:
      oname = old
      new = True
    
    if oname not in self.sns:
      print '%s not in %s' % (oname,str(self.sns) )
      raise
    
    self.currentIndex = self.sns.index(oname)
    self.currentSi = self.book.sheet_by_name( oname )

    if new:
      self.currentSo = self.get_sheet_by_name( name )
    else:
      self.currentSo = self.wb.get_sheet( self.currentIndex )

  def putValue(self,i,j,value,sti=None,stj=None):
    ##self.currentSi.write(i,j,value,self.plain)
    if sti == None:
      sti = i
    if stj == None:
      stj = j
    cell_style = self.styles[self.currentSi.cell(sti,stj)]
    self.currentSo.write(i,j,value,cell_style)

  def write(self,file='output.xls'):
    self.wb.save( file )


  def get_sheet_by_name(self, name):
    """Get a sheet by name from xlwt.Workbook, a strangely missing method.
    Returns None if no sheet with the given name is present.
    http://stackoverflow.com/questions/14587271/accessing-worksheets-using-xlwt-get-sheet-method dhdaines
    """
    # Note, we have to use exceptions for flow control because the
    # xlwt API is broken and gives us no other choice.
    try:
        sheets = []
        for idx in itertools.count():
            sheet = self.wb.get_sheet(idx)
            sheets.append( sheet.name )
            if sheet.name == name:
                return sheet
    except:
        print '################# failed to find sheet: %s ############' % name
        return None

  def copy_sheet(self, source_index, new_name): 
    '''
    self.wb	 == source + book in use 
    source_index == index of sheet you want to copy (0 start) 
    new_name	 == name of new copied sheet 
    return: copied sheet
    Original code: https://groups.google.com/forum/#!topic/python-excel/gafa0rP3KyU [John Machin]
    '''

    source_worksheet = self.wb.get_sheet(source_index)
    copied_sheet = copy.deepcopy(source_worksheet) 
    copied_workbook = copied_sheet._Worksheet__parent

    self.wb._Workbook__worksheets.append(copied_sheet)

    copied_sheet.set_name(new_name)
    self.wb._Workbook__sst = copied_workbook._Workbook__sst
    self.wb._Workbook__styles = copied_workbook._Workbook__styles
    return copied_sheet

class tupsort:
   def __init__(self,k=0):
     self.k = k
   def cmp(self,x,y):
     return cmp( x[self.k], y[self.k] )

def uniquify( ll ):
  ll.sort()
  l0 = [ll[0],]
  for l in ll[1:]:
    if l != l0[-1]:
      l0.append(l)
  return l0

class workbook(object):
  def __init__(self,file):
    assert os.path.isfile(file), 'File %s not found' % file
    self.book = xlrd.open_workbook( file )
    self.sns = self.book.sheet_names()

clabs = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
def clab(n):
  i = n/26
  assert i < 26, 'Not ready for row number greater than 26*26'
  if i == 0:
    return clabs[n]
  else:
    return clabs[i-1] + clabs[ n - i*26]

def getRow(sht):
  ee = {}
  for i in range(sht.nrows):
    if sht.row(i)[0].ctype == 2 and str( sht.row(i)[0].value ) != '0.0':
      l = map( lambda x: str( x.value ), sht.row(i) )
      ##k = string.replace( l[5], ' ','')
      k = l[5]
      try:
        ee[k] = l
      except:
        print l
        raise
  return ee
    
def outvSer( ov ):
  ll = []
  for i in ov:
    ll.append( '%s|%s|%s' % tuple( map( str, i) ) )
  return string.join(ll, '; ' )
  

class cpsh(object):

  def __init__(self,wk0,mip,path,kk=3,oo=None):
    self.oo = oo
    self.nn = 0
    self.kk = kk
    wk = wbcp( path )
    wk0.focus( u'New variables')
    self.wk = wk
    self.mip = mip
    self.nvgs = []
    for s in wk.sns:
      if s not in ['Objectives','Experiments','Experiment Groups','Request scoping','New variables','__lists__']:
        self.nvgs.append(s)
    self.outv = collections.defaultdict(list)
    for s in self.nvgs:
      thiss = wk.book.sheet_by_name( s )
      for k in range(4,thiss.nrows):
        r = thiss.row(k)
        v = r[1].value
        t = r[2].value
        f = r[3].value
        s = r[5].value
        m = r[7].value
        if t[:3] == 'new':
          self.outv[v].append( (f,s,m) )
    this = wk.book.sheet_by_name(u'New variables')
    ee = collections.defaultdict( list )
    for i in range(3,this.nrows):
      r = this.row(i)
      if r[0].value == "**end**":
        break
      v = r[0].value
      ee[v].append(i)

    for i in range(3,this.nrows):
      r = this.row(i)
      if r[0].value == "**end**":
        break

      v = r[0].value
      l = r[4].value
      novar = v == '' and l == ''
      omitOld = True
      omit = False
      if vdict.has_key(v) and omitOld:
        omit = True

      if not omit:
        if not novar:
          wk0.putValue2( self.kk, 0, mip )
          s = r[1].value
          if s in ['','?']:
            chk = 0
          elif esn.has_key(s):
            chk = 1
          elif esna.has_key(s):
            chk = 2
          else:
            chk = -1
          wk0.putValue2( self.kk, 1, chk )
          self.nn += 1
          htmlline = "<td>%s</td>" % mip
        else:
          chk = 0
          htmlline = "<td></td>"
      
        j = 3
        jo = 1
        wk0.putValue2( self.kk, 3, outvSer( self.outv[v] ) )
        for x in r:
          if j == 3:
            v = x.value
            v0 = x.value
            if str(v0) != "":
              if len(ee[v0]) != 1:
                 v += '!'
              if vdict.has_key(v0):
                 v += '**'
            wk0.putValue2( self.kk, j+jo, v )
          else:
            wk0.putValue2( self.kk, j+jo, x.value )
          if j in [3,7]:
            htmlline += "<td>%s</td>\n" % x.value
          elif j == 4:
            if chk == -1:
              htmlline += "<td>?%s?</td>\n" % x.value
            else:
              htmlline += "<td>%s</td>\n" % x.value
          elif j == 8:
            y = x.value
          elif j == 9:
            htmlline += '<td><span title="%s">%s</span></td>\n' % (x.value,y)
          j += 1
        self.kk += 1
        if not novar:
          if mip == "SIMIP":
            print htmlline
          htmlline = string.replace( htmlline, u'\u2013', '-' )
          htmlline = string.replace( htmlline, u'\u2018', "'" )
          htmlline = string.replace( htmlline, u'\u2019', "'" )
          htmlline = string.replace( htmlline, u'\u2026', '...' )
          htmlline = string.replace( htmlline, u'\u25e6', 'o' )
          htmlline = string.replace( htmlline, u'\xb2', '2' )
          htmlline = string.replace( htmlline, u'\xb3', '3' )
          if self.oo != None:
            self.oo.write( "<tr>%s</tr>" % str(htmlline) + '\n' )


  def parseRQ(self):
    this = self.wk.book.sheet_by_name(u'Request scoping')
    for i in range(6,this.nrows):
      r = this.row(i)
      mipt = r[0].value
      s = r[1].value
      if mipt[:4]  in ['SPEC','CORD', 'CCMI'] and s != 'none':
        print self.mip,mipt
