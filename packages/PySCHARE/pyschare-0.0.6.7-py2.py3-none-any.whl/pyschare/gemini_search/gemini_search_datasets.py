import os
import pandas as pd
import re
import warnings
import ipywidgets as wd

warnings.filterwarnings("ignore")
from pyschare.helpers.constants import MAIN_TITLE, FILEPATH

from pyschare.helpers.styles import get_styles
from pyschare.helpers.data_functions import get_data_dir, get_main_table_info



styles = get_styles()


def generate_variable_table(df):
    html_content = f"""<html> <table style="{styles['table']}">
        <tr><th style="{styles['first_column']}">Variables</th>
        <th style="{styles['second_column']}">Descriptions</th>
        </tr>
    """
    for _, row in df.iterrows():
        html_content += f"""<tr><td style="{styles['first_cell']}">{row.iloc[0]}</td>
            <td style="{styles['second_cell']}">{row.iloc[1]}</td></tr>
        """
    html_content += "</table></html>"
    return html_content


def generate_combined_table(df):
    html_content = f"""
    <html><table style="{styles['table']}">
        <tr><th style="{styles['first_column']}">Dataset</th>
        <th style="{styles['second_column']}">Variables</th>
        <th style="{styles['third_column']}">Description</th>
        </tr>"""

    for _, row in df.iterrows():
        html_content += f"""
        <tr><td style="{styles['first_cell']}">{row.iloc[0]}</td>
        <td style="{styles['first_cell']}">{row.iloc[1]}</td>
        <td style="{styles['second_cell']}">{row.iloc[2]}</td>
        </tr>"""
    html_content += "</table></html>"
    return html_content


class _DataSearch:
    def __init__(self):
        self.dataset_info = get_main_table_info()
        self.data_directory = get_data_dir()

    def update_table(self, search_text):
        error_messages = []
        search_words = search_text.strip().split() if search_text and search_text.strip() else []

        data_list = []
        for idx, ds in self.dataset_info.iterrows():
            ds_title = ds[MAIN_TITLE]
            file_name = ds[FILEPATH]
            file_path = os.path.join(self.data_directory, file_name)

            try:
                df = None
                try:
                    df = pd.read_csv(str(file_path))
                except FileNotFoundError:
                    error_messages.append(f"ERROR: File not found for '{ds_title}': {file_path}")
                    continue
                except UnicodeDecodeError:
                    try:
                        df = pd.read_csv(str(file_path), encoding='latin-1')
                        error_messages.append(f"INFO: Read '{ds_title}' with latin-1 encoding.")  # Changed to INFO
                    except Exception as e_enc:
                        error_messages.append(
                            f"ERROR: Failed to read '{ds_title}' with multiple encodings: {e_enc}")
                        continue
                except pd.errors.EmptyDataError:
                    error_messages.append(f"WARNING: File for '{ds_title}' is empty or unparseable.")
                    continue
                except Exception as e_read:
                    error_messages.append(f"ERROR: Reading file for '{ds_title}': {e_read}")
                    continue

                if df is None or df.empty:
                    continue

                df.columns = df.columns.str.strip()

                variable_col = 'Variable'
                description_col = 'Description'
                if not (variable_col in df.columns and description_col in df.columns):
                    found_var = False
                    found_desc = False
                    for col in df.columns:
                        if col.lower() == 'variable':
                            variable_col = col
                            found_var = True
                        if col.lower() == 'description':
                            description_col = col
                            found_desc = True
                    if not (found_var and found_desc):
                        error_messages.append(
                            f"WARNING: Dataset '{ds_title}' skipped - missing required columns (looked for '{variable_col}', '{description_col}').")
                        continue

                temp_df = df[[variable_col, description_col]].copy()
                temp_df.columns = ['Variable Name', 'Description']  # Standard names

                try:
                    temp_df['Variable Name'] = temp_df['Variable Name'].astype(str).fillna('')
                    temp_df['Description'] = temp_df['Description'].astype(str).fillna('')
                except Exception as e_conv:
                    error_messages.append(
                        f"WARNING: Could not convert columns to string for '{ds_title}': {e_conv}. Skipping filtering for this file.")
                    continue

                if not search_words:
                    filtered_df = temp_df
                else:
                    final_mask = pd.Series([True] * len(temp_df), index=temp_df.index)
                    for word in search_words:
                        escaped_word = re.escape(word)
                        try:
                            word_mask = (
                                    temp_df['Variable Name'].str.contains(escaped_word, case=False, na=False,
                                                                          regex=True) |
                                    temp_df['Description'].str.contains(escaped_word, case=False, na=False, regex=True)
                            )
                            final_mask &= word_mask
                        except Exception as e_filter:
                            error_messages.append(
                                f"WARNING: Error during filtering for word '{word}' in '{ds_title}': {e_filter}. Skipping word.")

                    filtered_df = temp_df[final_mask]

                if not filtered_df.empty:
                    filtered_df.insert(0, 'Dataset', ds_title)
                    data_list.append(filtered_df)

            except Exception as e_proc:
                error_messages.append(f"ERROR: Processing dataset '{ds_title}': {e_proc}")

        combined_df_for_term = pd.DataFrame()
        if data_list:
            try:
                combined_df_for_term = pd.concat(data_list, ignore_index=True)
            except Exception as e_concat:
                error_messages.append(f"ERROR: Failed to combine results for search term '{search_text}': {e_concat}")

        return combined_df_for_term, error_messages