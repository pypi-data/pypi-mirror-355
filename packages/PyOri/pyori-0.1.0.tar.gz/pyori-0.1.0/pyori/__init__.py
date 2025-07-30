#import pyori.animator
#import pyori.axioms
from pyori.convert import fold_to_svg #, convert_svg_to_fold
import pyori.fold
from pyori.foldfile import FoldFile
from pyori.geometry import distance, midpoint, vector, normalize, angle_between
from pyori.graph import Graph
'''import pyori.layer
import pyori.layout'''
import pyori.save
import pyori.svg
#import pyori.utils
import pyori.veiwer
#import pyori.vertex

#what should be imported when: from PACKAGENAME import *
__all__ = [#'animator', 
           #'axioms', 
           'convert', 'fold_to_svg', #'convert_svg_to_fold',
           'fold', 
           'FoldFile',
           'geometry', 'distance', 'midpoint', 'vector', 'normalize', 'angle_between'
           'Graph',
           #'layer',
           #'layout',
           'save',
           'svg',
           #'utils',
           'veiwer',
           #'vertex',
           ]