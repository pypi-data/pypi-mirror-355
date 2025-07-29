import { D3Viz, drag} from "../d3_viz.js";
import { Loop, UnderLine, TagLine, Center, BandHighlight, SashimiLine} from "../viz_actions/d3_actions.js";
import { Layouts }  from "../viz_actions/layout_actions_band.js"; 
import { rc } from "../utils.js";
import { PARTIALLY } from "../config.js";
import { barycenter, shift_on_vector } from "../geo.js"; 


// In this vizu, we split unitig nodes into two types of nodes:
// extremal nodes (represented by k-1-mer of the unitig) 
// internal nodes which are the list of non-overallping kmer of the initig
// PARTIAL nodes will be dangling simply
//
// we connect extermal nodes to the first kmer of the unitig, consecutive unitig together 
//


function extremals(seq, k){
    let rc_seq = rc(seq);
    let bound = k-1;
    let left1 = seq.slice(0, bound);
    let left2 = rc_seq.slice(-bound);
    let left = (left1 < left2)? left1: left2;
    let right1 = seq.slice(-bound);
    let right2 = rc_seq.slice(0, bound);
    let right = (right1 < right2)? right1: right2;
    return [left, right];

}


const line = d3.line()
  .x(d => d.x)
  .y(d => d.y)
  .curve(d3.curveCatmullRom);


let coefs_values = {
    L4: {label:"Cst: 5",  fct:x=>5},
    L3: {label:"Cst: 3",  fct:x=>3},
    Log:{label:"Log",     fct:x=>Math.log(x)},
    S1: {label:"Square root",fct:x=>Math.sqrt(x)},
    L1: {label:"Cst: 1",  fct:x=>1},
}

export class BandGraph extends D3Viz{
    get vizname(){
        return "Bands Graph";
    }
    constructor(graph, container, properties){
        super(graph, container, properties);
        this.d3_propr.alpha=1.3;
        this.d3_propr.alphaDecay = 0.003;
        console.log(this);
    }

    get default_layout(){
        return Layouts;
    }

    get actions(){
        let acts = super.actions; // [ShowId, Scale, Tag, Transparency, Hide, Label];
        acts.push(...[BandHighlight, UnderLine, TagLine, Layouts, SashimiLine]);
        return acts;
    }

