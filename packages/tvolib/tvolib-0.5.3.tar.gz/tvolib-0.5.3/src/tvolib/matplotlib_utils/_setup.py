__all__ = ["_setup_matplotlib"]

import atexit
import os
import shutil
import logging
import tempfile
from importlib.resources import files

import matplotlib as mpl
import matplotlib.pyplot as plt

_latex_binary = shutil.which("latex")
_stylesheet = files("tvolib.matplotlib_utils") / "data" / "tvolib.mplstyle"


def _setup_matplotlib(use_tex=False, cache_tex=False):
    r"""
    Configure matplotlib with custom stylesheet and settings

    Parameter
    ---------
    use_tex: bool
        Enable latex if toggled and a binary is found in the system path
    cache_tex: bool
        Configure caching behavior of matplotlib for latex outputs.
        Recommended for multiprocessing
    """

    logging.info("Using tvolib stylesheet")
    plt.style.use(_stylesheet)
    plt.rc("text", usetex=use_tex and _latex_binary is not None)

    if cache_tex:
        # Quick fix for matplotlib's tex cache in multiprocessing
        mpldir = tempfile.mkdtemp()
        atexit.register(shutil.rmtree, mpldir)
        umask = os.umask(0)
        os.umask(umask)
        os.chmod(mpldir, 0o777 & ~umask)
        os.environ["HOME"] = mpldir
        os.environ["MPLCONFIGDIR"] = mpldir

        class TexManager(mpl.texmanager.TexManager):
            texcache = os.path.join(mpldir, "tex.cache")

        mpl.texmanager.TexManager = TexManager
