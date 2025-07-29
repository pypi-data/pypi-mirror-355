from pathlib import Path as Path
from bioplumber import configs
from typing import Iterable

def index_bowtie_(
    sequence_dir: str,
    database_dir: str,
    configs: configs.Configs,
    container: str = "none",
    **kwargs: dict[str, configs.kwgs_tuple]
    ) -> str:
    """
    This function ouputs a command to use bowtie2 to index a genome.
    
    Args:
        sequence_dir (str): The path to the fasta file
        database_dir (str): The output directory for the indexed files
        container (str): The container to use
        **kwargs: Additional arguments to pass to bowtie2
    """
    if container=="none":
        sequence_dir=Path(sequence_dir).absolute()
        database_dir=Path(database_dir).absolute()
        command = f"bowtie2-build {sequence_dir} {database_dir}"

        
    elif container=="docker":
        sequence_dir=Path(sequence_dir).absolute()
        database_dir=Path(database_dir).absolute()
        command = f"docker run -v {sequence_dir}:{sequence_dir} -v {database_dir}:{database_dir} {configs.docker_container} bowtie2-build {sequence_dir} {database_dir}"

    elif container=="singularity":
        sequence_dir=Path(sequence_dir).absolute()
        database_dir=Path(database_dir).absolute()
        database_dir_parent=Path(database_dir).parent
        command = f"singularity exec {configs.singularity_container} --bind {sequence_dir}:{sequence_dir},{database_dir_parent}:{database_dir_parent} bowtie2-build {sequence_dir} {database_dir}"

    for _,value in kwargs.items():
        command = command + f" {value.pre} {value.value}"
    
    return command

def align_bowtie_(
    read1:str,
    read2:str|None,
    database_dir:str,
    outdir:str,
    config:configs.Configs,
    container:str="none",
    **kwargs
    )->str:
    """
    This function ouputs a command to use bowtie2 to align fastq files to a genome.
    
    Args:
        read1 (str): The path to the first fastq file
        read2 (str): The path to the second fastq file
        database_dir (str): The path to the indexed genome
        outdir (str): The output directory for the sam file
        container (str): The container to use
        **kwargs: Additional arguments to pass to bowtie2
    """
    

    
    if read2 is not None:
        paired = True
    else:
        paired = False
    
    if container=="none":
        if paired:
            read1=Path(read1).absolute()
            read2=Path(read2).absolute()
            database_dir=Path(database_dir).absolute()
            outdir=Path(outdir).absolute()
            command = f"bowtie2 -x {database_dir} -1 {read1} -2 {read2} -S {outdir}"
        
        else:
            read1=Path(read1).absolute()
            database_dir=Path(database_dir).absolute()
            outdir=Path(outdir).absolute()
            command = f"bowtie2 -x {database_dir} -U {read1} -S {outdir}"
        
    elif container=="docker":
        if paired:
            read1=Path(read1).absolute()
            read2=Path(read2).absolute()
            database_dir=Path(database_dir).absolute()
            outdir=Path(outdir).absolute()
            command = f"docker run -v {read1}:{read1} -v {read2}:{read2} -v {database_dir}:{database_dir} -v {outdir}:{outdir} {config.docker_container} bowtie2 -x {database_dir} -1 {read1} -2 {read2} -S {outdir}"

        else:
            read1=Path(read1).absolute()
            database_dir=Path(database_dir).absolute()
            outdir=Path(outdir).absolute()
            command = f"docker run -v {read1}:{read1} -v {database_dir}:{database_dir} -v {outdir}:{outdir} {config.docker_container} bowtie2 -x {database_dir} -U {read1} -S {outdir}"
    
    elif container=="singularity":
        if paired:
            read1=Path(read1).absolute()
            read2=Path(read2).absolute()
            database_dir=Path(database_dir).absolute()
            outdir=Path(outdir).absolute()
            outdir_parent=Path(outdir).parent
            command = f"singularity exec -B {read1}:{read1} -B {read2}:{read2} -B {database_dir}:{database_dir} -B {outdir_parent}:{outdir_parent} {config.singularity_container} bowtie2 -x {database_dir} -1 {read1} -2 {read2} -S {outdir}"


        else:
            read1=Path(read1).absolute()
            database_dir=Path(database_dir).absolute()
            outdir=Path(outdir).absolute()
            outdir_parent=Path(outdir).parent
            command = f"singularity exec -B {read1}:{read1} -B {database_dir}:{database_dir} -B {outdir_parent}:{outdir_parent} {config.singularity_container} bowtie2 -x {database_dir} -U {read1} -S {outdir}"
    
    for _,value in kwargs.items():
        command = command + f" {value.pre} {value.value}"
    
    return command



