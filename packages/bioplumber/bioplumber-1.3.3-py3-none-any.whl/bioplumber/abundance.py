from bioplumber import configs
import pathlib 

def relative_abundance_coverm_(
    read1:str,
    read2:str|None,
    genomes_dir:str,
    output_file:str,
    genome_extension:str,
    config:configs.Configs,
    container:str="none",
    **kwargs: dict[str,configs.kwgs_tuple]
                        )->str:
    """
    This function will return the script to calculate the relative abundance of genomes using coverm.
    
    Args:
    read1 (str): The path to the read1 file.
    read2 (str|None): The path to the read2 file.
    genomes_dir (str): The path to the directory containing the genomes.
    output_file (str): The path to the output file.
    genome_extension (str): The extension of the genomes.
    config (configs.Configs): The configuration object.
    container (str): The container to use. Default is "none".
    **kwargs: Additional arguments.

    Returns:
    str: The script to calculate the relative abundance of genomes using coverm.
    
    """
    if read2 is None:
        paired =False
    
    else:
        paired = True
    
    if container == "none":
        if paired:
            command= f"coverm genome -m relative_abundance -1 {read1} -2 {read2} --genome-fasta-directory {genomes_dir} -x {genome_extension} > {output_file}"
        
        else:
            command= f"coverm genome -m relative_abundance --single {read1} --genome-fasta-directory {genomes_dir} -x {genome_extension} > {output_file} "
        
    elif container == "docker":
        if paired:
            bind_path=" -v ".join([i+":"+i for i in set(str(pathlib.Path(read1).absolute()),str(pathlib.Path(read2).absolute()),str(pathlib.Path(genomes_dir).absolute()),str(pathlib.Path(output_file).parent.absolute()))])
            command= f"docker run -v {bind_path} {config.docker_container} coverm genome -m relative_abundance -1 {read1} -2 {read2} --genome-fasta-directory {genomes_dir} -x {genome_extension}  > {output_file}"
        else:
            bind_path=" -v ".join([i+":"+i for i in set(str(pathlib.Path(read1).absolute()),str(pathlib.Path(genomes_dir).absolute()),str(pathlib.Path(output_file).parent.absolute()))])
            command= f"docker run -v {bind_path} {config.docker_container} coverm genome -m relative_abundance --single {read1} --genome-fasta-directory {genomes_dir}  -x {genome_extension} > {output_file}"
    
    elif container == "singularity":
        if paired:
            bind_path=" --bind ".join([i+":"+i for i in set(str(pathlib.Path(read1).absolute()),str(pathlib.Path(read2).absolute()),str(pathlib.Path(genomes_dir).absolute()),str(pathlib.Path(output_file).parent.absolute()))])
            command= f"singularity exec --bind {bind_path} {config.singularity_container} coverm genome -m relative_abundance -1 {read1} -2 {read2} --genome-fasta-directory {genomes_dir}  -x {genome_extension} > {output_file}"
        else:
            bind_path=" --bind ".join([i+":"+i for i in set(str(pathlib.Path(read1).absolute()),str(pathlib.Path(genomes_dir).absolute()),str(pathlib.Path(output_file).parent.absolute()))])
            command= f"singularity exec --bind {bind_path} {config.singularity_container} coverm genome -m relative_abundance --single {read1} --genome-fasta-directory {genomes_dir}  -x {genome_extension} > {output_file}"

    for _,value in kwargs.items():
        command+= f"{value.pre} {value.value}"
    
    return command