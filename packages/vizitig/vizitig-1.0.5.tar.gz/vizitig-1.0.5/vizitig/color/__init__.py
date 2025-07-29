import gzip
import os
from os.path import isfile, join
from datetime import datetime
from pathlib import Path
from typing import Callable, IO

from vizitig.cli import subparsers
from vizitig.info import get_graph, reload_graph
from vizitig.parsing import parse_fasta_dna, parse_fasta_with_bcalm_abundances
from vizitig.types import Color
from vizitig.color.bulk_update import bulk_annotate_graph
from vizitig.utils import SubLog
from vizitig.errors import FormatInputError, InvalidPath, ParseError
from vizitig.utils import vizitig_logger as logger
from vizitig.types import DNA


now = datetime.now


def main(args):
    if args.abundances:
        color_method = color_with_abundance
    else:
        color_method = color_graph
        # with SubLog("Color"):
        #     color_with_abundance(
        #         args.graph_name,
        #         args.metadata_name,
        #         args.metadata_description,
        #         args.file,
        #         buffer_size=args.buffer_size,
        #     )

    if args.folder and args.metadata_name:
        if args.abundances:
            logger.warn(
                "Abundances cannot be ingested with a single metadata for a folder. Remove metadata name or use vizitig color -h to get help."
            )
        try:
            d = args.description
        except AttributeError:
            d = ""
        with SubLog("Color_with_folder_and_metadata"):
            color_graph_with_folder_and_meta(
                args.graph_name, args.metadata_name, d, args.folder, args.buffer_size
            )

    elif args.folder:
        try:
            assert os.path.isdir(args.folder)
        except AssertionError:
            raise InvalidPath(
                "The provided path is not a folder or is not a valid path. "
            )
        files = [f for f in os.listdir(args.folder) if isfile(join(args.folder, f))]
        for file_name in files:
            file = Path(args.folder) / file_name
            with SubLog("Color"):
                color_method(
                    args.graph_name,
                    file_name.split(".")[0],
                    "",
                    file,
                    buffer_size=args.buffer_size,
                )

    elif args.csv_file:
        graph_name = args.graph_name  # namespace issue
        buffer_size = args.buffer_size  # namespace issue
        try:
            with open(args.csv_file, "r") as handle:
                for line in handle:
                    args = line.split("\t")
                    if len(args) == 2:
                        file_name, metadata_name = args
                        description = ""
                    elif len(args) == 3:
                        file_name, metadata_name, description = args
                    else:
                        raise ParseError(
                            "CSV file does not respect the format. Type vizitig color -h to get documentation."
                        )

                    try:
                        with SubLog("Color"):
                            color_method(
                                graph_name,
                                metadata_name,
                                description,
                                Path(file_name),
                                buffer_size=buffer_size,
                            )
                    except FormatInputError:
                        logger.warning(
                            "File {} it of unknown format. This file will be skipped.".format(
                                file_name
                            )
                        )

        except FileNotFoundError:
            raise InvalidPath("The path to csv file was not found. Aborting")

    else:
        with SubLog("Color"):
            color_method(
                args.graph_name,
                args.metadata_name,
                args.metadata_description,
                args.file,
                args.abundances,
            )


valid_extensions = (".fa", ".fna", ".gz", ".fasta")


def color_graph_with_folder_and_meta(
    graph_name: str, m: str, d: str, folder: Path, buffer_size=10**6
):
    G = get_graph(graph_name)
    color = G.metadata.add_metadata(
        Color(id=m, description=d),
    )
    ret_int = G.metadata.encoder(color)

    def generator():
        files = [f for f in os.listdir(folder) if isfile(join(folder, f))]
        for file_name in files:
            file = Path(folder) / file_name
            if file.suffix not in valid_extensions:
                logger.warn("File extension not supported. Skipping {}".format(file))
            if file.suffix == ".gz":
                handle = gzip.open
            else:
                handle = open
            with handle(file, "rt") as file:
                for dna in parse_fasta_dna(file, G.metadata.k, buffer_size=buffer_size):
                    yield (dna, ret_int)

    bulk_annotate_graph(graph_name, generator)


