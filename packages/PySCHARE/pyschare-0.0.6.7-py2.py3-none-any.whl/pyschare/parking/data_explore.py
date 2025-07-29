import ipywidgets as wd
from IPython.display import display, clear_output, HTML
import numpy as np

from .constants import data_explore_helper_text, MAIN_TITLE
from .data_functions import (select_data_options, get_dropdown_value,
                                     get_parsed_data, get_bucket, save_to_bucket, get_main_table_info)
from .create_widgets import (create_select_dropdown,
                                                      create_multiple_select_dropdown, create_label, create_button,
                                                      create_helper)

from .styles import get_styles, button_style


def calculate_categorical(df):
    styles = get_styles()
    html_content = f"""<tr>
                <th style="{styles['first_header']}">type</th>
                <th style="{styles['first_header']}">name</th>
                <th style="{styles['header']}">count</th>
                <th style="{styles['header']}">missing</th>
                <th style="{styles['header']}">unique</th>
                <th style="{styles['header']}">mostFreq</th>
                <th style="{styles['header']}">leastFreq</th>"""
    categorical_cols = df.select_dtypes(exclude=[np.number]).columns
    for col in categorical_cols:
        html_content += f"""<tr><td style="{styles['cell']}">Categorical</td>"""
        html_content += f"""<td style="{styles['stats_cell']}">{col}</td>"""
        count = df[col].count()
        html_content += f"""<td style="{styles['stats_cell']}">{count}</td>"""
        missing = df[col].isnull().sum()
        missing_pct = (missing / len(df[col])) * 100
        html_content += f"""<td style="{styles['stats_cell']}">{missing_pct:.2f}%</td>"""
        html_content += f"""<td style="{styles['stats_cell']}">{df[col].nunique()}</td>"""
        html_content += f"""<td style="{styles['stats_cell']}">{df[col].mode()[0] if not df[col].mode().empty else 'N/A'}</td>"""
        html_content += f"""<td style="{styles['stats_cell']}">{df[col].value_counts().idxmin() if not df[col].value_counts().empty else 'N/A'}</td></tr>"""

    return html_content


def calculate_numeric(df):
    styles = get_styles()
    html_content = f"""<tr>
                <th style="{styles['first_header']}">type</th>
                <th style="{styles['first_header']}">name</th>
                <th style="{styles['header']}">count</th>
                <th style="{styles['header']}">missing</th>
                <th style="{styles['header']}">min</th>
                <th style="{styles['header']}">median</th>
                <th style="{styles['header']}">max</th>
                <th style="{styles['header']}">mean</th>
                <th style="{styles['header']}">stdDeviation</th>
                <th style="{styles['header']}">zeros</th>"""
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        html_content += f"""<tr><td style="{styles['cell']}">Numeric</td>"""
        html_content += f"""<td style="{styles['stats_cell']}">{col}</td>"""
        count = df[col].count()
        html_content += f"""<td style="{styles['stats_cell']}">{count}</td>"""
        missing = df[col].isnull().sum()
        missing_pct = (missing / len(df[col])) * 100
        html_content += f"""<td style="{styles['stats_cell']}">{missing_pct:.2f}%</td>"""
        html_content += f"""<td style="{styles['stats_cell']}">{df[col].min():.2f}</td>"""
        html_content += f"""<td style="{styles['stats_cell']}">{df[col].median():.2f}</td>"""
        html_content += f"""<td style="{styles['stats_cell']}">{df[col].max():.2f}</td>"""
        html_content += f"""<td style="{styles['stats_cell']}">{df[col].mean():.2f}</td>"""
        html_content += f"""<td style="{styles['stats_cell']}">{df[col].std():.2f}</td>"""
        html_content += f"""<td style="{styles['stats_cell']}">{missing_pct:.2f}%</td>"""
    return html_content


