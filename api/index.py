import sys
from os.path import dirname, abspath

# Add project root to sys.path so app can be imported properly
sys.path.insert(0, dirname(dirname(abspath(__file__))))

from app import app
