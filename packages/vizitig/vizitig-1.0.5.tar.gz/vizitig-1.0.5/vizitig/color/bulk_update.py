from itertools import groupby
from typing import Tuple, Callable, Iterator, MutableMapping, List, Any, cast
from statistics import median

from vizitig.index import load_kmer_index
from vizitig.info import get_graph
from vizitig.index import temporary_kmerindex
from vizitig.types import DNA, SubseqData, Color
from vizitig.env_var import VIZITIG_NO_TMP_INDEX
from vizitig.utils import vizitig_logger as logger, progress, IteratableFromGenerator


def bulk_annotate_graph(
    gname: str,
    generator: Callable[[], Iterator[Tuple[DNA, int]]],
    color: Color | None = None,
    agg: Callable = median,
    metas: list[SubseqData] | None = None,
):
    Graph = get_graph(gname)
    k = Graph.metadata.k
    index = load_kmer_index(gname)

    def pos_int_generator():
        for dna, i in generator():
            yield (dna, abs(i))

    if VIZITIG_NO_TMP_INDEX:
        it_dna = pos_int_generator()
        it_kmer = (
            (kmer, key) for dna, key in it_dna for kmer in dna.enum_canonical_kmer(k)
        )
        res_join = groupby(sorted(index.join(it_kmer)), key=lambda e: e[0])
    else:
        tmp_index = temporary_kmerindex(
            pos_int_generator,
            k,
            index_type=index.index_type.__name__,
            shard_number=index.shard_number,
        )
        res_join = groupby(sorted(index.join_index(tmp_index)), key=lambda e: e[0])
        # sorted could probably be removed in index join is in sorted order.

    # This could be done by chunk, if too big to hold in RAM
    graph_annotations: List[
        Tuple[Any, MutableMapping[SubseqData, int] | MutableMapping[Color, int]]
    ] = []

    annotation_size = 0

    if color:
        for inode, f in res_join:
            graph_annotations.append(
                (inode, {color: agg(tuple(abundance for _, abundance in f))})
            )
            annotation_size += 1
    else:
        if metas is not None:
            decoder_dict: dict[int, SubseqData] = {
                m.offset: m for m in metas if m.offset is not None
            }

            assert len(decoder_dict) == len(metas)

            def decoder(e: int) -> SubseqData:
                return decoder_dict[e]
        else:

            def decoder(e: int) -> SubseqData:
                return Graph.metadata.decoder(-e)

        meta_to_add: set[SubseqData] = set()
        for inode, E in res_join:
            d: MutableMapping[SubseqData, int] = {}
            for _, meta_int in E:
                meta = decoder(meta_int)
                d[meta] = -1
                if not isinstance(meta, Color) and meta.gene:
                    upstream_gene = SubseqData(
                        id=meta.gene,
                        type="Gene",
                        start=meta.start,
                        stop=meta.stop,
                        list_attr=meta.list_attr,
                    )
                    meta_to_add.add(upstream_gene)
                    d[upstream_gene] = -1

                if not isinstance(meta, Color) and meta.transcript:
                    upstream_transcript = SubseqData(
                        id=meta.transcript,
                        type="Transcript",
                        start=meta.start,
                        stop=meta.stop,
                        list_attr=meta.list_attr,
                    )
                    meta_to_add.add(upstream_transcript)
                    d[upstream_transcript] = -1
                    if upstream_transcript.gene:
                        upstream_gene = SubseqData(
                            id=upstream_transcript.gene,
                            type="Gene",
                            start=meta.start,
                            stop=meta.stop,
                            list_attr=meta.list_attr,
                        )
                        meta_to_add.add(upstream_gene)
                        d[upstream_gene] = -1

            graph_annotations.append((inode, d))
            annotation_size += len(d)
        if meta_to_add:
            meta_to_add = set(Graph.metadata.add_iterative_metadatas(meta_to_add))
            meta_to_add_dict = {m.short_repr(): m for m in meta_to_add}
            for i in range(len(graph_annotations)):
                inode, val = graph_annotations[i]
                new_d = {
                    meta_to_add_dict.get(m.short_repr(), cast(SubseqData, m)): v
                    for m, v in val.items()
                }
                graph_annotations[i] = (inode, new_d)

    logger.info(f"Adding {annotation_size} annotations to graph")
    iter_from_gene = IteratableFromGenerator(
        lambda: progress(graph_annotations, total=len(graph_annotations))
    )
    Graph.add_node_data_from(iter_from_gene)
