
class cmvFilter(object):
  """Class to filter list of CMOR variables by rank.
     dq: data request object, as returned by dreq.loadDreq()"""

  def __init__(self,sc,dq=None):
    self.sc = sc
    if dq == None:
      self.dq = self.sc.dq
    else:
      self.dq = dq

    self.defaultPriority = 3

  def __test__(self,silentFail=False,silentPass=True):
    """Test the class against default request document.
       Returns True if test is passed, False otherwise.
	silentFail: return without printing a message if test fails.
	silentPass: return without printing a message if test passes.
    """
    cmv = self.filterByChoiceRank()
    self.cmv = cmv
    vidt = [i.uid for i in self.dq.coll['var'].items if i.label == 'ta']
    if len(vidt) != 1:
      if not silentFail:
        print ('FAIL: could not identify ta in "var" section' )
      return False

    vidt = vidt[0]
    taf = [i for i in cmv if self.dq.inx.uid[i].vid == vidt and self.dq.inx.uid[i].frequency in ['3hr','6hr']]
    tau = [i for i in self.sc.allVars if self.dq.inx.uid[i].vid == vidt and self.dq.inx.uid[i].frequency in ['3hr','6hr']]
##
## NB not easy to separate pressure level from model level variables here
## at 01.beta.06 do not filter CMIP5 6hrPlev and 27 level HighResMIP ....
##
    if len(taf) == 5 and len(tau) == 6:
      if not silentPass:
        print ('OK: tests passed')
      return True
    else:
      if not silentFail:
        print ( 'FAIL: tests failed: len filtered=%s, unfiltered=%s' % (len(taf),len(tau)) )
      return False

  def filterByChoiceCfg(self,cmv=None,cfg={}):
    """Filter a set of CMOR variable identifiers by configuration as specified in varChoiceLinkC section of the data request.
       cmv: set of CMOR variable identifiers.
      
       Returns the filetered set. The items removed are available in self.rejected."""
##
## cmv is a set of CMORvar ids
##
    if cmv == None:
      self.sc.volByMip( 'HighResMIP', pmax=self.defaultPriority )
      cmv = self.sc.allVars.copy()

## set of vids associated with choices
    s = set()
    for i in self.dq.coll['varChoiceLinkC'].items:
      s.add( i.vid )

## set of variables in current selection associated with choices
    v1 = set( [ u for u in cmv if u in s ] )
    if len(v1) == 0:
      ## print 'Nothing to do'
      return cmv

## set of "rank" choice groups relevant to current selection
    s1 = set( [i.cid for i in self.dq.coll['varChoiceLinkC'].items if i.vid in v1] )

    self.rejected = set()
    for s in s1:
      imr = set()
##
## set of choice links in group s which relate to a variable in current selection
##
      this = set()
      for i in self.dq.coll['varChoiceLinkC'].items:
         if i.vid in v1 and i.cid == s:
           set.add(i)
##
## value of configuration option (defaults to True here).
##
      testval = cfg.get( s, True )
      for i in this:
          if i.cfg != testval:
            l1 = len(cmv)
            cmv.remove( i.vid )
            if len(cmv) == l1:
              print ( 'Failed to remove i.vid=%s' % i.vid )
            self.rejected.add( i.vid )
          else:
            imr.add( i )
      ## print self.dq.inx.uid[s].label, len(this), len(imr)

    return cmv
  def filterByChoiceRank(self,cmv=None):
    """Filter a set of CMOR variable identifiers by rank as specified in varChoiceLinkR section of the data request.
       cmv: set of CMOR variable identifiers.
      
       Returns the filetered set. The items removed are available in self.rejected."""
##
## cmv is a set of CMORvar ids
##
    if cmv == None:
      self.sc.volByMip( 'HighResMIP', pmax=self.defaultPriority )
      cmv = self.sc.allVars.copy()

## set of vids associated with choices
    s = set( [i.vid for i in self.dq.coll['varChoiceLinkR'].items] )

## set of variables in current selection associated with choices
    v1 = set( [ u for u in cmv if u in s ] )
    if len(v1) == 0:
      ## print 'Nothing to do'
      return cmv

## set of "rank" choice groups relevant to current selection
    s1 = set( [i.cid for i in self.dq.coll['varChoiceLinkR'].items if i.vid in v1] )

    self.rejected = set()
    for s in s1:
      imr = set()
##
## set of choice links in group s which relate to a variable in current selection
##
      this = set( [i for i in self.dq.coll['varChoiceLinkR'].items if i.vid in v1 and i.cid == s] )
      if len(this) > 1:
        mr = max( [i.rank for i in this ] )
        for i in this:
          if i.rank < mr:
            l1 = len(cmv)
            cmv.remove( i.vid )
            if len(cmv) == l1:
              print ( 'Failed to remove i.vid=%s' % i.vid )
            self.rejected.add( i.vid )
          else:
            imr.add( i )
        ## print self.dq.inx.uid[s].label, len(this), len(imr), mr
      else:
        ## print self.dq.inx.uid[s].label, len(this)
        pass

    return cmv


test = cmvFilter
