import ipywidgets as wd

def get_styles():
    styles = {
        "div": "padding-left: 10px; padding-right: 10px; margin: 20px auto;",
        "table": "width: 100%; border-spacing: 0; border-bottom: 1px solid black;",
        "title": "background-color: #FFFFFF; text-align: left; font-size: 20px; font-weight: bold; font-family: Helvetica, Neue; border-bottom: 3px solid black;",
        "first_title": "background-color: #FFFFFF; width: 30%;text-align: left; font-size: 20px; font-weight: bold; font-family: Helvetica, Neue; border-bottom: 3px solid black;",
        "cell": "background-color: #FFFFFF; text-align: right; border-spacing: 0; border-bottom: 1px solid black; font-family: Helvetica, Neue;word-break:break-all;",
        "stats_cell": "background-color: #FFFFFF; text-align: center; border-spacing: 0; border-bottom: 1px solid black; font-family: Helvetica, Neue;",
        "key_cell": "background-color: #FFFFFF; text-align: left; border-spacing: 0;font-weight: bold;  border-bottom: 1px solid black; font-family: Helvetica, Neue;",
        "key_cell_variable": "background-color: #FFFFFF; text-align: left; border-spacing: 0;font-weight: bold;  border-bottom: 1px solid black; font-family: Helvetica, Neue;  word-break:break-all;",
        "sub_cell": "background-color: #FFFFFF;text-align: left; border-spacing: 0;font-weight: bold;  border-bottom: 1px solid black; font-family: Helvetica, Neue;  padding-left: 16px",
        "first_header": "text-align: left; border-spacing: 0; border-bottom: 1px solid black; background-color: white; font-family: Helvetica, Neue; font-weight: bold",
        "header": "text-align: center; border-spacing: 0; border-bottom: 1px solid black; background-color: white; font-family: Helvetica, Neue; font-weight: bold",
        "stats_header": "text-align: center; border-spacing: 0; border-bottom: 1px solid black; background-color: white; font-family: Helvetica, Neue; font-weight: bold; word-break:break-all;",
        "label": "text-align: left; font-weight: bold; font-size: 12px; margin-left: 5px; font-family: Helvetica, Neue",
        "helper": "text-align: left; font-size: 14px; margin-left: 5px; margin-right: 5px; font-family: Helvetica, Neue",
        "first_column": "background-color: #FFFFFF; text-align: left; width: 25%; font-size: 12px; font-weight: bold; font-family: Tahoma, Verdana, serif; border-bottom: 3px solid black;",
        "second_column": "background-color: #FFFFFF; text-align: left; width: 25%; font-size: 12px; font-family: Tahoma, Verdana, serif; border-bottom: 3px solid black;",
        "third_column": "background-color: #FFFFFF; text-align: right; font-size: 12px; font-family: Tahoma, Verdana, serif; border-bottom: 3px solid black;",
        "first_cell": "background-color: #FFFFFF; text-align: left; border-spacing: 0; border-bottom: 1px solid black;font-size: 12px; font-family:Tahoma, Verdana; word-break:break-all;",
        "second_cell": "background-color: #FFFFFF; text-align: right; border-spacing: 0;  border-bottom: 1px solid black;font-size: 12px; font-family: Tahoma, Verdana; word-break:break-all;"
    }
    return styles


style_base = {'font_size': '14px', 'text_color': 'black', 'background': 'rgb(247, 247, 247)'}

button_style = {'font_size': '14px', 'text_color': 'white',
                'font_weight': 'bold', 'font_family': ' Tahoma, Verdana,sans-serif',
                'text_align': 'center'}

meta_layout = dict(width='95%', height='50px', justify_content="flex-end")
meta_style = dict(font_size='12px', text_color='black', background='#FFFFFF',
                  description_width='150px')

box_layout = wd.Layout(display='flex', flex_flow='column', align_items='center', width='100%')
vbox_layout = wd.Layout(padding_block='10px', margin = '2px')

def get_label_styles():
    styles = {
        "table": "width: 100%; border-spacing: 0; border-bottom: 1px solid black;",
        "title": "background-color: #FFFFFF; text-align: left; font-size: 20px; font-weight: bold; font-family: Tahoma, Verdana, serif; border-bottom: 3px solid black;",
        "first_title": "background-color: #FFFFFF; width: 30%;text-align: left; font-size: 20px; font-weight: bold; font-family: Tahoma, Verdana, serif; border-bottom: 3px solid black;",
        "cell": "background-color: #FFFFFF; text-align: right; border-spacing: 0; border-bottom: 1px solid black; font-family:Georgia, serif;word-break:break-all;",
        "stats_cell": "background-color: #FFFFFF; text-align: center; border-spacing: 0; border-bottom: 1px solid black; font-family:Georgia, serif;",
        "key_cell": "background-color: #FFFFFF; text-align: left; border-spacing: 0;font-weight: bold;  border-bottom: 1px solid black; font-family: Georgia, serif;",
        "key_cell_variable": "background-color: #FFFFFF; text-align: left; border-spacing: 0;font-weight: bold;  border-bottom: 1px solid black; font-family: Georgia, serif;  word-break:break-all;",
        "sub_cell": "background-color: #FFFFFF;text-align: left; border-spacing: 0;font-weight: bold;  border-bottom: 1px solid black; font-family: Georgia, serif;  padding-left: 16px",
        "first_header": "text-align: left; border-spacing: 0; border-bottom: 1px solid black; background-color: white; font-family: Georgia, serif; font-weight: bold",
        "header": "text-align: center; border-spacing: 0; border-bottom: 1px solid black; background-color: white; font-family: Georgia, serif; font-weight: bold",
        "stats_header": "text-align: center; border-spacing: 0; border-bottom: 1px solid black; background-color: white; font-family: Georgia, serif; font-weight: bold; word-break:break-all;",
    }
    return styles

