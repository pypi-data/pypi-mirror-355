from .new_visuals import _AdjustedVisuals

def _init_visuals():
    global new_plots
    new_plots = _AdjustedVisuals()


_init_visuals()