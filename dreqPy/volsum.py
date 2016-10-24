
import scope
import dreq
import xlsxwriter
from xlsxwriter.utility import xl_rowcol_to_cell
import collections, os
import makeTables
import overviewTabs

###cell = xl_rowcol_to_cell(1, 2)  # C2
 

class xlsx(object):
  def __init__(self,fn,txtOpts=None):
    self.txtOpts = txtOpts
    self.mcfgNote = 'Reference Volume (1 deg. atmosphere, 0.5 deg. ocean)'
    self.wb = xlsxwriter.Workbook('%s.xlsx' % fn)
    self.hdr_cell_format = self.wb.add_format({'text_wrap': True, 'font_size': 14, 'font_color':'#0000ff', 'bold':1, 'fg_color':'#aaaacc'})
    self.hdr_cell_format.set_text_wrap()
    self.sect_cell_format = self.wb.add_format({'text_wrap': True, 'font_size': 14, 'font_color':'#0000ff', 'bold':1, 'fg_color':'#ccccbb'})
    self.sect_cell_format.set_text_wrap()
    self.cell_format = self.wb.add_format({'text_wrap': True, 'font_size': 11})
    self.cell_format.set_text_wrap()

  def newSheet(self,name):
    self.sht = self.wb.add_worksheet(name=name)
    return self.sht

  def tabrec(self,j,orec):
        for i in range(len(orec)):
          if orec[i] != '' and type( orec[i] ) == type( '' ) and orec[i][0] == '$':
             self.sht.write_formula(j,i, '{=%s}' % orec[i][1:])
          else:
             if j == 0:
               self.sht.write( j,i, orec[i], self.hdr_cell_format )
             else:
               self.sht.write( j,i, orec[i], self.cell_format )

  def close(self):
      self.wb.close()

