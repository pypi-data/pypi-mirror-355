from pytest import mark
from vizibridge import DNA, Kmer

from vizitig.info import get_graph
from vizitig.types import DNAPython, KmerPython

mixed_types_kmers = [KmerPython, Kmer]
mixed_types_dna = [DNAPython, DNA]

sequences = [
    "TGCTATCGATTCGATATCAGATTCGATCGG",
    "ATGCTAGTCTGATCGATTAGCTTAGCTTAGTCTAGTAGCTAGGCTAGATCGATCGTAGCTGAT",
]


class TestVizibridge:
    @mark.parametrize("seq", sequences)
    def test_vizibridge_kmers(self, seq: str, viz_dir, test_graph_name):
        G = get_graph(test_graph_name)
        k = G.metadata.k
        l1 = list(next(DNA.from_str(seq)).enum_canonical_kmer(k))
        l2 = list(next(DNAPython.from_str(seq)).enum_canonical_kmer(k))
        assert len(l1) == len(l2)
        for i in range(len(l1)):
            assert l1[i].data == l2[i].data

    @mark.parametrize("seq", sequences)
    def test_vizibridge_kmers_enumeration(self, seq: str, viz_dir, test_graph_name):
        G = get_graph(test_graph_name)
        k = G.metadata.k
        l1 = list(next(DNA.from_str(seq)).enum_kmer(k))
        l2 = list(next(DNAPython.from_str(seq)).enum_kmer(k))
        assert len(l1) == len(l2)
        for i in range(len(l1)):
            assert l1[i].data == l2[i].data
