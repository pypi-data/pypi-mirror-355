from pytest import mark
from vizibridge import DNA, Kmer

from vizitig.types import DNAPython, KmerPython, Nucleotide, AvailableKmerSize

sequences_and_revcomp = [
    ("ATCGTAGCTGATCG", "CGATCAGCTACGAT"),
    ("ATCGTAGCTGATC", "GATCAGCTACGAT"),
    ("ATCGTAGCTGAT", "ATCAGCTACGAT"),
    ("ATCGTAGCTG", "CAGCTACGAT"),
    ("AAAAAAAAAA", "TTTTTTTTTT"),
    ("ACTGCATATGCAGT", "ACTGCATATGCAGT"),
    (
        "ATGCTAGTCTGATCGATTAGCTTAGCTTAGTCTAGTAGCTAGGCTAGATCGATCGTAGCTGAT",
        "ATCAGCTACGATCGATCTAGCCTAGCTACTAGACTAAGCTAAGCTAATCGATCAGACTAGCAT",
    ),
]

kmers_and_canonical = [
    ("CGATCAGCTACGAT", "ATCGTAGCTGATCG"),
    ("ATCGTAGCTGATC", "ATCGTAGCTGATC"),
    ("ATCGTAGCTGAT", "ATCAGCTACGAT"),
    ("CAGCTACGAT", "ATCGTAGCTG"),
    ("AAAAAAAAAA", "AAAAAAAAAA"),
    ("ACTGCATATGCAGT", "ACTGCATATGCAGT"),
    (
        "ATGCTAGTCTGATCGATTAGCTTAGCTTAGTCTAGTAGCTAGGCTAGATCGATCGTAGCTGAT",
        "ATCAGCTACGATCGATCTAGCCTAGCTACTAGACTAAGCTAAGCTAATCGATCAGACTAGCAT",
    ),
]

sequences = [
    "CGATCAGCTACGAT",
    "ATCGTAGCTGATC",
    "ATCGTAGCTGAT",
    "CAGCTACGAT",
    "AAAAAAAAAA",
    "ACTGCATATGCAGT",
    "ATGCTAGTCTGATCGATTAGCTTAGCTTAGTCTAGTAGCTAGGCTAGATCGATCGTAGCTGAT",
    "ATGCTAGTCTGATCGATTAGCTTAGCTTAGTCTAGTAGCTAGGCTAGATCGATCGTAGCTGAT" * 5,
    "ATGCTAGTCTGATCGATTAGCTTAGCTTAGTCTAGTAGCTAGGCTAGATCGATCGTAGCTGAT" * 30,
]

kmers_add_left = [
    ("ATCG", "T", "TATC"),
    ("AAAA", "C", "CAAA"),
    ("TTTT", "G", "GTTT"),
    ("GCGC", "G", "GGCG"),
    ("CAGCTACGAT", "A", "ACAGCTACGA"),
    ("ATCGTAGCTGATC", "T", "TATCGTAGCTGAT"),
    (
        "ATGCTAGTCTGATCGATTAGCTTAGCTTAGTCTAGTAGCTAGGCTAGATCGATCGTAGCTGAT",
        "T",
        "TATGCTAGTCTGATCGATTAGCTTAGCTTAGTCTAGTAGCTAGGCTAGATCGATCGTAGCTGA",
    ),
]

kmers_add_right = [
    ("ATCG", "T", "TCGT"),
    ("AAAA", "C", "AAAC"),
    ("TTTT", "G", "TTTG"),
    ("GCGC", "G", "CGCG"),
    ("CAGCTACGAT", "A", "AGCTACGATA"),
    ("ATCGTAGCTGATC", "T", "TCGTAGCTGATCT"),
    (
        "ATGCTAGTCTGATCGATTAGCTTAGCTTAGTCTAGTAGCTAGGCTAGATCGATCGTAGCTGAT",
        "A",
        "TGCTAGTCTGATCGATTAGCTTAGCTTAGTCTAGTAGCTAGGCTAGATCGATCGTAGCTGATA",
    ),
]

kmer_eq = [
    ("AAAA", KmerPython(0, 4), True),
    ("AAAC", KmerPython(1, 4), True),
    ("AAAG", KmerPython(2, 4), True),
    ("AAAT", KmerPython(3, 4), True),
    ("AACA", KmerPython(4, 4), True),
    ("AACA", KmerPython(5, 4), False),
    ("TACA", KmerPython(0, 4), False),
]

kmer_types = [(KmerPython, DNAPython), (Kmer, DNA)]