class vsum(object):
  def __init__(self,sc,odsz,npy,exptFilter=None, odir='xls'):
    idir = dreq.DOC_DIR
    self.sc = sc
    self.odsz=odsz
    self.npy = npy
    self.exptFilter = exptFilter
    self.strSz = dict()
    self.accum = False
    self.odir = odir
    self.efnsfx = ''
    if sc.gridPolicyDefaultNative:
      self.efnsfx = '_dn'
    if not os.path.isdir( odir ):
      print ( 'Creating new directory for xlsx output: %s' % odir )
      os.mkdir( odir )
    ii = open( '%s/sfheadings.csv' % idir, 'r' )
    self.infoRows = []
    for l in ii.readlines():
      ll = l.strip().split( '\t' )
      assert len(ll) == 2, 'Failed to parse info row: %s' % l
      self.infoRows.append( ll )
    ii.close()

  def analAll(self,pmax):
      volsmm={}
      volsmmt={}
      volsme={}
      volsue={}
      for m in ['TOTAL',] + self.sc.mips:
        if m != 'TOTAL':
          cmv1 = self.sc.cmvByInvMip(m,pmax=pmax,includeYears=True)
          self.uniqueCmv = self.sc.differenceSelectedCmvDict(  cmv1, cmvTotal )
        self.run( m, '%s/requestVol_%s_%s_%s' % (self.odir,m,self.sc.tierMax,pmax), pmax=pmax )

        self.anal(olab=m,doUnique=True, makeTabs=True)
        ttl = sum( [x for k,x in self.res['vu'].items()] )*2.*1.e-12
        print ( '%s volume: %8.2fTb' % (m,ttl) )
        volsmm[m] = self.res['vm']
        volsmmt[m] = self.res['vmt']
        volsme[m] = self.res['ve']
        volsue[m] = self.res['uve']
        if m == 'TOTAL':
          cmvTotal = self.sc.selectedCmv.copy()
          self.uniqueCmv =  {}
      r1 = overviewTabs.r1( self.sc, pmax=pmax, vols=( volsmm, volsme, volsmmt,volsue ) )

  def _analSelectedCmv(self,cmv):
    lex = collections.defaultdict( list )
    vet = collections.defaultdict( int )
    vf = collections.defaultdict( int )
    vu = collections.defaultdict( float )
    mvol = collections.defaultdict( dict )

    for u in cmv:
      i = self.sc.dq.inx.uid[u]
      if i._h.label != 'remarks':
        npy = self.npy[ i.frequency ]
        isClim = i.frequency.lower().find( 'clim' ) != -1
        st = self.sc.dq.inx.uid[i.stid]
        c1 = 0
        for e,g in cmv[u]:
          ee = self.sc.dq.inx.uid[e]
          if ee.mip not in ['SolarMIP']:
            lex[e].append( u )
            t1, tt = self.sc.getStrSz( g, stid=i.stid, tt=True )
            np = t1[1]*npy
            if not isClim:
              np = np*cmv[u][(e,g)]
            c1 += cmv[u][(e,g)]
            vet[(e,i.mipTable)] += np
            vf[i.frequency] += np
            vu[u] += np
          else:
            print ('ERROR.obsoleteMip.00001: %s,%s,%s' % (ee.mip,ee.label,ee.uid) )
        if i.frequency == 'mon':
            mvol[tt][u] = c1

    return lex, vet, vf, vu, mvol

  def anal(self,olab=None,doUnique=False,makeTabs=False):
    vmt = collections.defaultdict( int )
    vm = collections.defaultdict( int )
    ve = collections.defaultdict( int )
    uve = collections.defaultdict( int )
    lm = collections.defaultdict( set )

    lex, vet, vf, vu, mvol = self._analSelectedCmv(self.sc.selectedCmv )
    if olab != 'TOTAL' and doUnique:
      s_lex, s_vet, s_vf, s_vu, s_mvol = self._analSelectedCmv(self.uniqueCmv )
      s_lm = set( self.uniqueCmv.keys() )
      s_cc = collections.defaultdict( int )
      for e,t in s_vet:
        s_cc[t] += s_vet[(e,t)]
        vm['Unique'] += s_vet[(e,t)]
        vmt[('Unique',t)] += s_vet[(e,t)]
        uve[e] += s_vet[(e,t)]

    checkMvol = 1
    for k in mvol:
      sp = self.sc.dq.inx.uid[k[0]]
      if k not in self.mvol:
        print ( '%s missing from mvol: ' % str(k) )
      else:
        if checkMvol > 1:
          for u in mvol[k]:
            la = self.sc.dq.inx.uid[u].label
            if self.mvol[k][u] != mvol[k][u]:
              print ( 'MISMATCH IN %s (%s): %s:: %s,%s' % (str(k),sp.label,la,mvol[k][u],self.mvol[k][u]) )
          
    for e in lex:
      ee = self.sc.dq.inx.uid[e]
      for i in lex[e]:
        lm[ee.mip].add( i )

    for e,t in vet:
      ee = self.sc.dq.inx.uid[e]
      if ee.mip == 'SolarMIP':
        print ('ERROR.solarmip: %s,%s,%s' % (ee.label, ee.title, ee.uid) )
      vmt[(ee.mip,t)] += vet[(e,t)]
      vm[ee.mip] += vet[(e,t)]
      ve[e] += vet[(e,t)]