def bowtie2_decontaminate_(
    read1:str,
    read2:str|None,
    sample_name:str,
    database_dir:str,
    outdir:str,
    config:configs.Configs,
    container:str="none",
    **kwargs
    )->str:
    """
    This function ouputs a command to use bowtie2 to decontaminate fastq by providing the indexed bowtie database.

    Args:
        read1 (str): The path to the first fastq file
        read2 (str): The path to the second fastq file
        sample_name (str): The name of the sample
        database_dir (str): The path to the indexed genome
        outdir (str): The output directory for the sam file
        container (str): The container to use
        **kwargs: Additional arguments to pass to bowtie2
    """
    if read2 is not None:
        paired = True
    else:
        paired = False

    
    if container=="none":
        if paired:
            read1=Path(read1).absolute()
            read2=Path(read2).absolute()
            database_dir=Path(database_dir).absolute()
            outdir=Path(outdir).absolute()
            if paired:
                output_files_zipped_unaligned=Path(outdir)/f"{sample_name}_host_removed"
                output_files_zipped_aligned=Path(outdir)/f"{sample_name}_host_aligned"
                
                command =f"bowtie2 -p {config.bowtie2_cpus} -x {database_dir} -1 {read1} -2 {read2} --un-conc-gz {output_files_zipped_unaligned} --al-conc-gz {output_files_zipped_aligned}"

            
        else:
            output_files_zipped_unaligned=Path(outdir)/f"{sample_name}_host_removed"
            output_files_zipped_aligned=Path(outdir)/f"{sample_name}_host_aligned"
            
            command =f"bowtie2 -p {config.bowtie2_cpus} -x {database_dir} -U {read1} --un-gz {output_files_zipped_unaligned} --al-gz {output_files_zipped_aligned}"

                    
    elif container=="docker":
        read1=Path(read1).absolute()
        database_dir=Path(database_dir).absolute()
        outdir=Path(outdir).absolute()
        if paired:
            output_files_zipped_unaligned=Path(outdir)/f"{sample_name}_host_removed"
            output_files_zipped_aligned=Path(outdir)/f"{sample_name}_host_aligned"
            
            command =f"docker run -v {read1}:{read1} -v {read2}:{read2} -v {database_dir}:{database_dir} -v {outdir}:{outdir} {config.docker_container} bowtie2 -p {config.bowtie2_cpus} -x {database_dir} -1 {read1} -2 {read2} --un-conc-gz {output_files_zipped_unaligned} --al-conc-gz {output_files_zipped_aligned}"

        
        else:
            output_files_zipped_unaligned=Path(outdir)/f"{sample_name}_host_removed"
            output_files_zipped_aligned=Path(outdir)/f"{sample_name}_host_aligned"
            
            command =f"docker run -v {read1}:{read1} -v {database_dir}:{database_dir} -v {outdir}:{outdir} {config.docker_container} bowtie2 -p {config.bowtie2_cpus} -x {database_dir} -U {read1} --un-gz {output_files_zipped_unaligned} --al-gz {output_files_zipped_aligned}"

        
    elif container=="singularity":
        read1=Path(read1).absolute()
        database_dir=Path(database_dir).absolute()
        outdir=Path(outdir).absolute()
        if paired:
            output_files_zipped_unaligned=Path(outdir)/f"{sample_name}_host_removed"
            output_files_zipped_aligned=Path(outdir)/f"{sample_name}_host_aligned"
            
            command =f"singularity exec {config.singularity_container} bowtie2 -p {config.bowtie2_cpus} -x {database_dir} -1 {read1} -2 {read2} --un-conc-gz {output_files_zipped_unaligned} --al-conc-gz {output_files_zipped_aligned}"

        
        else:
            output_files_zipped_unaligned=Path(outdir)/f"{sample_name}_host_removed"
            output_files_zipped_aligned=Path(outdir)/f"{sample_name}_host_aligned"
            
            command =f"singularity exec  {config.singularity_container} bowtie2 -p {config.bowtie2_cpus} -x {database_dir} -U {read1} --un-gz {output_files_zipped_unaligned} --al-gz {output_files_zipped_aligned}"
    for _,value in kwargs.items():
        command = command + f" {value.pre} {value.value}"
        
        
    return command 
                


    
