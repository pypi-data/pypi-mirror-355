from pathlib import Path
from typing import Tuple, Iterator, Literal, TypeAlias, get_args, List

from vizitig.cli import subparsers
from vizitig.info import get_graph, reload_graph
from vizitig.parsing import (
    parse_annotations,
    parse_reference_sequence_for_full_annotation,
    parse_transcript_or_exon_refseq,
)
from vizitig.errors import ParseError, FormatInputError
from vizitig.types import DNA, SubseqData
from vizitig.color.bulk_update import bulk_annotate_graph
from vizitig.utils import SubLog
from vizitig.utils import vizitig_logger as logger, progress
import re


def annotate_genome(
    graph_name: str, metadata: Path, ref_seq: Path, select_only: List[str] | None = None
):
    with SubLog("Annotate annotate"):
        Graph = get_graph(graph_name)
        k = Graph.metadata.k

        if select_only is not None:
            annotation_data: list[SubseqData] = list(  # type: ignore
                elem
                for elem in parse_annotations(metadata, k)
                if elem.type.lower() in select_only
            )
        else:
            annotation_data: list[SubseqData] = list(  # type: ignore
                elem for elem in parse_annotations(metadata, k)
            )

        l: int = len(annotation_data)
        logger.info("Found {} annotations. Ingesting annotations.".format(l))

        annotation_data = Graph.metadata.add_iterative_metadatas(
            progress(annotation_data, l)
        )

        logger.info("Metadata were ingested. Procceding to annotate.")

        if not annotation_data:
            raise ParseError("No metadata found in the GFT or GFF file")

        def generator() -> Iterator[Tuple[DNA, int]]:
            it = parse_reference_sequence_for_full_annotation(
                ref_seq,
                annotation_data,
                k,
            )
            
            for meta, dna in it:
                if len(dna) > k:
                    yield (dna, Graph.metadata.encoder(meta))

        bulk_annotate_graph(graph_name, generator)

        Graph.metadata.commit_to_graph()
        reload_graph(graph_name)


annotate_metadata_type: TypeAlias = Literal["Exon", "Transcript"]


def annotate_other(
    graph_name: str,
    metadata_type: str,
    refseqs_file: Path,
    annotation_file: Path | None,
    select_only: List[str] | None = None,
):
    with SubLog("Annotate annotate"):
        Graph = get_graph(graph_name)

        logger.info("Adding all metadata to graph metadata before ingestion")

        parser = parse_transcript_or_exon_refseq(refseqs_file)

        if metadata_type not in get_args(annotate_metadata_type):
            raise FormatInputError(
                f"metadata_type {metadata_type} not in {get_args(annotate_metadata_type)}"
            )

        metas = []
        for i, elem in enumerate(parser):
            if metadata_type == "Exon":
                meta: SubseqData = str_to_exon(elem, i, meta_only=True)  # type: ignore
            elif metadata_type == "Transcript":
                meta, _ = str_to_transcript(elem)
            metas.append(meta)

        if annotation_file:
            logger.info(
                "Annotating graph {} with {} reference sequences and annotation file {}.".format(
                    graph_name, metadata_type, annotation_file
                )
            )
            for meta in parse_annotations(annotation_file, Graph.metadata.k):
                if select_only is None or meta.type.lower() in select_only:
                    metas.append(meta)

        else:
            logger.info(
                "Annotating graph {} with {} reference sequences.".format(
                    graph_name, metadata_type
                )
            )

        metas = Graph.metadata.add_iterative_metadatas(metas)

        metas_dict = {m.short_repr(): -m.offset for m in metas if m.offset is not None}

        def generator() -> Iterator[Tuple[DNA, int]]:
            parser = parse_transcript_or_exon_refseq(refseqs_file)
            for i, elem in enumerate(parser):
                if metadata_type == "Exon":
                    res = str_to_exon(elem, i)
                    assert isinstance(res, tuple)
                    metadata, sequences = res
                elif metadata_type == "Transcript":
                    metadata, sequences = str_to_transcript(elem)
                else:
                    raise NotImplementedError
                # enc = Graph.metadata.encoder(metadata)
                for s in sequences:
                    yield (s, -metas_dict[metadata.short_repr()])

        bulk_annotate_graph(graph_name, generator, metas=metas)
        reload_graph(graph_name)