##
## makeTab needs: cc[m]: volume summary, by table,   lm[m]: list of CMOR variables
##
    cc = collections.defaultdict( dict )
    cct = collections.defaultdict( int )
    for m,t in vmt:
      cc[m][t] = vmt[(m,t) ]
    ss = set()
    for m in sorted( vm.keys() ):
      if olab != None:
        for t in cc[m]:
          cct[t] += cc[m][t]
        ss = ss.union( lm[m] )
        if makeTabs:
          makeTables.makeTab(self.sc.dq, subset=lm[m], dest='%s/cmvmm_%s_%s_%s_%s%s' % (self.odir,olab,m,self.sc.tierMax,self.pmax,self.efnsfx), collected=cc[m])

    if olab != None and makeTabs:
        makeTables.makeTab(self.sc.dq, subset=ss, dest='%s/cmvmm_%s_%s_%s_%s%s' % (self.odir,olab,'TOTAL',self.sc.tierMax,self.pmax,self.efnsfx), collected=cct)
        if olab != 'TOTAL' and doUnique:
          makeTables.makeTab(self.sc.dq, subset=s_lm, dest='%s/cmvmm_%s_%s_%s_%s%s' % (self.odir,olab,'Unique',self.sc.tierMax,self.pmax,self.efnsfx), collected=s_cc)

    cc = collections.defaultdict( dict )
    ucc = collections.defaultdict( dict )
    cct = collections.defaultdict( int )
    for e,t in vet:
      cc[e][t] = vet[(e,t) ]
    for e in sorted( ve.keys() ):
      if olab != None and makeTabs:
        el = self.sc.dq.inx.uid[e].label
        makeTables.makeTab(self.sc.dq, subset=lex[e], dest='%s/cmvme_%s_%s_%s_%s%s' % (self.odir,olab,el,self.sc.tierMax,self.pmax,self.efnsfx), collected=cc[e])

    if olab != 'TOTAL' and doUnique:
      for e,t in s_vet:
        ucc[e][t] = s_vet[(e,t) ]
      for e in sorted( uve.keys() ):
        if olab != None and makeTabs:
          el = self.sc.dq.inx.uid[e].label
          makeTables.makeTab(self.sc.dq, subset=s_lex[e], dest='%s/cmvume_%s_%s_%s_%s%s' % (self.odir,olab,el,self.sc.tierMax,self.pmax,self.efnsfx), collected=ucc[e])

    self.res = { 'vmt':vmt, 'vet':vet, 'vm':vm, 'uve':uve, 've':ve, 'lm':lm, 'lex':lex, 'vu':vu, 'cc':cc, 'cct':cct}
    cc8 = collections.defaultdict( int )
    for e,t in vet:
      cc8[t] += vet[(e,t)]
    for f in sorted( vf.keys() ):
      print ( 'Frequency: %s: %s' % (f,vf[f]*2.*1.e-12 ) )
        
  def csvFreqStrSummary(self,mip,pmax=1):
    sf, c3 = self.sc.getFreqStrSummary(mip,pmax=pmax)
    self.c3 = c3
    self.pmax = pmax
    lf = sorted( list(sf) )
    hdr0 = ['','','','']
    hdr1 = ['','','','']
    for f in lf:
      hdr0 += [f,'','','']
      hdr1 += ['','','',str( self.npy.get( f, '****') )]
    orecs = [hdr0,hdr1,]
    crecs = [None,None,]
    self.mvol = collections.defaultdict( dict )
    self.rvol = dict()

    ix = 3
    for tt in sorted( c3.keys() ):
      s,o,g = tt
      i = self.sc.dq.inx.uid[ s ]
      if o != '':
        msg = '%48.48s [%s]' % (i.title,o)
      else:
        msg = '%48.48s' % i.title
      if g != 'native':
        msg += '{%s}' % g
      szg = self.sc.getStrSz( g, s=s, o=o )[1]
      self.rvol[tt] = szg

      rec = [msg,szg,2,'']
      crec = ['','','','']
      for f in lf:
        if f in c3[tt]:
            nn,ny,ne,labs,expts = c3[tt][f]
            rec += [nn,ny,ne,'']
            clabs = [self.sc.dq.inx.uid[x].label for x in labs.keys()]
            crec += [sorted(clabs),'',expts,'']
            if f.lower().find( 'clim' ) == -1:
              assert abs( nn*ny - sum( [x for k,x in labs.items()] ) ) < .1, 'Inconsistency in year count: %s, %s, %s' % (str(tt),nn,ny)
            if f == 'mon':
              for k in labs:
                self.mvol[tt][k] = labs[k]
        else:
            rec += ['','','','']
            crec += ['','','','']
      colr = xl_rowcol_to_cell(0, len(rec))
      colr = colr[:-1]
      eq = '$SUMPRODUCT(--(MOD(COLUMN(E%(ix)s:%(colr)s%(ix)s)-COLUMN(A%(ix)s)+1,4)=0),E%(ix)s:%(colr)s%(ix)s)' % {'ix':ix,'colr':colr}
      ix += 1
      rec[3] = eq
      orecs.append( rec )
      crecs.append( crec )
    
    return (orecs, crecs)

  def byExpt(self):
    for cmv in self.sc.selectedCmv.keys():
      pass
      
  def run(self,mip='_all_',fn='test',pmax=1):
    if mip == '_all_':
      mip = set(self.sc.mips )
    self.mip = mip
    self.x = xlsx( fn )
    self.sht = self.x.newSheet( 'Volume' )
    orecs, crecs = self.csvFreqStrSummary(mip,pmax=pmax)
    oh = orecs[0]
    self.sht.set_column(0,0,60)
    self.sht.set_column(1,1,15)
    self.sht.set_column(2,2,4)
    self.sht.set_column(3,3,15)
    for k in range( int( (len(oh)-3)/4 ) ):
      self.sht.set_column((k+1)*4,(k+1)*4,4)
      self.sht.set_column((k+1)*4+1,(k+1)*4+1,8)
      self.sht.set_column((k+1)*4+2,(k+1)*4+2,4)
      self.sht.set_column((k+1)*4+3,(k+1)*4+3,12)
      
    oo = []
    for i in range( len(oh) ):
      oo.append( '' )
    kk = 0
    rr1 = 2
    rr1p = rr1 + 1
    for ix in range(len(orecs)):
      o = orecs[ix]
      kk += 1
      if kk > 2:
        for i in range( 7,len(o),4):
          frq = oh[i-3]
          
          cell = xl_rowcol_to_cell(0, i)[:-1]
          ca = xl_rowcol_to_cell(0, i-3)[:-1]
          ##if frq.lower().find( 'clim' ) == -1:
          cb = xl_rowcol_to_cell(0, i-2)[:-1]
          ##else:
          ##cb = xl_rowcol_to_cell(0, i-1)[:-1]
          eq = '$%(cell)s$%(rr1)s*%(cb)s%(kk)s*%(ca)s%(kk)s*$B%(kk)s*$C%(kk)s*0.000000001' % locals()
          o[i] = eq
        self.x.tabrec(kk-1, o )
        if crecs[ix] != None:
          crec = crecs[ix]
          for j in range(len(crec)):
            if crec[j] != '':
              self.sht.write_comment( kk-1, j, ' '.join( crec[j] ) )
      else:
        if kk == 1:
          for i in range( 4,len(o),4):
            cell = xl_rowcol_to_cell(0, i)[:-1]
            cell2 = xl_rowcol_to_cell(0, i+3)[:-1]
            self.sht.merge_range('%s1:%s1' % (cell,cell2), 'Merged Range')
        self.x.tabrec(kk-1, o )

    n = len(orecs)
    for i in range( 3,len(oo),4):
      cell = xl_rowcol_to_cell(0, i)[:-1]
      oo[i] = '$SUM(%(cell)s%(rr1p)s:%(cell)s%(n)s)*0.001' % locals()
    for i in range( 5,len(oo),4):
      oo[i] = oh[i-1]
    oo[0] = 'TOTAL VOLUME (Tb)'
    self.x.tabrec(kk, oo )

    n += 2
    for a,b in self.infoRows:
       self.sht.merge_range('B%s:H%s' % (n+1,n+1), 'Merged Range')
       self.sht.write( n,0, a )
       self.sht.write( n,1, b )
       n += 1

    self.x.close()
