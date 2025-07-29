from pytest import fixture, mark

from vizitig.info import get_graph
from vizitig.index import (
    load_kmer_index,
    index_info,
    build_kmer_index,
    temporary_kmerindex,
    temporary_kmerset,
)
from vizitig.index import index_types, Shard
from vizitig.types import DNA

from random import choices


from tempfile import TemporaryDirectory
from pathlib import Path


@fixture(scope="session")
def index_dir():
    tmp = TemporaryDirectory()
    path = Path(tmp.name)
    yield path
    tmp.cleanup()


@fixture(scope="session")
def dna():
    return DNA("".join(choices("ACGT", k=100)))


@fixture(scope="session")
def dnas():
    """Generate DNA sequence with number without repeating min_k-mer"""
    res = []
    kmer = set()
    for i in range(20):
        dna = DNA("".join(choices("ACGT", k=i**2)))
        nkmer = set(dna.enum_canonical_kmer(min_k))
        if not kmer.intersection(nkmer):
            res.append((dna, i))
        kmer.update(nkmer)
    return tuple(res)


valid_k = [2, 7, 10, 11, 21, 31, 33, 55, 63, 127, 511]


@mark.parametrize("IndexType", [Shard.subclasses[e] for e in index_types])
@mark.parametrize("k", valid_k)
def test_build_dna(index_dir, IndexType, dnas, k):
    filt_dnas = []  # to filter dna seq with shared kmer
    kmers = set()
    for dna, _ in dnas:
        nkmers = set(dna.enum_canonical_kmer(k))
        if kmers.intersection(nkmers):
            continue
        kmers.update(nkmers)
        filt_dnas.append(dna)
    d_dna = {dna: i for i, dna in enumerate(filt_dnas)}
    d_kmer = {
        kmer: i
        for i, dna in enumerate(filt_dnas)
        for kmer in dna.enum_canonical_kmer(k)
    }

    path_dna = index_dir / (IndexType.__name__ + "dna")
    index_dna = IndexType.build_dna(path_dna, 0, 1, iter(d_dna.items()), k)

    path_kmer = index_dir / (IndexType.__name__ + "kmer")
    index_kmer = IndexType.build_kmer(path_kmer, 0, 1, iter(d_kmer.items()), k)

    assert dict(index_dna) == d_kmer
    assert dict(index_kmer) == d_kmer


@mark.parametrize("IndexType", [Shard.subclasses[e] for e in index_types])
@mark.parametrize("k", valid_k)
def test_all_index(index_dir, IndexType, dna, k):
    path = index_dir / IndexType.__name__
    d = dict((kmer, i) for i, kmer in enumerate(dna.enum_canonical_kmer(k)))
    index = IndexType.build_kmer(path, 0, 1, iter(d.items()), k)
    assert set(index) == set(dna.enum_canonical_kmer(k))
    assert dict(index) == d

    subset = {k: i for k, i in d.items() if i % 2 == 0}
    # join_iter
    expected_res = {i: i for i in subset.values()}
    obtained_res = index.join(iter(subset.items()))
    assert dict(obtained_res) == expected_res

    # intersection_iter
    expected_res_intersection = {i for i in subset.values()}
    obtained_res_intersection = index.intersection(iter(subset))
    assert set(obtained_res_intersection) == expected_res_intersection

    subset_2 = {k: i**2 for k, i in d.items() if i % 2 == 0}
    # join_index:
    path2 = Path(path.parent, path.name + "2")
    index2 = IndexType.build_kmer(path2, 0, 1, iter(subset_2.items()), k)
    assert dict(index2) == subset_2
    expected_res_join_index = {i: i**2 for i in d.values() if i % 2 == 0}
    obtained_res_join_index = index.join_index(index2)
    assert dict(obtained_res_join_index) == expected_res_join_index

    # intersection_index
    path3 = Path(path.parent, path.name + "3")
    index3 = IndexType.Set.build_kmer(path3, 0, 1, iter(subset_2), k)
    assert set(index3) == set(subset_2)

    expected_res_join_index = {i for i in d.values() if i % 2 == 0}
    obtained_res_join_index = index.intersection_index(index3)
    assert set(obtained_res_join_index) == expected_res_join_index


@mark.parametrize("IndexType", [Shard.subclasses[e] for e in index_types])
@mark.parametrize("k", valid_k)
def test_join_val_duplicate(index_dir, IndexType, dna, k):
    path = index_dir / (IndexType.__name__ + "_join")
    d = {kmer: i % 3 for i, kmer in enumerate(dna.enum_canonical_kmer(k))}
    index = IndexType.build_kmer(path, 0, 1, iter(d.items()), k)
    assert set(index) == set(dna.enum_canonical_kmer(k))
    assert dict(index) == d

    path2 = index_dir / (IndexType.__name__ + "_join2")
    d2 = {kmer: i for i, kmer in enumerate(dna.enum_canonical_kmer(k))}
    index2 = IndexType.build_kmer(path2, 0, 1, iter(d2.items()), k)
    assert set(index) == set(dna.enum_canonical_kmer(k))
    assert dict(index2) == d2

    # join_index:
    expected_res_join = sorted(
        set((d[kmer], d2[kmer]) for kmer in dna.enum_canonical_kmer(k))
    )

    obtained_res_join_iter = sorted(index.join(d2.items()))
    assert obtained_res_join_iter == expected_res_join

    obtained_res_join_index = sorted(index.join_index(index2))
    assert obtained_res_join_index == expected_res_join


min_k = 12


@mark.parametrize("index_type", index_types)
@mark.parametrize("k", [k for k in valid_k if k > min_k])
@mark.parametrize("shard_number", [1, 5])
def test_tmp_kmerindex(index_type, dnas, k, shard_number):
    def generator():
        return iter(dnas)

    index = temporary_kmerindex(
        generator, k=k, shard_number=shard_number, index_type=index_type
    )
    expected = {
        kmer: i for dna, i in generator() for kmer in dna.enum_canonical_kmer(k)
    }
    for kmer, i in expected.items():
        assert index[kmer] == i

    assert len(index) == len(expected)


@mark.parametrize("index_type", index_types)
@mark.parametrize("k", [k for k in valid_k if k > min_k])
@mark.parametrize("shard_number", [1, 5])
def test_tmp_kmerset(index_type, dnas, k, shard_number):
    def generator():
        return (d for d, _ in dnas)

    index = temporary_kmerset(
        generator, k=k, shard_number=shard_number, index_type=index_type
    )
    expected = {kmer for dna in generator() for kmer in dna.enum_canonical_kmer(k)}
    for kmer in expected:
        assert kmer in index
    assert len(index) == len(expected)


def test_fixture_setup_test_graph(viz_dir, test_graph_name):
    G = get_graph(test_graph_name)
    indexes = index_info(G.name)
    assert len(indexes) > 0


def test_drop_index(viz_dir, test_graph_name):
    G = get_graph(test_graph_name)
    inst_index_info = index_info(G.name)
    index_type = inst_index_info[0].type
    index_info_size = len(inst_index_info)
    index = load_kmer_index(G.name, index_type)
    assert index is not None
    index.drop()
    assert len(index_info(G.name)) == (index_info_size - 1)
    build_kmer_index(G.name, index_type)  # to restore the situation
