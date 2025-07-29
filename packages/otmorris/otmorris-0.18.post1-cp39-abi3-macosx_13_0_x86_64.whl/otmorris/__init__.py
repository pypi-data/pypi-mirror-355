"""
    otmorris --- An OpenTURNS module
    ================================

    Contents
    --------
      'otmorris' is a module for OpenTURNS, which enables to compute the
      elementary effects using the screening Morris method

"""

# flake8: noqa

# ensures swig type tables order & dll load
import openturns as _ot

from .otmorris import *

__version__ = '0.18.post1'
