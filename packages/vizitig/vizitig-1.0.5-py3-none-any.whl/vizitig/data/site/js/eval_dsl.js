import {PARTIALLY} from "./config.js";
import {rc} from "./dna_utils.js";

let keys_to_filter = new Set(["abundance", "threshold", "smallk"]);

export class Eval{
    #graph;

    constructor(graph){
        this.#graph = graph;
    }

    get graph(){
        return this.#graph;
    }

    rewrite(query_ast, type, new_ast){
        let root = this.ast_root_key(query_ast);

        if (query_ast.par != undefined){
            let [rewrite, rewritten] = this.rewrite(query_ast.par);
            return [{par: this.rewrite(query_ast.par)}, rewritten];
        }

        if (query_ast.lnot != undefined){
            let [rewrite, rewritten] = this.rewrite(query_ast.lnot);
            return [{lnot: this.rewrite(query_ast.lnot)}, rewritten];
        }
        if (query_ast.land != undefined){
            let [rewrite, rewritten] = query_ast
                    .land
                    .map(e=>this.rewrite(e, type, new_ast))
                    .reduce((x,y) => [x[0].push(y[0]), x[1] || y[1]], [[], false]);
            return {land: query_ast.land.map(e=>this.rewrite(e, type, new_ast))}
        }
        if (query_ast.lor != undefined){
            let [rewrite, rewritten] = query_ast
                    .lor
                    .map(e=>this.rewrite(e, type, new_ast))
                    .reduce((x,y) => [x[0].push(y[0]), x[1] || y[1]], [[], false]);
            return {lor: query_ast.lor.map(e=>this.rewrite(e, type, new_ast))}
        }

        if (root == type)
            return [new_ast, true]
        return [query_ast, false];
    }

    ast_root_key(query_ast){
        if (query_ast.type != undefined)
            return query_ast.type.toLowerCase();
        let keys = Object.keys(query_ast).filter(e => !keys_to_filter.has(e));

        if (keys.length > 1)
            throw new Error("AST should have at most one key");
        return keys[0].toLowerCase();
    }

    eval(query_ast, node_id){
        if (query_ast.par != undefined)
            return this.eval(query_ast.par, node_id);
        let key = this.ast_root_key(query_ast);        
        let data = this.graph.node_with_data(node_id);
        if (this[key]== undefined)
            return this.var_meta(key, query_ast, node_id, data);

        return this[key](query_ast, node_id, data);
    }

    land(query_ast, node_id, data){
        return query_ast.land.map((e) => this.eval(e, node_id, data)).every(e=>e); 
    }

    lor(query_ast, node_id, data){
        return query_ast.lor.map((e) => this.eval(e, node_id, data)).some(e=>e);
    }

    lnot(query_ast, node_id, data){
        return ! this.eval(query_ast.lnot, node_id, data)
    }

    id(query_ast, node_id, data){
        if (Array.isArray(query_ast.id))
            return query_ast.id.includes(node_id);
        return node_id == query_ast.id; 
    }

    all(query_ast, node_id, data){
        return true;
    }

    selection(query_ast, node_id, data){
        return this.graph.is_selected(node_id);
    }

    partial(query_ast, node_id, data){
        return data == PARTIALLY;
    }

    loop(query_ast, node_id, data){
        if (data == PARTIALLY)
            return false;
        return this.graph.is_self_loop(node_id);
    }

    degree(query_ast, node_id, data){
        if (data == PARTIALLY)
            return false;
        return Object.keys(data.neighbors).length == query_ast.degree;
    }

    var_meta(key, query_ast, node_id, data){
        if (data == PARTIALLY)
            return false;
        let m_type = key.toLowerCase();
        if (query_ast.name != null) {
            let m_id = query_ast.name.toLowerCase();
            for (const [metadata, val] of data.metadatas)
                if (metadata.type.toLowerCase() == m_type && metadata.id.toLowerCase() == m_id)
                    return true;
            return false;
        }
        else {
            for (const [metadata, val] of data.metadatas)
                if (metadata.type.toLowerCase() == m_type)
                    return true;
            return false;
        }



    }

    color(query_ast, node_id, data){
        if (data == PARTIALLY)
            return false;
        let color_name = query_ast.color.toLowerCase();
        for (const [metadata, val] of data.metadatas)
            if (metadata.type.toLowerCase() == 'color'  && metadata.id.toLowerCase() == color_name){
                if (query_ast.abundance && !isNaN(query_ast.abundance.value) && !isNaN(val)){
                    let target_value = query_ast.abundance.value;
                    let meta_value = parseInt(val);
                    let op = query_ast.abundance.operation.operation;
                    if (meta_value <  target_value && op == "<" ) return true;
                    if (meta_value <= target_value && op == "<=") return true;
                    if (meta_value >  target_value && op == ">" ) return true;
                    if (meta_value == target_value && op == "=" ) return true;
                    if (meta_value >= target_value && op == ">=") return true;
                }
                else return true;
            }
        return false;
    }

    seq(query_ast, node_id, data){
        let sequence = query_ast.seq;
        if (data.seq != undefined){
            return data.seq.includes(sequence) || data.seq.includes(rc(sequence));
        };
        return false;
    }

    kmer(query_ast, node_id, data){
        let sequence = query_ast.kmer;
        if (sequence.length != this.graph.k)
            throw new Error(`Invalid kmer (get size ${sequence.length}, allowed k:  ${this.graph.k})`);
        return  data.seq.includes(sequence) || data.seq.includes(rc(sequence));
    }
}