def main(args) -> None:
    assert args.graph_name
    select_only: List[str] | None = (
        [elem.lower() for elem in args.select_only] if args.select_only else None
    )

    if args.genome:
        try:
            assert Path(args.metadata)
        except AssertionError:
            logger.warning(
                """
                You are trying to annotate a graph with a refseq but without metadata.
                Consider using vizitig color instead. 
                Use vizitig -h, vizitig color -h or vizitig annotate -h to get help. 
            """
            )
        logger.info(
            "Annotating graph {} with reference sequence and annotation file".format(
                args.graph_name
            )
        )

        annotate_genome(
            args.graph_name, Path(args.metadata), Path(args.genome), select_only
        )
        return

    if (args.exons and args.transcripts) or not (args.exons or args.transcripts):
        raise FormatInputError(
            "Incorrect arguments. Please choose between Transcripts or Exons ingestion."
        )

    if args.exons:
        refseqs_file = args.exons
        metadata_type = "Exon"
    elif args.transcripts:
        refseqs_file = args.transcripts
        metadata_type = "Transcript"

    if args.metadata:
        annotation_file = args.metadata
        logger.info(
            "Found annotation file. Annotations will be added with the reference sequences."
        )
    else:
        annotation_file = None
    annotate_other(
        args.graph_name, metadata_type, refseqs_file, annotation_file, select_only
    )


parser = subparsers.add_parser(
    "annotate",
    help="""
    Add annotations to a given graph. The following usages are possible :
        - If you have a genomic full reference sequence and an annotation file (gtf or gff), use 'vizitig annotate --genome path_to_genome_file --metadata path_to_annotation_file'. 
        - If you have exons or transcripts reference sequences, use 'vizitig annotate --exons path_to_exons_file'. Replace 'exons' by 'transcripts' if you have transcripts sequences. 
        
        With the later feature, you can also add --metadata path_to_annotation_file if you have an annotation file that corresponds to the exons or transcripts reference sequence, but it is not mandatory.
    
    What it does : 
        - For the genomic sequence and the annotation file, Vizitig will sort and ingest all the metadata in the annotation file and read the reference sequence using a reading frame. 
        Everytime the whole sequence of a metadata has been read, it will tag the graph with the corresponding metadata. 
        - For the exons or transcripts reference sequence, it will tag the graph with the a generic metadata that has the header of the reference sequence and later add the additional data of the annotation file. The later is therefore optional
        """,
)

parser.add_argument(
    "graph_name",
    help="A graph name. List possible graph with python3 -m vizitig info",
    metavar="graph",
    type=str,
)

parser.add_argument(
    "-g",
    "--genome",
    help="Path toward a (possibly compressed) fasta file containing a reference genome",
    metavar="genome_ref",
    type=Path,
)

parser.add_argument(
    "-m",
    "--metadata",
    help="Path towards a (possibly compressed) gtf file containing metadata of a reference sequence",
    metavar="gtf",
    type=Path,
    required=False,
)

parser.add_argument(
    "-e",
    "--exons",
    help="Path towards a fasta file containing exon reference sequences",
    type=Path,
    required=False,
)

parser.add_argument(
    "-t",
    "--transcripts",
    help="Path towards a fasta file containing transcript reference sequences",
    type=Path,
    required=False,
)

parser.add_argument(
    "-so",
    "--select_only",
    action="append",
    default=None,
    help="Select values (can be used multiple times)",
)

parser.set_defaults(func=main)


def str_to_exon(
    chunk: str, exon_offset: int, meta_only=False
) -> Tuple[SubseqData, DNA] | SubseqData:
    """
    Takes a line of exon parsing as input and returns the SubseqData and DNA corresponding to it
    """

    try:
        id = re.findall(r"\|([A-Z]{2}_.*)\|", chunk)[0]
        start = int(re.findall(":([0-9]*)-", chunk)[0])
        stop = int(re.findall("-([0-9]*)", chunk)[0])
        seq = re.findall("\n[ACTGN\n]*", chunk.upper())[0].replace("\n", "").upper()

        gene_id = re.findall(r"\(([A-Za-z0-9]*)\)", chunk)[0]

    except IndexError:
        raise ValueError("Exon parsing does not match the expected format.")

    s = SubseqData(
        id=id + "_exon_number_{}".format(exon_offset + 1),
        type="Exon",
        start=start,
        stop=stop,
        list_attr=[],
        gene=gene_id,
    )
    if meta_only:
        return s
    d = DNA.from_str(seq)
    return (s, d)


def str_to_transcript(chunk: str) -> Tuple[SubseqData, list[DNA]]:
    """
    Takes a line of transcript parsing as input and returns the SubseqData and DNA corresponding to it
    """
    match = re.match(r">(?P<id>[^\s\n]+)\s+(?P<seq>[ACGTNacgtn\n]+)", chunk)

    if match:
        s = SubseqData(
            id=match.group("id"), type="Transcript", start=0, stop=0, list_attr=[]
        )
        d = list(DNA.from_str(match.group("seq").replace("\n", "").upper()))
        return (s, d)
    else:
        raise ValueError("Transcript data does not match the expected format.")
