from vizitig import info
from vizitig.env_var import (
    VIZITIG_DEFAULT_INDEX,
    VIZITIG_PYTHON_ONLY,
    VIZITIG_PROC_NUMBER,
    VIZITIG_WORK_MEM,
)
from vizitig.cli import subparsers
from vizitig.errors import (
    NoIndex,
    UnknownIndexType,
    VizIndexError,
    NoData,
)
from vizitig.index.classes import (
    Shard,
    IndexInfo,
    GraphIndex,
    TemporaryKmerSet,
    TemporaryKmerIndex,
    index_path_name,
)
from vizitig.index.sqlite_index import SQLiteIndex

if not VIZITIG_PYTHON_ONLY:
    from vizitig.index.rust_index import RustIndex
from vizitig.utils import sizeof_fmt
from vizitig.types import Kmer, DNA, AvailableKmerSize

from typing import Callable, Iterator, Tuple


__all__ = [
    "load_kmer_index",
    "index_info",
    "build_kmer_index",
    "drop_kmer_index",
    "SQLiteIndex",
    "RustIndex",
]

index_types: list[str] = sorted(
    Shard.subclasses,
    key=lambda e: Shard.subclasses[e].priority,
)


def temporary_kmerset(
    iterator: Callable[[], Iterator[Kmer]] | Callable[[], Iterator[DNA]],
    shard_number: int | None = None,
    k: int | None = None,
    index_type: str | None = None,
) -> TemporaryKmerSet:
    """Build a temporary set to store kmer."""
    if shard_number is None:
        shard_number = VIZITIG_PROC_NUMBER
    if index_type is None:
        var_env_default_index = VIZITIG_DEFAULT_INDEX
        if not var_env_default_index:
            index_type = index_types[-1]
        else:
            index_type = var_env_default_index
    IndexType = Shard.subclasses[index_type]
    try:
        first = next(iterator())
    except StopIteration:
        raise NoData

    if isinstance(first, Kmer):
        k = k or first.size
        assert k is not None
        return TemporaryKmerSet.build_kmer(IndexType, iterator, shard_number, k)
    if isinstance(first, DNA):
        assert k is not None
        print("AAAAAAAAAAAAAAAAAAAAAAAAAAAAa")
        print(shard_number)
        return TemporaryKmerSet.build_dna(IndexType, iterator, shard_number, k)

    raise ValueError(first)


def temporary_kmerindex(
    iterator: Callable[[], Iterator[Tuple[Kmer, int]]]
    | Callable[[], Iterator[Tuple[DNA, int]]],
    k: int | None = None,
    shard_number: int | None = None,
    index_type: str | None = None,
) -> TemporaryKmerIndex:
    """Build a temporary set to store a Kmer index"""
    if shard_number is None:
        shard_number = VIZITIG_PROC_NUMBER
    if index_type is None:
        var_env_default_index = VIZITIG_DEFAULT_INDEX
        if not var_env_default_index:
            index_type = index_types[-1]
        else:
            index_type = var_env_default_index
    first, _ = next(iterator())
    IndexType = Shard.subclasses[index_type]
    if isinstance(first, Kmer):
        k = k or first.size
        return TemporaryKmerIndex.build_kmer(IndexType, iterator, shard_number, k)
    if isinstance(first, DNA):
        assert k is not None
        return TemporaryKmerIndex.build_dna(IndexType, iterator, shard_number, k)

    raise ValueError(first)


def build_kmer_index(
    gname: str,
    index_type: str | None = None,
    shard_number: int | None = None,
    small_k: int | None = None,
):
    if shard_number is None:
        G = info.get_graph(gname)
        shard_number = int(
            max(
                G.metadata.k
                * G.metadata.kmer_size
                * VIZITIG_PROC_NUMBER
                / VIZITIG_WORK_MEM,
                VIZITIG_PROC_NUMBER,
            )
        )
    try:
        if index_type is None:
            var_env_default_index = VIZITIG_DEFAULT_INDEX
            if not var_env_default_index:
                index_type = index_types[-1]
            else:
                index_type = var_env_default_index
        IndexType = Shard.subclasses[index_type]
        GraphIndex.build_dna(gname, IndexType, shard_number, small_k=small_k)

    except KeyError:
        raise UnknownIndexType(index_type)


def load_kmer_index(
    gname: str, index_type: str | None = None, small_k: int | None = None
) -> GraphIndex:
    if index_type is None:
        p = len(index_types) - 1
        IndexType = Shard.subclasses[index_types[p]]
        while p >= 0:
            try:
                return GraphIndex.from_graph(gname, IndexType, small_k=small_k)
            except VizIndexError:
                p -= 1
                IndexType = Shard.subclasses[index_types[p]]
                continue
        raise NoIndex
    else:
        try:
            IndexType = Shard.subclasses[index_type]
        except KeyError:
            raise UnknownIndexType(index_type)
    return GraphIndex.from_graph(gname, IndexType, small_k)


def index_info(gname: str) -> list[IndexInfo]:
    result = []
    for index_type in index_types:
        try:
            idx = load_kmer_index(gname, index_type)
            result.append(idx.info())
        except VizIndexError:
            pass
    result.extend(small_k_index_info(gname))
    return result


def small_k_index_info(gname: str) -> list[IndexInfo]:
    result = []
    index_path = index_path_name(gname) / "small_k"
    for fsmall_k in index_path.glob("*"):
        small_k = int(str(fsmall_k.name))
        for idx_type in (index_path / fsmall_k).glob("*"):
            try:
                idx = load_kmer_index(gname, str(idx_type.name), small_k)
                result.append(idx.info())
            except VizIndexError:
                pass
    return result


def drop_kmer_index(gname: str, version: str, small_k: int | None = None):
    index = load_kmer_index(gname, version, small_k)
    index.drop()


def main(args):
    if args.action == "list":
        L = index_info(args.name)
        for index in L:
            print(f"{index.type}\t{sizeof_fmt(index.size)}")
    if args.action == "build":
        build_kmer_index(args.name, args.type, args.shard_number, small_k=args.small_k)
    if args.action == "drop":
        drop_kmer_index(args.name, args.type, small_k=args.small_k)


parser = subparsers.add_parser(
    "index",
    help="Index utilities of graph.",
    description=f"""
Index accelerate a lot many ingestion and search operation.
Default index can be setup through environnement variable VIZITIG_DEFAULT_INDEX. 
Possible values are {index_types}""",
    epilog=f"Available values for k {AvailableKmerSize}",
)

parser.set_defaults(func=main)


parser.add_argument(
    "action",
    choices=("build", "drop", "list"),
    help="The action to perform on the graph",
)

parser.add_argument(
    "name",
    help=f"Name of the graph to index: {info.graphs_list()}",
    metavar="name",
    choices=info.graphs_list(),
    type=str,
)
parser.add_argument(
    "-t",
    "--type",
    help=f"The index type: {index_types}",
    metavar="type",
    choices=index_types,
    default=None,
)

parser.add_argument(
    "--small-k",
    help="Force index on a smaller kmer value that the one provided by the graph",
    metavar="small_k",
    type=int,
    default=None,
)
parser.add_argument(
    "-s",
    "--shard_number",
    help="The number of shard (default will depend of the graph size and available RAM)",
    type=int,
    metavar="shard_nb",
    default=None,
)
