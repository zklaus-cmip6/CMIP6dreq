"""
Entry point for command line usage -- see ccinit for usage information.
"""

import scope, sys

def main_entry():
  """
   Wrapper for use with setuptools.
  """
  if len(sys.argv) == 1:
      # Show command-line info and report that you must provide arguments
      print( scope.dreqUI.__doc__ )
      print( "\nERROR: Please provide command-line arguments." )
      return

  if sys.argv[1] == '-v':
      from packageConfig import __version__, __versionComment__
      print( 'dreqPy version %s [%s]' % (__version__,__versionComment__) )
  elif sys.argv[1] == '--unitTest':
      print( "Starting test suite 1" )
      import simpleCheck
      print( "Starting test suite 2" )
      import examples.ex203
      print( "Tests completed" )
  else:
     x = scope.dreqUI(sys.argv[1:])
     x.run()

if __name__ == '__main__':
  main_entry()
