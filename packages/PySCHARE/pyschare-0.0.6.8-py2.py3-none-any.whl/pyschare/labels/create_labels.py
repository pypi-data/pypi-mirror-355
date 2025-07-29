from pyschare.helpers.styles import get_label_styles, meta_layout, meta_style, box_layout, vbox_layout

from pyschare.helpers.create_widgets import create_helper, get_text_fields, get_label_buttons, get_uploader, \
    get_date_picker, get_text_area, get_variable_text_area

from pyschare.helpers.constants import datafacts_helper, metatable_helper, provenance_helper, dictionary_helper, \
    stats_helper, bar_plot_helper, plot_helper, correlation_helper, metadata, output_names, button_labels, field_names
import warnings

warnings.filterwarnings("ignore")
#chunk 1
import ipywidgets as wd
from ipywidgets import HBox, VBox, Label, Layout
from IPython.display import display, HTML, Image, clear_output
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO
import os
from scipy.stats import pearsonr, chi2_contingency
#
# outputs = {}
#
# for name in output_names:
#     outputs[name] = wd.Output()
#
# edit_button = {}
# save_button = {}
#
# for label in button_labels:
#     edit_button[label] = get_label_buttons('Edit', 'firebrick')
#     save_button[label] = get_label_buttons('Save', 'darkgray')
#
# stats_button = get_label_buttons('Show Statistics Table', 'darkgray')
# show_data_button = get_label_buttons('Show Data', 'darkgray')
# dictionary_uploader = get_uploader('Upload Data Dictionary')
# data_uploader = get_uploader('Upload Data')
#
# datafacts_help = create_helper(datafacts_helper, 'datafacts')
# metatable_help = create_helper(metatable_helper, 'metatable')
# provenance_help = create_helper(provenance_helper, 'provenance')
# dictionary_help = create_helper(dictionary_helper, 'dictionary')
# stats_help = create_helper(stats_helper, 'stats')
# barplot_help = create_helper(bar_plot_helper, 'barplot')
# plot_help = create_helper(plot_helper, 'plot')
# correlation_help = create_helper(correlation_helper, 'correlation')
#
# fields = {}
#
# for name in field_names:
#     new_name = name.replace(' ', '_').lower()
#     fields[new_name] = get_text_fields(name)
#
# ordinal_text = get_variable_text_area('Ordinal Variables')
# nominal_text = get_variable_text_area('Nominal Variables')
# continuous_text = get_variable_text_area('Continuous Variables')
# discrete_text = get_variable_text_area('Discrete Variables')
#
# time_from_field = get_date_picker('Data Collection (From)')
# time_to_field = get_date_picker('Data Collection (To)')
#
# text_container = wd.VBox([ordinal_text, nominal_text, continuous_text, discrete_text])
#
# var1_dropdown = wd.Dropdown(description='Variable Names:', disabled=False, style=meta_style, layout=meta_layout)
# var2_dropdown = wd.Dropdown(description='Variable Descriptions:', disabled=False, style=meta_style, layout=meta_layout)
# dropdown_container1 = wd.HBox([var1_dropdown, var2_dropdown])
#
# varA_dropdown = wd.Dropdown(description="Variable A:", options=["None", ""], value="None")
# varB_dropdown = wd.Dropdown(description="Variable B:", options=["None", ""], value="None")
# categorical_dropdown = wd.SelectMultiple(description="Categorical:", options=[], style={'description_width': 'initial'})
# continuous_dropdown = wd.SelectMultiple(description="Continuous:", options=[], style={'description_width': 'initial'})
#
# dropdown_container2 = wd.HBox([varA_dropdown, varB_dropdown])
# dropdown_container3 = wd.HBox([categorical_dropdown, continuous_dropdown])
#
# first_dropdown = wd.Dropdown(description='Variable 1:', options=["None", ""], value="None")
# second_dropdown = wd.Dropdown(description='Variable 2:', options=["None", ""], value="None")
# third_dropdown = wd.Dropdown(description='Variable 3:', options=["None", ""], value="None")
# dropdown_container4 = wd.HBox([first_dropdown, second_dropdown, third_dropdown])
# #chunk 8
#
# facts_input_area = wd.VBox([fields['project_title'], fields['project_description'], save_button['facts']])
#
# meta_input_area = wd.VBox(
#     [fields['filename'], fields['format'], fields['url'], fields['domain'], fields['keywords'], fields['type'],
#      fields['geography'], fields['data_collection_method'], fields['time_method'], fields['rows'], fields['columns'],
#      fields['cdes'],
#      fields['missing'], fields['license'], fields['released'], time_from_field, time_to_field, fields['funding_agency'],
#      fields['description'], save_button['meta']])
#
# pro_input_area = wd.VBox(
#     [fields['source_name'], fields['source_url'], fields['source_email'], fields['author_name'], fields['author_url'],
#      fields['author_email'], save_button['pro']])
#
#
# def generate_facts():
#     facts = {
#         "Project Title": fields['project_title'].value,
#         "Project Description": fields['project_description'].value
#     }
#
#     styles = get_label_styles()
#
#     facts_content = f"""
#         <html>
#         <table style="{styles['table']}">
#             <tr><th style="{styles['first_title']}">Data Facts</th>
#                <th style="{styles['title']}"></th>
#            </tr>
#        """
#
#     for key, value in facts.items():
#         facts_content += f"""
#                <tr>
#                    <td style="{styles['key_cell']}">{key}</td>
#                    <td style="{styles['cell']}">{value}</td>
#                </tr>
#                """
#     facts_content += "</table></html>"
#
#     with open('facts.html', 'w') as f:
#         f.write(facts_content)
#     return facts_content
#
#
# def save_facts_button_clicked(b):
#     facts_input_area.layout.display = 'none'
#     facts_html = generate_facts()
#
#     with outputs['facts']:
#         clear_output(wait=True)
#         display(HTML(facts_html))
#         display(edit_button['facts'])
#
#
# def edit_facts_button_clicked(b):
#     outputs['facts'].clear_output()
#     facts_input_area.layout.display = 'block'
#
#
# save_button['facts'].on_click(save_facts_button_clicked)
# edit_button['facts'].on_click(edit_facts_button_clicked)
#
#
# def generate_metatable(metadata):
#     new_fields = {
#         "Filename": fields['filename'],
#         "Format": fields['format'],
#         "Study/Project URL": fields['url'],
#         "Domain": fields['domain'],
#         "Keywords": fields['keywords'],
#         "Type": fields['type'],
#         "Geography": fields['geography'],
#         "Data Collection Method": fields['data_collection_method'],
#         "Time Method": fields['time_method'],
#         "Rows": fields['rows'],
#         "Columns": fields['columns'],
#         "CDEs": fields['cdes'],
#         "Missing": fields['missing'],
#         "License": fields['license'],
#         "Released": fields['released'],
#         "Data Collection Timeline": (time_from_field, time_to_field),
#         "Funding Agency": fields['funding_agency'],
#         "Description": fields['description']
#     }
#
#     for key, field in new_fields.items():
#         if isinstance(field, tuple):
#             metadata[key] = (field[0].value.strftime("%Y-%m-%d") if field[0].value else None,
#                              field[1].value.strftime("%Y-%m-%d") if field[1].value else None)
#         else:
#             metadata[key] = field.value if key != "Released" else field.value.strptime(
#                 "%Y-%m-%d") if field.value else None
#
#     styles = get_label_styles()
#
#     meta_content = f"""
#         <html>
#         <table style="{styles['table']}">
#             <tr><th style="{styles['first_title']}">Metadata Table</th>
#                <th style="{styles['title']}"></th>
#            </tr>
#        """
#
#     for key, value in metadata.items():
#         if isinstance(value, tuple):
#             meta_content += f"""
#                <tr>
#                    <td colspan="2" style="{styles['key_cell']}">{key}</td>
#                </tr>
#                <tr>
#                    <td style="{styles['sub_cell']}">From</td>
#                    <td style="{styles['cell']}">{value[0]}</td>
#                </tr>
#                <tr>
#                    <td style="{styles['sub_cell']}">To</td>
#                    <td style="{styles['cell']}">{value[1]}</td>
#                </tr>
#                """
#         else:
#             meta_content += f"""
#                <tr>
#                    <td style="{styles['key_cell']}">{key}</td>
#                    <td style="{styles['cell']}">{value}</td>
#                </tr>
#                """
#     meta_content += "</table></html>"
#
#     with open('metatable.html', 'w') as f:
#         f.write(meta_content)
#     return meta_content
#
#
# def save_meta_button_clicked(b):
#     meta_input_area.layout.display = 'none'
#     meta_html = generate_metatable(metadata)
#
#     with outputs['meta']:
#         clear_output(wait=True)
#         display(HTML(meta_html))
#         display(edit_button['meta'])
#
#
# def edit_meta_button_clicked(b):
#     outputs['meta'].clear_output()
#     meta_input_area.layout.display = 'block'
#
#
# save_button['meta'].on_click(save_meta_button_clicked)
# edit_button['meta'].on_click(edit_meta_button_clicked)
#
#
# # chunk 13
# def generate_pro_table():
#     provenance_data = {
#         "Source": (fields['source_name'].value, fields['source_url'].value, fields['source_email'].value),
#         "Author": (fields['author_name'].value, fields['author_url'].value, fields['author_email'].value)
#     }
#
#     styles = get_label_styles()
#
#     pro_content = f"""
#     <html>
#     <table style="{styles['table']}">
#         <tr><th style="{styles['first_title']}">Provenance</th>
#            <th style="{styles['title']}"></th>
#        </tr>
#    """
#
#     for key, value in provenance_data.items():
#         pro_content += f"""
#            <tr>
#                <td colspan="2" style="{styles['key_cell']}">{key}</td>
#            </tr>
#            <tr>
#                <td style="{styles['sub_cell']}">Name</td>
#                <td style="{styles['cell']}">{value[0]}</td>
#            </tr>
#            <tr>
#                <td style="{styles['sub_cell']}">URL</td>
#                <td style="{styles['cell']}">{value[1]}</td>
#            </tr>
#            <tr>
#                <td style="{styles['sub_cell']}">Email</td>
#                <td style="{styles['cell']}">{value[2]}</td>
#            </tr>
#         """
#
#     pro_content += "</table></html>"
#
#     with open('provenance_data.html', 'w') as f:
#         f.write(pro_content)
#
#     return pro_content
#
#
# def save_pro_button_clicked(b):
#     pro_input_area.layout.display = 'none'
#     prov_html = generate_pro_table()
#
#     with outputs['pro']:
#         clear_output(wait=True)
#         display(HTML(prov_html))
#         display(edit_button['pro'])
#
#
# def edit_pro_button_clicked(b):
#     outputs['pro'].clear_output()
#     pro_input_area.layout.display = 'block'
#
#
# save_button['pro'].on_click(save_pro_button_clicked)
# edit_button['pro'].on_click(edit_pro_button_clicked)
#
#
# # chunk 14
# def get_variables(df, var1, var2):
#     return df[[var1, var2]].drop_duplicates()
#
#
# dropdown_container = wd.HBox([var1_dropdown, var2_dropdown])
#
#
# def dictionary_uploaded(change):
#     global dictionary_df
#     dictionary_df = pd.read_csv(BytesIO(dictionary_uploader.value[0]['content']))
#
#     options = dictionary_df.columns.tolist()
#     var1_dropdown.options = options
#     var2_dropdown.options = options
#
#     display(dropdown_container)
#
#
# dictionary_uploader.observe(dictionary_uploaded, names='value')
#
#
# # chunk 15
# def generate_variable_table(variables_df):
#     styles = get_label_styles()
#
#     html_content = f"""
#     <html>
#     <table style="{styles['table']}">
#         <tr>
#             <th style="{styles['first_title']}">Variables</th>
#             <th style="{styles['title']}"></th>
#         </tr>
#     """
#
#     for index, row in variables_df.iterrows():
#         html_content += f"""
#         <tr>
#             <td style="{styles['key_cell_variable']}">{row[0]}</td>
#             <td style="{styles['cell']}">{row[1]}</td>
#         </tr>
#         """
#
#     html_content += "</table></html>"
#
#     with open("variables.html", 'w') as file:
#         file.write(html_content)
#
#     # display(HTML(html_content))
#     return html_content
#
#
# def dropdown_changed(change):
#     if var1_dropdown.value and var2_dropdown.value:
#         variables_df = get_variables(dictionary_df, var1_dropdown.value, var2_dropdown.value)
#         var_html = generate_variable_table(variables_df)
#
#     with outputs['var']:
#         clear_output(wait=True)
#         display(HTML(var_html))
#
#
# var1_dropdown.observe(dropdown_changed, names='value')
# var2_dropdown.observe(dropdown_changed, names='value')
#
#
# # chunk 16
# def get_columns(text):
#     return [col.strip() for col in text.split(',')]
#
#
# def get_options(ordinal_text, nominal_text):
#     return ["None"] + get_columns(ordinal_text) + get_columns(nominal_text)
#
#
# def update_dropdown_options(change=None):
#     value_options = get_options(ordinal_text.value, nominal_text.value)
#     first_dropdown.options = value_options
#     second_dropdown.options = value_options
#     third_dropdown.options = value_options
#
#
# def upload_data():
#     global stats_df
#     stats_df = pd.read_csv(BytesIO(data_uploader.value[0]['content']))
#     # display(stats_df.head())
#
#
# def show_data_button_clicked(b):
#     upload_data()
#     with outputs['show_data']:
#         clear_output(wait=True)
#         display(stats_df.head())
#         display(text_container)
#
#
# ordinal_text.observe(update_dropdown_options, names='value')
# nominal_text.observe(update_dropdown_options, names='value')
#
# show_data_button.on_click(show_data_button_clicked)
#
#
# def generate_stats_table(df, columns, title, styles):
#     html_content = f""" <html><table style="{styles['table']}">"""
#     html_content += f""" <tr><th colspan="10" style="{styles['title']}">{title}</th></tr>"""
#     html_content += f""" <tr><th style="{styles['first_header']}">name</th>"""
#     html_content += f""" <th style="{styles['stats_header']}">type</th>"""
#     html_content += f""" <th style="{styles['stats_header']}">count</th>"""
#     html_content += f""" <th style="{styles['stats_header']}">missing</th>"""
#
#     if title == "Ordinal" or title == "Nominal":
#         html_content += f"""<th style="{styles['stats_header']}">unique</th>"""
#         html_content += f"""<th style="{styles['stats_header']}">mostFreq</th>"""
#         html_content += f"""<th style="{styles['stats_header']}">leastFreq</th></tr>"""
#     else:
#         html_content += f"""<th style="{styles['stats_header']}">min</th>"""
#         html_content += f"""<th style="{styles['stats_header']}">median</th>"""
#         html_content += f"""<th style="{styles['stats_header']}">max</th>"""
#         html_content += f"""<th style="{styles['stats_header']}">mean</th>"""
#         html_content += f"""<th style="{styles['stats_header']}">stdDeviation</th>"""
#         html_content += f"""<th style="{styles['stats_header']}">zeros</th></tr>"""
#
#     for col in columns:
#         if col in df.columns:
#             html_content += f"""<tr><td style="{styles['cell']}">{col}</td>"""
#             html_content += f"""<td style="{styles['stats_cell']}">{df[col].dtype}</td>"""
#             html_content += f"""<td style="{styles['stats_cell']}">{df[col].count()}</td>"""
#             html_content += f"""<td style="{styles['stats_cell']}">{df[col].isnull().mean() * 100:.2f}%</td>"""
#
#             if title == "Ordinal" or title == "Nominal":
#                 html_content += f"""<td style="{styles['stats_cell']}">{df[col].nunique()}</td>"""
#                 html_content += f"""<td style="{styles['stats_cell']}">{df[col].mode()[0] if not df[col].mode().empty else 'N/A'}</td>"""
#                 html_content += f"""<td style="{styles['stats_cell']}">{df[col].value_counts().idxmin() if not df[col].value_counts().empty else 'N/A'}</td></tr>"""
#             else:
#                 html_content += f"""<td style="{styles['stats_cell']}">{df[col].min():.2f}</td>"""
#                 html_content += f"""<td style="{styles['stats_cell']}">{df[col].median():.2f}</td>"""
#                 html_content += f"""<td style="{styles['stats_cell']}">{df[col].max():.2f}</td>"""
#                 html_content += f"""<td style="{styles['stats_cell']}">{df[col].mean():.2f}</td>"""
#                 html_content += f"""<td style="{styles['stats_cell']}">{df[col].std():.2f}</td>"""
#                 html_content += f"""<td style="{styles['stats_cell']}">{(df[col] == 0).mean() * 100:.2f}%</td></tr>"""
#     html_content += "</table></html>"
#
#     with open(f'{title.lower()}_data.html', 'w') as f:
#         f.write(html_content)
#
#     display(HTML(html_content))
#     return html_content
#
#
# # chunk 18
# def stats_button_clicked(b):
#     display(wd.VBox([stats_button], layout=box_layout))
#     with outputs['stats']:
#         clear_output(wait=True)
#
#         # df = pd.read_csv(BytesIO(data_uploader.value[0]['content']))
#         styles = get_label_styles()
#         ordinal_var = get_columns(ordinal_text.value)
#         nominal_var = get_columns(nominal_text.value)
#         continuous_var = get_columns(continuous_text.value)
#         discrete_var = get_columns(discrete_text.value)
#
#         if ordinal_var:
#             generate_stats_table(stats_df, ordinal_var, "Ordinal", styles)
#         if nominal_var:
#             generate_stats_table(stats_df, nominal_var, "Nominal", styles)
#         if continuous_var:
#             generate_stats_table(stats_df, continuous_var, "Continuous", styles)
#         if discrete_var:
#             generate_stats_table(stats_df, discrete_var, "Discrete", styles)
#
#
# stats_button.on_click(stats_button_clicked)
#
#
# def update_data(change):
#     global stats_df
#     upload_data()
#     options = ["None"] + stats_df.columns.tolist()
#     varA_dropdown.options = options
#     varB_dropdown.options = options
#     categorical_dropdown.options = options
#     continuous_dropdown.options = options
#     #update_dropdown_options(None)
#     create_pair_plot(None)
#     # show_barplots(None)
#     show_catplots(None)
#     calculate_correlations_new(None)
#
#
# def show_catplots(change):
#     global stats_df
#
#     cat1 = first_dropdown.value
#     cat2 = second_dropdown.value
#     cat3 = third_dropdown.value
#
#     with outputs['hist']:
#         clear_output(wait=True)
#     # plt.figure(figsize=(10, 6))
#
#     if cat1 == "None" and cat2 == "None" and cat3 == "None":
#         return
#
#     if cat1 != "None" and cat2 == "None" and cat3 == "None":
#         sns.catplot(data=stats_df, x=cat1, kind="count")
#         plt.show()
#         plt.close()
#
#     elif cat1 != "None" and cat2 != "None" and cat3 == "None":
#         sns.catplot(data=stats_df, x=cat1, kind="count")
#         sns.catplot(data=stats_df, x=cat2, kind="count")
#         sns.catplot(data=stats_df, x=cat1, hue=cat2, kind="count")
#         plt.show()
#         plt.close()
#
#     elif cat1 != "None" and cat2 != "None" and cat3 != "None":
#         sns.catplot(data=stats_df, x=cat1, kind="count")
#         sns.catplot(data=stats_df, x=cat2, kind="count")
#         sns.catplot(data=stats_df, x=cat3, kind="count")
#         sns.catplot(data=stats_df, x=cat1, hue=cat2, kind="count")
#         sns.catplot(data=stats_df, x=cat1, hue=cat3, kind="count")
#         sns.catplot(data=stats_df, x=cat2, hue=cat3, kind="count")
#         sns.catplot(data=stats_df, x=cat1, hue=cat2, col=cat3, kind="count")
#         plt.show()
#         plt.close()
#
#
# def create_pair_plot(change):
#     global stats_df
#     clear_output(wait=True)
#     fig, axes = plt.subplots(2, 2, figsize=(14, 12))
#     if varA_dropdown.value != "None" and varB_dropdown.value != "None":
#         ct_counts = stats_df.groupby([varA_dropdown.value, varB_dropdown.value]).size()
#         ct_counts = ct_counts.reset_index(name='count')
#         ct_countsA = ct_counts.pivot(index=varA_dropdown.value, columns=varB_dropdown.value, values='count')
#         ct_countsB = ct_counts.pivot(index=varB_dropdown.value, columns=varA_dropdown.value, values='count')
#
#         sns.histplot(stats_df[varA_dropdown.value], kde=False, color=".3", ax=axes[0, 0])
#         sns.histplot(stats_df[varB_dropdown.value], kde=False, color=".3", ax=axes[1, 1])
#
#         sns.heatmap(ct_countsA, ax=axes[0, 1])
#         sns.heatmap(ct_countsB, ax=axes[1, 0])
#     elif varA_dropdown.value != "None":
#         sns.histplot(stats_df[varA_dropdown.value], kde=False, color=".3", ax=axes[0, 0])
#         axes[1, 1].set_visible(False)
#         axes[0, 1].set_visible(False)
#         axes[1, 0].set_visible(False)
#     elif varB_dropdown.value != "None":
#         sns.histplot(stats_df[varB_dropdown.value], kde=False, color=".3", ax=axes[1, 1])
#         axes[0, 0].set_visible(False)
#         axes[0, 1].set_visible(False)
#         axes[1, 0].set_visible(False)
#     else:
#         print("Please select at least one variable for analysis.")
#         axes[0, 0].set_visible(False)
#         axes[1, 1].set_visible(False)
#         axes[0, 1].set_visible(False)
#         axes[1, 0].set_visible(False)
#
#     with outputs['pair_plot']:
#         clear_output(wait=True)
#         plt.show()
#
#
# # chunk 22
# def calculate_correlations_new(change):
#     global stats_df
#
#     clear_output(wait=True)
#     display(wd.VBox([categorical_dropdown, continuous_dropdown]))
#
#     categorical_vars = [var for var in categorical_dropdown.value if var != "None"]
#     continuous_vars = [var for var in continuous_dropdown.value if var != "None"]
#
#     if categorical_vars:
#         df_categorical = pd.get_dummies(stats_df[categorical_vars])
#     else:
#         df_categorical = pd.DataFrame()
#
#     df_continuous = stats_df[continuous_vars] if continuous_vars else pd.DataFrame()
#
#     df_combined = pd.concat([df_categorical, df_continuous], axis=1)
#
#     corr_matrix = pd.DataFrame(np.zeros((df_combined.shape[1], df_combined.shape[1])),
#                                columns=df_combined.columns,
#                                index=df_combined.columns)
#
#     for var1 in df_combined.columns:
#         for var2 in df_combined.columns:
#             if var1 in df_categorical.columns and var2 in df_categorical.columns:
#                 confusion_matrix = pd.crosstab(df_combined[var1], df_combined[var2])
#                 chi2, _, _, _ = chi2_contingency(confusion_matrix)
#                 n = confusion_matrix.sum().sum()
#                 r, k = confusion_matrix.shape
#                 cramers_v = np.sqrt(chi2 / (n * (min(k - 1, r - 1))))
#                 corr_matrix.at[var1, var2] = cramers_v
#             elif var1 in df_continuous.columns and var2 in df_continuous.columns:
#                 corr_matrix.at[var1, var2], _ = pearsonr(df_combined[var1], df_combined[var2])
#             else:
#                 corr_matrix.at[var1, var2], _ = pearsonr(df_combined[var1], df_combined[var2])
#
#     plt.figure(figsize=(14, 12))
#     sns.heatmap(corr_matrix, annot=True, cmap='Spectral', fmt='.2f', square=False)
#     plt.title('Correlation Matrix')
#
#     with outputs['corr_plot']:
#         clear_output(wait=True)
#         plt.show()
#
#
# data_uploader.observe(update_data, names='value')
# varA_dropdown.observe(create_pair_plot, names='value')
# varB_dropdown.observe(create_pair_plot, names='value')
# categorical_dropdown.observe(calculate_correlations_new, names='value')
# continuous_dropdown.observe(calculate_correlations_new, names='value')
# first_dropdown.observe(show_catplots, names='value')
# second_dropdown.observe(show_catplots, names='value')
# third_dropdown.observe(show_catplots, names='value')
#
#
# def get_facts():
#     return display(wd.VBox([datafacts_help], layout=vbox_layout),
#                    wd.VBox([facts_input_area], layout=vbox_layout),
#                    outputs['facts'])
#
#
# def get_meta():
#     return display(wd.VBox([metatable_help], layout=vbox_layout), wd.VBox([meta_input_area], layout=vbox_layout),
#                    outputs['meta'])
#
#
# def get_provenance():
#     return display(wd.VBox([provenance_help], layout=vbox_layout), wd.VBox([pro_input_area], layout=vbox_layout),
#                    outputs['pro'])
#
#
# def get_dictionary():
#     return display(wd.VBox([dictionary_help]), wd.VBox([dictionary_uploader]), dropdown_container1, outputs['var'])
#
#
# def get_data_summary():
#     return display(wd.VBox([stats_help]), wd.VBox([data_uploader], layout=vbox_layout),
#                    wd.VBox([show_data_button], layout=vbox_layout), wd.VBox([outputs['show_data']]))
#
#
# def get_summary_stats():
#     return display(stats_button, outputs['stats'])
#
#
# def get_show_barplots():
#     return display(wd.VBox([barplot_help]), dropdown_container4, outputs['bars'])
#
#
# def get_show_pairplots():
#     return display(wd.VBox([plot_help]), dropdown_container2, outputs['pair_plot'])
#
#
# def get_show_correlations():
#     return display(wd.VBox([correlation_help]), dropdown_container3, outputs['corr_plot'])
#
#
# class _DataLabels:
#     def __init__(self):
#         self.new_facts = get_facts()
#         self.new_meta = get_meta()
#         self.new_provenance = get_provenance()
#         self.new_dictionary = get_dictionary()
#         self.new_data_summary = get_data_summary()
#         self.new_summary_stats = get_summary_stats()
#         self.new_show_barplots = get_show_barplots()
#         self.new_show_pairplots = get_show_pairplots()
#         self.new_show_correlations = get_show_correlations()
import warnings

