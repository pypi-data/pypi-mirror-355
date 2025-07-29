import functools
import shutil
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Annotated, cast, Literal
from uuid import uuid4

import networkx as nx
from fastapi import FastAPI, HTTPException, UploadFile, status, Form

from vizitig.env_var import VIZITIG_TMP_DIR
from vizitig import query as vizquery
from vizitig import version as vizversion
from vizitig.api.async_utils import async_subproc
from vizitig.api.errors import (
    NodeNotFoundException,
    NoEmptyGraphNameAllowed,
    NoPathFoundException,
    UnknownFormat,
    UnsupportedExtension,
)
from vizitig.api.path import site
from vizitig.api.types import Alignment
from vizitig.errors import VizitigException
from vizitig.export import export_format, export_graph
from vizitig.generate_graph import generate_graph
from vizitig.index import (
    IndexInfo,
    build_kmer_index as base_build_kmer_index,
    drop_kmer_index as base_drop_kmer_index,
    index_info as base_index_info,
    index_types as base_index_types,
)
from vizitig.info import (
    add_vizitig_graph,
    get_graph,
    reload_graph,
    delete_graph as delete_graph_base,
    graph_info as base_graph_info,
    graphs_list as base_graphs_list,
    rename_graph as rename_graph_base,
)
from vizitig.color import color_graph as base_update_graph
from vizitig.annotate import (
    annotate_genome as base_annotate_genome,
    annotate_other as base_annotate_other,
)
from vizitig.metadata import GraphMetadata, NodeDesc
from vizitig.paths import graph_path_name, log_path_name, root
from vizitig.types import ESign, Metadata

app = FastAPI()


def wrap_error(fct):
    """Wrap the Vizitig Error into HTTP Error"""

    @functools.wraps(fct)
    async def _fct(*args, **kwargs):
        try:
            return await fct(*args, **kwargs)
        except VizitigException as E:
            # This could be more efficient with an appropriate
            # layout of VizitiException.
            raise HTTPException(detail=f"{E!r}", status_code=400)

    return _fct


def get(*args, **kwargs):
    def ndec(f):
        f = wrap_error(f)
        return app.get(*args, operation_id=f.__name__, **kwargs)(f)

    return ndec


def post(*args, **kwargs):
    def ndec(f):
        f = wrap_error(f)
        return app.post(*args, operation_id=f.__name__, **kwargs)(f)

    return ndec


def patch(*args, **kwargs):
    def ndec(f):
        f = wrap_error(f)
        return app.patch(*args, operation_id=f.__name__, **kwargs)(f)

    return ndec


def delete(*args, **kwargs):
    def ndec(f):
        f = wrap_error(f)
        return app.delete(*args, operation_id=f.__name__, **kwargs)(f)

    return ndec


export_path = Path(root, "export")
if not export_path.exists():
    export_path.mkdir()


@get(
    path="/ryalive",
    status_code=status.HTTP_200_OK,
    description="Endpoint to check that server is online",
)
async def ryalive():
    return "yes master !!"


@get(
    path="/version",
    status_code=status.HTTP_200_OK,
    description="Endpoint to get the current vizitig version",
)
async def version() -> str:
    return vizversion


@get(
    path="/load_viz",
    status_code=status.HTTP_200_OK,
    description="Get the list of available visualisation",
)
async def load_viz() -> list[str]:
    return list(map(lambda e: e.stem, site.glob("js/viz/*.js")))


@get(
    path="/list_graphs",
    status_code=status.HTTP_200_OK,
    description="Get the list of available graphs",
)
async def graphs_list() -> dict[str, Any]:
    result = dict()
    for e in base_graphs_list():
        try:
            data = base_graph_info(e, human_size=True)
        except Exception as E:
            data = dict(error=str(E))
        result[e] = data
    return result


@get(
    path="/export_format",
    status_code=status.HTTP_200_OK,
    description="Get the list of available format to export some graph",
)
async def get_export_format() -> list[str]:
    return sorted(export_format)


@delete(
    path="/graphs/{name}",
    status_code=status.HTTP_200_OK,
    description="Delete the graph",
)
async def delete_graph(name: str) -> None:
    delete_graph_base(name)


@get("/log/{name}")
async def get_log(name: str) -> list[str]:
    try:
        with open(log_path_name(name)) as f:
            return list(f)
    except FileNotFoundError:
        return []


@post(
    path="/graph/rename/{old_name}/{new_name}",
    status_code=status.HTTP_200_OK,
    description="Rename the graph",
)
async def rename_graph(old_name, new_name):
    rename_graph_base(old_name, new_name, replace=False)