def convert_sam_bam_(
    sam_file:str,
    outdir:str,
    config:configs.Configs,
    container:str="none",
    **kwargs

    )->str:
    """
    This function ouputs a command to use samtools to convert a sam file to a bam file.
    
    Args:
        sam_file (str): The path to the sam file
        outdir (str): The output directory for the bam file
        container (str): The container to use
    """

    if container=="none":
        sam_file=Path(sam_file).absolute()
        outdir=Path(outdir).absolute()
        command = f"samtools view -bS {sam_file} > {outdir}"
        
    elif container=="docker":
        sam_file=Path(sam_file).absolute()
        outdir=Path(outdir).absolute()
        command = f"docker run -v {sam_file}:{sam_file} -v {outdir}:{outdir} {config.docker_container} samtools view -bS {sam_file} > {outdir}"
    
    elif container=="singularity":
        sam_file=Path(sam_file).absolute()
        outdir=Path(outdir).absolute()
        outdir_parent=Path(outdir).parent
        command = f"singularity exec -B {sam_file}:{sam_file} -B {outdir_parent}:{outdir_parent} {config.singularity_container} samtools view -bS {sam_file} > {outdir}"
        
    for _, value in kwargs.items():
        command = command + f" {value.pre} {value.value}"
    return command

def get_mapped_reads_(
    bam_file:str,
    outdir:str,
    config:configs.Configs,
    paired:bool=True,
    container:str="none",
    **kwargs
    )->str:
    """
    This function ouputs a command to use samtools to extract mapped reads from a bam file.
    
    Args:
        bam_file (str): The path to the bam file
        outdir (str): The output directory for the fastq file
        container (str): The container to use
        **kwargs: Additional arguments to pass to samtools
    
    Returns:
        str: The command to extract the mapped reads
    """
    if container=="none":
        bam_file=Path(bam_file).absolute()
        outdir=Path(outdir).absolute()
        if paired:
            command = f"samtools view -b -f 3 {bam_file} > {outdir}"
        else:
            command = f"samtools view -b -F 4 {bam_file} > {outdir}"
        
    elif container=="docker":
        bam_file=Path(bam_file).absolute()
        outdir=Path(outdir).absolute()
        if paired:
            command = f"docker run -v {bam_file}:{bam_file} -v {outdir}:{outdir} {config.docker_container} samtools view -b -f 3 {bam_file} > {outdir}"
        else:
            command = f"docker run -v {bam_file}:{bam_file} -v {outdir}:{outdir} {config.docker_container} samtools view -b -F 4 {bam_file} > {outdir}"
        
    elif container=="singularity":
        bam_file=Path(bam_file).absolute()
        outdir=Path(outdir).absolute()
        if paired:
            command = f"singularity exec -B {bam_file}:{bam_file} -B {outdir}:{outdir} {config.singularity_container} samtools view -b -f 3 {bam_file} > {outdir}"
        else:
            command = f"singularity exec -B {bam_file}:{bam_file} -B {outdir}:{outdir} {config.singularity_container} samtools view -b -F 4 {bam_file} > {outdir}"

    for _, value in kwargs.items():
        command = command + f" {value.pre} {value.value}"
        
    return command






def get_unmapped_reads_(
    bam_file:str,
    outdir:str,
    config:configs.Configs,
    paired:bool=True,
    container:str="none",
    **kwargs
    )->str:
    """
    This function ouputs a command to use samtools to extract unmapped reads from a bam file.

    Args:
        bam_file (str): The path to the bam file
        outdir (str): The output directory for the fastq file
        container (str): The container to use
        **kwargs: Additional arguments to pass to samtools
    
    Returns:
        str: The command to extract the unmapped reads
    """
    if container=="none":
        bam_file=Path(bam_file).absolute()
        outdir=Path(outdir).absolute()
        if paired:
            command = f"samtools view -b -f 12 -F 256 {bam_file} > {outdir}"
        else:
            command = f"samtools view -b -f 4 {bam_file} > {outdir}"
            
    elif container=="docker":
        bam_file=Path(bam_file).absolute()
        outdir=Path(outdir).absolute()
        if paired:
            command = f"docker run -v {bam_file}:{bam_file} -v {outdir}:{outdir} {config.docker_container} samtools view -b -f 12 -F 256 {bam_file} > {outdir}"
        else:
            command = f"docker run -v {bam_file}:{bam_file} -v {outdir}:{outdir} {config.docker_container} samtools view -b -f 4 {bam_file} > {outdir}"
    
    elif container=="singularity":
        bam_file=Path(bam_file).absolute()
        outdir=Path(outdir).absolute()
        if paired:
            command = f"singularity exec -B {bam_file}:{bam_file} -B {outdir}:{outdir} {config.singularity_container} samtools view -b -f 12 -F 256 {bam_file} > {outdir}"
        else:
            command = f"singularity exec -B {bam_file}:{bam_file} -B {outdir}:{outdir} {config.singularity_container} samtools view -b -f 4 {bam_file} > {outdir}"
    
    for _, value in kwargs.items():
        command = command + f" {value.pre} {value.value}"
        
    return command

