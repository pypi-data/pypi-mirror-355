import os
from datetime import datetime

class ChalkBoardLogger:
    def __init__(self, experiment_name):
        self.exp_name = experiment_name.upper()

        self.chkpt_folder = os.path.join(os.path.expanduser("~"), "SoundByteResults", self.exp_name)
        if not os.path.isdir(self.chkpt_folder):
            os.makedirs(self.chkpt_folder)
    
        self.log_file = os.path.join(self.chkpt_folder, "LOG_FILE.txt")
        with open(self.log_file, "w") as f:
            f.write(f"{self.exp_name} Experiment Results\n")
            f.write(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

    def write(self, *args):
        with open(self.log_file, "a") as logfile:
            logfile.write(">> >>"+" ".join([str(i) for i in args])+"\n")
