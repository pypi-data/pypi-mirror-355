from functools import singledispatch
from typing import Iterable

import networkdisk as nd

from vizitig.errors import InvalidKmerSize, MetaNotFound, NoIndex, QueryError
from vizitig.index import load_kmer_index, index_info
from vizitig.info import get_graph
from vizitig.query import query
from vizitig.query.query import Term, parse
from vizitig.types import DNA, Kmer
from vizitig.utils import vizitig_logger as logger


def search_kmers(
    graph_name, kmers, small_k: int | None = None
) -> nd.sql.helper.IterableQuery:
    G = get_graph(graph_name)
    kmers = set(kmers)
    if not kmers:
        return empty_iterable_query(G)
    try:
        kmer_index = load_kmer_index(graph_name, small_k=small_k)
    except NoIndex:
        small_ks = sorted((idx.k for idx in index_info(graph_name)))
        small_ks_repr = "None" if not small_ks else str(small_ks)
        raise QueryError(
            f"Index needed with small-k={small_k}, (available {small_ks_repr})"
        )
    nids = set(kmer_index.intersection(kmers))
    if nids:
        return constants_to_iterable_query(G, nids)
    return empty_iterable_query(G)


def constant_to_iterable_query(
    G: nd.sqlite.DiGraph,
    nid: int,
) -> nd.sql.helper.IterableQuery:
    col = G.dialect.columns.ValueColumn(nid)
    query = G.dialect.queries.SelectQuery(columns=(col,))
    return G.dialect.helper.IterableQuery(G.helper, query).map(lambda e: e[0])


def constants_to_iterable_query(
    G: nd.sqlite.DiGraph,
    nodes: Iterable[int],
) -> nd.sql.helper.IterableQuery:
    query = G.dialect.queries.ValuesQuery(*nodes)
    return G.dialect.helper.IterableQuery(G.helper, query).map(lambda e: e[0])


def empty_iterable_query(G: nd.sqlite.DiGraph) -> nd.sql.helper.IterableQuery:
    col = G.dialect.columns.ValueColumn(1)
    cond = G.dialect.conditions.FalseCondition()
    query = G.dialect.queries.SelectQuery(columns=(col,), condition=cond)
    return G.dialect.helper.IterableQuery(G.helper, query).map(lambda e: e[0])


def limit_iterable_query(
    iq: nd.sql.helper.IterableQuery, limit: int
) -> nd.sql.helper.IterableQuery:
    dialect = iq.helper.dialect

    return nd.sql.helper.IterableQuery(
        iq.helper, dialect.queries.SelectQuery(iq.query, limit=limit)
    ).map(lambda e: e[0])


@singledispatch
def _search(T: Term, gname: str) -> nd.sql.helper.IterableQuery:
    raise NotImplementedError(T)


@_search.register(query.Meta)
def _(T, gname):
    G = get_graph(gname)
    if T.attrs:
        raise NotImplementedError
    try:
        if T.name is None:
            metadata = list(G.metadata.get_all_by_type(T.type))
            if metadata:
                iq = G.find_all_nodes(metadata[0])
            else:
                raise MetaNotFound(T.type)
            for meta in metadata[1:]:
                iq = iq.union(G.find_all_nodes(meta))
            return iq
        meta = G.metadata.get_metadata(T.type, T.name)
    except KeyError:
        raise MetaNotFound(T)
    return G.find_all_nodes(meta)


@_search.register(query.Color)
def _(T, gname):
    G = get_graph(gname)
    try:
        color = G.metadata.get_metadata("Color", T.t)
    except KeyError:
        raise MetaNotFound(T.t)
    kwargs = {}
    if T.abundance:
        if T.abundance.operation.t == "<":
            kwargs = {color: lambda e: e.cast("INTEGER").lt(T.abundance.value)}
        if T.abundance.operation.t == "<=":
            kwargs = {color: lambda e: e.cast("INTEGER").le(T.abundance.value)}
        if T.abundance.operation.t == "=":
            kwargs = {color: lambda e: e.cast("INTEGER").eq(T.abundance.value)}
        if T.abundance.operation.t == ">":
            kwargs = {color: lambda e: e.cast("INTEGER").gt(T.abundance.value)}
        if T.abundance.operation.t == ">=":
            kwargs = {color: lambda e: e.cast("INTEGER").ge(T.abundance.value)}

    return G.find_all_nodes(color, kwargs)


