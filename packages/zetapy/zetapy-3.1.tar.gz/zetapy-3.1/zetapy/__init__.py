from zetapy.main import zetatest, zetatest2, zetatstest, zetatstest2, ifr
from zetapy.plot_dependencies import plotzeta, plotzeta2, plottszeta, plottszeta2
from zetapy.legacy.main import getZeta, getIFR

try:
    import tkinter
except ImportError:
    raise ImportError("This package requires Tkinter. Please install it via your system's package manager or enable it in your Python installation.")

#from zetapy.msd import getMultiScaleDeriv
#from zetapy.dependencies import getPeak, getGumbel, getOnset, getTempOffset, flatten, calculatePeths