    more_header(){
        let that = this;
        let extra = this.holder.querySelector(".header-buttons");
        let coef = document.createElement("form");
        coef.classList.add("form", "col");
        coef.setAttribute("id", `coef_${this.viz_id}`);
        let options = Object.keys(coefs_values)
                    .map(key=>`<option value="${key}"> ${coefs_values[key].label}</option>`)
                    .join("\n");
        coef.innerHTML = `
            <select class="form-select">
                ${options}
            </select>
        `;

        coef.onchange = () => {
            that.simulation.stop();
            delete that.nodes_map;
            delete that.d3_nodes;
            delete that.d3_edges;
            delete that.extremal_map;
            that.draw();
        }
        extra.prepend(coef);
        this.coef=coef.children[0];
    }
    prepare(){
        let k = this.graph.k;
        super.prepare();
        // nodes_map map nid to an array of d3_nodes
        if (this.nodes_map == undefined)
            this.nodes_map = new Map(); 
        if (this.d3_nodes == undefined)
            this.d3_nodes = []; 
        if (this.extremal_map == undefined)
            this.extremal_map = new Map(); // map the sequence to the associated d3_nodes
        if (this.d3_edges == undefined)
            this.d3_edges = [];

        let coef_fct = coefs_values[this.coef.value].fct;
        for (const [nid, data] of this.graph.nodes_with_data){
            if (!this.nodes_map.has(nid)){
                let cdata;
                if (data == PARTIALLY){
                    continue;
                }
                let internal = new Array();
                let seq = data.seq;
                let [first_seq, last_seq] = extremals(seq, k);
                let first;
                if (this.extremal_map.has(first_seq)) {
                    first = this.extremal_map.get(first_seq); 
                    first.nodes.push(nid);
                } else { 
                    first = {id: first_seq, type:'extremal', nodes: [nid]};
                    this.extremal_map.set(first_seq, first); 
                    this.d3_nodes.push(first);
                }
                let last;
                if (this.extremal_map.has(last_seq)){
                    last = this.extremal_map.get(last_seq); 
                    last.nodes.push(nid);

                } else { 
                    last = {id: last_seq, type:'extremal', nodes: [nid]};
                    this.extremal_map.set(last_seq, last); 
                    this.d3_nodes.push(last);
                }
                let coef = Math.max(coef_fct(seq.length), 1);
                let anchor = {};
                if (first.x & last.x)
                    anchor = barycenter(first, last, 0.5);
                else if (first.x)
                    anchor = first;
                else if (last.x)
                    anchor = last;

                for (let i=0; i<=seq.length-k; i+=parseInt(coef*k)){
                    let kmer = seq.slice(i, i+k);
                    let node = { nid: nid, id: kmer, type: 'kmer', middle:false, x:anchor.x, y:anchor.y};
                    internal.push(node);
                }
                internal[parseInt(internal.length/2)].middle = true; 
                this.d3_nodes.push(...internal);
                this.d3_edges.push({source: first, target:internal[0]});
                this.d3_edges.push({source: internal[internal.length-1], target:last});

                for (let i=0; i < internal.length - 1; i++)
                    this.d3_edges.push({source: internal[i], target: internal[i+1]});

                    
                let node_data = {first: first, last:last, internal: internal, type:'full'};
                this.nodes_map.set(nid, node_data);
            } 
        }

        if (this.simulation == undefined)
            this.simulation = d3.forceSimulation();
        this.simulation.nodes(this.d3_nodes);
        let that = this;
        this.simulation 
            .alphaDecay(this.d3_propr.alpha_decay)
            .force("link", d3.forceLink(this.d3_edges)
                .id(d=>d.id)
            )
            .force("center", d3.forceCenter(0, 0).strength(1)) 
            .force("charge", d3.forceManyBody().distanceMax(this.d3_propr.charge_radius/2))
            .on("tick", ()=>that.update()).restart();
        this.sim_restart();
    }

    draw_node(node){
        let that = this;
        let data = this.nodes_map.get(node);
        if (data == undefined)
            return undefined;
    
        let g = this.g.append("g");
        data.g = g;
        if (data.type == "full"){
            data.internal_path = data.g.append("path")
                .attr("class", "main_path")
                .datum(this.path(data))
                .attr("id", "node_path_"+node)
                .attr("fill", "none")
                .attr("stroke", "grey")
                .attr("stroke-linecap", "round")
                .attr("stroke-width", "8px");
            data.internal_d3 = g.selectAll(null).data(data.internal).enter().append("g").attr("id", d=>d.id);
            function draggable(el, data){
                el.style("cursor", "pointer")
                    .on("click", function(event, d){
                        let cdata = d?d:data;
                        if (that.pointer_action == "move")
                            cdata.px=data.py=undefined
                        else{
                            that.graph.select_nodes([node]);
                            event.stopPropagation(); // prevent the selection rectangle to be triggered
                        }})
                    .call(
                        d3.drag().on("start",
                            function(event, d){
                                let cdata = d?d:data;
                                if (that.pointer_action == "move")
                                    cdata.px = cdata.py = undefined;
                            })
                        .on("drag", function(event, d){
                            let cdata = d?d:data;
                            if (that.pointer_action == "move"){
                                cdata.px = event.x;
                                cdata.py = event.y;
                                that.sim_restart();
                            }
                        }));
            }
            data.internal_d3.call(draggable);
            data.internal_d3.append("circle")
                .attr("r", 4)
               .attr("fill", "black")
                .attr("id", d=>d.kmer);
            if (data.last.g != undefined)
                data.last.g.remove();
            if (data.first.g != undefined)
                data.first.g.remove();
            data.first.g = this.g.append("g")
            //        .attr("class", "extremal")
            //        .attr("id", data.first.id);
            //data.first.g.append("circle")
            //    .attr("r", 4)
            //    .attr("fill", "darkred");
            data.last.g = this.g.append("g")
                .attr("class", "extremal")
                .attr("id", data.last.id);
            //data.last.g.append("circle")
            //    .attr("r", 4)
            //    .attr("fill", "darkred");
            //draggable(data.first.g, data.first);
            //draggable(data.last.g, data.last);
            //let bary = barycenter(data.first, data.last, 0.5);
            //data.x = bary.x;
            //data.y = bary.y;
            let sub = data.internal_d3.filter(d=>d.middle)
                    .append("g")
                    .attr("class", "add_info");
        }
        else {
            g.append("circle")
             .attr("r", 5)
             .attr("stroke", "black");
        }
        data.redraw_path = () => {};
        data.g.data = data; // :(

        g.attr("class", "nodeg node_"+node);

        return data.g;
    }

