import gzip
import logging
import re
from itertools import groupby
from pathlib import Path
from typing import (
    Iterable,
    Iterator,
    List,
    NamedTuple,
    TextIO,
    Tuple,
    IO,
)

from vizitig.metadata import GraphMetadata
from vizitig.types import DNA, ESign, SubseqData
from vizitig.utils import vizitig_logger
from vizitig.errors import FormatInputError


class NodeHeader(NamedTuple):
    node_id: int
    metadatas: List[SubseqData]
    sequence: DNA
    successors: tuple[tuple[int, ESign], ...]
    occurence: float | None = None


dna_parse = re.compile(r"(([ACGTacgt]+\n)*)", re.DOTALL)


def parse_fasta_with_bcalm_abundances(f: IO) -> Iterator[Tuple[DNA, float]]:
    buffer = str()
    for i, line in enumerate(f):
        if line[0] == ">":
            if "km:f:" in line:
                if i > 0:
                    for elem in DNA.from_str(buffer):
                        yield (elem, abundance)  # noqa: F821
                    buffer = str()
                abundance: float = float(re.findall(r"k[am]:f:(\d+\.\d+)", line)[0])
                assert isinstance(abundance, float)
        else:
            buffer += line.strip().upper()
    for elem in DNA.from_str(buffer):
        yield (elem, abundance)


def parse_fasta_dna(f: TextIO, k: int, buffer_size: int = 10**8) -> Iterator[DNA]:
    buffer = ""
    for line in f:
        if line[0] == ">":
            yield from DNA.from_str(buffer)
            buffer = ""
        else:
            buffer += line.strip().upper()
    yield from DNA.from_str(buffer)


# def parse_fasta(f: TextIO, k: int, buffer_size: int = 10**6) -> Iterator[Kmer]:
#     for dna in parse_fasta_dna(f, k, buffer_size=buffer_size):
#         yield from dna.enum_canonical_kmer(k)


def parse_reference_sequences_dna(
    file_path: Path, GM: GraphMetadata, annotation_data: dict[str, SubseqData]
) -> Iterable[Tuple[SubseqData, DNA]]:
    for bulk in parse_transcript_or_exon_refseq(file_path):
        assert bulk[0] == ">"
        name, remain = bulk.split(maxsplit=1)
        parse_name = annotation_data.get(name[1:])
        if not parse_name:
            continue
        yield from (
            (parse_name, dna) for dna in DNA.from_str(remain.upper().replace("\n", ""))
        )


def parse_transcript_or_exon_refseq(file_path: Path) -> Iterator[str]:
    """
    Amazing and simple parser
    """
    with open(file_path) as file:
        buffer = ""
        for line in file:
            if line[0] == ">" and buffer:
                yield buffer
                buffer = line
            else:
                buffer += line
        yield buffer


def parse_genes(gene_desc: str) -> Iterator[SubseqData]:
    for gene in gene_desc.split(";"):
        gene_name, transcripts_desc = gene.split(":", maxsplit=1)
        transcripts = list(transcripts_desc.split(","))
        yield SubseqData(
            id=gene_name,
            type="Gene",
            list_attr=list(),
            start=-1,
            stop=-1,
        )  # We don't know yet start and stop. TODO
        for t in transcripts:
            yield SubseqData(
                id=t,
                type="Transcript",
                list_attr=list(),
                start=-1,
                stop=-1,
            )


find_succ = re.compile(r"L:([+-]):(\d+):([+-])")
find_annotation = re.compile(r"genes:\[(.*?)\]")
occurence_pattern = re.compile(r"(?<=km:f:)[+-]?\d+(?:\.\d+)?")


def parse_one(line: str, seq: str) -> NodeHeader:
    """Function parsing one line of BCALM file
    Its important to note that one line refers
    to the one line that was grouped by the previous
    function
    Hereby one line is the header of a bcalm graph
    plus its sequence
    """
    assert line[0] == ">"
    gene_annotations = find_annotation.findall(line)
    assert len(gene_annotations) <= 1
    if gene_annotations:
        parsed_gene_annotations = list(parse_genes(gene_annotations[0]))
    else:
        parsed_gene_annotations = []

    occurence_match = occurence_pattern.findall(line)
    occurence: float | None = None
    if occurence_match:
        assert len(occurence_match) == 1
        occurence = float(occurence_match[0])

    return NodeHeader(
        node_id=int(line.split(" ")[0][1:]),
        occurence=occurence,
        metadatas=parsed_gene_annotations,
        sequence=DNA(seq),
        successors=tuple(
            map(lambda e: (int(e[1]), ESign(e[0] + e[2])), find_succ.findall(line)),
        ),
    )


def parse_one_ggcat(spec, seq) -> Tuple[int, str]:
    """Function parsing one line of BCALM file"""
    node_id = int(spec.split(" ")[0])
    return (node_id, seq)


def _buffer_read_data(f, buffsize) -> Iterator[str]:
    remain = ""
    while True:
        read = f.read(buffsize).decode()
        if not read:
            if remain.strip():
                yield remain.strip()
            return
        x = remain + read
        if "\n" not in x:
            remain = x
            continue
        body, remain = x.rsplit("\n", maxsplit=1)
        yield from body.split("\n")


def get_data(filename: Path, buffsize=10**6) -> Iterator[str]:
    if filename.name.endswith(".gz"):
        with gzip.open(filename) as f:
            yield from _buffer_read_data(f, buffsize)
    else:
        with open(filename, "rb") as f:
            yield from _buffer_read_data(f, buffsize)


