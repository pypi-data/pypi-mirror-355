import {API} from "./api.js";
import {PARTIALLY, API_HREF} from "./config.js";
import { Eval } from "./eval_dsl.js";

// Overall datastructure //
//
// Nodes are represented by their node id.
// The applications follows the nx data structure.
// Nodes can be in two states:
//  - fully loaded from the backend
//  - partially loaded from the backend 
// This distinction is required to not load all the graph
// from the backend into the front end.
//
//
// Edges are a Map of Map to object where the object contains the
// edge description (signature of BCALM, and other informations found in the nx Graph).
//
// Metadata Description are an object aligned with the spec of the metadata python project.
//
// On the top of that, we have Tags that is a named query of the DSL. A Tag will matched
// all fully_loaded nodes (and only them, not the other one) dynamically.
// all partially_loaded nodes must be connected to at least one fully_loaded nodes.
//
// A Visualisation of the graph should hook the onready_callback. 


export class Graph{
    logger;
    #gname;
    #metadata; 
    #nodes; 
    #adj;
    #eval;
    #filters;
    #onready_callback;
    #onupdate_filter_callback;
    #selection;
    #viz_list;

    // gname is the string name of the graph
    // logger is a Logger object
    constructor(gname, logger){
        this.#gname = gname;
        this.#eval = new Eval(this, logger);
        this.#nodes = new Map(); // nid to Node properties 
        this.#adj = new Map(); // nid to nid to edge properties
        this.api = new API(API_HREF, logger); 
        this.logger = logger; 
        this.#viz_list = [];
        this.#filters = new Map(); 
        this.#selection = new Set();
        this.#onready_callback = new Set(); // callback when the graph has finished some maintenance operations after modification.
        this.#onupdate_filter_callback = new Set(); // callback when the graph has update its set of filter.
        this.add_onupdate_filter_callback(()=>this.state_in_url());
        this.add_onready_callback(()=>this.state_in_url());
        let that = this;
    }

    get front_only_filters() {
        return [["Degree(1)", "tips"], ["Partial()", "partial nodes"], ["Loop()", "self loop"], ["Selection()", "selection"]];
    }


    async build(){
        await this.api.build();
        this.api.get.version().then(v=>version.innerHTML = v);
        let that = this;


        // default filters
        this.parse_query("ALL()").then( ast => that.add_filter("all", ast, "ALL()"));
        for (const [query, label] of this.front_only_filters) {
            this.parse_query(query).then( ast => that.add_filter(label, ast, query));
        }

        this.default_filters = ['all'].concat(this.front_only_filters.map(e=>e[1]));
        // end of default filters

        this.#metadata = await this.api.get.graph_info(this.gname);
        this.api.get.get_export_format().then(function(L){
            for (const format of L){
                let option = document.createElement("option");
                option.innerHTML = option.value = format;
                export_format_list.appendChild(option);
            }
        }); 
        this.add_onupdate_filter_callback(function(graph){
            export_filter_list.innerHTML = ""; 
            for (const filter of graph.filters){
                let option = document.createElement("option");
                option.innerHTML = option.value = filter;
                export_filter_list.appendChild(option);
            } 
        });
        this.list_filters().then(Lfilters => Lfilters.map(e => that.add_filter_str(e[0], e[1])));
        this.onupdate_filter();

        console.log('Finished building graph.');
    }

