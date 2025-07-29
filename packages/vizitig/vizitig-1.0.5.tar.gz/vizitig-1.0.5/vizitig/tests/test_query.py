from typing import List

from pytest import mark

from vizitig.query import search
from vizitig.env_var import VIZITIG_SHORT_TEST
from vizitig.info import get_graph


simple_queries = [
    ("NodeId(193397)", [193397]),
    ("NodeId(582502)", [582502]),
    ("NodeId(886623)", [886623]),
    ("NodeId(193397, 886623)", [193397, 886623]),
]

metadata_queries = [
    (
        "Transcript(NM_001375317)",
        [
            459264,
            755299,
            552748,
            607290,
            652815,
            1007774,
            294772,
            428330,
            342008,
            950094,
            886623,
            848170,
            582502,
            955234,
            962261,
            379045,
            319176,
            554991,
            529001,
            575709,
        ],
    ),
    (
        "Transcript(NM_001042440)",
        [
            459264,
            812799,
            607290,
            652815,
            1007774,
            529001,
            294772,
            755299,
            428330,
            853615,
            950094,
            886623,
            848170,
            582502,
            955234,
            962261,
            238324,
            379045,
            319176,
            554991,
            737860,
            575709,
            248683,
            467529,
            442212,
            746963,
            786988,
            491686,
            412066,
            425161,
            554637,
            993992,
            655635,
            193397,
            338447,
            552932,
            352158,
            830782,
        ],
    ),
    (
        "Color(sample1)",
        [
            193397,
            238173,
            238180,
            991180,
            926692,
            238324,
            238181,
            950094,
            955234,
            962261,
            972716,
            977360,
            981820,
            993992,
            238309,
            338447,
            1000907,
            1007774,
            1020376,
            165114,
            248683,
            294772,
            319176,
        ],
    ),
    (
        "Color(sample2)",
        [
            363300,
            527171,
            338447,
            319176,
            342008,
            346767,
            352158,
            425161,
            384747,
            376041,
            379045,
            407716,
            412066,
            428330,
            442212,
            448483,
            459264,
            598817,
            467529,
            468146,
            474484,
            477589,
            477844,
            489535,
            491686,
            529001,
            536477,
            537781,
            552748,
            552932,
            554637,
            554991,
            564171,
            567261,
            575709,
            578603,
            582502,
            607290,
            610914,
            615767,
            617273,
            626412,
            623620,
            652815,
            655635,
            668531,
            703881,
            737860,
            746963,
            755299,
            767053,
            786988,
            800328,
            812799,
            830782,
            846009,
            846155,
            848170,
            853615,
            883197,
            886623,
            893117,
        ],
    ),
    (
        "Gene(CAST)",
        [
            193397,
            238324,
            248683,
            294772,
            319176,
            338447,
            342008,
            352158,
            379045,
            412066,
            425161,
            428330,
            442212,
            459264,
            467529,
            477589,
            489535,
            491686,
            529001,
            552748,
            552932,
            554637,
            554991,
            567261,
            575709,
            578603,
            582502,
            607290,
            623620,
            652815,
            655635,
            737860,
            746963,
            755299,
            786988,
            812799,
            830782,
            846155,
            848170,
            853615,
            886623,
            950094,
            955234,
            962261,
            993992,
            1007774,
        ],
    ),
]
sequence_queries = [
    ("Kmer(AAATCACCCTACTTCTATTGA)", [767053]),
    ("Kmer(AAAAAATTATATATATATATA)", [238180]),
    ("Kmer(ATGAGGCAAAAGCTAAAGAAG)", [379045]),
    ("Kmer(GCCGGCTCCCCCGCCGTGCGG)", [552748]),
    ("Kmer(TGTTAGGAAGATGTGGTCCTT)", [623620]),
    ("Kmer(CTATGTAGGTGGAACTCATTG)", [955234]),
    (
        "Seq(AGGTTCTGTTTTTACAGCCTGTTTTTTGTGTTTTTTCTTGTTAGGAAGATGTGGTCCTTCCATCTGTTGGCTGACTGGAATGGCCTTGGTTTCTGTG)",
        [623620],
    ),
    (
        "Seq(CTTTATAATTTTTGTAGAAATTATATAAGGAGTCAGGAGTTTGAGACTGCCCGGGCCGAGTCTGGCTTACACACCGGTTGAATTC)",
        [926692],
    ),
    (
        "Seq(AAGAAGGCATCAAACAAAACAAGGATGTTTACAGACATATGCAAAGGGTCAGGATATCTATCCTCCAGTATAT)",
        [1000907],
    ),
    ("Seq(GCACTGTGTGTAGAATGTGCAAAAATTCACTTAGCTTTTCTTTTGTTTTTTTGGTGTTGCTT)", [248683]),
]

kmer_set_21 = [
    "ATCGTGAGTCGGCTGATGCTA",
    "GCTGATCGATCGGATGTCGTA",
    "ATTCGATGCTTAGATCCGATT",
    "ATCGGGCTAAATCGATTCGGT",
]

