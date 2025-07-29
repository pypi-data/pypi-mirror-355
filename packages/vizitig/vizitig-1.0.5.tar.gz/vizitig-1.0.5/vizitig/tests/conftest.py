from pytest import fixture
from subprocess import run, PIPE
from pathlib import Path
import os
import shutil

from vizitig.env_var import VIZITIG_SHORT_TEST
from vizitig.utils import vizitig_logger as log
from vizitig.info import delete_graph


@fixture(scope="session")
def viz_dir():
    vizitig_dir = Path(os.environ["VIZITIG_DIR"])
    if vizitig_dir.exists():
        shutil.rmtree(vizitig_dir)
    run("make small_ex", stdout=PIPE, stderr=PIPE, shell=True)
    if not VIZITIG_SHORT_TEST:
        run("make small_ex_alt", stdout=PIPE, stderr=PIPE, shell=True)
        run("make small_ex_alt2", stdout=PIPE, stderr=PIPE, shell=True)
    else:
        log.warning("SHORT TEST ONLY")
    yield vizitig_dir
    shutil.rmtree(vizitig_dir)


def reset_graph():
    delete_graph("mini_bcalm")
    if not VIZITIG_SHORT_TEST:
        delete_graph("mini_bcalm_alt1")
        delete_graph("mini_bcalm_alt2")

    run("make small_ex", stdout=PIPE, stderr=PIPE, shell=True)

    if not VIZITIG_SHORT_TEST:
        run("make small_ex_alt", stdout=PIPE, stderr=PIPE, shell=True)
        run("make small_ex_alt2", stdout=PIPE, stderr=PIPE, shell=True)
    else:
        log.warning("SHORT TEST ONLY")


@fixture(scope="function")
def test_graph_name():
    return "mini_bcalm"


@fixture(scope="function")
def kmer_set_and_nodes():
    return [
        ("ATCGTGAGTCGTAGCTGATGC", [1]),
        ("TTATTCGATTAGCAGTTAGCT", [2]),
        ("AGTCGGATCGATAGCTGATAG", [3]),
    ]


@fixture(scope="function")
def sequences_set():
    return [
        ("ATCGTGAGTCGTAGCTGATGCTAGCTGATCGATCGGATGTCGTAGCATCGNATTCCAaaaC", [1]),
        ("AGTTATTCGATTAGCAGTTAGCT".lower, [2]),
        ("AGTCGGATCGATAGCTGATAGCTAGCT", [3]),
    ]