warnings.filterwarnings("ignore")
# chunk 1
import ipywidgets as wd
from ipywidgets import HBox, VBox, Label, Layout
from IPython.display import display, HTML, Image, clear_output
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO
import os
from scipy.stats import pearsonr, chi2_contingency
import datetime

outputs = {}

for name in output_names:
    outputs[name] = wd.Output()

edit_button = {}
save_button = {}

for label in button_labels:
    edit_button[label] = get_label_buttons('Edit', 'firebrick')
    save_button[label] = get_label_buttons('Save', 'darkgray')

stats_button = get_label_buttons('Show Statistics Table', 'darkgray')
show_data_button = get_label_buttons('Show Data', 'darkgray')
dictionary_uploader = get_uploader('Upload Data Dictionary')
data_uploader = get_uploader('Upload Data')

datafacts_help = create_helper(datafacts_helper, 'datafacts')
metatable_help = create_helper(metatable_helper, 'metatable')
provenance_help = create_helper(provenance_helper, 'provenance')
dictionary_help = create_helper(dictionary_helper, 'dictionary')
stats_help = create_helper(stats_helper, 'stats')
barplot_help = create_helper(bar_plot_helper, 'barplot')
plot_help = create_helper(plot_helper, 'plot')
correlation_help = create_helper(correlation_helper, 'correlation')

