from dataclasses import dataclass
import json
from collections import namedtuple

kwgs_tuple=namedtuple("kwgs_tup",["pre","value"])

@dataclass
class Configs:
    singularity_container:str
    docker_container:str
    gtdb_tk_db_url:str="https://data.ace.uq.edu.au/public/gtdb/data/releases/latest/auxillary_files/gtdbtk_package/full_package/gtdbtk_data.tar.gz"
    gtdb_local_db_dir:str="NA"
    
    @classmethod
    def from_dict(cls,dictionary:dict):
        return cls(**dictionary)



        

DEFAULT_CONFIGS = Configs(
    singularity_container="",
    docker_container="",
)

RECOMMENDED_DOCKER_CONTAINERS ={
    "checkm":"NA",
    "drep":"parsaghadermazi/drep",
    "megahit": "NA"
}