@post(
    path="/graph/rename",
    status_code=status.HTTP_200_OK,
    description="Rename the graph via a formular",
)
async def rename_graph_form(
    name: Annotated[str, Form()], new_name: Annotated[str, Form()]
):
    rename_graph_base(name, new_name, replace=False)


def fmt_name(name, idx):
    return f"{name}_copy_{idx}"


@get(
    path="/align/{gname}/{nid1}/{nid2}",
    status_code=status.HTTP_200_OK,
    description="Align the unit data of two nodes",
)
async def align(
    gname: str,
    nid1: int,
    nid2: int,
) -> Alignment:
    G = get_graph(gname)
    try:
        seq1 = G.nodes[nid1]["sequence"]
        seq2 = G.nodes[nid2]["sequence"]
    except KeyError as E:
        raise NodeNotFoundException(detail=E.args[0], status_code=404)
    return Alignment.from_seq(seq1, seq2)


@get(
    path="/index/{name}/info",
    status_code=status.HTTP_200_OK,
    description="Get info on the index of the graph",
)
async def index_info(name: str) -> list[IndexInfo]:
    return base_index_info(name)


@get(
    path="/index_types",
    status_code=status.HTTP_200_OK,
    description="Get info on the index of the graph",
)
async def index_types() -> list[str]:
    return base_index_types


@post(
    path="/index/{name}/{index_type}/drop",
    status_code=status.HTTP_200_OK,
    description="Drop indexes of the graph. If the index type is provided, drop only this type",
)
async def drop_index(name: str, index_type: str, small_k: int | None = None):
    if index_type is not None:
        base_drop_kmer_index(name, index_type, small_k=small_k)
    else:
        base_drop_kmer_index(name, index_type, small_k=small_k)


@post(
    path="/index/{name}/build",
    status_code=status.HTTP_200_OK,
    description="Build an index for the graph. If no type is provided, the some index_type is selected somehow",
)
async def build_index(
    name: str, index_type: str | None = None, small_k: int | Literal[""] | None = None
):
    if index_type is None:
        index_type = base_index_types[-1]
    if isinstance(small_k, str):
        small_k = None
    await async_subproc(base_build_kmer_index)(name, index_type, small_k=small_k)


@post(
    path="/graph/color/",
    status_code=status.HTTP_200_OK,
    description="Color the graph with an input file",
)
async def color_graph(
    name: Annotated[str, Form()], file: UploadFile, color: Annotated[str, Form()]
):
    assert file.filename is not None
    path = Path(file.filename)
    tmp = NamedTemporaryFile(prefix=VIZITIG_TMP_DIR, delete=False, suffix=path.suffix)
    shutil.copyfileobj(file.file, tmp)  # type: ignore
    tmp_path = Path(tmp.name)
    await async_subproc(base_update_graph)(name, color, "", tmp_path)
    file.file.close()
    tmp_path.unlink()
    reload_graph(name)


@post(
    path="/graph/annotate_gene/",
    status_code=status.HTTP_200_OK,
    description="Color the graph with an input file",
)
async def annotate_gene(
    name: Annotated[str, Form()], ref_gen: UploadFile, gtf_gff: UploadFile
):
    assert ref_gen.filename
    assert gtf_gff.filename
    path_gen = Path(ref_gen.filename)
    path_gtf_gff = Path(gtf_gff.filename)

    tmp_gen = NamedTemporaryFile(
        prefix=VIZITIG_TMP_DIR, delete=False, suffix=path_gen.suffix
    )
    shutil.copyfileobj(ref_gen.file, tmp_gen)  # type: ignore

    tmp_gtf_gff = NamedTemporaryFile(
        prefix=VIZITIG_TMP_DIR, delete=False, suffix=path_gtf_gff.suffix
    )

    shutil.copyfileobj(gtf_gff.file, tmp_gtf_gff)  # type: ignore

    tmp_path_gen = Path(tmp_gen.name)
    tmp_path_gtf_gff = Path(tmp_gtf_gff.name)

    await async_subproc(base_annotate_genome)(name, tmp_path_gtf_gff, tmp_path_gen)

    ref_gen.file.close()
    gtf_gff.file.close()
    tmp_path_gen.unlink()
    tmp_path_gtf_gff.unlink()
    reload_graph(name)