fields = {}

for name in field_names:
    new_name = name.replace(' ', '_').lower()
    fields[new_name] = get_text_fields(name)

ordinal_text = get_variable_text_area('Ordinal Variables')
nominal_text = get_variable_text_area('Nominal Variables')
continuous_text = get_variable_text_area('Continuous Variables')
discrete_text = get_variable_text_area('Discrete Variables')

time_from_field = get_date_picker('Data Collection (From)')
time_to_field = get_date_picker('Data Collection (To)')

text_container = wd.VBox([ordinal_text, nominal_text, continuous_text, discrete_text])

var1_dropdown = wd.Dropdown(description='Variable Names:', disabled=False, style=meta_style, layout=meta_layout)
var2_dropdown = wd.Dropdown(description='Variable Descriptions:', disabled=False, style=meta_style, layout=meta_layout)
dropdown_container1 = wd.HBox([var1_dropdown, var2_dropdown])

varA_dropdown = wd.Dropdown(description="Variable A:", options=["None", ""], value="None")
varB_dropdown = wd.Dropdown(description="Variable B:", options=["None", ""], value="None")
categorical_dropdown = wd.SelectMultiple(description="Categorical:", options=[], style={'description_width': 'initial'})
continuous_dropdown = wd.SelectMultiple(description="Continuous:", options=[], style={'description_width': 'initial'})

