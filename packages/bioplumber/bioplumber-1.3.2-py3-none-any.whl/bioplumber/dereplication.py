from typing import Iterable
from bioplumber import configs
import pathlib
def drep_dereplicate_(
    genomes_dir: str,
    output_dir: str,
    config: configs.Configs,
    genomes_extension: str=".fa",
    container: str = "none",
    **kwargs: dict[str, configs.kwgs_tuple]
)->str:
    """
    Dereplicate genomes using dRep.

    Args:
    genomes (str): Path to genomes.
    output_dir (str): Path to output directory.
    config (configs.Configs): Configuration object.
    genomes_extension (str): File extension for genomes. Defaults to ".fa".
    container (str): Software container to use. Defaults to "none".
    **kwargs: Additional arguments to pass to the function.
    
    Returns:
    str: command to execute drep
    """
    genomes=pathlib.Path(genomes_dir).absolute()
    output_dir=pathlib.Path(output_dir).absolute()
    if container == "none":
        cmd = f"dRep dereplicate {str(output_dir)} -g {str(genomes/('*'+genomes_extension))}"

    
    elif container == "docker":
        cmd = f"docker run -it -v {genomes}:{genomes} -v {output_dir}:{output_dir} {config.docker_container} dRep dereplicate {str(output_dir)} -g {str(genomes/('*'+genomes_extension))}"

            

    elif container == "singularity":
        cmd = f"singularity exec --bind {genomes}:{genomes} --bind {output_dir}:{output_dir} {config.singularity_container} dRep dereplicate {str(output_dir)} -g {str(genomes/('*'+genomes_extension))}"

    else:
        raise ValueError("Container not supported")
    
    for _, value in kwargs.items():
        cmd += f" {value.pre} {value.value}"
    return cmd