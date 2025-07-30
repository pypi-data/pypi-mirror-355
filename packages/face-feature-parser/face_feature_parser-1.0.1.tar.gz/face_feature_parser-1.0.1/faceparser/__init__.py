"""
FaceParser - A Python library for face parsing and feature extraction
"""

from .model import FaceParser, get_coordinates
from .coordinates import FaceCoordinates
from .cli import cli

__version__ = '1.0.0'
__author__ = 'Jayesh J. Pandey'
__email__ = 'pandeyjayesh020@gmail.com'

__all__ = [
    'FaceParser',
    'get_coordinates',
    'FaceCoordinates',
    'cli'
]
