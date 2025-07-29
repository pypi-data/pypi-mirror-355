import pandas as pd
import ipywidgets as wd
from IPython.display import display, HTML, clear_output
import dictionary.data.access_data as dt
import os
import re


# styles
def get_styles():
    styles = {
        "table": "width: 100%; border-spacing: 0; border-bottom: 1px solid black;",
        "stats_header": "text-align: center; border-spacing: 0; border-bottom: 1px solid black; background-color: white; font-family: Helvetica, Neue; font-weight: bold; word-break:break-all;",
        "label": "text-align: left; font-weight: bold; font-size: 12px;  font-family: Helvetica, Neue",
        "helper": "text-align: left; font-size: 14px;margin-left: 5px; margin-right: 5px;font-family: Helvetica, Neue",
        "first_column": "background-color: #FFFFFF; text-align: left; width: 25%; font-size: 12px; font-weight: bold; font-family: Tahoma, Verdana, serif; border-bottom: 3px solid black;",
        "second_column": "background-color: #FFFFFF; text-align: left; width: 25%; font-size: 12px; font-family: Tahoma, Verdana, serif; border-bottom: 3px solid black;",
        "third_column": "background-color: #FFFFFF; text-align: right; font-size: 12px; font-family: Tahoma, Verdana, serif; border-bottom: 3px solid black;",
        "first_cell": "background-color: #FFFFFF; text-align: left; border-spacing: 0; border-bottom: 1px solid black;font-size: 12px; font-family:Tahoma, Verdana; word-break:break-all;",
        "second_cell": "background-color: #FFFFFF; text-align: right; border-spacing: 0;  border-bottom: 1px solid black;font-size: 12px; font-family: Tahoma, Verdana; word-break:break-all;"
    }
    return styles


style_base = {'font_size': '12px', 'text_color': 'black', 'background': 'rgb(247, 247, 247)'}
button_style = {'font_size': '12px', 'text_color': 'white', 'font_weight': 'bold',
                'font_family': ' Tahoma, Verdana,sans-serif', 'text_align': 'center'}

search_helper_text = f"""<p>This widget allows you to search for variables and descriptions across multiple datasets. Follow these instructions to effectively use the search functionality:
        <li><strong>If you want to search within a specific dataset:</strong> Use the "Datasets" dropdown menu to select the dataset you wish to search. Scroll down to see the list of available datasets and select your choice.
        </li><li><strong>If you want to search across all datasets:</strong>Leave the "Datasets" dropdown set to "None". This is the default option.
        </li>In the text box, type the word or phrase you want to search for and click the "Search" button. Note: You need to enter at least 3 characters for the search to function.</p>
        <p><strong>Search Results:</strong> The widget will display a table below the search box, showing the search results.
        <li><strong>If a specific dataset was selected:</strong> The table will show the variables and descriptions from that dataset that match your search terms.
        </li><li><strong>If "None" was selected:</strong> The table will show results from all datasets that match your search terms, including the dataset name, variable name, and description.
        </li></p><p><strong>Save Table:</strong> If you want to save the search results as an HTML file, click the "Save Table" button.
        <li><strong>If a specific dataset was selected:</strong> The file will be named using the dataset name and the search terms (e.g., "Food Security Data 2021_searchterm.html").
        </li><li><strong>If "None" was selected:</strong> The file will be named using "Datasets" and the search terms (e.g., "Datasets_with_searchterm.html").
        </li>A confirmation message will appear below the "Save Table" button, indicating the file name and location.</p>"""


def create_helper(text, helper_name, writing_style=None):
    if writing_style is None:
        writing_style = get_styles().get('helper', '')
    helper = wd.HTML(value=f"""<div style="{writing_style}"><p>{text}</p></div>""",
                     layout=wd.Layout(grid_area=f'{helper_name}_helper_box', border='1px solid gray', width='96%',
                                      justify='center'),
                     style={**style_base, 'word_break': 'break_all', 'padding': '3px'}, disabled=False)
    return helper


def create_select_dropdown(options=None, box_name=None, value=None):
    select_dropdown = wd.Select(
        options=options, disabled=False, rows=10, value=value,
        layout=wd.Layout(grid_area=f'{box_name}_select_box', width='100%',
                         background_color='white', border='1px solid #ababab'))
    return select_dropdown


def create_label(text, writing_style=None):
    lower_text = text.lower()
    label = wd.HTML(value=f"""<div style="{writing_style}"><p>{text}</p></div>""",
                    disabled=False,
                    layout=wd.Layout(grid_area=f'{lower_text}_label_box', width='100%', border='1px solid #ababab'),
                    style={**style_base, 'border': '1px solid #ababab'})
    return label


def create_button(text, box_name, style):
    button = wd.Button(description=f'{text}', style=style,
                       layout=wd.Layout(grid_area=f'{box_name}_button_box', width='100%'))
    return button