dropdown_container2 = wd.HBox([varA_dropdown, varB_dropdown])
dropdown_container3 = wd.HBox([categorical_dropdown, continuous_dropdown])

first_dropdown = wd.Dropdown(description='Variable 1:', options=["None", ""], value="None")
second_dropdown = wd.Dropdown(description='Variable 2:', options=["None", ""], value="None")
third_dropdown = wd.Dropdown(description='Variable 3:', options=["None", ""], value="None")
dropdown_container4 = wd.HBox([first_dropdown, second_dropdown, third_dropdown])
# chunk 8

facts_input_area = wd.VBox([fields['project_title'], fields['project_description'], save_button['facts']])

meta_input_area = wd.VBox(
    [fields['filename'], fields['format'], fields['url'], fields['domain'], fields['keywords'], fields['type'],
     fields['geography'], fields['data_collection_method'], fields['time_method'], fields['rows'], fields['columns'],
     fields['cdes'],
     fields['missing'], fields['license'], fields['released'], time_from_field, time_to_field, fields['funding_agency'],
     fields['description'], save_button['meta']])

pro_input_area = wd.VBox(
    [fields['source_name'], fields['source_url'], fields['source_email'], fields['author_name'], fields['author_url'],
     fields['author_email'], save_button['pro']])


def generate_facts():
    facts = {
        "Project Title": fields['project_title'].value,
        "Project Description": fields['project_description'].value
    }

    styles = get_label_styles()

    facts_content = f"""
        <html>
        <table style="{styles['table']}">
            <tr><th style="{styles['first_title']}">Data Facts</th>
               <th style="{styles['title']}"></th>
           </tr>
       """

    for key, value in facts.items():
        facts_content += f"""
               <tr>
                   <td style="{styles['key_cell']}">{key}</td>
                   <td style="{styles['cell']}">{value}</td>
               </tr>
               """
    facts_content += "</table></html>"

    with open('facts.html', 'w') as f:
        f.write(facts_content)
    return facts_content


