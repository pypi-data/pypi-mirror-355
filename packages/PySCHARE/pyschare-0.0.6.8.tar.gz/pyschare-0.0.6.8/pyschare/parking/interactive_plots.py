import ipywidgets as wd
from IPython.display import display, clear_output
import seaborn as sns
from matplotlib import pyplot as plt


from .constants import calculate_helper_text, MAIN_TITLE
from .create_widgets import create_label, create_select_dropdown, create_dropdown, create_button, \
    create_helper
from .data_functions import select_data_options, get_parsed_data, \
    get_main_table_info
from .styles import button_style

class _Visuals:
    def __init__(self):
        self.data_info = get_main_table_info()
        self.data_options = select_data_options(self.data_info)
        self.dataset_label = create_label(text='Dataset')
        self.x_axis_label = create_label(text='X')
        self.y_axis_label = create_label(text='Y')

        self.hue_dropdown_label = create_label(text='Hue')
        self.style_dropdown_label = create_label(text='Style')
        self.size_dropdown_label = create_label(text='Size')
        self.col_dropdown_label = create_label(text='Column')
        self.row_dropdown_label = create_label(text='Row')
        self.multiple_dropdown_label = create_label(text='Layer')
        self.plot_dropdown_label = create_label(text='Plot')
        self.dataset_dropdown = create_select_dropdown(options=['None'] + self.data_options, box_name='dataset')

        self.x_axis_dropdown = create_dropdown(name='x', options=[])
        self.y_axis_dropdown = create_dropdown(name='y', options=[])
        self.hue_dropdown = create_dropdown(name='hue', options=[])
        self.style_dropdown = create_dropdown(name='style', options=[])
        self.size_dropdown = create_dropdown(name='size', options=[])

        self.col_dropdown = create_dropdown(name='col', options=[])
        self.row_dropdown = create_dropdown(name='row', options=[])

        self.multiple_dropdown = create_dropdown(name='layer',
                                                 options=[('None', 'None'), ('Layer', 'layer'), ('Dodge', 'dodge'),
                                                          ('Stack', 'stack'), ('Fill', 'fill')], value='layer')
        self.plot_dropdown = create_select_dropdown(
            options=[('None', 'None'), ('Bar Plot', 'bar'), ('Box Plot', 'box'), ('Boxen Plot', 'boxen'),
                     ('Count Plot', 'count'),
                     ('Histogram', 'histogram'), ('Line Plot', 'line'), ('Point Plot', 'point'),
                     ('Scatter Plot', 'scatter'),
                     ('Strip Plot', 'strip'), ('Swarm Plot', 'swarm'), ('Violin Plot', 'violin')], box_name='plot',
            value='None')

        self.dataset_dropdown.observe(self.update_variable_options, names='value')

        self.show_plot_button = create_button(text='Show Plot', box_name='show_plot',
                                              style={**button_style, 'button_color': 'blue'})

        self.clear_plot_button = create_button(text='Clear Output', box_name='clear_plot',
                                               style={**button_style, 'button_color': 'red'})

        self.visual_helper = create_helper(text=calculate_helper_text, helper_name='visual')
        self.show_plot_output = wd.Output(layout=wd.Layout(grid_area='output_box', width='98%', height='80vh'))

        self.show_plot_button.on_click(self.show_plot)
        self.clear_plot_button.on_click(self.clear_output)

        self.visual_grid_layout = wd.GridBox(
            children=[self.visual_helper, self.dataset_label, self.dataset_dropdown,
                      self.x_axis_label, self.x_axis_dropdown,
                      self.y_axis_label, self.y_axis_dropdown,
                      self.hue_dropdown_label, self.hue_dropdown,
                      self.style_dropdown_label, self.style_dropdown,
                      self.size_dropdown_label, self.size_dropdown,
                      self.plot_dropdown_label, self.plot_dropdown,
                      self.col_dropdown_label, self.col_dropdown,
                      self.row_dropdown_label, self.row_dropdown,
                      self.multiple_dropdown_label, self.multiple_dropdown,
                      self.show_plot_button, self.clear_plot_button
                      ],
            layout=wd.Layout(display='grid',
                             grid_template_columns='15% 35% 15% 35%',
                             grid_template_rows='repeat(12, auto)',
                             grid_template_areas='''    
                             "visual_helper_box visual_helper_box visual_helper_box visual_helper_box "
                             "visual_helper_box visual_helper_box visual_helper_box visual_helper_box "
                             "dataset_label_box  dataset_select_box x_label_box x_dropdown_box "
                             " . dataset_select_box  y_label_box y_dropdown_box"
                             " . dataset_select_box hue_label_box hue_dropdown_box"
                             " . dataset_select_box  style_label_box style_dropdown_box" 
                             "plot_label_box plot_select_box  size_label_box size_dropdown_box"
                             " . plot_select_box  column_label_box col_dropdown_box "
                             " . plot_select_box  row_label_box row_dropdown_box"
                              " . plot_select_box layer_label_box layer_dropdown_box"
                              ". . . ."
                              " . show_plot_button_box . clear_plot_button_box"


                              ''',
                             grid_gap='10px',
                             width='98%',
                             height='auto',
                             margin='5px 5px 5px 5px'

                             ))

        display(wd.VBox([self.visual_grid_layout, self.show_plot_output]))

        self.input_data = self.data_info[self.data_info[MAIN_TITLE] == self.dataset_dropdown.value]

    def show_plot(self, b):
        with self.show_plot_output:
            clear_output(wait=True)
            self.create_plot()

    def update_variable_options(self, change):
        selected_title = self.dataset_dropdown.value
        selected_data = self.data_info[self.data_info[MAIN_TITLE] == selected_title]
        dataset = get_parsed_data(selected_data)
        if dataset is not None:
            self.x_axis_dropdown.options = ['None'] + dataset.columns.tolist()
            self.y_axis_dropdown.options = ['None'] + dataset.columns.tolist()
            self.hue_dropdown.options = ['None'] + dataset.columns.tolist()
            self.style_dropdown.options = ['None'] + dataset.columns.tolist()
            self.size_dropdown.options = ['None'] + dataset.columns.tolist()
            self.col_dropdown.options = ['None'] + dataset.columns.tolist()
            self.row_dropdown.options = ['None'] + dataset.columns.tolist()

    def get_x_axis(self):
        return self.x_axis_dropdown.value

    def get_y_axis(self):
        return self.y_axis_dropdown.value

    def get_hue(self):
        return self.hue_dropdown.value

    def get_style(self):
        return self.style_dropdown.value

    def get_size(self):
        return self.style_dropdown.value

    def get_multiple(self):
        return self.multiple_dropdown.value

    def get_column(self):
        return self.col_dropdown.value

    def get_row(self):
        return self.row_dropdown.value

    def get_plot(self):
        return self.plot_dropdown.value

    def create_plot(self):
        selected_title = self.dataset_dropdown.value
        selected_data = self.data_info[self.data_info[MAIN_TITLE] == selected_title]

        dataset = get_parsed_data(selected_data)
        if dataset is None:
            print("No dataset selected.")
            return

        plot_parameters = {
            'x': self.get_x_axis(),
            'data': dataset
        }
        temp_multiple = ""

        if self.get_y_axis() is not None:
            plot_parameters['y'] = self.get_y_axis()

        if self.get_hue() is not None:
            plot_parameters['hue'] = self.get_hue()

        if self.get_style() is not None:
            plot_parameters['style'] = self.get_style()
        if self.get_size() is not None:
            plot_parameters['size'] = self.get_size()
        if self.get_multiple() is not None:
            temp_multiple = self.get_multiple()

        if self.get_column() is not None:
            plot_parameters['col'] = self.get_column()
        if self.get_row() is not None:
            plot_parameters['row'] = self.get_row()

        plot_type = self.get_plot()

        with self.show_plot_output:
            clear_output(wait=True)
            if plot_type in ['bar', 'box', 'boxen', 'count', 'point', 'strip', 'swarm', 'violin']:
                g = sns.catplot(kind=plot_type, **plot_parameters)
                g.set_xticklabels(rotation=45, ha='right')
                #                 plt.tight_layout()
                plt.show()
                plt.close()

            elif plot_type == 'scatter':
                g = sns.relplot(kind='scatter', **plot_parameters)
                g.set_xticklabels(rotation=45, ha='right')
                #                 plt.tight_layout()
                plt.show()
                plt.close()

            elif plot_type == 'line':
                g = sns.relplot(kind='line', **plot_parameters)
                g.set_xticklabels(rotation=45, ha='right')
                #                 plt.tight_layout()
                plt.show()
                plt.close()

            elif plot_type == 'histogram':
                g = sns.displot(kind='hist', multiple=temp_multiple, **plot_parameters)
                g.set_xticklabels(rotation=45, ha='right')
                #                 plt.tight_layout()
                plt.show()
                plt.close()

    def clear_output(self, b):
        with self.show_plot_output:
            self.show_plot_output.clear_output()
        self.dataset_dropdown.value = 'None'
        self.x_axis_dropdown.value = []
        self.y_axis_dropdown.value = []
        self.hue_dropdown.value = []
        self.style_dropdown.value = []
        self.size_dropdown.value = []

        self.col_dropdown.value = []
        self.row_dropdown.value = []

        self.multiple_dropdown.value = 'layer'
        self.plot_dropdown.value = 'None'

