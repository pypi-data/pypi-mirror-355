from .gemini_data_search import _GeminiDataSearch


def _init_gemini_search():
    global gemini_search
    gemini_search = _GeminiDataSearch()

_init_gemini_search()