    get selection(){
        return new Set(this.#selection);
    }

    is_selected(node_id){
        return this.#selection.has(node_id);
    }

    // Return an object representaiton of the state of the application
    get_state(){
        return {
                gname: this.#gname,
                nodes: [...this.#nodes.keys()], 
                selection: [...this.#selection.keys()],
                viz: this.#viz_list.map(e => e.get_state())
        }
    }

    is_self_loop(node_id){
        return this.#adj.has(node_id) && this.#adj.get(node_id).has(node_id);
    }

    get_enc_state(){
        let state = this.get_state();
        let enc_state = btoa(JSON.stringify(state));
        return enc_state;
    }

    state_in_url(){
        if (!document.title.endsWith("*"))
            document.title += "*";
    }

    async from_state(state_name){
        const BULK_FETCH_SIZE = 500;
        let state_enc = await this.api.get.get_state_by_name(this.gname, state_name);
        let obj = JSON.parse(atob(state_enc));
        let promises = obj.viz.map(v => this.restore_viz(v));
        await Promise.all(promises);
        this.select_nodes(obj.selection);
        if (obj.nodes.length > 0){
            let i = 0;
            let promises = [];
            while (i < obj.nodes.length){
                let query = `NodeId(${obj.nodes.slice(i, i+BULK_FETCH_SIZE).join(',')})`; 
                promises.push(this.fetch_nodes(query));
                i += BULK_FETCH_SIZE;
            }
            await Promise.all(promises); 
        }
        document.title = `Vizitig:${this.gname} -- ${state_name}`;
    }

    static async load_vizmodule(key){
        let module = await import(`./viz/${key}.js`);
        let arr = Object.values(module); 
        if (arr.length > 1)
            this.logger.error(`viz/${key}.js should contains only one exported element`);       
        return arr[0]
    }

    async add_viz(key){
        let vizclass = await this.constructor.load_vizmodule(key);
        let viz = new vizclass(this);
        await viz.build();
        this.#viz_list.push(viz);
        this.state_in_url();
        return viz;
    }

    async restore_viz(obj){
        let vizclass = await this.constructor.load_vizmodule(obj.vizname.toLowerCase().replace(" ", "_"));
        let viz = vizclass.from_state(this, obj);
        this.#viz_list.push(viz);
        return viz;
    }

    get viz_list(){
        return this.#viz_list;
    }

    remove_viz(viz){
        this.#viz_list.splice(this.#viz_list.indexOf(viz), 1);
        this.state_in_url();
    }

    get k(){
        return this.#metadata.k;
    }

    get metadata_types_list(){
        return this.#metadata.types_list;
    }

    get metadata_vars_values(){
        return this.#metadata.vars_values;
    }

    get nodes(){
        return [... this.#nodes.keys()];
    }

    get nodes_with_data(){
        return this.#nodes.entries();
    }

    node_with_data(node_id){
        return this.#nodes.get(node_id);
    }

    get total_size(){
        return this.#metadata.size;
    }

    node_data(nid){
        return this.#nodes.get(nid);
    }

    get gname(){
        return this.#gname;
    }

    add_onready_callback(callback){
        this.#onready_callback.add(callback); 
    }

    delete_onready_callback(callback){
        this.#onready_callback.delete(callback);
    }

    add_onupdate_filter_callback(callback){
        this.#onupdate_filter_callback.add(callback); 
    }

    delete_onupdate_filter_callback(callback){
        this.#onupdate_filter_callback.delete(callback); 
    }

    get fully_loaded_nodes(){
        return [...this.#nodes.entries()].filter(e => e[1] != PARTIALLY).map(e=>e[0]);
    }

    get partially_loaded_nodes(){
        return [...this.#nodes.entries()].filter(e => e[1] == PARTIALLY).map(e=>e[0]);
    }

    // Fully load all nodes in nodes.
    async expand_nodes(nodes){
        let node_desc = await this.api.get.nodes_data(this.gname, nodes)
    }

    // add node data list of (nid, NodeDesc)
    add_nodes(node_data){
        for (const [nid, desc] of node_data){
            this.#nodes.set(nid, desc);
            if (!this.#adj.has(nid))
                this.#adj.set(nid, new Map());
            let neighbors_nid = this.#adj.get(nid);
            for (const [oid_base, odesc] of Object.entries(desc.neighbors)){
                let oid = parseInt(oid_base);
                if (!this.#nodes.has(oid))
                    this.#nodes.set(oid, PARTIALLY);
                neighbors_nid.set(oid, new Map());
            }
        }
        this.onready();
    }

    get adj(){
    }

    get edges(){
        return this._edges()
    }
    * _edges(){
        for (const x of this.#adj.keys())
            for (const y of this.#adj.get(x).keys())
                yield [x, y];
    }

    // execute the query and fully load all the nodes and edges
    async fetch_nodes(query){
        await this.parse_query(query);
        let result = await this.api.get.find_with_query(this.gname, query);
        if (result.length == 0){
            this.logger.warn("No nodes found");
        }
        else
            this.add_nodes(result);
    }

    // toggle nodes to partially_loaded
    delete_nodes(nodes){
        for (const nid of nodes){
            this.#nodes.set(nid, PARTIALLY);
        }
        this.clean_graph();
        this.onready();
    }

    select_nodes(nodes){
        this.#selection = new Set(nodes);
        this.onready();
    }

    // Delete partially loaded nodes connected to only partially loaded nodes
    clean_graph(){
        for (const nid of this.partially_loaded_nodes){
            let neighbors = [... this.#adj.get(nid).entries()]
            if (neighbors.every(e=>that.#nodes.get(e) == PARTIALLY)){
                this.#adj.delete(nid);
                this.#nodes.delete(nid);
                for (const oid of neighbors){
                    this.#adj.get(oid).delete(nid);
                }
            }
        }
    }

    onready(){
        let that = this;
        this.#onready_callback.forEach(f=>f(that));
    }

    onupdate_filter(){
        let that = this;
        this.#onupdate_filter_callback.forEach(f=>f(that));
    }
        
    async parse_query(query_str){
        return await this.api.get.parse_query(this.gname, query_str);
    }

    async list_filters(){
        return await this.api.get.list_filters(this.gname);
    }

    //add the query in the add_filter here
    add_filter(key, query_ast, query_str){
        if (Object.keys(query_ast).length == 0) // empty object
            this.#filters.delete(key);
        else
            this.#filters.set(key, [query_ast, query_str]);
        this.onupdate_filter();
    }


    async add_filter_str(key, query_str){
        let ast;
        if (query_str.trim() == "")
            ast = {}; 
        else
            ast = await this.parse_query(query_str);
        this.add_filter(key, ast, query_str);
    }

    get filters(){
        return [...this.#filters.keys()]
    }

    remove_filter(key){
        this.#filters.remove(key);
    };


    node_satisfy(key, nodeid){
        if (!this.#filters.get(key)){
            this.logger.error(`Unkown filter key: ${key}`);
        }
        try {
            return this.#eval.eval(this.#filters.get(key)[0], nodeid);
        } catch (E){
            this.logger.error(`Query evaluation error: ${E.message}`);
            throw E;
        }
    }

    all_nodes_satisfying(key){
        let that = this;
        return this.nodes.filter((e) => that.node_satisfy(key, e));
    }

    export_current(format){}
    
}
