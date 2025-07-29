import { VizAction } from "./default_actions.js";
import { Graphviz }  from "../../libs/graphviz/graphviz.js";

export const graphviz = await Graphviz.load();

function random_value(min, max){
    return min + Math.floor(Math.random()*(max-min));
}

export function Random(nodes, edges, stay_static){
    let xpos = [...nodes.values()].map(e=>e.x);
    let ypos = [...nodes.values()].map(e=>e.y);
    let min_x = Math.min(...xpos);
    let min_y = Math.min(...ypos);
    let max_x = Math.max(...xpos);
    let max_y = Math.max(...ypos);
    for (const node of nodes.values()){
        if (stay_static){
            node.px = random_value(min_x, max_x);
            node.py = random_value(min_x, max_x);
        } else {
            node.px = node.py = null;
            node.x = random_value(min_x, max_x);
            node.y = random_value(min_x, max_x);
        }
    }
}

export function compute_graphviz(layout, nodes, edges, stay_static){
        let graph_str = `
Graph G {
    node [shape=rect label=""]
`;
        for (const [source, target] of edges.keys())
                graph_str += `${source}--${target};\n`;
        graph_str += "}";
        const layout_res = JSON.parse(graphviz.layout(graph_str, "json0", layout));
        let node_pos = new Map();
        for (let obj of layout_res.objects){
            let [x_str, y_str] = obj.pos.split(",");
            let x = parseFloat(x_str);
            let y = parseFloat(y_str);
            let node = nodes.get(obj.name);
            if (stay_static){
                node.px = x;
                node.py = y;
            } else {
                node.px = node.py = null;
                node.x = x;
                node.y = y;
            }
        }
}

const neato = (nodes, edges, stay_static) => compute_graphviz("neato", nodes, edges, stay_static);
const dot   = (nodes, edges, stay_static) => compute_graphviz("dot"  , nodes, edges, stay_static);
const sfdp   = (nodes, edges, stay_static) => compute_graphviz("sfdp"  , nodes, edges, stay_static);
const fdp   = (nodes, edges, stay_static) => compute_graphviz("fdp"  , nodes, edges, stay_static);
const circo   = (nodes, edges, stay_static) => compute_graphviz("circo"  , nodes, edges, stay_static);
const Layout_Fcts =  [neato, Random, dot, sfdp, fdp, circo];

export class Layouts extends VizAction{
    prepare(){
        this.viz.start_spin();
        
        this.nodes = new Map();
        this.edges = new Map();
    }

    get one_shot(){
        return true;
    }

    transform_node(nodeid, draw_node){
        if (this.check(nodeid)){
            this.nodes.set(nodeid.toString(), draw_node.data);
        }
        return draw_node;
    }

    transform_edge(source, target, draw_edge){
        if (this.check(source) & this.check(target)){
            this.edges.set([source.toString(), target.toString()], draw_edge);
        }

        return draw_edge;
    }


    static get form_desc() {
        let options = Layout_Fcts.map((e)=> `<option>${e.name}</option>`);
        
        return [
            {
                type: "select", 
                tag: "select",
                name: "layout_select",
                label: "Layouts",
                content: options,
            },
            {
                type: "checkbox",
                name: "stay_static",
                container_class: "",
                class_name: "form-check-input my-auto",
                label: "Fix node position",
                checked: true
            }
        ];
    }

    finish(){
        let layout_name = this.args.get("layout_select");
        let layout_fct = Layout_Fcts.filter(e => e.name == layout_name)[0];
        layout_fct(this.nodes, this.edges, this.args.get("stay_static"));
        this.viz.end_spin();
    }
}