@post(
    path="/graph/annotate_other/",
    status_code=status.HTTP_200_OK,
    description="Color the graph with an input file",
)
async def annotate_other(
    name: Annotated[str, Form()],
    reference_seqs: UploadFile,
    metadata_type: Annotated[str, Form()],
    gtf_gff: UploadFile | None = None,
):
    assert reference_seqs.filename
    path_reference_seqs = Path(reference_seqs.filename)
    tmp_reference_seqs = NamedTemporaryFile(
        prefix=VIZITIG_TMP_DIR, delete=False, suffix=path_reference_seqs.suffix
    )
    shutil.copyfileobj(reference_seqs.file, tmp_reference_seqs)  # type: ignore
    tmp_ref_seq = Path(tmp_reference_seqs.name)

    if gtf_gff:
        assert gtf_gff.filename
        path_gtf_gff = Path(gtf_gff.filename)
        tmp_gtf_gff = NamedTemporaryFile(
            prefix=VIZITIG_TMP_DIR, delete=False, suffix=path_gtf_gff.suffix
        )

        shutil.copyfileobj(gtf_gff.file, tmp_gtf_gff)  # type: ignore

        tmp_path_gtf_gff = Path(tmp_gtf_gff.name)
    else:
        tmp_path_gtf_gff = None
    await async_subproc(base_annotate_other)(
        name, metadata_type, tmp_ref_seq, tmp_path_gtf_gff
    )

    reference_seqs.file.close()
    tmp_ref_seq.unlink()
    if gtf_gff:
        cast(Path, tmp_path_gtf_gff).unlink()
    reload_graph(name)


@post(
    path="/duplicate/{name}",
    status_code=status.HTTP_200_OK,
    description="Duplicate the graph",
)
async def duplicate(name: str):
    L = set(base_graphs_list())
    path = graph_path_name(name)
    new_name = name
    idx = 0
    while fmt_name(new_name, idx) in L:
        idx += 1

    name = fmt_name(new_name, idx)
    await async_subproc(add_vizitig_graph)(path, name=name, replace=False, copy=True)


@post(
    path="/upload/{name}",
    status_code=status.HTTP_200_OK,
    description="""
    Upload a graph. 
    If replace is set to True, replace existing graph. 
    If check_compatibility is set to true, check is graph is compatible
    with the current vizitig version (default True)""",
)
async def upload_graph(file: UploadFile, name: str):
    assert file.filename is not None
    path = Path(file.filename)
    gname = path.stem
    if name != "":
        gname = name
    if name == "":
        raise NoEmptyGraphNameAllowed(status_code=402)

    if path.suffix in (".fa", ".gz", ".fasta"):
        try:
            tmp = NamedTemporaryFile(
                prefix=VIZITIG_TMP_DIR, delete=False, suffix=path.suffix
            )
            shutil.copyfileobj(file.file, tmp)  # type: ignore
            tmp_path = Path(tmp.name)
        finally:
            file.file.close()
        await async_subproc(generate_graph)(tmp_path, graph_path_name(name), name)
        tmp_path.unlink()
    elif path.suffix == ".db":
        try:
            with NamedTemporaryFile(
                prefix=VIZITIG_TMP_DIR, delete=False, suffix=".db"
            ) as tmp:
                shutil.copyfileobj(file.file, tmp)  # type: ignore
                tmp_path = Path(tmp.name)
        finally:
            file.file.close()
        await async_subproc(add_vizitig_graph)(
            tmp_path,
            name=gname,
            replace=False,
            check_compatibility=True,
        )
    else:
        raise UnsupportedExtension(extension=path.suffix, status_code=400)


@post(
    path="/graphs/{name}/export/{format}",
    status_code=status.HTTP_200_OK,
    description="Return a link to the exported file",
)
async def export_nodes(name: str, format: str, nodes: list[int]) -> str:
    """Exports the current nodes of the graph to a file"""
    # If the format is not supported, raise an error
    if format not in export_format:
        raise UnknownFormat(details=format, status_code=404)

    # Matches the export format of front with end
    # This calls the export_format dict from vizitig/export/__init__.py
    ext = export_format.get(format)

    # Generates a 128 bit random string that will serve as file name
    fname = f"{uuid4()}.{ext}"

    # Build the path
    target_path = Path(export_path, fname)

    await async_subproc(export_graph)(name, nodes, format, target_path)
    return f"export/{fname}"


@get(
    path="/graphs/{name}/info",
    status_code=status.HTTP_200_OK,
    description="Returns informations about the graph",
)
async def graph_info(name: str) -> GraphMetadata:
    return get_graph(name).metadata


def build_node_return(
    G,
    nodes: list[int],
) -> list[tuple[int, NodeDesc]]:
    nodes_with_data = G.subgraph(nodes).nodes(data=True)
    L: list[tuple[int, NodeDesc]] = []
    for x, d in nodes_with_data:
        neighbors: dict[int, ESign] = dict()
        adj = G._adj[x].fold()
        for y, od in adj.items():
            neighbors[y] = od.get("sign", None)
        L.append((x, G.metadata.to_nodedesc(d, neighbors)))
    return L


