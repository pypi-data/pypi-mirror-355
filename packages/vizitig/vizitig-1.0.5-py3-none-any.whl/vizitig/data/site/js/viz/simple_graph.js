import { D3Viz, drag } from "../d3_viz.js";
import { Scale, Loop, Center, Highlight, Sashimi} from "../viz_actions/d3_actions.js";
import { Layouts }  from "../viz_actions/layout_actions.js"; 
import { barycenter_many } from "../geo.js";
import { PARTIALLY } from "../config.js";

export class SimpleGraph extends D3Viz{
    get vizname(){
        return "Simple graph";
    }
    get actions(){
        let acts = super.actions; // [ShowId, Scale, Tag, Transparency, Hide, Label];
        acts.push(...[Loop, Center, Highlight, Sashimi, Layouts, Scale]);
        return acts;
    }

    get default_layout(){
        return Layouts;
    }

    prepare(){
        let that = this;
        super.prepare();
        if (this._nodes_map == undefined)
            this._nodes_map = new Map(); 
        if (this.d3_nodes == undefined)
            this.d3_nodes = []; 
        for (const [nid, data] of this.graph.nodes_with_data){
            if (this._nodes_map.has(nid)){
                let nid_data = this._nodes_map.get(nid)
                if (nid_data.g != undefined)
                    nid_data.g.remove();
                nid_data.g = undefined;
                nid_data.data = data;
                continue;
            }
            let cdata = {id: nid, data:data};
            let bary = barycenter_many(this.d3_nodes.filter(e=>e.data != PARTIALLY && e.data.neighbors[nid] && e.x));
            cdata.x = bary.x;
            cdata.y = bary.y;
            this._nodes_map.set(nid, cdata);
            this.d3_nodes.push(cdata);
        }

        this._edges = [];
        this.g.selectAll("line").remove();
        for (const [source, target] of this.edges){
            this._edges.push({source: source, target:target});
        }
        if (this.simulation == undefined)
            this.simulation = d3.forceSimulation();
        this.simulation.nodes(this.d3_nodes);
        this.simulation 
            .alphaDecay(this.d3_propr.alpha_decay)
            .force("link", d3.forceLink(this._edges).id(d=>d.id).strength(this.d3_propr.link_strength))
            .force("center", d3.forceCenter(0, 0).strength(1)) 
            .force("charge", d3.forceManyBody(this.d3_propr.charge_strength).distanceMax(this.d3_propr.charge_radius))
            .on("tick", ()=>that.update()).restart();
        this.sim_restart();
    }

    end_update(){
        this.g.selectAll(".node").call(drag(this));
    }

    get nodes(){
        return this._nodes_map.keys(); 
    }

    draw_node(node){
        let data = this._nodes_map.get(node);
        if (data.g == undefined){
            let g = d3.create("svg:g");
            g.attr("fill", "white")
             .attr("class", "node");
            if (data.data.seq != undefined){
                let width =  Math.min(1 + data.data.seq.length - this.graph.k, 10) + 4*Math.log(data.data.seq.length);
                g.append("rect")
                    .attr("width", width)
                    .attr("height", 10)
                    .attr("rx", 3)
                    .attr("stroke", "black")
                    .attr("transform", `translate(-${width/2}, -5)`);
            }
                    
            else
                g.append("circle")
                 .attr("r", 5)
                 .attr("stroke", "black");
            let sub = g.append("g");
            sub.attr("class", "add_info");
            data.g = g;
        }
        data.g.style("cursor", "pointer");
        data.g.attr("class", "nodeg");
        let sub = data.g.select(".add_info");
        sub.selectAll("*").remove();
        data.g.attr("transform", "");
        data.g.attr("nid", node);
        data.g.call(drag(this, data));
        let that = this;
        data.g.on("click", function(event){
            if (that.pointer_action == "move")
                data.px=data.py=undefined
            else{
                that.graph.select_nodes([node]);
                event.stopPropagation(); // prevent the selection rectangle to be triggered
            }
        });
        data.g.data = data; // :(
        return data.g;
    }
    draw_edge(source, target){
        let line = d3.create("svg:line")
            .attr("stroke", "black");
        return line;
    } 

    attach_node(node){
        this.g.append(()=>node.node());
    }

    attach_edge(edge){
        this.g.append(()=>edge.node());
    }
    update_node(node, element){
        let data = this._nodes_map.get(node);
        this.handle_selection(element, data);
    }

    add_node_to_selection(node_list, node_data){
        node_list.push(node_data.id);
    }

    get post_default_actions(){
        return [
            ["selection", new Highlight(this.graph, {filter: "selection", color:"blue"})],
            ["loop", new Loop(this.graph, {filter: "self loop", color:"black"})]
        ]
    }

    update_edge(source, target, element){
        let source_data = this._nodes_map.get(source);
        let target_data = this._nodes_map.get(target);
        element.attr("x1", source_data.x)
            .attr("y1", source_data.y)
            .attr("x2", target_data.x)
            .attr("y2", target_data.y);
    }
}

