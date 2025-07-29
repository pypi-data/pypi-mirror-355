import ipywidgets as wd

from pyschare.helpers.styles import get_styles, style_base


def get_layout(box_name):
    layout_base = wd.Layout(grid_area=f'{box_name}', width='100%',
                            background_color='white', border='1px solid #ababab')
    return layout_base


def create_select_dropdown(options=None, box_name=None, value=None):
    select_dropdown = wd.Select(
        options=options,
        disabled=False,
        rows=10,
        value=value,
        layout=wd.Layout(grid_area=f'{box_name}_select_box', width='100%',
                         background_color='white', border='1px solid #ababab'))
    return select_dropdown


def create_multiple_select_dropdown(options=None, box_name=None):
    select_dropdown = wd.SelectMultiple(
        options=options,
        disabled=False,
        rows=10,
        layout=wd.Layout(grid_area=f'{box_name}_select_box', width='100%',
                         background_color='white', border='1px solid #ababab'))
    return select_dropdown


def create_dropdown(name, options=None, value=None):
    new_dropdown = wd.Dropdown(
        options=options,
        value=value,
        disabled=False,
        layout=wd.Layout(grid_area=f'{name}_dropdown_box')
    )
    return new_dropdown


def create_label(text, writing_style=None):
    if writing_style is None:
        writing_style = get_styles().get('label', '')
    lower_text = text.lower()
    label = wd.HTML(value=f"""<div style="{writing_style}"><p>Select {text}</p></div>""",
                    disabled=False,
                    layout=wd.Layout(grid_area=f'{lower_text}_label_box', width='100%',
                                     background_color='white', border='1px solid #ababab'),
                    style={**style_base, 'border': '1px solid #ababab'})
    return label


def create_helper(text, helper_name, writing_style=None):
    if writing_style is None:
        writing_style = get_styles().get('helper', '')
    helper = wd.HTML(value=f"""<div style="{writing_style}"><p>{text}</p></div>""",
                     disabled=False,
                     layout=wd.Layout(grid_area=f'{helper_name}_helper_box', border='1px solid gray', width='96%',
                                      justify='center'),
                     style={**style_base, 'word_break': 'break_all', 'padding': '3px'})
    return helper


def create_button(text, box_name, style):
    button = wd.Button(description=f'{text}', style=style,
                       layout=wd.Layout(grid_area=f'{box_name}_button_box', width='100%'))
    return button


def get_text_fields(text):
    new_field = wd.Text(value='', description=f'{text}: ',
                        style=dict(font_size='12px', text_color='black', background='#FFFFFF',
                                   description_width='150px'),
                        layout=wd.Layout(width='95%', height='50px', justify_content="flex-end"))
    return new_field


def get_date_picker(text):
    new_field = wd.DatePicker( description=f'{text}: ',
                              style=dict(font_size='12px', text_color='black', background='#FFFFFF',
                                         description_width='150px'),
                              layout=wd.Layout(width='95%', height='50px', justify_content="flex-end"))
    return new_field


def get_text_area(text):
    new_field = wd.Textarea(value='', description=f'{text}: ',
                            style=dict(font_size='12px', text_color='black', background='#FFFFFF',
                                       description_width='150px'),
                            layout=wd.Layout(width='95%', height='50px', justify_content="flex-end"))
    return new_field


def get_variable_text_area(text):
    lower_text = text.lower()
    new_text_area = wd.Textarea(value='', description=f'{text}',
                                placeholder=f'Enter column names for {lower_text}',
                                disabled=False, style=dict(description_width='150px'), layout=dict(width='700px'))
    return new_text_area


def button_styles(button_color):
    styles = dict(padding_block='10px', font_size='14px', button_color=f'{button_color}', text_color='white',
                  font_weight='bold', font_family=' Tahoma, Verdana,sans-serif')
    return styles


def get_label_buttons(text, color):
    new_button = wd.Button(description=f'{text}', style=button_styles(color),
                           layout=wd.Layout(margin='auto', display='block', width='fit-content', height='fit-content',
                                            padding_block='10px'))
    return new_button


def get_uploader(text):
    new_uploader = wd.FileUpload(accept='.csv', multiple=False, description=f'{text}',
                                 tooltip='Upload a CSV file', style=button_styles('firebrick'),
                                 layout=wd.Layout(margin='auto', display='block', width='fit-content',
                                                  height='fit-content', padding_block='10px'))
    return new_uploader

