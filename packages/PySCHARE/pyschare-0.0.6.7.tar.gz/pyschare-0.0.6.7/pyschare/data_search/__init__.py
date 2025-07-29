from .search import _DataSearch


def _init_data_search():
    global search
    search = _DataSearch()

_init_data_search()