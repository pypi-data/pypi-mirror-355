from .create_labels import get_facts, get_meta, get_provenance, get_dictionary, get_data_summary, \
    get_summary_stats, get_show_barplots, get_show_pairplots, get_show_correlations

def labels():
    get_facts()
    get_meta()
    get_provenance()
    get_dictionary()
    get_data_summary()
    get_summary_stats()
    get_show_barplots()
    get_show_pairplots()
    get_show_correlations()

labels()
