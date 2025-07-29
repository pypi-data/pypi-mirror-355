from .create_labels import _DataLabels

def _init_labels():
    global labels
    labels = _DataLabels()


_init_labels()
