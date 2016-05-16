import makeTables
import collections


class c1(object):
  def __init__(self):
    self.a = collections.defaultdict( int )

class xlsTabs(object):
  def __init__(self,sc,tiermax=1,pmax=1):
    self.pmax=pmax
    self.tiermax=tiermax
    self.sc = sc
    sc.setTierMax( tiermax )
    self.cc = collections.defaultdict( c1 )
    self.dq = sc.dq

    self.mips = ['AerChemMIP', 'C4MIP', 'CFMIP', 'DAMIP', 'DCPP', 'FAFMIP', 'GeoMIP', 'GMMIP', 'HighResMIP', 'ISMIP6', 'LS3MIP', 'LUMIP', 'OMIP', 'PMIP', 'RFMIP', 'ScenarioMIP', 'VolMIP', 'CORDEX', 'DynVar', 'SIMIP', 'VIACSAB']
    self.mipsp = ['DECK','CMIP6',] + self.mips[:-4]

    self.tabs = makeTables.tables( sc, self.mips )

  def run(self,m,colCallback=None,verb=False,mlab=None):
      if m == 'TOTAL':
        l1 = self.sc.rqiByMip( set( self.mips ) )
      else:
        l1 = self.sc.rqiByMip( m )

      if mlab == None:
        mlab = m

      if verb:
        print 'r1: m=%s, len(l1)=%s' % (mlab,len(l1))

      self.cc[mlab].dd = {}
      self.cc[mlab].ee = {}
      self.tabs.accReset()
      vcc = collections.defaultdict( int )
      for m2 in self.mipsp + ['TOTAL',]:
        if m2 == 'TOTAL':
          xx = self.dq.coll['experiment'].items
        else:
          xx = [i for i in self.dq.coll['experiment'].items if i.mip == m2]
        self.cc[mlab].ee[m2] = xx
        xxi = set( [i.label for i in xx] )
##
## need to check this option, and add a template for a view summarising the experiments for each mip-mip combinations
##
        if m2 != 'TOTAL':
          for i in xx:
              self.tabs.doTable(m,l1,i.uid,self.pmax,self.cc,acc=False,cc=vcc,exptids=xxi,mlab=None)

        self.tabs.doTable(m,l1,m2,self.pmax,self.cc,cc=vcc,exptids=xxi,mlab=None)

        if verb:
          print 'r1: mlab=%s,m2=%s, len(l1)=%s' % (mlab,m2,len(l1))

        if colCallback != None:
          colCallback( m,m2,mlab=mlab )


