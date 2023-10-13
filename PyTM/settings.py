import os 

data_foldername = "pytm"
data_filename = "data.json"
# make data folder hidden in the home directory
data_folder = os.path.expanduser(f"~/.{data_foldername}")
data_filepath = os.path.join(data_folder, data_filename )
    