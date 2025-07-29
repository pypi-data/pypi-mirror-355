from bioplumber import configs,files
from pathlib import Path as Path

def download_gtdb_tk_db_(output_dir:str,
                         config:configs.Configs,
                         container:str="none",
                         )->str:
    """
    This function will return the script to download the GTDB-Tk database.
    
    Args:
    output_dir (str): The path to the output directory.
    config (configs.Configs): The configuration object.
    container (str): The container to use. Default is "none".
    
    Returns:
    str: The script to download the GTDB-Tk database.
    
    """

    cmd=files.download_wget_(
        url=config.gtdb_tk_db_url,
        output_dir=output_dir,
        configs=config,
        container=container
    )
    cmd+="\n"
    cmd+= files.extract_tar_(
        tar_file=str(Path(output_dir)/"gtdbtk_db.tar.gz"),
        output_dir=output_dir,
        configs=config,
        container=container
    )
    
    return cmd

def assign_taxonomy_gtdb_tk_(
    genomes_dir:str,
    output_dir:str,
    db_dir:str,
    config:configs.Configs,
    container:str="none",
    **kwargs
                        )->str:
    """
    This function will return the script to assign taxonomy using GTDB-Tk.
    
    Args:
    genomes_dir (str): The path to the directory containing the genomes.
    output_dir (str): The path to the output directory.
    db_dir (str): The path to the GTDB-Tk database (Ignore when not using containers).
    config (configs.Configs): The configuration object.
    container (str): The container to use. Default is "none".
    **kwargs: Additional arguments.
    
    Returns:
    str: The script to assign taxonomy using GTDB-Tk.
    
    """
    genomes_dir = str(Path(genomes_dir).absolute())
    output_dir = str(Path(output_dir).absolute())
    if container == "none":
        command = f"gtdbtk classify_wf --genome_dir {genomes_dir} --out_dir {output_dir}"

        
    elif container == "docker":
        ref_dir = str(Path(db_dir).absolute())
        command = f"docker run -v {ref_dir}:/refdata -v {genomes_dir}:{genomes_dir} -v {output_dir}:{output_dir} {config.docker_container} gtdbtk classify_wf --genome_dir {genomes_dir} --out_dir {output_dir}"

    
    elif container == "singularity":
        ref_dir= str(Path(db_dir).absolute())
        bind_dir = ",".join(set([genomes_dir+":"+genomes_dir, output_dir+":"+output_dir]))
        command = f"singularity exec --bind {ref_dir}:/refdata --bind {bind_dir} {config.singularity_container} gtdbtk classify_wf --genome_dir {genomes_dir} --out_dir {output_dir}"

    
    else:
        raise ValueError("Invalid container")
    
    for _, value in kwargs.items():
        command += f" {value.pre} {value.value}"
    return command