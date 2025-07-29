from pathlib import Path

from vizitig.info import get_graph
from vizitig.index import load_kmer_index
from vizitig.errors import FixtureError


def test_fixture_setup_correctly(tmp_path: Path, viz_dir, test_graph_name):
    try:
        assert get_graph(test_graph_name)
        assert load_kmer_index(test_graph_name)
    except Exception as e:
        raise FixtureError(
            "The following issue occured with the fixture used for testing : {}. Please contact the developpers.".format(
                e
            )
        )