@get(
    path="/graphs/{name}/parse_query/{query}",
    status_code=status.HTTP_200_OK,
    description="Fetch all nodes with a query",
)
async def parse_query(name: str, query: str) -> vizquery.Term:
    return vizquery.parse(query)


@post(
    path="/graphs/{gname}/filters/{fname}/{filter}",
    status_code=status.HTTP_200_OK,
    description="Add a filter to the graph",
)
async def add_filter(gname: str, fname: str, filter: str):
    G = get_graph(gname)
    G.metadata.add_filter(fname, filter)
    G.metadata.commit_to_graph()


@post(
    path="/graphs/{gname}/filters/{fname}",
    status_code=status.HTTP_200_OK,
    description="Remove a filter from the graph",
)
async def remove_filter(gname: str, fname: str):
    G = get_graph(gname)
    G.metadata.remove_filter(fname)
    G.metadata.commit_to_graph()


@get(
    path="/graphs/{gname}/filters/",
    status_code=status.HTTP_200_OK,
    description="Get all filters of the graph",
)
async def list_filters(gname: str) -> list[tuple[str, str]]:
    G = get_graph(gname)
    return list(G.metadata.get_filters())


@get(
    path="/graphs/{gname}/states/",
    status_code=status.HTTP_200_OK,
    description="Get all the states of the graph",
)
async def list_states(gname: str) -> list[str]:
    G = get_graph(gname)
    return list(G.metadata.get_states())


@get(
    path="/graphs/{gname}/state/{state_name}",
    status_code=status.HTTP_200_OK,
    description="Get the state of the graph by name",
)
async def get_state_by_name(gname: str, state_name: str) -> str:
    G = get_graph(gname)
    return G.metadata.get_state(state_name)


@post(
    path="/graphs/{gname}/state/{state_name}/{state}",
    status_code=status.HTTP_200_OK,
    description="Set the state of the graph by name",
)
async def save_state(gname: str, state_name: str, state: str):
    G = get_graph(gname)
    G.metadata.set_state(state_name, state)


@post(
    path="/graphs/{gname}/delete_state/{state_name}",
    status_code=status.HTTP_200_OK,
    description="Delete the state of the graph by name",
)
async def delete_state(gname: str, state_name: str):
    G = get_graph(gname)
    G.metadata.delete_state(state_name)


@get(
    path="/graphs/{name}/find/query/{query}",
    status_code=status.HTTP_200_OK,
    description="Fetch all nodes with a query",
)
async def find_with_query(name: str, query: str) -> list[tuple[int, NodeDesc]]:
    G = get_graph(name)
    # nodes = vizquery.search(name, query)
    nodes = await async_subproc(vizquery.search)(name, query)
    return build_node_return(G, list(nodes))


@post(
    path="/graphs/{name}/node_data",
    status_code=status.HTTP_200_OK,
    description="Get nodes data in argument (POST only)",
)
async def nodes_data(name: str, nodes: list[int]) -> list[tuple[int, NodeDesc]]:
    G = get_graph(name)
    return build_node_return(G, nodes)


@get(
    path="/graphs/{name}/{nid}",
    status_code=status.HTTP_200_OK,
    description="Get data from `nid`",
)
async def all_nid(name: str, nid: int) -> NodeDesc:
    G = get_graph(name)
    try:
        d = G.nodes[nid].fold()
        nd = G.metadata.to_nodedesc(d, [y for y in G[nid]])
        return nd
    except KeyError:
        raise NodeNotFoundException(detail=nid, status_code=404)


@get(
    path="/graphs/{name}/meta/types",
    status_code=status.HTTP_200_OK,
    description="Return the metadata information stored in the graph",
)
async def get_all_types(name: str) -> list[str]:
    G = get_graph(name)
    return G.metadata.types_list


@get(
    path="/graphs/{gname}/meta/types/{type}",
    status_code=status.HTTP_200_OK,
    description="Return the metadata information stored in the graph",
)
async def all_metadata_of_types(gname: str, type: str) -> list[Metadata]:
    G = get_graph(gname)
    return G.metadata.all_metadata_by_types(type)


@get(
    path="/graphs/{name}/path/{source}/{target}",
    status_code=status.HTTP_200_OK,
    description="Get the path if it exists between `source` and `target`.",
)
async def get_path(name: str, source: int, target: int):
    G = get_graph(name)
    try:
        return nx.shortest_path(G, source, target)
    except nx.exception.NetworkXNoPath:
        return NoPathFoundException(detail=(source, target), status_code=404)
    except nx.exception.NodeNotFound:
        return NodeNotFoundException(detail=(source, target), status_code=404)