def color_graph(graph_name, m: str, d: str, file: Path, buffer_size=10**6):
    G = get_graph(graph_name)
    GM = G.metadata
    color = GM.add_metadata(
        Color(id=m, description=d),
    )

    GM.commit_to_graph()

    if file.suffix not in valid_extensions:
        raise FormatInputError(
            f"Invalid format extension {file.suffix} not in {valid_extensions}"
        )
    logger.info(f"Coloring graph {graph_name} with {str(file)}")

    def dna_generator(file=file):
        ret_int = GM.encoder(color)
        openfile = open
        if file.suffix == ".gz":
            openfile = gzip.open
        with openfile(file, "rt") as file:
            for dna in parse_fasta_dna(file, GM.k, buffer_size):
                yield (dna, ret_int)

    with SubLog("bulk_annotate_graph"):
        bulk_annotate_graph(graph_name, dna_generator)
    reload_graph(graph_name)


def color_with_abundance(graph_name, m: str, d: str, file: Path, buffer_size=10**6):
    G = get_graph(graph_name)
    GM = G.metadata
    color = GM.add_metadata(
        Color(id=m, description=d),
    )

    GM.commit_to_graph()

    if file.suffix not in valid_extensions:
        raise FormatInputError(
            f"Invalid format extension {file.suffix} not in {valid_extensions}"
        )
    logger.info(f"Coloring graph {graph_name} with {str(file)}")

    openfile: Callable[..., IO] = open
    if file.suffix == ".gz":
        openfile = gzip.open

    def dna_generator(file=file):
        with openfile(file, "rt") as file:
            for dna, abundance in parse_fasta_with_bcalm_abundances(file):
                assert isinstance(dna, DNA)
                yield (dna, int(abundance))

    with SubLog("bulk_annotate_graph_with_abundances"):
        bulk_annotate_graph(graph_name, dna_generator, color)

    reload_graph(graph_name)


parser = subparsers.add_parser(
    "color",
    help="""Color an existing graph. There are several ways to use this feature : 
    -vizitig color -f file_name -m color_name -> Will color the graph with whatever is in the provided file
    -vizitig color --folder folder_name -> Will color the graph with every file in the provided folder. The name of the color will be the name of the file for each file
    -vizitig color --folder folder_name -m color_name -> Same, but the name of the color will be color_name for all files
    -vizitig color --csv file.csv -> Will use a csv file to color the graph. Csv must respect the following format (tabèseparated):

    /path/to/file1        red           "Sample 1 - control group"
    /path/to/file2        green         "Sample 2 - condition 1"
    /path/to/file3        blue          "Sample 3 - condition 2"
    """,
)

parser.add_argument(
    "--folder",
    metavar="folder",
    type=str,
    help="""
    A folder path. Every parsable file of the folder will be used to color the graph. 
    Use argument -m to give a name to this color, otherwise the name of the files will be used.
    If you want to assign a file to a color and a description, consider using vizitig color --csv. 
    """,
)

parser.add_argument(
    "--csv_file",
    metavar="csv_file",
    type=str,
    help="""A csv file to use for coloring a graph. Must respect the following format (tab-separated):
    /path/to/file1        red           "Sample 1 - control group"
    /path/to/file2        green         "Sample 2 - condition 1"
    /path/to/file3        blue          "Sample 3 - condition 2"
    """,
)
parser.add_argument(
    "graph_name",
    help="A graph name. List possible graph with python3 -m vizitig info",
    metavar="graph",
    type=str,
)

parser.add_argument(
    "-m",
    "--metadata_name",
    help="A key to identify the metadata to add to the graph",
    metavar="metadata_name",
    required=False,
    type=str,
)

parser.add_argument(
    "-d",
    "--metadata-description",
    help="A description of the metadata",
    metavar="description",
    type=str,
    default="",
)

parser.add_argument(
    "-f",
    "--file",
    help="Path toward file containing DNA (fasta or bcalm format)",
    metavar="file",
    type=Path,
)

parser.add_argument(
    "-b",
    "--buffer-size",
    help="Maximum size of a buffer",
    metavar="buffer",
    type=int,
    default=10**6,
)

parser.add_argument(
    "-c",
    "--color",
    help="Default color to use in the vizualisation. Default is None",
    metavar="color",
    type=str,
)

parser.add_argument(
    "-abundances",
    action="store_true",
    default=False,
    help="""Activates abundance injestion. This means that the abundances in the file will be tagged on the graph. File must be a valid BCALM file with defaut abundance formation (i.e 'km:f:value')
    Note that the unitigs of this BCALM may not equals the unitigs of the graph you have currently ingested. In this case, the abundances of unitigs may be found on several nodes. The abundance
    ingestion is not compatible with the 'folder' parameter. You can use csv-file argument if you need to ingest abundances with a lot of files.
    """,
)

parser.set_defaults(func=main)