def sort_bam_(
    bam_file:str,
    outdir:str,
    config:configs.Configs,
    container:str="none",
    **kwargs
    )->str:
    """
    This function ouputs a command to use samtools to sort a bam file.
    
    Args:
        bam_file (str): The path to the bam file
        outdir (str): The output directory for the sorted bam file
        container (str): The container to use
        **kwargs: Additional arguments to pass to samtools
    
    Returns:
        str: The command to sort the bam file
    """
    
    if container=="none":
        bam_file=Path(bam_file).absolute()
        outdir=Path(outdir).absolute()
        command = f"samtools sort -n "
        
        command = command + f"{bam_file} -o {outdir}"
    
    elif container=="docker":
        bam_file=Path(bam_file).absolute()
        outdir=Path(outdir).absolute()
        command = f"docker run -v {bam_file}:{bam_file} -v {outdir}:{outdir} {config.docker_container} samtools sort -n "
        
        command = command + f"{bam_file} -o {outdir}"
    
    elif container=="singularity":
        bam_file=Path(bam_file).absolute()
        outdir=Path(outdir).absolute()
        outdir_parent=Path(outdir).parent
        command = f"singularity exec --bind {bam_file}:{bam_file},{outdir_parent}:{outdir_parent}  {config.singularity_container} samtools sort -n "

        
        command = command + f"{bam_file} -o {outdir}"
    
    for _, value in kwargs.items():
        command = command + f" {value.pre} {value.value}"
    return command

def sam_tools_fasq_(
    input_file:str,
    outdir1:str,
    outdir2:str|None,
    config:configs.Configs,
    paired:bool=True,
    container:str="none",
    **kwargs: dict[str, configs.kwgs_tuple]
    )->str:
    """
    This function ouputs a command to use samtools to convert a bam file to a fastq file.

    Args:
        input_file (str): The path to the input file
        paired (bool): Whether the input file is from a paired sequence alignment
        outdir1 (str): The output directory for the first fastq file
        outdir2 (str): The output directory for the second fastq file
        container (str): The container to use
        
    Returns:
        str: The command to convert the bam file to a fastq file
    
    """
    if container=="none":
        input_file=Path(input_file).absolute()
        outdir1=Path(outdir1).absolute()
        if paired:
            outdir2=Path(outdir2).absolute()
            command = f"samtools fastq -1 {outdir1} -2 {outdir2} {input_file}"
        else:
            command = f"samtools fastq {outdir1} > {input_file}"
    
    elif container=="docker":
        input_file=Path(input_file).absolute()
        outdir1=Path(outdir1).absolute()
        if paired:
            outdir2=Path(outdir2).absolute()
            command = f"docker run -v {input_file}:{input_file} -v {outdir1}:{outdir1} -v {outdir2}:{outdir2} {config.docker_container} samtools fastq -1 {outdir1} -2 {outdir2} {input_file}"
        else:
            command = f"docker run -v {input_file}:{input_file} -v {outdir1}:{outdir1} {config.docker_container} samtools fastq {outdir1} > {input_file}"
    
    elif container=="singularity":
        input_file=Path(input_file).absolute()
        outdir1=Path(outdir1).absolute()
        if paired:
            outdir2=Path(outdir2).absolute()
            command = f"singularity exec -B {input_file}:{input_file} -B {outdir1}:{outdir1} -B {outdir2}:{outdir2} {config.singularity_container} samtools fastq -1 {outdir1} -2 {outdir2} {input_file}"
        else:
            command = f"singularity exec -B {input_file}:{input_file} -B {outdir1}:{outdir1} {config.singularity_container} samtools fastq {outdir1} > {input_file}"
    
    for _, value in kwargs.items():
        command = command + f" {value.pre} {value.value}"
    return command

