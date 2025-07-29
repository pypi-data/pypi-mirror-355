from bioplumber import configs
from pathlib import Path as Path


def assemble_megahit_(
    read1:str,
    read2:str|None,
    output_dir:str,
    config:configs.Configs,
    container:str="none",
    **kwargs: dict[str,configs.kwgs_tuple]
)->str:
    """
    Generate a command to run MEGAHIT assembler.

    Args:
        read1 (str): Path to read1 file.
        read2 (str|None): Path to read2 file.
        output_dir (str): Path to output directory.
        config (configs.Configs): Configuration object.
        container (str): Container to use. Default is "none".
        **kwargs: Additional arguments.

    Returns:
        str: Command to run MEGAHIT.
    """
    if read2 is None:
        paired =False
    
    else:
        paired = True
    
    if container == "none":
        if paired:
            command= f"megahit -1 {read1} -2 {read2} -o {output_dir} -t {config.megahit_cpus}"

        
        else:
  
            command= f"megahit -r {read1} -o {output_dir} -t {config.megahit_cpus}"

            
    elif container =="docker":
        if paired:
            command= f"docker run -v {output_dir}:{output_dir} -v {read1}:{read1} -v {read2}:{read2} {config.docker_container} megahit -1 {read1} -2 {read2} -o {output_dir} -t {config.megahit_cpus}"


        else:
            command= f"docker run -v {output_dir}:{output_dir} -v {read1}:{read1} {config.docker_container} megahit -r {read1} -o {output_dir} -t {config.megahit_cpus}"

    
    elif container =="singularity":
        parent_output_dir = str(Path(output_dir).parent)
        if paired:
            command= f"singularity exec --bind {read1}:{read1},{read2}:{read2},{parent_output_dir}:{parent_output_dir} {config.singularity_container} megahit -1 {read1} -2 {read2} -o {output_dir} -t {config.megahit_cpus}"

        
        else:
            command= f"singularity exec --bind {read1}:{read1},{output_dir}:{output_dir} {config.singularity_container} megahit -r {read1} -o {output_dir} -t {config.megahit_cpus}"

    for _,value in kwargs.items():
        command += f" {value.pre} {value.value}"

    return command
            
    
        
        
    
    