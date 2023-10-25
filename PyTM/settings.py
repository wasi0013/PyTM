import os 

data_foldername = "pytm"
data_filename = "data.json"
state_filename = "state.json"
# make data folder hidden in the home directory
data_folder = os.path.expanduser(f"~/.{data_foldername}")
data_filepath = os.path.join(data_folder, data_filename )
state_filepath = os.path.join(data_folder, state_filename)

STARTED = "started"
STOPPED = "stopped"
FINISHED = "finished"
PAUSED = "paused"
ABORTED = "aborted"