def sam_tools_fasta_(
    input_file:str,
    outdir:str,
    config:configs.Configs,
    container:str="none",
    **kwargs: dict[str, configs.kwgs_tuple]
    )->str:
    
    """
    This function ouputs a command to use samtools to convert a bam file to a fasta file.
    
    Args:
        input_file (str): The path to the input file
        outdir (str): The output directory for the fasta file
        container (str): The container to use
        
    Returns:
        str: The command to convert the bam file to a fasta file
    """
    if container=="none":
        input_file=str(Path(input_file).absolute())
        outdir=str(Path(outdir).absolute())
        command = f"samtools fasta {input_file} > {outdir}"
    
    elif container=="docker":
        input_file=str(Path(input_file).absolute())
        outdir=str(Path(outdir).absolute())
        command = f"docker run -v {input_file}:{input_file} -v {outdir}:{outdir} {config.docker_container} samtools fasta {input_file} > {outdir}"
    
    elif container=="singularity":
        input_file=str(Path(input_file).absolute())
        outdir_parent=str(Path(outdir).parent.absolute())
        command = f"singularity exec -B {input_file}:{input_file} -B {outdir}:{outdir} {config.singularity_container} samtools fasta {input_file} > {outdir}"
    for _, value in kwargs.items():
        command = command + f" {value.pre} {value.value}"
        
    return command

    
def index_bwa_(
    sequence_dir:str,
    config:configs.Configs,
    container:str="none",
    **kwargs: dict[str, configs.kwgs_tuple]
    )->str:
    """
    This function ouputs a command to use bwa to index a genome.
    
    Args:
        sequence_dir (str): The path to the fasta file
        container (str): The container to use
        **kwargs: Additional arguments to pass to bwa
    """
    if container=="none":
        sequence_dir=Path(sequence_dir).absolute()
        command = f"bwa index {sequence_dir}"

        
    elif container=="docker":
        sequence_dir=Path(sequence_dir).absolute()
        command = f"docker run -v {sequence_dir}:{sequence_dir} {config.docker_container} bwa index {sequence_dir}"
    
    elif container=="singularity":
        sequence_dir=Path(sequence_dir).absolute()
        command = f"singularity exec {config.singularity_container} bwa index {sequence_dir}"
    for _,value in kwargs.items():
        command = command + f" --{value.pre} {value.value}"
        
    return command


def align_bwa_(
    read1:str,
    read2:str|None,
    database_dir:str,
    outdir:str,
    config:configs.Configs,
    container:str="none",
    **kwargs: dict[str, configs.kwgs_tuple]
    )->str:
    """
    This function ouputs a command to use bwa to align fastq files to a genome.
    
    Args:
        read1 (str): The path to the first fastq file
        read2 (str): The path to the second fastq file
        database_dir (str): The path to the indexed genome
        outdir (str): The output directory for the sam file
        container (str): The container to use
        **kwargs: Additional arguments to pass to bwa
    """
    
    if read2 is not None:
        paired = True
    else:
        paired = False
    
    if container=="none":
        if paired:
            read1=Path(read1).absolute()
            read2=Path(read2).absolute()
            database_dir=Path(database_dir).absolute()
            outdir=Path(outdir).absolute()
            command = f"bwa mem -t {config.bwa_cpus} {database_dir} {read1} {read2} > {outdir}"

        
        else:
            read1=Path(read1).absolute()
            database_dir=Path(database_dir).absolute()
            outdir=Path(outdir).absolute()
            command = f"bwa mem  -t {config.bwa_cpus} {database_dir} {read1} > {outdir}"

        
    elif container=="docker":
        if paired:
            read1=Path(read1).absolute()
            read2=Path(read2).absolute()
            database_dir=Path(database_dir).absolute()
            outdir=Path(outdir).absolute()
            command = f"docker run -v {read1}:{read1} -v {read2}:{read2} -v {database_dir}:{database_dir} -v {outdir}:{outdir} {config.docker_container} bwa mem  -t {config.bwa_cpus} {database_dir} {read1} {read2} > {outdir}"


        else:
            read1=Path(read1).absolute()
            database_dir=Path(database_dir).absolute()
            outdir=Path(outdir).absolute()
            command = f"docker run -v {read1}:{read1} -v {database_dir}:{database_dir} -v {outdir}:{outdir} {config.docker_container} bwa mem {database_dir} {read1} > {outdir}"


                    
    elif container=="singularity":
        if paired:
            read1=Path(read1).absolute()
            read2=Path(read2).absolute()
            database_dir=Path(database_dir).absolute()
            outdir=Path(outdir).absolute()
            command = f"singularity exec  {config.singularity_container} bwa mem -t {config.bwa_cpus} {database_dir} {read1} {read2} > {outdir}"


        else:
            read1=Path(read1).absolute()
            database_dir=Path(database_dir).absolute()
            outdir=Path(outdir).absolute()
            command = f"singularity exec {config.singularity_container} bwa mem -t {config.bwa_cpus} {database_dir} {read1} > {outdir}"
    for _,value in kwargs.items():
        command = command + f" --{value.pre} {value.value}"
                
    
    return command

