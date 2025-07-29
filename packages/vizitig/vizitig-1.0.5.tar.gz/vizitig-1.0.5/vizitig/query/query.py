from typing import Literal, TypeAlias

from lark import Lark, Transformer
from lark import exceptions as larkexceptions
from pydantic.dataclasses import dataclass
from vizitig.errors import ParseError


class Base:
    @property
    def t(self):
        keys = self.__dataclass_fields__.values()
        key = next(iter(keys))
        return getattr(self, key.name)


@dataclass(frozen=True)
class All(Base):
    all: None = None


@dataclass(frozen=True)
class Loop(Base):
    loop: None = None


@dataclass(frozen=True)
class Partial(Base):
    partial: None = None


@dataclass(frozen=True)
class Selection(Base):
    selection: None = None


@dataclass(frozen=True)
class NodeId(Base):
    id: tuple[int, ...]


@dataclass(frozen=True)
class Attr:
    key: str
    value: str | int
    op: Literal["=", "<", ">"]


@dataclass(frozen=True)
class Meta(Base):
    type: str
    name: str | None = None
    attrs: tuple[Attr, ...] = ()


@dataclass(frozen=True)
class Op(Base):
    operation: Literal["=", "<", ">", "<=", ">="]


@dataclass(frozen=True)
class Abundance(Base):
    operation: Op
    value: int


@dataclass(frozen=True)
class Color(Base):
    color: str
    abundance: Abundance | None = None


@dataclass(frozen=True)
class Kmer(Base):
    kmer: str


@dataclass(frozen=True)
class Degree(Base):
    degree: int


@dataclass(frozen=True)
class Threshold(Base):
    val: int


@dataclass(frozen=True)
class SmallK(Base):
    val: int


@dataclass(frozen=True)
class Seq(Base):
    seq: str
    threshold: Threshold | None = None
    smallk: SmallK | None = None


@dataclass(frozen=True)
class PseudoMapping(Base):
    psdomap: str


@dataclass(frozen=True)
class And(Base):
    land: list["Term"]


@dataclass(frozen=True)
class Or(Base):
    lor: list["Term"]


@dataclass(frozen=True)
class Not(Base):
    lnot: "Term"


@dataclass(frozen=True)
class Parenthesis(Base):
    par: "Term"


Term: TypeAlias = (
    NodeId
    | Meta
    | Color
    | And
    | Or
    | Not
    | Kmer
    | str
    | Seq
    | Op
    | Abundance
    | All
    | Loop
    | Partial
    | Selection
    | Degree
    | Parenthesis
)


Grammar = r"""
?formula: lor_infix  
        | lor_prefix
        | land 
        | lnot 
        | par  
        | literal

_LEFTPAR  : /\s*\(\s*/ 
_RIGHTPAR : /\s*\)\s*/
par      : _LEFTPAR formula _RIGHTPAR 
_SEP      : /\s*,\s*/
lor_infix : formula "or"i (_SPACES formula | par) 
lor_prefix: "or"i _LEFTPAR (formula ( _SEP formula )*)? _RIGHTPAR
land      : formula "and"i (_SPACES formula | par)
lnot      : "not"i (_SPACES formula | par)
_SPACES   : /\s+/
        
?literal: nodeid 
        | kmer 
        | color
        | psdomap
        | meta
        | seq
        | all
        | loop
        | partial
        | selection 
        | degree 
    
selection.1: "selection"i ((_LEFTPAR _RIGHTPAR) |)
partial.1  : "Partial"i ((_LEFTPAR _RIGHTPAR) |)
all.1      : "All"i ((_LEFTPAR _RIGHTPAR) |)
loop.1      : "loop"i ((_LEFTPAR _RIGHTPAR) |)
nodeid.1   : "NodeId"i _LEFTPAR  integer ("," integer)* _RIGHTPAR
color.1    : "Color"i _LEFTPAR  ident ("," abundance |)  _RIGHTPAR
degree.1   : "Degree"i _LEFTPAR integer _RIGHTPAR
meta.0     : ident _LEFTPAR (arg ( _SEP  arg )* | ) _RIGHTPAR
?arg       : ident | attr

abundance  : "A" op integer
kmer.2     : "Kmer"i _LEFTPAR acgt  _RIGHTPAR
attr       : ident op (ident | integer)
seq.1      : "Seq"i _LEFTPAR acgt ( "," threshold)? ("," small_k)?  _RIGHTPAR
psdomap.1  : ("PseudoMapping"i | "PM"i ) _LEFTPAR acgt _RIGHTPAR
?op        : (EQUAL | LT | GT | LTE | GTE)

EQUAL      : "="
LT         : "<"
GT         : ">"
LTE        : "<="
GTE        : ">="
threshold : ("T"i | "Threshold"i) "=" integer
small_k    : ("k"i | "small-k"i) "="  integer

acgt       : /[ACGT]+/i 
integer    : INT
ident      : /[a-zA-Z_][\w\.\-\_]*/i
    
%import common.CNAME
%import common.INT
%import common.WS 
%ignore WS
"""


class QueryEval(Transformer):
    def kmer(self, e):
        return Kmer(e[0])

    def degree(self, e):
        return Degree(e[0])

    def seq(self, e):
        kwargs = dict()
        for f in e[1:]:
            if isinstance(f, SmallK):
                kwargs["smallk"] = f
            if isinstance(f, Threshold):
                kwargs["threshold"] = f
        return Seq(e[0], **kwargs)

    def all(self, *args):
        return All()

    def loop(self, *args):
        return Loop()

    def partial(self, *args):
        return Partial()

    def selection(self, *args):
        return Selection()

    def acgt(self, e):
        # return next(DNA.from_str(e[0]))
        return e[0]

    def psdomap(self, e):
        return PseudoMapping(e[0])

    def integer(self, e):
        return int(e[0])

    def ident(self, e):
        return str(e[0])

    def threshold(self, e):
        return Threshold(e[0])

    def small_k(self, e):
        return SmallK(e[0])

    def abundance(self, e):
        return Abundance(Op(e[0]), e[1])

    def color(self, e):
        return Color(*e)

    def attr(self, e):
        return Attr(key=e[0], op=e[1], value=e[2])

    def op(self, e):
        return str(e[0])

    def meta(self, args):
        type = args[0]
        name = None
        attrs = []
        for arg in args[1:]:
            if isinstance(arg, Attr):
                attrs.append(arg)
                continue
            assert name is None
            name = arg
        return Meta(type=type, name=name, attrs=attrs)

    def nodeid(self, e):
        return NodeId(e)

    def land(self, e):
        return And(list(filter(bool, e)))

    def lor(self, e):
        return Or(list(filter(bool, e)))

    lor_prefix = lor
    lor_infix = lor

    def lnot(self, e):
        k = next(filter(bool, e))
        return Not(k)

    def par(self, e):
        k = next(filter(bool, e))
        return Parenthesis(k)


parser = Lark(Grammar, start="formula")


def parse(query: str) -> Term:
    try:
        tree = parser.parse(query)
    except larkexceptions.LarkError as E:
        raise ParseError(E)
    q = QueryEval().transform(tree)
    return q