def save_facts_button_clicked(b):
    facts_input_area.layout.display = 'none'
    facts_html = generate_facts()

    with outputs['facts']:
        clear_output(wait=True)
        display(HTML(facts_html))
        display(edit_button['facts'])


def edit_facts_button_clicked(b):
    outputs['facts'].clear_output()
    facts_input_area.layout.display = 'block'


save_button['facts'].on_click(save_facts_button_clicked)
edit_button['facts'].on_click(edit_facts_button_clicked)


def generate_metatable(metadata):
    new_fields = {
        "Filename": fields['filename'],
        "Format": fields['format'],
        "Study/Project URL": fields['url'],
        "Domain": fields['domain'],
        "Keywords": fields['keywords'],
        "Type": fields['type'],
        "Geography": fields['geography'],
        "Data Collection Method": fields['data_collection_method'],
        "Time Method": fields['time_method'],
        "Rows": fields['rows'],
        "Columns": fields['columns'],
        "CDEs": fields['cdes'],
        "Missing": fields['missing'],
        "License": fields['license'],
        "Released": fields['released'],
        "Data Collection Timeline": (time_from_field, time_to_field),
        "Funding Agency": fields['funding_agency'],
        "Description": fields['description']
    }

    for key, field in new_fields.items():
        if isinstance(field, tuple):
            metadata[key] = (field[0].value.strftime("%Y-%m-%d") if field[0].value else None,
                             field[1].value.strftime("%Y-%m-%d") if field[1].value else None)
        else:
            if key == "Released":
                if field.value:
                    parsed_date = None
                    formats = ["%m/%d/%Y", "%m-%d-%Y", "%Y-%m-%d"]
                    for fmt in formats:
                        try:
                            parsed_date = datetime.datetime.strptime(str(field.value), fmt)
                            break
                        except ValueError:
                            continue
                    if parsed_date:
                        metadata[key] = parsed_date.strftime("%Y-%m-%d")
                    else:
                        metadata[key] = None
                else:
                    metadata[key] = None
            else:
                metadata[key] = field.value

    styles = get_label_styles()

    meta_content = f"""
        <html>
        <table style="{styles['table']}">
            <tr><th style="{styles['first_title']}">Metadata Table</th>
               <th style="{styles['title']}"></th>
           </tr>
       """

    for key, value in metadata.items():
        if isinstance(value, tuple):
            meta_content += f"""
               <tr>
                   <td colspan="2" style="{styles['key_cell']}">{key}</td>
               </tr>
               <tr>
                   <td style="{styles['sub_cell']}">From</td>
                   <td style="{styles['cell']}">{value[0]}</td>
               </tr>
               <tr>
                   <td style="{styles['sub_cell']}">To</td>
                   <td style="{styles['cell']}">{value[1]}</td>
               </tr>
               """
        else:
            meta_content += f"""
               <tr>
                   <td style="{styles['key_cell']}">{key}</td>
                   <td style="{styles['cell']}">{value}</td>
               </tr>
               """
    meta_content += "</table></html>"

    with open('metatable.html', 'w') as f:
        f.write(meta_content)
    return meta_content