def find_circular_cirit_(
    input_file:str,
    output_file:str,
    cirit_jar_file_dir:str,
    config:configs.Configs,
    container:str="none",
    **kwargs: dict[str, configs.kwgs_tuple]
    )->str:
    """
    This function ouputs a command to use cirit to find circular RNA.

    Args:
        input_file (str): The path to the input file (usually a fasta file)
        output_file (str): The path to the output file (a fasta file including the circular sequences)
        cirit_jar_file_dir (str): The path to the cirit jar file
        container (str): The container to use
        **kwargs: Additional arguments to pass to cirit
    
    Returns:
        str: The command to run cirit
    """
    input_file=str(Path(input_file).absolute())
    output_file=str(Path(output_file).absolute())
    cirit_jar_file_dir=str(Path(cirit_jar_file_dir).absolute())
    output_file_parent=str(Path(output_file).parent)
    
    if container=="none":
        command = f"java -jar {cirit_jar_file_dir} -i {input_file} -o {output_file}"

    
    elif container=="docker":
        command = f"docker run -v {input_file}:{input_file} -v {output_file_parent}:{output_file_parent} -v {cirit_jar_file_dir}:{cirit_jar_file_dir} {config.docker_container} java -jar {cirit_jar_file_dir} -i {input_file} -o {output_file}"

            
    
    elif container=="singularity":
        
        command = f"singularity exec --bind {input_file}:{input_file},{output_file_parent}:{output_file_parent},{cirit_jar_file_dir}:{cirit_jar_file_dir} {config.singularity_container} java -jar {cirit_jar_file_dir} -i {input_file} -o {output_file}"

            
    else :
        raise ValueError("Invalid container")   
    
    for _, value in kwargs.items():
        command = command + f" {value.pre} {value.value}"
    return command


def mmseqs_create_db_(
    sequence_dir:str,
    output_dir:str,
    config:configs.Configs,
    container:str="none",
    **kwargs: dict[str, configs.kwgs_tuple]
    )->str:
    """
    This function ouputs a command to use mmseqs to create a database from a fasta file.

    Args:
        sequence_dir (str): The path to the fasta file
        output_dir (str): The directory for the database files
        container (str): The container to use
        
    Returns:
        str: The command to index the fasta file
    """
    sequence_dir=str(Path(sequence_dir).absolute())
    output_dir=str(Path(output_dir).absolute())
    output_dir_parent=str(Path(output_dir).parent.absolute())
    
    if container=="none":
        command = f"mmseqs createdb {sequence_dir} {output_dir}"

    
    elif container=="docker":
        command = f"docker run -v {sequence_dir}:{sequence_dir} -v {output_dir_parent}:{output_dir_parent} {config.docker_container} mmseqs createdb {sequence_dir} {output_dir}"

    
    elif container=="singularity":
        command = f"singularity exec --bind {sequence_dir}:{sequence_dir},{output_dir_parent}:{output_dir_parent} {config.singularity_container} mmseqs createdb {sequence_dir} {output_dir}"

    else :
        raise ValueError("Invalid container")
    
    for _, value in kwargs.items():
        command = command + f" {value.pre} {value.value}"

    return command

def mmseqs_index_db_(
    db_dir:str,
    config:configs.Configs,
    container:str="none",
    **kwargs: dict[str, configs.kwgs_tuple]
    )->str:
    """
    This function ouputs a command to use mmseqs to index a database.

    Args:
        db_dir (str): The path to the database
        config (configs.Configs): The configuration object to use
        container (str): The container to use
        
    Returns:
        str: The command to index the database
    """
    db_dir=str(Path(db_dir).absolute())
    tmp_dir=str(Path(db_dir).parent.absolute())
    
    if container=="none":
        command = f"mmseqs createindex {db_dir} {tmp_dir}"

    
    elif container=="docker":
        command = f"docker run -v {db_dir}:{db_dir} -v {tmp_dir}:{tmp_dir} {config.docker_container} mmseqs createindex {db_dir} {tmp_dir}/tmp"

    
    elif container=="singularity":
        command = f"singularity exec --bind {db_dir}:{db_dir},{tmp_dir}:{tmp_dir} {config.singularity_container} mmseqs createindex {db_dir} {tmp_dir}/tmp"

    else :
        raise ValueError("Invalid container")
    
    for _, value in kwargs.items():
        command = command + f" {value.pre} {value.value}"
        
    return command