@_search.register(query.All)
def _(T, gname):
    G = get_graph(gname)
    return G.find_all_nodes()


@_search.register(query.Partial)
def _(T, gname):
    raise QueryError("Partial is only for Client-side")


@_search.register(query.Degree)
def _(T, gname):
    raise QueryError("Degree is only for Client-side")


@_search.register(query.Selection)
def _(T, gname):
    raise QueryError("Selection is only for Client-side")


@_search.register(query.Loop)
def _(T, gname):
    raise QueryError("Loop is only for Client-side")


@_search.register(query.Kmer)
def _(T, gname):
    G = get_graph(gname)
    if len(T.t) != G.metadata.k:
        raise InvalidKmerSize(f"{T.size} expected {G.metadata.k}")

    kmer = Kmer.from_sequence(DNA(T.kmer)).canonical()
    return search_kmers(gname, (kmer,))


@_search.register(query.Seq)
def _(T, gname):
    G = get_graph(gname)
    if T.smallk:
        small_k = T.smallk.val
        threshold = T.threshold.val if T.threshold else 70
    else:
        # if small_k is not setup we compute one which is valid
        potential_idx = [idx.k for idx in index_info(gname) if idx.k <= len(T.seq)]
        threshold = T.threshold.val if T.threshold else 0
        if not potential_idx:
            if T.threshold:
                raise QueryError("Threshold can't be taken into account without index")
            return G.find_all_nodes(sequence=lambda e: e.like(f"%{T.seq}%"))
        idx = max(potential_idx)
        small_k = None
        if idx != G.metadata.k:
            small_k = idx

    k = small_k if small_k else G.metadata.k
    kmers = set(next(iter(DNA.from_str(T.seq))).enum_canonical_kmer(k))
    iq = search_kmers(gname, kmers, small_k=small_k)
    if threshold:  # if threshold is 0 we don't even take it into account
        nodes = list()
        for node in iq:
            dna = next(DNA.from_str(G.nodes[node]["sequence"]))
            local_kmers = set(dna.enum_canonical_kmer(k))
            if len(local_kmers.intersection(kmers)) / len(local_kmers) >= (
                threshold / 100
            ):
                nodes.append(node)
        if not nodes:
            return empty_iterable_query(G)
        iq = constants_to_iterable_query(G, nodes)
    return iq


@_search.register(query.NodeId)
def _(T, gname):
    G = get_graph(gname)
    return G.nbunch_iter(T.t)


@_search.register(query.And)
def _(T, gname):
    iqs = list(map(lambda t: _search(t, gname), T.t))
    return iqs[0].intersection(*iqs[1:])


@_search.register(query.Or)
def _(T, gname):
    iqs = list(map(lambda t: _search(t, gname), T.t))
    if iqs:
        return iqs[0].union(*iqs[1:])
    G = get_graph(gname)
    return empty_iterable_query(G)


@_search.register(query.Not)
def _(T, gname):
    G = get_graph(gname)
    return G.find_all_nodes().difference(_search(T.t, gname))


@_search.register(query.Parenthesis)
def _(T, gname):
    G = get_graph(gname)
    iq = _search(T.t, gname)
    return G.dialect.helper.IterableQuery(
        G.helper, G.dialect.queries.SelectQuery(iq.query)
    ).map(lambda e: e[0])


def search(name: str, q: str, limit=1000) -> list[int]:
    logger.info(f"Parsing {q}")
    term = parse(q)
    logger.info(f"Query {q} successfully parsed")
    iq = _search(term, name)
    logger.info(f"Query {q} successfully executed")
    if not isinstance(
        iq.query,
        nd.sqlite.queries.SelectQuery,
    ):  # ugly because of nd limit broken on iq with union/intersection
        return list(limit_iterable_query(iq, limit=limit))
    else:
        return list(iq.limit(limit))