def save_meta_button_clicked(b):
    meta_input_area.layout.display = 'none'
    meta_html = generate_metatable(metadata)

    with outputs['meta']:
        clear_output(wait=True)
        display(HTML(meta_html))
        display(edit_button['meta'])


def edit_meta_button_clicked(b):
    outputs['meta'].clear_output()
    meta_input_area.layout.display = 'block'


save_button['meta'].on_click(save_meta_button_clicked)
edit_button['meta'].on_click(edit_meta_button_clicked)


# chunk 13
def generate_pro_table():
    provenance_data = {
        "Source": (fields['source_name'].value, fields['source_url'].value, fields['source_email'].value),
        "Author": (fields['author_name'].value, fields['author_url'].value, fields['author_email'].value)
    }

    styles = get_label_styles()

    pro_content = f"""
    <html>
    <table style="{styles['table']}">
        <tr><th style="{styles['first_title']}">Provenance</th>
           <th style="{styles['title']}"></th>
       </tr>
   """

    for key, value in provenance_data.items():
        pro_content += f"""
           <tr>
               <td colspan="2" style="{styles['key_cell']}">{key}</td>
           </tr>
           <tr>
               <td style="{styles['sub_cell']}">Name</td>
               <td style="{styles['cell']}">{value[0]}</td>
           </tr>
           <tr>
               <td style="{styles['sub_cell']}">URL</td>
               <td style="{styles['cell']}">{value[1]}</td>
           </tr>
           <tr>
               <td style="{styles['sub_cell']}">Email</td>
               <td style="{styles['cell']}">{value[2]}</td>
           </tr>
        """

    pro_content += "</table></html>"

    with open('provenance_data.html', 'w') as f:
        f.write(pro_content)

    return pro_content


def save_pro_button_clicked(b):
    pro_input_area.layout.display = 'none'
    prov_html = generate_pro_table()

    with outputs['pro']:
        clear_output(wait=True)
        display(HTML(prov_html))
        display(edit_button['pro'])


def edit_pro_button_clicked(b):
    outputs['pro'].clear_output()
    pro_input_area.layout.display = 'block'


save_button['pro'].on_click(save_pro_button_clicked)
edit_button['pro'].on_click(edit_pro_button_clicked)


# chunk 14
def get_variables(df, var1, var2):
    return df[[var1, var2]].drop_duplicates()


dropdown_container = wd.HBox([var1_dropdown, var2_dropdown])


def dictionary_uploaded(change):
    global dictionary_df
    dictionary_df = pd.read_csv(BytesIO(dictionary_uploader.value[0]['content']))

    options = dictionary_df.columns.tolist()
    var1_dropdown.options = options
    var2_dropdown.options = options

    # display(dropdown_container)


dictionary_uploader.observe(dictionary_uploaded, names='value')


# chunk 15
def generate_variable_table(variables_df):
    styles = get_label_styles()

    html_content = f"""
    <html>
    <table style="{styles['table']}">
        <tr>
            <th style="{styles['first_title']}">Variables</th>
            <th style="{styles['second_title']}">Descriptions</th>
        </tr>
    """

    for index, row in variables_df.iterrows():
        html_content += f"""
        <tr>
            <td style="{styles['key_cell_variable']}">{row[0]}</td>
            <td style="{styles['cell']}">{row[1]}</td>
        </tr>
        """

    html_content += "</table></html>"

    with open("variables.html", 'w') as file:
        file.write(html_content)

    # display(HTML(html_content))
    return html_content


def dropdown_changed(change):
    if var1_dropdown.value and var2_dropdown.value:
        try:
            variables_df = get_variables(dictionary_df, var1_dropdown.value, var2_dropdown.value)
            var_html = generate_variable_table(variables_df)

            with outputs['var']:
                display(HTML(var_html))
        except Exception as e:
            with outputs['var']:
                display(HTML(f"<p>Error processing variables: {e}</p>"))


var1_dropdown.observe(dropdown_changed, names='value')
var2_dropdown.observe(dropdown_changed, names='value')


# chunk 16
def get_columns(text):
    return [col.strip() for col in text.split(',')]


def get_options(ordinal_text, nominal_text):
    return ["None"] + get_columns(ordinal_text) + get_columns(nominal_text)


def update_dropdown_options(change=None):
    value_options = get_options(ordinal_text.value, nominal_text.value)
    first_dropdown.options = value_options
    second_dropdown.options = value_options
    third_dropdown.options = value_options


def upload_data():
    global stats_df
    stats_df = pd.read_csv(BytesIO(data_uploader.value[0]['content']))


def show_data_button_clicked(b):
    upload_data()
    with outputs['show_data']:
        clear_output(wait=True)
        display(stats_df.head())
        display(text_container)


ordinal_text.observe(update_dropdown_options, names='value')
nominal_text.observe(update_dropdown_options, names='value')

show_data_button.on_click(show_data_button_clicked)