def mmseqs_search_(
    db_dir:str,
    query_file:str,
    output_file:str,
    config:configs.Configs,
    container:str="none",
    **kwargs
    )->str:
    """
    This function ouputs a command to use mmseqs to search a database.

    Args:
        db_dir (str): The path to the database
        query_file (str): The path to the query file
        output_file (str): The path to the output file
        config (configs.Configs): The configuration object to use
        container (str): The container to use
        
    Returns:
        str: The command to search the database
    """
    db_dir=str(Path(db_dir).absolute())
    query_file=str(Path(query_file).absolute())
    output_file=str(Path(output_file).absolute())
    output_file_parent=str(Path(output_file).parent.absolute())
    
    if container=="none":
        command = f"mmseqs search {query_file} {db_dir} {output_file} {output_file_parent}/tmp"

    
    elif container=="docker":
        command = f"docker run -v {db_dir}:{db_dir} -v {query_file}:{query_file} -v {output_file_parent}:{output_file_parent} {config.docker_container} mmseqs search {query_file} {db_dir} {output_file} {output_file_parent}/tmp"

    
    elif container=="singularity":
        command = f"singularity exec --bind {db_dir}:{db_dir},{query_file}:{query_file},{output_file_parent}:{output_file_parent} {config.singularity_container} mmseqs search {query_file} {db_dir} {output_file} {output_file_parent}/tmp"
        
    else :
        raise ValueError("Invalid container")
    
    for _, value in kwargs.items():
        command = command + f" {value.pre} {value.value}"
    
    return command


def mmseqs_convert_to_flat_(
    query_db:str,
    target_db:str,
    result_db:str,
    results_table:str,
    config:configs.Configs,
    mode:str="4",
    container:str="none",
    **kwargs
    )->str:
    """
    This function ouputs a command to use mmseqs to convert a search result to a flat file.

    Args:
        query_db (str): The path to the query database
        target_db (str): The path to the target database
        result_db (str): The path to the result database
        results_table (str): The path to the results table
        config (configs.Configs): The configuration object to use
        container (str): The container to use
    
    Returns:
        str: The command to convert the search result to a flat file
    """
    query_db=str(Path(query_db).absolute())
    target_db=str(Path(target_db).absolute())
    result_db=str(Path(result_db).absolute())
    results_table=str(Path(results_table).absolute())
    results_table_parent=str(Path(results_table).parent.absolute())
    
    if container=="none":
        command = f"mmseqs convertalis {query_db} {target_db} {result_db} {results_table} --format-mode {mode}"

        
    
    elif container=="docker":
        command = f"docker run -v {query_db}:{query_db} -v {target_db}:{target_db} -v {result_db}:{result_db} -v {results_table_parent}:{results_table_parent} {config.docker_container} mmseqs convertalis {query_db} {target_db} {result_db} {results_table} --format-mode {mode}"

            
    elif container=="singularity":
        command = f"singularity exec --bind {query_db}:{query_db},{target_db}:{target_db},{result_db}:{result_db},{results_table_parent}:{results_table_parent} {config.singularity_container} mmseqs convertalis {query_db} {target_db} {result_db} {results_table} --format-mode {mode}"

    else :
        raise ValueError("Invalid container")
    
    for _, value in kwargs.items():
        command = command + f" {value.pre} {value.value}"
    return command

def mmseqs_easy_search_(
    query_file:str,
    target_file:str,
    output_file:str,
    config:configs.Configs,
    container:str="none",
    **kwargs
    )->str:
    """
    This function ouputs a command to use mmseqs to search a database in fasta/fastq format.
    It is good for when alignment is done against the database once or database is small.

    Args:
        query_file (str): The path to the query file
        target_file (str): The path to the target file
        output_file (str): The path to the output file
        config (configs.Configs): The configuration object to use
        container (str): The container to use
    
    Returns:
        str: The command to search the database
    """
    
    query_file=str(Path(query_file).absolute())
    target_file=str(Path(target_file).absolute())
    output_file=str(Path(output_file).absolute())
    output_file_parent=str(Path(output_file).parent.absolute())
    
    if container=="none":
        command = f"mmseqs easy-search {query_file} {target_file} {output_file} {output_file_parent}/tmp"

            
    elif container=="docker":
        command = f"docker run -v {query_file}:{query_file} -v {target_file}:{target_file} -v {output_file_parent}:{output_file_parent} {config.docker_container} mmseqs easy-search {query_file} {target_file} {output_file} {output_file_parent}/tmp"

    
    elif container=="singularity":
        command = f"singularity exec --bind {query_file}:{query_file},{target_file}:{target_file},{output_file_parent}:{output_file_parent} {config.singularity_container} mmseqs easy-search {query_file} {target_file} {output_file} {output_file_parent}/tmp"
        
    else :
        raise ValueError("Invalid container")
    
    for _, value in kwargs.items():
        command = command + f" {value.pre} {value.value}"
        
            
    return command
    