def stat_bcalm(filename: Path, buffsize=10**6) -> tuple[int, int, int, int]:
    """Read a BCALM format and return the node size, edge size and an estimate for k
    obtained by taking the minimum length of a unitig node
    """
    data = get_data(filename, buffsize=buffsize)
    node_size = 0
    edge_size = 0
    kmer_size = 0
    estimate_k = 63
    for line in data:
        if line and line[0] != ">":
            dna_length = len(line.strip())
            estimate_k = min(estimate_k, dna_length)
            kmer_size += dna_length - estimate_k

            continue
        node_size += 1
        edge_size += line.count("L:")
    return node_size, edge_size, estimate_k, kmer_size


def parse(
    filename: Path,
    buffsize=10**6,
) -> Iterator[NodeHeader]:
    """Function parsing a BCALM file returning an iterator over the parsed value

    Assume the file fits in RAM. More work is needed if it isn't the case.
    """
    data = get_data(filename, buffsize=buffsize)
    values = groupby(enumerate(data), lambda e: e[0] // 2)
    yield from (parse_one(spec, seq) for i, ((_, spec), (_, seq)) in values)


def parse_annotations_for_genes(file_path: Path, k: int) -> Iterator[SubseqData]:
    if file_path.suffix == ".gff":
        with open(file_path) as file:
            for elem in _parse_gff(file, k):
                if elem.type.upper() == "TRANSCRIPT":
                    yield elem
    elif file_path.suffix == ".gtf":
        with open(file_path) as file:
            for elem in _parse_gtf(file, k):
                if elem.type.upper() == "TRANSCRIPT":
                    yield elem
    else:
        raise FormatInputError(
            f"Annotation format extension is: {file_path.suffix}. Should be .gff or .gtf."
        )


def parse_annotations(file_path: Path, k: int) -> Iterator[SubseqData]:
    if file_path.suffix == ".gff":
        with open(file_path) as file:
            yield from _parse_gff(file, k)
    elif file_path.suffix == ".gtf":
        with open(file_path) as file:
            yield from _parse_gtf(file, k)
    else:
        raise FormatInputError(
            f"Annotation format extension is: {file_path.suffix}. Should be .gff or .gtf."
        )


gene_search = re.compile(r'gene_id "([^"]+)"')
transcript_search = re.compile(r'transcript_id "([^"]+)"')


def _parse_gtf(file, k: int) -> Iterator[SubseqData]:
    for line_counter, line in enumerate(file):
        if not line.strip() or line.startswith("#"):
            continue
        fields = line.split("\t")
        match = gene_search.search(line)
        gene_id = match.group(1) if match else None
        match = transcript_search.search(line)
        transcript_id = match.group(1) if match else None
        id_desc = transcript_id or gene_id
        if not id_desc:
            vizitig_logger.error(
                f"ID not found for line {line_counter} of {file}. Make sure your annotation data respect the correct format.",
            )
            continue

        chr, _, feature_type, start, stop, _, str_strand, _, bulk_attributes = fields
        if str_strand not in ["-", "+"]:
            str_strand = None
        attributes = re.sub(r";\s+", ";", re.sub(r";\n", "", bulk_attributes))
        list_attributes = list(filter(bool, map(str.strip, attributes.split(";"))))
        start, stop = int(start), int(stop)
        object_type = feature_type[0].upper() + feature_type[1:]
        if stop - start < k:
            stop = start + k
        yield SubseqData(
            id=id_desc,
            type=object_type,
            list_attr=list_attributes,
            start=start,
            stop=stop,
            gene=gene_id,
            chr=chr,
            strand=str_strand,
        )


id_parser = re.compile(r"ID=([^;]+)")
parent_parser = re.compile(r"Parent=([^;]+)")


def _parse_gff(file, k: int) -> Iterator[SubseqData]:
    for line_counter, line in enumerate(file):
        if not line or line.startswith("#"):
            continue
        id_parsed = id_parser.search(line)
        parent_parsed = parent_parser.search(line)
        id_desc: str | None = None
        if id_parsed is not None:
            id_desc = id_parsed.group(1)
        elif parent_parsed is not None:
            id_desc = parent_parsed.group(1)
        if id_desc is None:
            vizitig_logger.error(
                f"ID not found for line {line_counter} of {file}. Make sure your annotation data respect the correct format.",
            )
            continue

        line = line.strip()
        fields = line.split("\t")

        _, _, feature_type, start, stop, _, strand, _, _ = fields
        _, _, feature_type, start, stop, _, _, _, bulk_attributes = fields
        attributes = re.sub(r";\s+", ";", re.sub(r";\n", "", bulk_attributes))
        list_attributes = attributes.split(";")
        start, stop = int(start), int(stop)
        object_type = feature_type[0].upper() + feature_type[1:]
        if stop - start < k:
            stop = start + k

        yield SubseqData(
            id=id_desc,
            type=object_type,
            list_attr=list_attributes,
            start=start,
            stop=stop,
        )


def parse_reference_sequence_for_full_annotation(
    refseq: Path,
    metadatas: Iterable[SubseqData],
    k: int,
    logger_name: str = "vizitig",
) -> Iterator[Tuple[SubseqData, DNA]]:
    logger = logging.getLogger(f"{logger_name}.refparsing")

    # This implementation will load the reference sequence in RAM.

    with open(refseq) as file:
        sequence: str = file.read().replace("\n", "")

        for i, meta in enumerate(metadatas):
            try:
                dna: str = DNA.from_str(sequence[meta.start : meta.stop])
                for d in dna:
                    yield (meta, d)
            except IndexError:
                logger.warning("""
                            Metadata {} of type {} has starts and stop that are not included in the provided reference sequence.
                            If you are not working with a subset, check your reference file corresponds to your annotation file.
                            """)
        logger.info("Finished")
