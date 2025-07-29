import re
import math
from dataclasses import dataclass
from enum import Enum
from typing import Iterator, List, Literal, Mapping, SupportsIndex, cast

from typing_extensions import Self

from vizitig.env_var import VIZITIG_PYTHON_ONLY
from vizitig.utils import vizitig_logger as log

Nucleotide = Literal["A", "C", "G", "T"]
non_CGTA = re.compile("[^ACGT]")


class ESign(Enum):
    pp = "++"
    mp = "-+"
    mm = "--"
    pm = "+-"


class DNAPython(str):
    """A light class to type string with only letters ACGT"""

    def __iter__(self) -> Iterator[Nucleotide]:
        for x in super().__iter__():
            yield cast(Nucleotide, x)

    def enum_kmer(self, k: int) -> Iterator["Kmer"]:
        if len(self) < k:
            return
        kmer = KmerPython.from_sequence(self[:k])
        yield kmer
        for a in self[k:]:
            kmer = kmer.add_right_nucleotid(a)
            yield kmer

    def enum_canonical_kmer(self, k: int) -> Iterator["Kmer"]:
        if len(self) < k:
            return
        kmer = KmerPython.from_sequence(self[:k])
        rc = kmer.reverse_complement()
        yield min(kmer, rc)
        for a in self[k:]:
            kmer = kmer.add_right_nucleotid(a)
            rc = rc.add_left(complement_table[char_to_int[a]])
            yield min(kmer, rc)

    @classmethod
    def from_str(cls, seq: str) -> Iterator["DNA"]:
        yield from (cls(subseq) for subseq in non_CGTA.split(seq))

    def __getitem__(self, __key: SupportsIndex | slice) -> Self:
        return type(self)(super().__getitem__(__key))


Quarter = Literal[0b00, 0b01, 0b10, 0b11]

char_to_int: Mapping[Nucleotide, Quarter] = {"A": 0b00, "C": 0b01, "G": 0b10, "T": 0b11}
int_to_char: Mapping[Quarter, Nucleotide] = {0b00: "A", 0b01: "C", 0b10: "G", 0b11: "T"}
complement_table: Mapping[Quarter, Quarter] = {
    k: cast(Quarter, (~k & 0b11)) for k in int_to_char
}


if not VIZITIG_PYTHON_ONLY:
    try:
        from vizibridge import DNA
    except ImportError:
        DNA = DNAPython
else:
    DNA = DNAPython


@dataclass
class KmerPython:
    data: int
    size: int

    @classmethod
    def from_sequence(cls, seq: DNA) -> Self:
        return cls.from_iter(map(char_to_int.__getitem__, seq))  # type: ignore
        # mypy claim that it expect a str instead of a Nucleotide ???

    def __reduce__(self):
        return (self.__class__, (self.data, self.size))

    @classmethod
    def from_iter(cls, it: Iterator[Quarter]) -> Self:
        data = 0
        size = 0
        for q in it:
            data += q
            data = data << 2
            size += 1
        return cls(data >> 2, size)

    def __iter__(self):
        data = self.data
        for a in range(self.size)[::-1]:
            yield (data & (0b11 << (a * 2))) >> (a * 2)

    def __repr__(self):
        return "".join(map(int_to_char.__getitem__, self))

    def add_left_nucleotid(self, n: Nucleotide) -> Self:
        return self.add_left(char_to_int[n])

    def add_right_nucleotid(self, n: Nucleotide) -> Self:
        return self.add_right(char_to_int[n])

    def add_left(self, n: Quarter) -> Self:
        data = (self.data >> 2) + (n << ((self.size - 1) * 2))
        return type(self)(data, self.size)

    def add_right(self, n: Quarter) -> Self:
        data = ((self.data << 2) + (n)) & ((1 << (2 * self.size)) - 1)
        return type(self)(data, self.size)

    def reverse_complement(self) -> Self:
        c = map(complement_table.__getitem__, reversed(list(self)))  # type: ignore
        return self.from_iter(c)  # type: ignore
        # mypy claim weird stuff ...

    def canonical(self) -> Self:
        return min(self, self.reverse_complement())

    def is_canonical(self) -> bool:
        return self == self.canonical()

    def __hash__(self):
        return hash((self.data, self.size))

    def __lt__(self, other) -> bool:
        assert self.size == other.size
        return self.data <= other.data

    def __gt__(self, other) -> bool:
        assert self.size == other.size
        return self.data >= other.data


