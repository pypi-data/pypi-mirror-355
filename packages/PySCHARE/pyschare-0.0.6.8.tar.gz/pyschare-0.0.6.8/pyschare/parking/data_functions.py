import pandas as pd
import io
import os
import subprocess

from .constants import MAIN_TABLE, MAIN_TITLE, VISUAL_TABLE, DPATH, FPATH

def get_main_table_path():
    dir_path = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(dir_path, DPATH, MAIN_TABLE)
    return csv_path


def get_data_dir():
    dir_path = os.path.dirname(os.path.abspath(__file__))
    # csv_path = os.path.join(dir_path, DPATH, MAIN_TABLE)
    data_directory = os.path.join(dir_path, DPATH)
    return data_directory


def get_data(input_data):
    df = pd.read_csv(input_data)
    return df


def get_search_table_info():
    dir_path: str = os.path.dirname(os.path.abspath(__file__))
    csv_path: str = os.path.join(dir_path, DPATH, VISUAL_TABLE)
    dataset_info = pd.read_csv(csv_path)
    return dataset_info

def get_main_table_info():
    dir_path: str = os.path.dirname(os.path.abspath(__file__))
    csv_path: str = os.path.join(dir_path, DPATH, MAIN_TABLE)
    dataset_info = pd.read_csv(csv_path)
    return dataset_info

def get_bucket():
    my_bucket = os.getenv('WORKSPACE_BUCKET')
    return my_bucket


def select_data_options(dataset_info) -> list:
    options = dataset_info[MAIN_TITLE].tolist()
    return options


def get_dropdown_value(dropdown):
    return dropdown.value

def get_input_path(selected_data):
    if selected_data is not None and not selected_data.empty:
        path = selected_data.iloc[0]['Data']
        dataset_name = selected_data.iloc[0][FPATH]
        return path, dataset_name
    else:
        print("No data found for the selected dataset title.")
        return None

def get_search_input_path(selected_data):
    if selected_data is not None and not selected_data.empty:
        path = selected_data.iloc[0]['Dictionary_path']
        dataset_name = selected_data.iloc[0][FPATH]
        return path, dataset_name
    else:
        print("No data found for the selected dataset title.")
        return None


def save_data_to_bucket(path, dataset_name):
    """
    :return: data_path not data
    """
    # path, dataset_name = get_input_path()
    my_bucket = get_bucket()
    args = ["gsutil", "cp", f"{path}", f"{my_bucket}/{dataset_name}"]
    output = subprocess.run(args, capture_output=True, text=True)
    if output.returncode == 0:
        target_path = f"{my_bucket}/{dataset_name}"
        return target_path


def save_to_bucket(dataframe, my_bucket):
    buffer = io.StringIO()
    dataframe.to_csv(buffer, index=False)
    buffer.seek(0)
    args = ['gsutil', 'cp', '-', my_bucket]
    process = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    process.communicate(buffer.getvalue().encode('utf-8'))


def load_data(path):
    """
    :return: data_path not data
    """
    # path, dataset_name = get_input_path()
    args = ["gsutil", "cat", f"{path}"]

    process = subprocess.Popen(args, stdout=subprocess.PIPE)
    output, _ = process.communicate()
    return output


def parse_data(dataset_name, output):
    if dataset_name.endswith("csv") or dataset_name.endswith("txt"):
        uploaded_data = pd.read_csv(io.StringIO(output.decode('utf-8')), low_memory=False)
        return uploaded_data

    if dataset_name.endswith("tsv"):
        uploaded_data = pd.read_csv(io.StringIO(output.decode('utf-8')), sep= '\t', low_memory=False)
        return uploaded_data

    elif dataset_name.endswith("xlsx"):
        uploaded_data = pd.read_excel(io.BytesIO(output))
        return uploaded_data

    # elif dataset_name.endswith("xpt"):
    #     uploaded_data = pd.read_sas(io.StringIO(output.decode('utf-8')), low_memory=False)
    #     return uploaded_data

    else:
        print("Unsupported file type.")
        return None


def get_parsed_data(selected_data):
    path, dataset_name = get_input_path(selected_data)
    output = load_data(path)
    parsed_data = parse_data(dataset_name, output)
    return parsed_data


