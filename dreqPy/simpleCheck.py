
try:
  import pkgutil
  l = pkgutil.iter_modules()
  ll = map( lambda x: x[1], l )
  pkgutilFailed=False
except:
  pkgutilFailed=True
  print 'Failed to load pkgutil .. more limited tests on available modules will be done'
  ll = []


requiredModules = ['xml','string','collections','os']
confirmed = []
installFailed = []
missingLib = []
for x in requiredModules:
  if x in ll or pkgutilFailed:
      try:
        cmd = 'import %s' % x
        exec cmd
        confirmed.append( x )
      except:
        installFailed.append( x )
        print 'Failed to install %s' % x
  else:
      missingLib.append( x )

if len( missingLib ) > 0 or len(installFailed) > 0:
  print 'Could not load all required python libraries'
  if len(missingLib) > 0:
    print 'MISSING LIBRARIES:',str(missingLib)
  if len(installFailed) > 0:
    print 'LIBRARIES PRESENT BUT FAILED TO INSTALL:',str(missingLib)
  all = False
  exit(0)
else:
  print 'Required libraries present'
  all = True


import inspect
class checkbase(object):
  def __init__(self,lab):
    self.lab = lab
    self.ok = True

#document directory
    self.docdir = '../docs'
#schema location
    self.schema = '%s/dreq2Schema.xsd' % self.docdir
#sample xml location
    self.sampleXml = '%s/dreq2Sample.xml' % self.docdir
#definition document xml location
    self.defnXml = '%s/dreq2Defn.xml' % self.docdir

    ml = inspect.getmembers( self, predicate=inspect.ismethod ) 
    ok = True
    for tag,m in ml:
      if tag[:3] == '_ch':
        try:
          self.ok = False
          m()
          ok &= self.ok
        except:
          print 'Failed to complete check %s' % tag
    if ok:
      print '%s: All checks passed' % lab
    else: 
      print '%s: Errors detected' % lab
       
class check1(checkbase):
  def _ch01_importDreq(self):
    import dreq
    print 'Dreq software import checked'
    self.ok = True

  def _ch02_importSample(self):
    import dreq
    rq = dreq.loadDreq( dreqXML=self.sampleXml,configdoc=self.defnXml )
    print 'Dreq sample load checked'
    self.ok = True

class check2(checkbase):

  def _clear_ch03(self):
    os.unlink( '.simpleCheck_check2_err.txt' )
    os.unlink( '.simpleCheck_check2.txt' )

  def _ch03_checkXML(self):
    import os
    os.popen( 'which xmllint 2> .simpleCheck_check2_err.txt 1>.simpleCheck_check2.txt' ).readlines()
    ii = open( '.simpleCheck_check2_err.txt' ).readlines()
    if len(ii) > 0:
      print 'WARNING[001]: failed to detect xmllint command line program'
      print 'optional checks omitted'
      self.ok = False
      self._clear_ch03()
      return
    ii = open( '.simpleCheck_check2.txt' ).readlines()
    if len(ii) < 1:
      print 'WARNING[002]: failed to detect xmllint command line program'
      print 'optional checks omitted'
      self.ok = False
      self._clear_ch03()
      return

    cmd = 'xmllint --noout --schema %s %s  2> .simpleCheck_check2_err.txt 1>.simpleCheck_check2.txt' % (self.schema,self.sampleXml) 
    os.popen( cmd ).readlines()
    ii = open( '.simpleCheck_check2_err.txt' ).readlines()
    if len(ii) == 0:
      print 'WARNING[003]: Failed to capture xmllint response'
      print cmd
      self.ok = False
      self._clear_ch03()
      return
    if string.find(ii[0],'validates') != -1:
      print 'Sample XML validated'
      self.ok = True
      self._clear_ch03()
    else:
      print 'Sample XML failed to validate'
      print cmd
      self.ok = False
    return
    
all &= check1('Suite 1 (dreq module)').ok
all &= check2('Suite 2 (xmllint)').ok

if all:
  print 'ALL CHECK PASSED'