def search_data():
    dir_path = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(dir_path, 'data', 'MainTableDatasets.csv')
    dataset_info = dt.get_data(csv_path)
    data_directory = os.path.join(dir_path, 'data')
    search_helper = create_helper(text=search_helper_text, helper_name='search')
    styles = get_styles()
    table_output = wd.Output()
    dataset_select = create_select_dropdown(options=["None"] + dataset_info['dataset_title'].tolist(),
                                            box_name='dataset', value='None')

    search_area = wd.Textarea(value='', placeholder='Type at least 3 characters',
                              layout=wd.Layout(grid_area='search_text_box', width='90%',
                                               background_color='white', border='1px solid #ababab'), disabled=False)

    search_button = create_button(text='Search', box_name='search', style={**button_style, 'button_color': 'blue'})
    save_button = create_button(text='Save Table', box_name='save', style={**button_style, 'button_color': 'green'})
    clear_button = create_button(text='Clear Table', box_name='clear', style={**button_style, 'button_color': 'red'})

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

        with open("combined_table.html", 'w') as file:
            file.write(html_content)
        return html_content

    table_display = wd.HTML(value="")
    error_output = wd.Output()

    def update_table(search_text):
        pattern = ".*" + re.escape(search_text) + ".*" if search_text else ".*"

        if dataset_select.value == "None":
            data_list = []
            for idx, ds in dataset_info.iterrows():
                ds_title = ds['dataset_title']
                file_name = ds['file_name']
                file_path = os.path.join(data_directory, file_name)
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
                        print(f"Dataset {ds_title} does not have required columns.")
                except Exception as e:
                    print(f"Error loading dataset {ds_title}: {e}")
            if data_list:
                combined_df = pd.concat(data_list, ignore_index=True)
            else:
                combined_df = pd.DataFrame(columns=['Dataset', 'Variable Name', 'Description'])

            var_html = generate_combined_table(combined_df)
            table_display.value = var_html
        else:

            file_info = dataset_info.loc[dataset_info['dataset_title'] == dataset_select.value, 'file_name']
            if not file_info.empty:
                file_name = file_info.values[0]
                file_path = os.path.join(data_directory, file_name)

                try:
                    df = pd.read_csv(file_path)
                    if 'Variable' in df.columns and 'Description' in df.columns:
                        temp_df = df[['Variable', 'Description']].copy()
                        temp_df.columns = ['Variable Name', 'Description']

                        filtered = temp_df[
                            temp_df['Variable Name'].str.contains(pattern, case=False, na=False, regex=True) |
                            temp_df['Description'].str.contains(pattern, case=False, na=False, regex=True)
                            ]
                        if not filtered.empty:
                            var_html = generate_variable_table(filtered)
                            table_display.value = var_html
                        else:
                            table_display.value = "No matching records found."
                    else:
                        table_display.value = "Error: Dataset does not have required columns."
                except Exception as e:
                    table_display.value = f"Error loading dataset: {e}"
            else:
                table_display.value = "Error: Dataset not found in MainTableDatasets.csv."

    def on_dataset_change(change):
        if change['type'] == 'change' and change['name'] == 'value':
            update_table(search_area.value)

    dataset_select.observe(on_dataset_change, 'value')

    def on_search_clicked(b):
        error_output.clear_output()
        update_table(search_area.value)

    search_button.on_click(on_search_clicked)
    save_output = wd.Output(layout=wd.Layout(width='100%'))

    def save_filtered_table(_):
        try:
            if not table_display.value.strip():
                with save_output:
                    save_output.clear_output()
                    print("No data to save")
            else:
                if dataset_select.value == "None":
                    filename = f"Datasets_with_{search_area.value}.html"
                else:
                    filename = f"{dataset_select.value}_{search_area.value}.html"
                with open(filename, "w", encoding="utf-8") as file:
                    file.write(table_display.value)

                with save_output:
                    save_output.clear_output()
                    print(f"Table saved as '{filename}'.")

        except Exception as e:
            with save_output:
                save_output.clear_output()
                print(f"Error saving file: {e}")

    def clear_output(b):
        table_display.value = ""
        save_output.clear_output()
        error_output.clear_output()
        dataset_select.value = 'None'
        search_area.value = ''

    save_button.on_click(save_filtered_table)
    clear_button.on_click(clear_output)

    error_output.layout.grid_area = 'error_output_box'

    dataset_label = wd.Label(value='Datasets', layout=wd.Layout(grid_area='dataset_label_box'))
    search_label = wd.Label(value='Search', layout=wd.Layout(grid_area='search_label_box'))

    search_grid_layout = wd.GridBox(
        children=[search_helper, dataset_label, dataset_select,
                  search_area, search_label, search_button, save_output, save_button,
                  clear_button, error_output],
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
    display(wd.VBox([search_grid_layout, table_display]))


search_data()