# -*- coding: utf-8 -*-
import os
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import rcParams
import warnings
from importlib.metadata import version, PackageNotFoundError
warnings.simplefilter('ignore')
import smplotlib

__name__ = 'smplotlib'
__author__ = ['Jiaxuan Li']

# Version
try:
    __version__ = version(__name__)
except PackageNotFoundError:
    # package is not installed
    pass

# Load font
pkg_path = smplotlib.__path__[0]
import matplotlib.font_manager as font_manager
for font in font_manager.findSystemFonts(pkg_path):
    font_manager.fontManager.addfont(font)
assert 'Hershey' in font_manager.findfont('AVHershey Complex'), "Hershey font is not found"

# Load style
plt.style.use(os.path.join(pkg_path, 'smplot.mplstyle'))

def set_style(usetex=False, fontsize=15, fontweight='normal', figsize=(6, 6), dpi=120, edgecolor='black'):
    '''
    Set matplotlib parameters for SuperMongo style.
    
    Parameters
    ----------
    usetex : bool, optional.
        Whether to use LaTeX to render the text. Default is False.
        The current font does not really support LaTeX.
    fontsize : int, optional.
        Font size. Default is 15.
    fontweight : str, optional.
        Font weight. Default is 'normal'. It can be 'normal' or 'light'.
        The current font does not really support 'light'.
    figsize : tuple, optional.
        Figure size. Default is (6, 6).
    dpi : int, optional.
        Dots per inch. Default is 100.
    edgecolor : str, optional.
        Edge color. Default is 'black'. If you don't like the black edge, you can set it to 'face'.
    '''
    rcParams.update({'font.size': fontsize,
                     'figure.figsize': "{0}, {1}".format(figsize[0], figsize[1]),
                     'text.usetex': usetex,
                     'figure.dpi': dpi})

    if fontweight == 'normal':
        rcParams.update({
            "font.weight": "normal",
            "axes.labelweight": "normal",
            "mathtext.fontset": "custom",
            "mathtext.bf": "AVHershey Complex:medium",
            "mathtext.cal": "AVHershey Complex:medium",
            "mathtext.it": "AVHershey Complex:italic",
            "mathtext.rm": "AVHershey Complex:medium",
            "mathtext.sf": "AVHershey Duplex:medium",
            "mathtext.tt": "AVHershey Complex:medium",
            "mathtext.fallback": "cm",
            "mathtext.default": 'it'
        })
        
    elif fontweight == 'light':
        rcParams.update({
            "axes.linewidth": 0.7,
            "xtick.major.width": 0.6,
            "xtick.minor.width": 0.5,
            "ytick.major.width": 0.6,
            "ytick.minor.width": 0.5,
            "font.weight": "light",
            "axes.labelweight": "light",
            "mathtext.fontset": "custom",
            "mathtext.bf": "AVHershey Complex:medium",
            "mathtext.cal": "AVHershey Complex:light",
            "mathtext.it": "AVHershey Complex:light:italic",
            "mathtext.rm": "AVHershey Complex:light",
            "mathtext.sf": "AVHershey Duplex:light",
            "mathtext.tt": "AVHershey Complex:light",
            "mathtext.fallback": "cm",
            "mathtext.default": 'it'
        })
        if usetex is True:
            rcParams.update({
                "text.latex.preamble": '\n'.join([
                    '\\usepackage{amsmath}'
                    '\\usepackage[T1]{fontenc}',
                    '\\usepackage{courier}',
                    '\\usepackage[variablett]{lmodern}',
                    '\\usepackage[LGRgreek]{mathastext}',
                    '\\renewcommand{\\rmdefault}{\\ttdefault}'
                ])
            })
    elif fontweight == 'heavy':
        rcParams.update({
            "axes.linewidth": 0.7,
            "font.weight": "heavy",
            "axes.labelweight": "heavy",
            "mathtext.fontset": "custom",
            "mathtext.bf": "AVHershey Complex:heavy",
            "mathtext.cal": "AVHershey Complex:heavy",
            "mathtext.it": "AVHershey Complex:heavy:italic",
            "mathtext.rm": "AVHershey Complex:heavy",
            "mathtext.sf": "AVHershey Duplex:heavy",
            "mathtext.tt": "AVHershey Simplex:heavy",
            "mathtext.fallback": "cm",
            "mathtext.default": 'it'
        })
        if usetex is True:
            rcParams.update({
                "text.latex.preamble": '\n'.join([
                    '\\usepackage{amsmath}'
                    '\\usepackage[T1]{fontenc}',
                    '\\usepackage{courier}',
                    '\\usepackage[variablett]{lmodern}',
                    '\\usepackage[LGRgreek]{mathastext}',
                    '\\renewcommand{\\rmdefault}{\\ttdefault}'
                ])
            })
            
    rcParams.update({'scatter.edgecolors': edgecolor})
smplotlib.set_style()

from .demo import demo_plot