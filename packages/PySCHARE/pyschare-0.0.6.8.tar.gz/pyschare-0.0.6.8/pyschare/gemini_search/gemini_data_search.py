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
def generate_variable_table( df):
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

    with open("variables.html", 'w') as file:
        file.write(html_content)
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
    #
    # with open("combined_table.html", 'w', encoding='utf-8') as file:
    #     file.write(html_content)
    return html_content

class _GeminiDataSearch:
    def __init__(self):
        self.dataset_info = get_main_table_info()
        self.data_directory = get_data_dir()
        self.table_display = wd.HTML(value="")


    def update_table(self, search_text):
        error_messages = []
        result_html = None
        search_words = search_text.strip().split() if search_text and search_text.strip() else []
        data_list = []
        for idx, ds in self.dataset_info.iterrows():
            ds_title = ds[MAIN_TITLE]
            file_name = ds[FILEPATH]
            file_path = os.path.join(self.data_directory, file_name)

            try:
                df = pd.read_csv(str(file_path))
            except FileNotFoundError:
                error_messages.append(f"ERROR: File not found for '{ds_title}': {file_path}")
                continue
            except UnicodeDecodeError:
                try:
                    df = pd.read_csv(str(file_path), encoding='latin-1')
                    error_messages.append(f"WARNING: Read '{ds_title}' with latin-1 encoding.")
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

            df.columns = df.columns.str.strip()

            if not ('Variable' in df.columns and 'Description' in df.columns):
                error_messages.append(
                    f"WARNING: Dataset '{ds_title}' skipped - missing 'Variable' or 'Description' column.")
                continue

            temp_df = df[['Variable', 'Description']].copy()
            temp_df.columns = ['Variable Name', 'Description']

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
                    word_mask = (
                            temp_df['Variable Name'].str.contains(escaped_word, case=False, na=False,
                                                                  regex=True) |
                            temp_df['Description'].str.contains(escaped_word, case=False, na=False,
                                                                regex=True)
                    )
                    final_mask &= word_mask
                filtered_df = temp_df[final_mask]

            if not filtered_df.empty:
                filtered_df.insert(0, 'Dataset', ds_title)
                data_list.append(filtered_df)

            if error_messages:
                print("Encountered issues while searching:")
                for msg in error_messages:
                    print(f"- {msg}")

        if data_list:
            try:
                combined_df = pd.concat(data_list, ignore_index=True)
                if not combined_df.empty:
                    var_html = generate_combined_table(combined_df)
                    self.table_display.value = var_html
                else:
                    self.table_display.value = "<p>No matching records found after combining.</p>"

            except Exception as e_concat:
                self.table_display.value = ""
                print(f"FATAL ERROR: Failed to combine results: {e_concat}")
        else:
            if not error_messages:
                self.table_display.value = "<p>No matching records found.</p>"
            else:
                self.table_display.value = "<p>Search incomplete due to errors. No matching records found in successfully processed files.</p>"

        return result_html, error_messages



