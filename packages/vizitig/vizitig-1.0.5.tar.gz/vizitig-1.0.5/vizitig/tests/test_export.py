from pathlib import Path

from pytest import raises, mark

from vizitig.errors import EmptyExportError
from vizitig.export import (
    export_graph,
    export_bcalm_by_iterator,
    dump_one_node_bcalm,
    dump_one_node_bcalm_for_iterator,
)
from vizitig.info import get_graph

formats = [
    "json",
    "bcalm",
    "nodelist",
]  # "networkx_pickle" and "gml" should be in this list


@mark.parametrize("format", formats)
def test_export_graph_bcalm_in_normal_conditions(
    tmp_path: Path, viz_dir, test_graph_name, format: str
):
    test_file = tmp_path / "file"
    export_graph(test_graph_name, [165114, 248683, 459264], format, test_file)
    assert test_file.exists()
    test_file.unlink()


@mark.parametrize("format", formats)
def test_export_graph_bcalm_subgraph(
    tmp_path: Path, viz_dir, test_graph_name, format: str
):
    test_file = tmp_path / "file"
    sample_nodes = [165114, 248683, 459264]

    export_graph(test_graph_name, sample_nodes, format, test_file)
    assert test_file.exists()
    test_file.unlink()


@mark.parametrize("format", formats)
def test_export_graph_bcalm_crashes_with_bad_nodes_id(
    tmp_path: Path, viz_dir, test_graph_name, format: str
):
    test_file = tmp_path / "file"
    with raises(EmptyExportError):
        export_graph(test_graph_name, list([-1]), format, test_file)
    assert not test_file.exists()


def test_export_graph_by_iterator(tmp_path: Path, viz_dir, test_graph_name):
    test_file = tmp_path / "file"
    export_bcalm_by_iterator(test_graph_name, test_file)
    assert tmp_path.exists()
    test_file.unlink()


def test_dump_one_node_bcalm_for_iterator(tmp_path: Path, viz_dir, test_graph_name):
    G = get_graph(test_graph_name)
    for node in G._node:
        dumped = dump_one_node_bcalm(G, node)
        assert isinstance(dumped, str)
        assert dumped[0] == ">"
        assert "\n" in dumped
        assert dumped[::-1][0] in ["A", "T", "C", "G"]