class TestKmer:
    @mark.parametrize("kmer, okmer, is_eq", kmer_eq)
    def test_kmer_eq(self, kmer: str, okmer: KmerPython, is_eq: bool):
        assert (KmerPython.from_sequence(DNAPython(kmer)) == okmer) == is_eq

    @mark.parametrize("kmer, nucleotide, rkmer", kmers_add_left)
    @mark.parametrize("Kmer, DNA", kmer_types)
    def test_kmer_class_add_left(
        self,
        kmer: str,
        nucleotide: Nucleotide,
        rkmer: str,
        Kmer,
        DNA,
    ):
        K = Kmer.from_sequence(DNA(kmer))
        K = K.add_left_nucleotid(nucleotide)
        RK = Kmer.from_sequence(DNA(rkmer))
        assert K == RK

    @mark.parametrize("kmer, nucleotide, rkmer", kmers_add_right)
    @mark.parametrize("Kmer, DNA", kmer_types)
    def test_kmer_class_add_right(
        self,
        kmer: str,
        nucleotide: Nucleotide,
        rkmer: str,
        Kmer,
        DNA,
    ):
        K = Kmer.from_sequence(DNA(kmer))
        K = K.add_right_nucleotid(nucleotide)
        RK = Kmer.from_sequence(DNA(rkmer))
        assert K == RK

    @mark.parametrize("seq, rseq", sequences_and_revcomp)
    @mark.parametrize("Kmer, DNA", kmer_types)
    def test_kmer_class_reverse_complement(self, seq: str, rseq: str, Kmer, DNA):
        assert Kmer.from_sequence(
            DNA(seq),
        ).reverse_complement() == Kmer.from_sequence(DNA(rseq))

    @mark.parametrize("kmer, c_kmer", kmers_and_canonical)
    @mark.parametrize("Kmer, DNA", kmer_types)
    def test_kmer_class_canonical(self, kmer: str, c_kmer: str, Kmer, DNA):
        assert Kmer.from_sequence(DNA(kmer)).canonical() == Kmer.from_sequence(
            DNA(c_kmer),
        )

    @mark.parametrize("Kmer, DNA", kmer_types)
    def test_kmer_class_enum_kmer(self, Kmer, DNA):
        assert list(map(str, DNA("ACTG"))) == [i for i in "ACTG"]


class TestDNA:
    @mark.parametrize("seq", sequences)
    @mark.parametrize("Kmer, DNA", kmer_types)
    def test_DNAPython_builder(self, seq: str, Kmer, DNA):
        assert str(DNA(seq)) == seq

    @mark.parametrize("Kmer, DNA", kmer_types)
    def test_dna_class_enum_canonical_kmer(self, Kmer, DNA):
        assert list(DNA("ACTG").enum_canonical_kmer(2)) == [
            Kmer.from_sequence(DNA("AC")),
            Kmer.from_sequence(DNA("AG")),
            Kmer.from_sequence(DNA("CA")),
        ]

    @mark.parametrize("seq", sequences)
    @mark.parametrize("Kmer, DNA", kmer_types)
    def test_dna_class_enum_kmer_returns_right_kmer_count(self, seq: str, Kmer, DNA):
        for m in AvailableKmerSize:
            assert len(list(DNA(seq).enum_kmer(m))) == max(0, len(seq) - m + 1)

    @mark.parametrize("seq", sequences)
    @mark.parametrize("Kmer, DNA", kmer_types)
    def test_dna_class_enum_canonical_kmer_returns_right_kmer_count(
        self,
        seq: str,
        Kmer,
        DNA,
    ):
        for m in sorted(AvailableKmerSize):
            assert len(list(DNA(seq).enum_canonical_kmer(m))) == max(
                0, len(seq) - m + 1
            )

    @mark.parametrize("seq", sequences)
    @mark.parametrize("Kmer, DNA", kmer_types)
    def test_dna_class_enum_valid_kmer(
        self,
        seq: str,
        Kmer,
        DNA,
    ):
        for m in sorted(AvailableKmerSize):
            for i, kmer in enumerate(DNA(seq).enum_kmer(m)):
                assert str(kmer) in seq

    @mark.parametrize("seq", sequences)
    @mark.parametrize("Kmer, DNA", kmer_types)
    def test_dna_class_canonicality_of_enum_canonical_kmer(self, seq: str, Kmer, DNA):
        for m in sorted(AvailableKmerSize):
            assert all(kmer.is_canonical() for kmer in DNA(seq).enum_canonical_kmer(m))
