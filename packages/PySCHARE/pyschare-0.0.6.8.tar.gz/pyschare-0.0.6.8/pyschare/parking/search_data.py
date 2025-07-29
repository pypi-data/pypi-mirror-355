import os
import ipywidgets as wd
import pandas as pd
import re
from IPython.display import display

from .constants import search_helper_text, MAIN_TITLE, FPATH, DPATH, DICTPATH
from .create_widgets import create_helper, create_select_dropdown, create_button
from .styles import get_styles, button_style
from .data_functions import get_data_dir, get_search_table_info


class _Search:
    def __init__(self):
        # self.dir_path = os.path.dirname(__file__)
        # self.csv_path = get_main_table_path()
        self.dataset_info = get_search_table_info()
        self.data_directory = get_data_dir()
        self.search_helper = create_helper(text=search_helper_text, helper_name='search')
        self.styles = get_styles()

        self.dataset_select = create_select_dropdown(options=["None"] + self.dataset_info[MAIN_TITLE].tolist(),
                                                     box_name='dataset', value='None')

        self.search_area = wd.Textarea(value='', placeholder='Type at least 3 characters',
                                       layout=wd.Layout(grid_area='search_text_box', width='90%',
                                                        background_color='white', border='1px solid #ababab'),
                                       disabled=False)

        self.search_button = create_button(text='Search', box_name='search',
                                           style={**button_style, 'button_color': 'blue'})
        self.save_button = create_button(text='Save Table', box_name='save',
                                         style={**button_style, 'button_color': 'green'})
        self.clear_button = create_button(text='Clear Table', box_name='clear',
                                          style={**button_style, 'button_color': 'red'})

        self.dataset_label = wd.Label(value='Datasets', layout=wd.Layout(grid_area='dataset_label_box'))
        self.search_label = wd.Label(value='Search', layout=wd.Layout(grid_area='search_label_box'))
        self.table_display = wd.HTML(value="")
        self.error_output = wd.Output()

        self.save_button.on_click(self.save_filtered_table)
        self.clear_button.on_click(self.clear_output)
        self.search_button.on_click(self.on_search_clicked)
        self.save_output = wd.Output(layout=wd.Layout(width='100%'))
        self.dataset_select.observe(self.on_dataset_change, 'value')

        self.error_output.layout.grid_area = 'error_output_box'

        self.search_grid_layout = wd.GridBox(
            children=[self.search_helper, self.dataset_label, self.dataset_select,
                      self.search_area, self.search_label, self.search_button, self.save_output, self.save_button,
                      self.clear_button, self.error_output],
            layout=wd.Layout(grid_template_columns='40% 15% 30% 15%',
                             grid_template_rows='auto',
                             display='grid',
                             grid_template_areas='''
                                     "search_helper_box search_helper_box  search_helper_box search_helper_box"
                                    "dataset_label_box search_label_box . ."
                                     "dataset_select_box  search_text_box  search_text_box search_text_box "
                                    "dataset_select_box  . search_button_box ."
                                     "dataset_select_box  . save_button_box ."
                                      "dataset_select_box  . clear_button_box ."
                                       "dataset_select_box  . error_output_box ."
                                      "save_output_box  save_output_box save_output_box save_output_box"
                                    ''',
                             grid_gap='5px',
                             width='98%'
                             ))
        display(wd.VBox([self.search_grid_layout, self.table_display]))

    def generate_variable_table(self, df):
        html_content = f"""<html> <table style="{self.styles['table']}">
            <tr><th style="{self.styles['first_column']}">Variables</th>
            <th style="{self.styles['second_column']}">Descriptions</th>
            </tr>
        """
        for _, row in df.iterrows():
            html_content += f"""<tr><td style="{self.styles['first_cell']}">{row.iloc[0]}</td>
                <td style="{self.styles['second_cell']}">{row.iloc[1]}</td></tr>
            """
        html_content += "</table></html>"

        with open("variables.html", 'w') as file:
            file.write(html_content)
        return html_content

    def generate_combined_table(self, df):
        html_content = f"""
        <html><table style="{self.styles['table']}">
            <tr><th style="{self.styles['first_column']}">Dataset</th>
            <th style="{self.styles['second_column']}">Variables</th>
            <th style="{self.styles['third_column']}">Description</th>
            </tr>"""

        for _, row in df.iterrows():
            html_content += f"""
            <tr><td style="{self.styles['first_cell']}">{row.iloc[0]}</td>
            <td style="{self.styles['first_cell']}">{row.iloc[1]}</td>
            <td style="{self.styles['second_cell']}">{row.iloc[2]}</td>
            </tr>"""
        html_content += "</table></html>"

        with open("combined_table.html", 'w') as file:
            file.write(html_content)
        return html_content

    def update_table(self, search_text):
        pattern = ".*" + re.escape(search_text) + ".*" if search_text else ".*"

        if self.dataset_select.value == "None":
            data_list = []
            for idx, ds in self.dataset_info.iterrows():
                ds_title = str(ds[MAIN_TITLE])
                # file_name = str(ds[FPATH])
                # file_path = os.path.join(self.data_directory, file_name)
                file_path = str(ds[DICTPATH])
                try:
                    df = pd.read_csv(file_path)
                    if 'Variable' in df.columns and 'Description' in df.columns:
                        temp_df = df[['Variable', 'Description']]
                        temp_df.columns = ['Variable Name', 'Description']

                        filtered_df = temp_df[
                            temp_df['Variable Name'].str.contains(pattern, case=False, na=False, regex=True) |
                            temp_df['Description'].str.contains(pattern, case=False, na=False, regex=True)
                            ]
                        if not filtered_df.empty:
                            filtered_df.insert(0, 'Dataset', ds_title)
                            data_list.append(filtered_df)
                    else:
                        # print(f"Dataset {ds_title} does not have required columns.")
                        print("")
                except Exception as e:
                    # print(f"Error loading dataset {ds_title}: {e}")
                    print("")
            if data_list:
                combined_df = pd.concat(data_list, ignore_index=True)
            else:
                combined_df = pd.DataFrame(columns=['Dataset', 'Variable Name', 'Description'])

            var_html = self.generate_combined_table(combined_df)
            self.table_display.value = var_html
        else:
            file_info = self.dataset_info.loc[
                self.dataset_info[MAIN_TITLE] == self.dataset_select.value, FPATH]
            if not file_info.empty:
                file_name = file_info.values[0]
                file_path = os.path.join(self.data_directory, file_name)

                try:
                    df = pd.read_csv(str(file_path))
                    if 'Variable' in df.columns and 'Description' in df.columns:
                        temp_df = df[['Variable', 'Description']].copy()
                        temp_df.columns = ['Variable Name', 'Description']

                        filtered = temp_df[
                            temp_df['Variable Name'].str.contains(pattern, case=False, na=False, regex=True) |
                            temp_df['Description'].str.contains(pattern, case=False, na=False, regex=True)
                            ]
                        if not filtered.empty:
                            var_html = self.generate_variable_table(filtered)
                            self.table_display.value = var_html
                        else:
                            # self.table_display.value = "No matching records found."
                            self.table_display.value = ""

                    else:
                        # self.table_display.value = "Error: Dataset does not have required columns."
                        self.table_display.value = ""
                except Exception as e:
                    # self.table_display.value = f"Error loading dataset: {e}"
                    self.table_display.value = ""
            else:
                # self.table_display.value = "Error: Dataset not found in MainTableDatasets.csv."
                self.table_display.value = ""

    def on_dataset_change(self, change):
        if change['type'] == 'change' and change['name'] == 'value':
            self.update_table(self.search_area.value)

    def on_search_clicked(self, b):
        self.error_output.clear_output()
        self.update_table(self.search_area.value)

    def save_filtered_table(self, _):
        try:
            if not self.table_display.value.strip():
                with self.save_output:
                    self.save_output.clear_output()
                    print("No data to save")
            else:
                if self.dataset_select.value == "None":
                    filename = f"Datasets_with_{self.search_area.value}.html"
                else:
                    filename = f"{self.dataset_select.value}_{self.search_area.value}.html"
                with open(filename, "w", encoding="utf-8") as file:
                    file.write(self.table_display.value)

                with self.save_output:
                    self.save_output.clear_output()
                    print(f"Table saved as '{filename}'.")

        except Exception as e:
            with self.save_output:
                self.save_output.clear_output()
                # print(f"Error saving file: {e}")
                print("")

    def clear_output(self, b):
        self.table_display.value = ""
        self.save_output.clear_output()
        self.error_output.clear_output()
        self.dataset_select.value = 'None'
        self.search_area.value = ''


def data_search():
    search = _Search()
    return search

data_search()