def mmseqs_download_database_(
    database_name:str,
    output_dir:str,
    config:configs.Configs,
    container:str="none",
    **kwargs: dict[str, configs.kwgs_tuple]
    )->str:
    """
    This function ouputs a command to use mmseqs to download a database.
    
    Args:
        database_name (str): The name of the database
        output_dir (str): The output directory for the database
        config (configs.Configs): The configuration object to use
        container (str): The container to use
    
    Returns:
        str: The command to download the database
    
    """
    output_dir=str(Path(output_dir).absolute())
    output_dir_parent=str(Path(output_dir).parent.absolute())
    
    if container=="none":
        command = f"mmseqs databases {database_name} {output_dir} {output_dir_parent}/tmp"

    
    elif container=="docker":
        command = f"docker run -v {output_dir_parent}:{output_dir_parent} {config.docker_container} mmseqs databases {database_name} {output_dir} {output_dir_parent}/tmp"

    
    elif container=="singularity":
        command = f"singularity exec --bind {output_dir_parent}:{output_dir_parent} {config.singularity_container} mmseqs databases {database_name} {output_dir} {output_dir_parent}/tmp"

    else :
        raise ValueError("Invalid container")
    
    for _, value in kwargs.items():
        command = command + f" {value.pre} {value.value}"
        
    return command
def fastani_compare_genomes_(
    query_genomes:str|Iterable[str],
    reference_genomes:str|Iterable[str],
    output_file:str,
    config:configs.Configs,
    container:str="none",
    **kwargs: dict[str, configs.kwgs_tuple]
    )->str:
    """
    This function ouputs a command to use fastANI to compare genomes.
    
    Args:
        query_genomes (str|Iterable): The path to the query genomes
        reference_genomes (str|Iterable): The path to the reference genomes
        output_file (str): The path to the output file
        container (str): The container to use
        **kwargs: Additional arguments to pass to fastANI
    
    Returns:
        str: The command to compare genomes
    """
    if isinstance(query_genomes,str):
        query_genomes=[query_genomes]
    if isinstance(reference_genomes,str):
        reference_genomes=[reference_genomes]
    query_genomes=[str(Path(x).absolute()) for x in query_genomes]
    query_genomes_parent=list(set(str(Path(x).parent.absolute()) for x in query_genomes))
    reference_genomes=[str(Path(x).absolute()) for x in reference_genomes]
    reference_genomes_parent=list(set(str(Path(x).parent.absolute()) for x in reference_genomes))
    output_file=str(Path(output_file).absolute())
    output_file_parent=str(Path(output_file).parent.absolute())
    tmp_dir_q=Path(output_file).parent/"tmp_q"
    tmp_dir_r=Path(output_file).parent/"tmp_r"
    with open(tmp_dir_q,"w") as f:
        for x in query_genomes:
            f.write(x+"\n")
    with open(tmp_dir_r,"w") as f:
        for x in reference_genomes:
            f.write(x+"\n")
    
    if container=="none":
        command = f"fastANI --ql {tmp_dir_q} --rl {tmp_dir_r} -o {output_file}"

    
    elif container=="docker":
        bind_paths=" -v ".join([i+":"+i for i in query_genomes_parent+reference_genomes_parent+[output_file_parent]])
        command = f"docker run -v {bind_paths} {config.docker_container} fastANI --ql {tmp_dir_q} --rl {tmp_dir_r} -o {output_file}"


    
    elif container=="singularity":
        bind_paths=",".join([i+":"+i for i in query_genomes_parent+reference_genomes_parent+[output_file_parent]])
        command = f"singularity exec --bind {bind_paths} {config.singularity_container} fastANI --ql {tmp_dir_q} --rl {tmp_dir_r} -o {output_file}"

        
    
    else:
        raise ValueError("Invalid container")
    
    for _, value in kwargs.items():
        command = command + f" {value.pre} {value.value}"
    
    return command