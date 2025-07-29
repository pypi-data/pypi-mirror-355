from IPython.core.display_functions import display

from pyschare.chat import get_gemini_chat

# Display widgets
def gemini_chat():
    model_dropdown, location_dropdown, user_input, generate_button, output_area = get_gemini_chat()
    display(model_dropdown, location_dropdown, user_input, generate_button, output_area)


gemini_chat()