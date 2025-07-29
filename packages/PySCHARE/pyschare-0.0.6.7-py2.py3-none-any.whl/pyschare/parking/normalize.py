import re
import pandas as pd

def process_tsv_file():
    df = pd.read_csv('A_MainTableDatasets.tsv', sep="\t")
    return df

def normalize_dataset_names():
    df = process_tsv_file()
    names = df['entity:A_MainTableDatasets_id']
    new_names = []
    normalize_text(names, new_names)
    df['main_table_dataset_id'] = new_names
    return df


def normalize_text(names, normalized_names):
    for name in names:
        year_match = re.search(r'(\d{4})', name)
        year = year_match.group(1) if year_match else ""
        name_without_year = re.sub(r'(\d{4})', '', name)
        name_split = re.sub(r'(?<!_)([A-Z][a-z])', r'_\1', name_without_year)
        name_split = re.sub(r'([a-z])([A-Z])', r'\1_\2', name_split)
        name_split = re.sub(r'[-\s]+', '_', name_split)
        name_split = re.sub(r'_+', '_', name_split).strip('_')
        normalized_name = f"{name_split}_{year}" if year else name_split
        normalized_names.append(normalized_name.lower())