if not VIZITIG_PYTHON_ONLY:
    try:
        from vizibridge import Kmer, KmerTypeMap

        # Here Kmer is a only a type (a union of classes) and can't be instantiated directly.
        AvailableKmerTypes = KmerPython | Kmer
        AvailableKmerSize = set(KmerTypeMap)
    except ImportError as E:
        log.warning(f"Error importing Rust backend {E}")

        AvailableKmerTypes = KmerPython
        Kmer = KmerPython
        AvailableKmerSize = set(range(2, 63))
else:
    AvailableKmerTypes = KmerPython
    Kmer = KmerPython
    AvailableKmerSize = set(range(2, 63))


@dataclass
class Color:
    id: str
    description: str
    type: str = "Color"
    offset: int | None = None

    def set_offset(self, offset: int):
        self.offset = offset

    def __hash__(self):
        return hash((self.id, self.type, self.offset))

    def short_repr(self):
        return f"Color({self.id})"

    def as_dict(self):
        return dataclass.as_dict(self)


@dataclass
class Abundance:
    id: str
    value: float
    type: str = "Abundance"
    encoded_color_value: int | None = None
    offset: int | None = None

    def set_offset(self, offset: int):
        self.offset = offset

    def __hash__(self):
        return hash((self.id, self.value, self.offset))

    def short_repr(self):
        return f"Abundance({self.id}, {self.value})"


@dataclass
class SubseqData:
    id: str
    type: str
    start: int
    stop: int
    list_attr: List[str]
    chr: str | None = None
    strand: str | None = None
    offset: int | None = None
    first_kmer: int | None = None
    last_kmer: int | None = None
    gene: str | None = None
    transcript: str | None = None

    def short_repr(self):
        return f"{self.type}{self.id}"

    def set_offset(self, offset: int):
        self.offset = offset

    def __hash__(self):
        return hash((self.id, self.type, self.offset))

    def add_first_kmer(self, kmer: Kmer):
        assert isinstance(kmer, Kmer)
        self.first_kmer = kmer.data
        return self

    def get_first_kmer(self, k):
        return Kmer(int.from_bytes(self.first_kmer), k)

    def get_last_kmer(self, k):
        return Kmer(int.from_bytes(self.last_kmer), k)

    def add_last_kmer(self, kmer: Kmer):
        assert isinstance(kmer, Kmer)
        self.last_kmer = kmer.data
        return self

    def __eq__(self, other):
        if type(self) is not type(other):
            return False
        if self.id != other.id:
            return False
        if self.type != other.type:
            return False
        return True

    def as_dict(self):
        return dataclass.as_dict(self)


class Zero:
    """Abstract symbol to be used to be encoded as the INT 0.
    Should be used for filtering between kmer and non kmer metadata.
    e.g. G.find_all_nodes(lambda e:e.lt(Zero())) will return all nodes
    with some metadata.

    Remark that it works as BLOB type in SQLite are always larger than 0 apparently.

    """


Metadata = Color | SubseqData
ViziKey = Metadata | Literal["sequence"] | Kmer | Zero


def metadata_from_dict(d: dict) -> Metadata:
    if d["type"] == "Color":
        return Color(**d)
    return SubseqData(**d)


def encode_kmer(kmer: Kmer, k: int) -> int | bytes:
    data = kmer.data
    if k < 32:
        return data
    if k < 64:
        return int.to_bytes(data, length=math.ceil(k / 4))
    assert isinstance(data, bytes)
    return data


def decode_kmer(data: bytes | int, k: int) -> Kmer:
    if isinstance(data, bytes):
        if len(data) <= 16:
            return Kmer(int.from_bytes(data), k)
        return Kmer(data, k)
    return Kmer(data, k)