conditionnal_queries = [
    (
        "Transcript(NM_001375317) and Transcript(NM_001042440)",
        [
            294772,
            319176,
            379045,
            428330,
            459264,
            529001,
            554991,
            575709,
            582502,
            607290,
            652815,
            755299,
            848170,
            886623,
            950094,
            955234,
            962261,
            1007774,
        ],
    ),
    ("Color(sample1) and Color(sample2)", [319176, 338447]),
    (
        "Color(sample1) or Color(sample2)",
        [
            165114,
            193397,
            238173,
            238180,
            238181,
            238309,
            238324,
            248683,
            294772,
            319176,
            338447,
            342008,
            346767,
            352158,
            363300,
            376041,
            379045,
            384747,
            407716,
            412066,
            425161,
            428330,
            442212,
            448483,
            459264,
            467529,
            468146,
            474484,
            477589,
            477844,
            489535,
            491686,
            527171,
            529001,
            536477,
            537781,
            552748,
            552932,
            554637,
            554991,
            564171,
            567261,
            575709,
            578603,
            582502,
            598817,
            607290,
            610914,
            615767,
            617273,
            623620,
            626412,
            652815,
            655635,
            668531,
            703881,
            737860,
            746963,
            755299,
            767053,
            786988,
            800328,
            812799,
            830782,
            846009,
            846155,
            848170,
            853615,
            883197,
            886623,
            893117,
            926692,
            950094,
            955234,
            962261,
            972716,
            977360,
            981820,
            991180,
            993992,
            1000907,
            1007774,
            1020376,
        ],
    ),
    ("Transcript(NM_001375317) and not Transcript(NM_001042440)", [342008, 552748]),
    (
        "Transcript(NM_001375317) or not Transcript(NM_001042440)",
        [
            165114,
            238173,
            238180,
            238181,
            238309,
            342008,
            346767,
            363300,
            376041,
            384747,
            407716,
            448483,
            468146,
            474484,
            477589,
            477844,
            489535,
            527171,
            536477,
            537781,
            552748,
            564171,
            567261,
            578603,
            598817,
            610914,
            615767,
            617273,
            623620,
            626412,
            668531,
            703881,
            767053,
            800328,
            846009,
            846155,
            883197,
            893117,
            894619,
            926349,
            926692,
            972716,
            977360,
            981820,
            991180,
            1000907,
            1020376,
        ],
    ),
]

if VIZITIG_SHORT_TEST:
    graphs = ["mini_bcalm"]
else:
    graphs = ["mini_bcalm", "mini_bcalm_alt1", "mini_bcalm_alt2"]


class TestQuery:
    @mark.parametrize("query, result", simple_queries)
    @mark.parametrize("graph_name", graphs)
    def test_simple_queries(self, query: str, result: List[int], viz_dir, graph_name):
        assert result == search(graph_name, query)

    def test_small_k_seq(self):
        nids1 = set(
            search("mini_bcalm", "Seq(AAACAGATCACCCGCTATCTGTT, T=0, k=2)")
        )  # All 2mer are there
        nids2 = set(search("mini_bcalm", "all"))
        assert nids1 == nids2

    @mark.parametrize("query, result", metadata_queries)
    @mark.parametrize("graph_name", graphs)
    def test_metadata_queries(self, query: str, result: List[int], viz_dir, graph_name):
        assert sorted(result) == sorted(search(graph_name, query))

    @mark.parametrize("query, result", sequence_queries)
    @mark.parametrize("graph_name", graphs)
    def test_sequence_queries(self, query: str, result: List[int], viz_dir, graph_name):
        assert result == search(graph_name, query)

    @mark.parametrize("kmer", kmer_set_21)
    @mark.parametrize("graph_name", graphs)
    def test_query_coherence(self, kmer, viz_dir, graph_name):
        s1 = search(graph_name, f"Kmer({kmer})")
        s2 = search(
            graph_name,
            f"Seq({kmer})",
        )
        assert s1 == s2

    @mark.parametrize("query, result", conditionnal_queries)
    @mark.parametrize("graph_name", graphs)
    def test_query_conditionnal(
        self, query: str, result: List[int], viz_dir, graph_name
    ):
        assert result == search(graph_name, query)

    @mark.parametrize(
        "graph_name", ["mini_bcalm", "mini_bcalm_alt1", "mini_bcalm_alt2"]
    )
    def test_query_keep_abundance(self, graph_name: str):
        r = search(graph_name, "Color(sample3)")
        assert r is not None

    def test_parentesis(self):
        x0 = 830782
        x1 = 846009
        x2 = 846155
        v1 = search(
            "mini_bcalm", f"NodeId({x1}, {x2}) OR (NodeId({x0}) AND NodeId({x2}))"
        )
        assert set(v1) == set([x1, x2])

        v2 = search(
            "mini_bcalm", f"(NodeId({x1}, {x2}) OR NodeId({x0})) AND NodeId({x2})"
        )
        assert set(v2) == set([x2])
