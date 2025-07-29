from typing import Iterable, List, MutableMapping, Tuple, Any
from itertools import groupby
import dataclasses
from functools import lru_cache

import networkdisk as nd
from pydantic import BaseModel

from vizitig import compatible_versions, version
from vizitig.errors import (
    IncompatibleViziGraph,
    NotAViziGraphError,
    MetadataDuplicate,
    MetaNotFound,
)
from vizitig.types import (
    AvailableKmerTypes,
    ESign,
    SubseqData,
    ViziKey,
    Zero,
    encode_kmer,
    decode_kmer,
    Metadata,
    metadata_from_dict,
)

from vizitig.utils import vizitig_logger


class NodeDesc(BaseModel):
    seq: str
    metadatas: List[Tuple[Metadata, Any]]
    neighbors: dict[int, ESign | None] = {}


class GraphMetadata(BaseModel):
    k: int
    size: int
    name: str
    edge_size: int  # number of edges
    gid: str  # a uniq global identifier of the graph generated once
    states: dict[str, str] = dict()
    types_list: List[str] = list()
    filter_list: MutableMapping[str, str] = dict()
    vizitig_version: str = version
    kmer_size: int | None

    def __hash__(self):
        return hash((type(GraphMetadata).__name__, self.name))

    def model_post_init(self, __context):
        nd.utils.serialize.encoderFunctions[self.key_type] = (
            self.encoder,
            self.decoder,
        )

    @property
    def graph(self) -> nd.sqlite.Graph | nd.sqlite.DiGraph:
        from vizitig.info import get_graph

        return get_graph(self.name)

    @property
    def metadata_graph(self) -> nd.sqlite.DiGraph:
        return self.graph.metadata_graph

    @property
    def key_type(self):
        return f"vizi_{self.gid}".upper()

    @lru_cache(maxsize=None)
    def encoder(self, to_encode: ViziKey | Zero) -> int | float | bytes:
        if isinstance(to_encode, float):
            return to_encode
        if isinstance(to_encode, Metadata):
            if to_encode.offset is None:
                to_encode = self.get_metadata(to_encode.type, to_encode.id)
                assert to_encode.offset is not None
            return -(to_encode.offset + 10)
        if isinstance(to_encode, AvailableKmerTypes):
            return encode_kmer(to_encode, self.k)
        if to_encode == "sequence":
            return -1
        if to_encode == "occurence":
            return -2

        if "Kmer" in str(type(to_encode)):
            raise TypeError(f"""your Kmer Class ({type(to_encode)})is locally unknown. 
                                Avoid if this error occurs during tests.""")
        if isinstance(to_encode, Zero):
            return 0
        raise NotImplementedError(f"to_encode is of incorrect type {type(to_encode)}")

    def add_filter(self, fname: str, filter: str):
        assert isinstance(filter, str)
        self.filter_list[fname] = filter

    def get_filters(self) -> Iterable[tuple[str, str]]:
        return self.filter_list.items()

    def remove_filter(self, fname: str):
        assert fname in self.filter_list
        self.filter_list.pop(fname)

    @lru_cache(maxsize=None)
    def decoder(self, to_decode):
        if isinstance(to_decode, bytes) or (
            isinstance(to_decode, int) and to_decode >= 0
        ):
            return decode_kmer(to_decode, self.k)
        if isinstance(to_decode, float):
            return to_decode
        if to_decode == -1:
            return "sequence"
        if to_decode == -2:
            return "occurence"
        if to_decode <= -3:
            return self.get_metadata_offset(-to_decode - 10)

        raise NotImplementedError(
            f"to_decode is of incorrect type or value {to_decode, type(to_decode)}",
        )

    def add_iterative_metadatas(
        self,
        iterator: Iterable[Metadata],
    ) -> Iterable[Metadata]:
        grouped_metadata = groupby(
            sorted(iterator, key=lambda e: (e.type, e.id)),
            key=lambda e: (e.type, e.id),
        )
        meta_to_add = []
        meta_to_get = []
        all_metas = {key: d for key, d in self.metadata_graph.nodes(data=True)}
        offset = len(all_metas)
        assert self.metadata_graph.graph["size"] == offset
        for (typ, id_), group in grouped_metadata:
            versions = list(group)

            short_repr = versions[0].short_repr()
            meta_to_get.append(short_repr)
            if short_repr in all_metas:
                continue
            m = dataclasses.asdict(versions[0])
            if isinstance(versions[0], SubseqData):
                start = m["start"]
                stop = m["stop"]
                for vers in versions[1:]:
                    assert isinstance(vers, SubseqData)
                    start = min(vers.start, start)
                    stop = max(vers.stop, stop)
                    for key in ("gene", "transcript"):
                        if key in m:
                            m[key] = m[key] or getattr(vers, key)
                m["start"] = start
                m["stop"] = stop

            if typ not in self.types_list:
                self.types_list.append(typ)
            m["offset"] = offset
            offset += 1
            meta_to_add.append((short_repr, m))
        self.metadata_graph.add_nodes_from(meta_to_add)
        all_metas.update({k: d for k, d in meta_to_add})
        res = list(metadata_from_dict(all_metas[k]) for k in meta_to_get)
        self.metadata_graph.graph["size"] = len(all_metas)
        self.commit_to_graph()
        return res

    def add_metadata(self, m_to_add: Metadata) -> Metadata:
        return next(iter(self.add_iterative_metadatas([m_to_add])))

    def set_all_offsets(self):
        nodes_without_offset = self.metadata_graph.find_all_nodes("offset", offset=None)
        size = self.metadata_graph.graph["size"]
        data = [
            (node, dict(offset=size + 1 + i))
            for i, node in enumerate(nodes_without_offset)
        ]
        self.metadata_graph.add_node_data_from(data)
        self.metadata_graph.graph["size"] = size + len(data)

    def get_metadata(self, type: str, id: str) -> Metadata:
        iq = self.metadata_graph.find_all_nodes("type", type=type)
        iq = iq.intersection(self.metadata_graph.find_all_nodes("id", id=id))
        nodes = list(iq)
        if len(nodes) > 1:
            raise MetadataDuplicate(f"{nodes[0]} founds with {len(nodes)} copy")
        if not nodes:
            vizitig_logger.warning(f"Not node returned for Meta {type}{id}. Skipping")
            # return SubseqData()
            raise MetaNotFound(f"{type}({id})")
        return metadata_from_dict(self.metadata_graph.nodes[nodes[0]].fold())

    def all_metadata_by_types(self, type: str) -> Iterable[Metadata]:
        select_metadata = self.metadata_graph.find_all_nodes("type", type=type)
        iq = self.metadata_graph.nbunch_iter(select_metadata, data=True)
        return list(iq.map(lambda e: metadata_from_dict(e[1])))

    def get_metadata_offset(self, offset: int) -> Metadata:
        try:
            node = self.metadata_graph.find_one_node("offset", offset=offset)
            return metadata_from_dict(self.metadata_graph.nodes[node].fold())
        except nd.exception.NetworkDiskError:
            raise MetaNotFound(offset)

    def get_all_by_type(self, type: str) -> Iterable[Metadata]:
        iq = self.metadata_graph.find_all_nodes("type", type=type)
        L = list(self.metadata_graph.subgraph(iq).nodes(data=True))
        return [metadata_from_dict(e) for _, e in L]

    def commit_to_graph(
        self,
        G: nd.sqlite.Graph | nd.sqlite.DiGraph | None = None,
        set_offset: bool = True,
    ) -> None:
        if G is None:
            G = self.graph
        G.graph = self.model_dump()

    def get_states(self) -> list[str]:
        return list(self.states)

    def get_state(self, state_name: str) -> str:
        return self.states[state_name]

    def set_state(self, state_name: str, state: str):
        self.states[state_name] = state
        self.commit_to_graph()

    def delete_state(self, state_name: str):
        del self.states[state_name]
        self.commit_to_graph()

    @classmethod
    def set_metadata(
        cls,
        G: nd.sqlite.DiGraph | nd.sqlite.Graph,
        check_compatibility: bool = True,
        name: str | None = None,
    ):
        d = G.graph.fold()
        d.setdefault("name", name)
        if "vizitig_version" not in d:
            raise NotAViziGraphError()
        if check_compatibility and d["vizitig_version"] not in compatible_versions:
            raise IncompatibleViziGraph(d["vizitig_version"])
        GM = cls(**d)
        assert GM.gid
        G.metadata = GM

    def to_nodedesc(
        self,
        d: dict[ViziKey, None | Any],
        neighbors: dict[int, ESign | None],
    ) -> NodeDesc:
        metadatas = list()
        for k, v in d.items():
            if isinstance(k, Metadata):
                metadatas.append((k, v))
        return NodeDesc(
            seq=str(d["sequence"]),
            metadatas=metadatas,
            neighbors=neighbors,
        )