class _Explore:
    def __init__(self):
        self.data_info = get_main_table_info()
        self.data_options = select_data_options(self.data_info)
        self.dataset_dropdown = create_select_dropdown(options=self.data_options, box_name='dataset')
        self.variable_dropdown = create_multiple_select_dropdown(options=[], box_name='variable')
        self.dataset_label = create_label(text='Dataset')
        self.variable_label = create_label(text='Variable')
        self.show_data_button = create_button(text='Show Data', box_name='show',
                                              style={**button_style, 'button_color': 'blue'})
        self.save_data_button = create_button(text='Save Data', box_name='save',
                                              style={**button_style, 'button_color': 'green'})
        self.clear_data_button = create_button(text='Clear Output', box_name='clear',
                                               style={**button_style, 'button_color': 'red'})
        self.describe_data_button = create_button(text='Describe Data', box_name='describe',
                                                  style={**button_style, 'button_color': 'darkblue'})
        self.describe_data_button.on_click(self.calculate_descriptive_stats)

        self.subset_helper = create_helper(text=data_explore_helper_text, helper_name='subset')
        self.show_data_output = wd.Output()
        self.describe_data_output = wd.Output()
        self.save_data_output = wd.Output(layout=wd.Layout(grid_area='save_output_box'))
        self.save_data_button.on_click(self.save_data)
        self.show_data_button.on_click(self.show_data)
        self.clear_data_button.on_click(self.clear_output)

        self.subset_grid_layout = wd.GridBox(
            children=[self.subset_helper, self.dataset_label, self.dataset_dropdown,
                      self.variable_dropdown, self.variable_label,
                      self.clear_data_button, self.describe_data_button, self.show_data_button, self.save_data_button,
                      self.save_data_output],
            layout=wd.Layout(display='grid',
                             grid_template_columns='40% 40% 20%',
                             grid_template_rows='repeat(8,auto)',
                             grid_template_areas='''
                                             "subset_helper_box subset_helper_box subset_helper_box"
                                             "subset_helper_box subset_helper_box  subset_helper_box"
                                              "dataset_label_box variable_label_box . "
                                              "dataset_select_box  variable_select_box clear_button_box"
                                              "dataset_select_box  variable_select_box   show_button_box"
                                              "dataset_select_box  variable_select_box   describe_button_box"
                                              "dataset_select_box  variable_select_box   save_button_box"
                                              " save_output_box save_output_box save_output_box"
                                           ''',

                             grid_gap='10px',
                             width='98%',
                             height='auto',
                             margin='5px',
                             overflow='hidden'))

        display(wd.VBox([self.subset_grid_layout, self.show_data_output, self.describe_data_output]))

        self.dataset_dropdown.observe(self.update_variable_options, names='value')

        self.input_data = self.data_info[self.data_info[MAIN_TITLE] == self.dataset_dropdown.value]

    def update_variable_options(self, change):
        input_data = self.get_dataset()

        if input_data is not None:
            self.variable_dropdown.options = input_data.columns.tolist()
            self.variable_dropdown.disabled = False
        else:
            self.variable_dropdown.options = []
            self.variable_dropdown.disabled = True

    #     def get_input(self):
    #         return self.dataset_dropdown.value

    def get_dataset(self):
        input_df = get_dropdown_value(self.dataset_dropdown)
        if input_df is not None:
            selected_data = self.data_info[self.data_info[MAIN_TITLE] == input_df]
            parsed_data = get_parsed_data(selected_data)
            return parsed_data
        else:
            return None

    def get_subset_data(self):
        parsed_data = self.get_dataset()
        #         parsed_data = new_data.to_csv(index= False)
        selected_variables = get_dropdown_value(self.variable_dropdown)
        if selected_variables:
            subset_data = parsed_data[list(selected_variables)]
        else:
            subset_data = parsed_data
        return subset_data

    def show_data(self, b):
        subset_data = self.get_subset_data()
        with self.show_data_output:
            self.show_data_output.clear_output(wait=True)
            if subset_data is not None:
                display(subset_data.head())
            else:
                print("No dataset selected. Please select a dataset.")

    def save_data(self, b):
        input_df = get_dropdown_value(self.dataset_dropdown)
        selected_data = self.data_info[self.data_info[MAIN_TITLE] == input_df]
        parsed_data = self.get_subset_data()
        if parsed_data is not None:
            my_bucket = get_bucket()
            dataset_name = selected_data.iloc[0]['file_name']
            bucket_path = f"{my_bucket}/subset_{dataset_name}"
            try:
                save_to_bucket(parsed_data, bucket_path)

                with self.save_data_output:
                    self.save_data_output.clear_output()
                    print(f"Saving data to: {bucket_path}")

            except Exception as e:
                with self.save_data_output:
                    self.save_data_output.clear_output()
                    print(f"Error saving data: {e}")

        else:
            with self.save_data_output:
                self.save_data_output.clear_output()
                print("No data to save. Please select a dataset first.")

    def calculate_descriptive_stats(self, b):
        dataset = self.get_subset_data()
        if dataset is not None:
            html_content = self.generate_html_stats(dataset)
            with self.describe_data_output:
                clear_output(wait=True)
                display(HTML(html_content))
        else:
            print("Failed to load data. Please check the dataset or file type.")

    def generate_html_stats(self, df):
        if df.empty:
            return "No data available."

        styles = get_styles()
        html_content = f"""<html><table style="{styles['table']}">"""
        html_content += f"""<tr><th colspan='10' style="{styles['title']}">Descriptive Statistics</th></tr>"""

        html_content += calculate_categorical(df)
        html_content += "</table><table>"
        html_content += calculate_numeric(df)
        html_content += "</table></html>"
        return html_content

    def clear_output(self, b):
        with self.show_data_output and self.save_data_output and self.describe_data_output:
            self.show_data_output.clear_output()
            self.save_data_output.clear_output()
            self.describe_data_output.clear_output()

        self.dataset_dropdown.value = 'None'
        self.variable_dropdown.value = []