def generate_stats_table(df, columns, title, styles):
    html_content = f""" <html><table style="{styles['table']}">"""
    html_content += f""" <tr><th colspan="10" style="{styles['title']}">{title}</th></tr>"""
    html_content += f""" <tr><th style="{styles['first_header']}">name</th>"""
    html_content += f""" <th style="{styles['stats_header']}">type</th>"""
    html_content += f""" <th style="{styles['stats_header']}">count</th>"""
    html_content += f""" <th style="{styles['stats_header']}">missing</th>"""

    if title == "Ordinal" or title == "Nominal":
        html_content += f"""<th style="{styles['stats_header']}">unique</th>"""
        html_content += f"""<th style="{styles['stats_header']}">mostFreq</th>"""
        html_content += f"""<th style="{styles['stats_header']}">leastFreq</th></tr>"""
    else:
        html_content += f"""<th style="{styles['stats_header']}">min</th>"""
        html_content += f"""<th style="{styles['stats_header']}">median</th>"""
        html_content += f"""<th style="{styles['stats_header']}">max</th>"""
        html_content += f"""<th style="{styles['stats_header']}">mean</th>"""
        html_content += f"""<th style="{styles['stats_header']}">stdDeviation</th>"""
        html_content += f"""<th style="{styles['stats_header']}">zeros</th></tr>"""

    for col in columns:
        if col in df.columns:
            html_content += f"""<tr><td style="{styles['cell']}">{col}</td>"""
            html_content += f"""<td style="{styles['stats_cell']}">{df[col].dtype}</td>"""
            html_content += f"""<td style="{styles['stats_cell']}">{df[col].count()}</td>"""
            html_content += f"""<td style="{styles['stats_cell']}">{df[col].isnull().mean() * 100:.2f}%</td>"""

            if title == "Ordinal" or title == "Nominal":
                html_content += f"""<td style="{styles['stats_cell']}">{df[col].nunique()}</td>"""
                html_content += f"""<td style="{styles['stats_cell']}">{df[col].mode()[0] if not df[col].mode().empty else 'N/A'}</td>"""
                html_content += f"""<td style="{styles['stats_cell']}">{df[col].value_counts().idxmin() if not df[col].value_counts().empty else 'N/A'}</td></tr>"""
            else:
                html_content += f"""<td style="{styles['stats_cell']}">{df[col].min():.2f}</td>"""
                html_content += f"""<td style="{styles['stats_cell']}">{df[col].median():.2f}</td>"""
                html_content += f"""<td style="{styles['stats_cell']}">{df[col].max():.2f}</td>"""
                html_content += f"""<td style="{styles['stats_cell']}">{df[col].mean():.2f}</td>"""
                html_content += f"""<td style="{styles['stats_cell']}">{df[col].std():.2f}</td>"""
                html_content += f"""<td style="{styles['stats_cell']}">{(df[col] == 0).mean() * 100:.2f}%</td></tr>"""
    html_content += "</table></html>"

    with open(f'{title.lower()}_data.html', 'w') as f:
        f.write(html_content)

    display(HTML(html_content))
    return html_content


# chunk 18
def stats_button_clicked(b):
    # display(wd.VBox([stats_button], layout=box_layout))
    with outputs['stats']:
        clear_output(wait=True)

        styles = get_label_styles()
        ordinal_var = get_columns(ordinal_text.value)
        nominal_var = get_columns(nominal_text.value)
        continuous_var = get_columns(continuous_text.value)
        discrete_var = get_columns(discrete_text.value)

        if ordinal_var:
            generate_stats_table(stats_df, ordinal_var, "Ordinal", styles)
        if nominal_var:
            generate_stats_table(stats_df, nominal_var, "Nominal", styles)
        if continuous_var:
            generate_stats_table(stats_df, continuous_var, "Continuous", styles)
        if discrete_var:
            generate_stats_table(stats_df, discrete_var, "Discrete", styles)


stats_button.on_click(stats_button_clicked)


def show_catplots(change):
    global stats_df

    cat1 = first_dropdown.value
    cat2 = second_dropdown.value
    cat3 = third_dropdown.value

    with outputs['bars']:
        clear_output(wait=True)
        # plt.figure(figsize=(10, 6))

        if cat1 == "None" and cat2 == "None" and cat3 == "None":
            return

        if cat1 != "None" and cat2 == "None" and cat3 == "None":
            sns.catplot(data=stats_df, x=cat1, kind="count")
            plt.show()
            plt.close()

        elif cat1 != "None" and cat2 != "None" and cat3 == "None":
            sns.catplot(data=stats_df, x=cat1, kind="count")
            sns.catplot(data=stats_df, x=cat2, kind="count")
            sns.catplot(data=stats_df, x=cat1, hue=cat2, kind="count")
            plt.show()
            plt.close()

        elif cat1 != "None" and cat2 != "None" and cat3 != "None":
            sns.catplot(data=stats_df, x=cat1, kind="count")
            sns.catplot(data=stats_df, x=cat2, kind="count")
            sns.catplot(data=stats_df, x=cat3, kind="count")
            sns.catplot(data=stats_df, x=cat1, hue=cat2, kind="count")
            sns.catplot(data=stats_df, x=cat1, hue=cat3, kind="count")
            sns.catplot(data=stats_df, x=cat2, hue=cat3, kind="count")
            sns.catplot(data=stats_df, x=cat1, hue=cat2, col=cat3, kind="count")
            plt.show()
            plt.close()


def create_pair_plot(change):
    global stats_df
    # clear_output(wait=True)
    fig, axes = plt.subplots(2, 2, figsize=(14, 12))
    if varA_dropdown.value != "None" and varB_dropdown.value != "None":
        ct_counts = stats_df.groupby([varA_dropdown.value, varB_dropdown.value]).size()
        ct_counts = ct_counts.reset_index(name='count')
        ct_countsA = ct_counts.pivot(index=varA_dropdown.value, columns=varB_dropdown.value, values='count')
        ct_countsB = ct_counts.pivot(index=varB_dropdown.value, columns=varA_dropdown.value, values='count')

        sns.histplot(stats_df[varA_dropdown.value], kde=False, color=".3", ax=axes[0, 0])
        sns.histplot(stats_df[varB_dropdown.value], kde=False, color=".3", ax=axes[1, 1])

        sns.heatmap(ct_countsA, ax=axes[0, 1])
        sns.heatmap(ct_countsB, ax=axes[1, 0])
    elif varA_dropdown.value != "None":
        sns.histplot(stats_df[varA_dropdown.value], kde=False, color=".3", ax=axes[0, 0])
        axes[1, 1].set_visible(False)
        axes[0, 1].set_visible(False)
        axes[1, 0].set_visible(False)
    elif varB_dropdown.value != "None":
        sns.histplot(stats_df[varB_dropdown.value], kde=False, color=".3", ax=axes[1, 1])
        axes[0, 0].set_visible(False)
        axes[0, 1].set_visible(False)
        axes[1, 0].set_visible(False)
    else:
        print("Please select at least one variable for analysis.")
        axes[0, 0].set_visible(False)
        axes[1, 1].set_visible(False)
        axes[0, 1].set_visible(False)
        axes[1, 0].set_visible(False)

    with outputs['pair_plot']:
        clear_output(wait=True)
        plt.show()


# chunk 22

