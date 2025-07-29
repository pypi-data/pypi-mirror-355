import json
import subprocess
import pandas as pd
from io import StringIO
import os

USER=os.environ['USER']


def query_squeue()->dict:
    """Query squeue to get the job status."""
    result = subprocess.run(
        ["squeue", "-u" ,f"{USER}" ,'--Format=",jobid,name,state,timeused,timelimit,"'],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        )
    return pd.read_csv(StringIO(result.stdout),delimiter=r"\s+").to_dict(orient="list")
    
    
    