    attach_node(node){
        this.g.append(()=>node.node());
    }

    attach_edge(edge){
        this.g.append(()=>edge.node());
    }
    add_node_to_selection(node_list, node_data){
        if (node_data.type == "extremal")
            node_list.push(...node_data.nodes);
        else
            node_list.push(node_data.nid);
    }

    get post_default_actions(){
        return [
            ["selection", new BandHighlight(this.graph, {filter: "selection", color:"blue", width:20})],
        ]
    }

    path(data){
        let first_bary = barycenter(data.first, data.internal[0], 0.6);
        let last_bary = barycenter(data.last, data.internal[data.internal.length - 1], 0.6);
        let path = []
        path.push(first_bary);
        path.push(...data.internal);
        path.push(last_bary);
        return path;
    }

    draw_edge(source, target){
        let line = d3.create("svg:line")
            .attr("stroke-width", 2)
            .attr("stroke", "darkred");
        return line;
    } 

    attach_edge(edge){
        this.g.append(()=>edge.node());
    }

    update_edge(source_id, target_id, element){
        let source_data = this.nodes_map.get(source_id);
        let target_data = this.nodes_map.get(target_id);
        if (source_data != undefined && target_data != undefined) {
            let source;
            let target;
            let src_internal = source_data.path;
            let trg_internal = target_data.path;
            if (source_data.first.id == target_data.first.id){
                source = src_internal[0];
                target = trg_internal[0];
            }
            if (source_data.first.id == target_data.last.id){
                source = src_internal[0];
                target = trg_internal[trg_internal.length - 1];
            }
            if (source_data.last.id == target_data.first.id){
                source = src_internal[src_internal.length - 1];
                target = trg_internal[0];
            }
            if (source_data.last.id == target_data.last.id){
                source = src_internal[src_internal.length - 1];
                target = trg_internal[trg_internal.length - 1];
            }
            element.attr("x1", source.x)
                .attr("y1", source.y)
                .attr("x2", target.x)
                .attr("y2", target.y);
        }
    }

    update_node(node, element){
        let data = this.nodes_map.get(node);
        data.internal.forEach(fix_node);
        fix_node(data.first);
        fix_node(data.last);
        data.path = this.path(data);
        data.internal_path.datum(data.path).attr("d", line);
        data.internal_d3.attr("transform", d=>`translate(${d.px?d.px:d.x},${d.py?d.py:d.y})`);
        data.first.g.attr("transform", `translate(${data.first.px?data.first.px:data.first.x},${data.first.py?data.first.py:data.first.y})`);
        data.last.g.attr("transform", `translate(${data.last.px?data.last.px:data.last.x},${data.last.py?data.last.py:data.last.y})`);
    }
}

function fix_node(d){
    d.x = d.px?d.px:d.x;
    d.y = d.py?d.py:d.y;
}

