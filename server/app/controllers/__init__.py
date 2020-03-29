import glob
from os.path import dirname, basename, isfile, join

# Default export of all controllers in directory
# for one time import in routes.py.
# In this directory should be placed only Flask controllers.
modules = glob.glob(join(dirname(__file__), "*.py"))

__all__ = [ basename(f)[:-3] for f in modules if isfile(f) ]