def calculate_correlations_new(change):
    global stats_df

    if 'stats_df' not in globals() or stats_df.empty:
        with outputs['corr_plot']:
            clear_output(wait=True)
            display(HTML("<p'>Please upload data first.</p>"))
        return

    with outputs['corr_plot']:
        clear_output(wait=True)

        categorical_vars = [var for var in categorical_dropdown.value if var != "None"]
        continuous_vars = [var for var in continuous_dropdown.value if var != "None"]

        valid_categorical_vars = [var for var in categorical_vars if var in stats_df.columns]
        valid_continuous_vars = [var for var in continuous_vars if var in stats_df.columns]

        all_selected_vars = valid_categorical_vars + valid_continuous_vars

        if not all_selected_vars:
            display(HTML("<p>Please select at least two variables for correlation analysis.</p>"))
            plt.close('all')
            return

        df_combined = pd.DataFrame()
        df_categorical_encoded = pd.DataFrame()

        if valid_categorical_vars:
            df_categorical_encoded = pd.get_dummies(stats_df[valid_categorical_vars], drop_first=False)
            df_combined = pd.concat([df_combined, df_categorical_encoded], axis=1)

        if valid_continuous_vars:
            df_combined = pd.concat([df_combined, stats_df[valid_continuous_vars]], axis=1)

        df_combined_clean = df_combined.dropna(subset=df_combined.columns, how='any')

        if df_combined_clean.empty or df_combined_clean.shape[1] == 0:
            display(HTML("<p>Not enough valid data points after handling missing values for correlation analysis.</p>"))
            plt.close('all')
            return

        corr_matrix = pd.DataFrame(np.nan, index=df_combined_clean.columns, columns=df_combined_clean.columns)

        for i, var1_name in enumerate(df_combined_clean.columns):
            for j, var2_name in enumerate(df_combined_clean.columns):
                if i > j:
                    continue

                col1_data = df_combined_clean[var1_name]
                col2_data = df_combined_clean[var2_name]

                is_ohe_cat1 = any(var1_name.startswith(v + '_') for v in valid_categorical_vars)
                is_ohe_cat2 = any(var2_name.startswith(v + '_') for v in valid_categorical_vars)
                is_continuous1 = var1_name in valid_continuous_vars
                is_continuous2 = var2_name in valid_continuous_vars

                if var1_name == var2_name:
                    corr_matrix.at[var1_name, var2_name] = 1.0
                    continue

                if col1_data.nunique() < 2 or col2_data.nunique() < 2:
                    corr_matrix.at[var1_name, var2_name] = np.nan
                    corr_matrix.at[var2_name, var1_name] = np.nan
                    continue

                if is_continuous1 and is_continuous2:
                    try:
                        r_val, _ = pearsonr(col1_data, col2_data)
                        corr_matrix.at[var1_name, var2_name] = r_val
                        corr_matrix.at[var2_name, var1_name] = r_val
                    except ValueError:
                        corr_matrix.at[var1_name, var2_name] = np.nan
                        corr_matrix.at[var2_name, var1_name] = np.nan
                elif (is_ohe_cat1 and is_ohe_cat2):
                    try:
                        r_val, _ = pearsonr(col1_data, col2_data)
                        corr_matrix.at[var1_name, var2_name] = r_val
                        corr_matrix.at[var2_name, var1_name] = r_val
                    except ValueError:
                        corr_matrix.at[var1_name, var2_name] = np.nan
                        corr_matrix.at[var2_name, var1_name] = np.nan
                elif (is_ohe_cat1 and is_continuous2) or (is_continuous1 and is_ohe_cat2):
                    try:
                        r_val, _ = pearsonr(col1_data, col2_data)
                        corr_matrix.at[var1_name, var2_name] = r_val
                        corr_matrix.at[var2_name, var1_name] = r_val
                    except ValueError:
                        corr_matrix.at[var1_name, var2_name] = np.nan
                        corr_matrix.at[var2_name, var1_name] = np.nan
                else:
                    corr_matrix.at[var1_name, var2_name] = np.nan
                    corr_matrix.at[var2_name, var1_name] = np.nan

        if corr_matrix.isnull().all().all():
            display(HTML("<p>No valid correlations could be computed for the selected variables.</p>"))
            plt.close('all')
            return

        plt.figure(figsize=(14, 12))
        sns.heatmap(corr_matrix, annot=True, cmap='Spectral', fmt='.2f', square=False)
        plt.title('Correlation Matrix')
        plt.tight_layout()
        plt.show()
        plt.close()


def update_data(change):
    global stats_df
    upload_data()
    options = ["None"] + stats_df.columns.tolist()
    varA_dropdown.options = options
    varB_dropdown.options = options
    categorical_dropdown.options = options
    continuous_dropdown.options = options
    # update_dropdown_options(None)
    # create_pair_plot(None)
    # show_catplots(None)
    # calculate_correlations_new(None)


data_uploader.observe(update_data, names='value')
varA_dropdown.observe(create_pair_plot, names='value')
varB_dropdown.observe(create_pair_plot, names='value')
categorical_dropdown.observe(calculate_correlations_new, names='value')
continuous_dropdown.observe(calculate_correlations_new, names='value')
first_dropdown.observe(show_catplots, names='value')
second_dropdown.observe(show_catplots, names='value')
third_dropdown.observe(show_catplots, names='value')


def get_facts():
    return display(wd.VBox([datafacts_help], layout=vbox_layout),
                   wd.VBox([facts_input_area], layout=vbox_layout),
                   outputs['facts'])


def get_meta():
    return display(wd.VBox([metatable_help], layout=vbox_layout), wd.VBox([meta_input_area], layout=vbox_layout),
                   outputs['meta'])


def get_provenance():
    return display(wd.VBox([provenance_help], layout=vbox_layout), wd.VBox([pro_input_area], layout=vbox_layout),
                   outputs['pro'])


def get_dictionary():
    return display(wd.VBox([dictionary_help]), wd.VBox([dictionary_uploader]), dropdown_container1, outputs['var'])


def get_data_summary():
    return display(wd.VBox([stats_help]), wd.VBox([data_uploader], layout=vbox_layout),
                   wd.VBox([show_data_button], layout=vbox_layout), wd.VBox([outputs['show_data']]))


def get_summary_stats():
    return display(stats_button, outputs['stats'])


def get_show_catplots():
    return display(wd.VBox([barplot_help]), dropdown_container4, outputs['bars'])


def get_show_pairplots():
    return display(wd.VBox([plot_help]), dropdown_container2, outputs['pair_plot'])


def get_show_correlations():
    return display(wd.VBox([correlation_help]), dropdown_container3, outputs['corr_plot'])


class _DataLabels:
    def __init__(self):
        self.new_facts = get_facts()
        self.new_meta = get_meta()
        self.new_provenance = get_provenance()
        self.new_dictionary = get_dictionary()
        self.new_data_summary = get_data_summary()

        self.new_summary_stats = get_summary_stats()
        self.new_show_catplots = get_show_catplots()
        self.new_show_pairplots = get_show_pairplots()
        self.new_show_correlations = get_show_correlations()