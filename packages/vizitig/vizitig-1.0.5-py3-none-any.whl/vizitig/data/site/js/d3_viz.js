import "../libs/d3/d3.v7.min.js";
import { BaseViz } from "./visualisation.js";
import { Rotate, Center, Loop, ShowId, Highlight, Scale, Tag, Transparency, Label} from "./viz_actions/d3_actions.js";
import { Hide } from "./viz_actions/default_actions.js";
import { default_prop } from "./d3_default.js";
import { PARTIALLY } from "./config.js";
import { dl_svg, create_svg, hand, move, file_svg, start, stop} from "./utils.js";


const translate_attr = /(.*)translate\([^()]*\)(.*)/ // allow to remove translate(...) from a transform attr
function remove_translate(attr){
    let m = attr.match(translate_attr);
    if (m == null)
        return attr
    return m.splice(1).join("");
}

export class D3Viz extends BaseViz{
    width = "100%";
    height = "100%";

    get_container(container) {
        return container;
    }

    get actions(){
        return [ShowId, Tag, Transparency, Hide, Label];
    }

    constructor(graph, container, properties){
        super(graph, container);
        this.d3_propr = {};
        this.init_posX = 0;
        this.init_posY = 0;
        this.init_scale = 1;
        Object.assign(this.d3_propr, default_prop);
        if (properties != undefined)
            Object.assign(this.d3_prowpr, properties);
    }

    get_state(){
        let state = super.get_state();
        let transform = this.g.node().transform.baseVal.consolidate();
        if (transform){
            state.args.init_posX = transform.matrix.e;
            state.args.init_posY = transform.matrix.f;
            state.args.init_scale = transform.matrix.a;
        }
        return state;
    }


    delete_selection(){
        if (this.selection != undefined){
            delete this.selection;
            this.svg.on("click", ()=>{}); 
            this.svg.on("mousemove", ()=>{}); 
        }
        this.svg.selectAll(".select_group").remove();
    }

    extra_header(){
        let that = this;
        let extra = this.holder.querySelector(".header-buttons");

        let linearize = document.createElement("input");
        linearize.classList.add("btn", "viz-toggle", "navbar-toggler", "my-auto",  "mx-2");
        linearize.setAttribute("type", "button");
        linearize.value = "Linearize";
        linearize.onclick = function(){
            const formData = new FormData();
            formData.set("filter", "all");
            formData.set("layout_select", "neato");
            let act_inst = new that.default_layout(that.graph, formData, that);
            that.add_action(act_inst);
        }

        let center = document.createElement("input");
        center.classList.add("btn", "viz-toggle", "navbar-toggler", "my-auto",  "mx-2");
        center.setAttribute("type", "button");
        center.value = "Center";
        center.onclick = function(){
            const formData = new FormData();
            formData.set("filter", "all");
            let act_inst = new Center(that.graph, formData, that);
            that.add_action(act_inst);
        }

        let rotate = document.createElement("input");
        rotate.classList.add("btn", "viz-toggle", "navbar-toggler", "my-auto",  "mx-2");
        rotate.setAttribute("type", "button");
        rotate.value = "Rotate";
        rotate.onclick = function(){
            const formData = new FormData();
            formData.set("filter", "all");
            let act_inst = new Rotate(that.graph, formData, that);
            that.add_action(act_inst);
        }
        
        let start_stop = document.createElement("form");
        start_stop.classList.add("btn-group", "mx-1");
        start_stop.setAttribute("id", `start_stop_${this.viz_id}`);
        start_stop.setAttribute("role", "group");
        start_stop.innerHTML = `
<input id="vizstart_${this.viz_id}" type="radio" class="btn-check" name="start_stop" value="start" autocomplete="off" checked>
<label class="btn btn-secondary-outline" for="vizstart_${this.viz_id}">${start}</label>
<input id="vizstop_${this.viz_id}" type="radio" class="btn-check" name="start_stop" value="stop" autocomplete="off">
<label class="btn btn-secondary-outline" for="vizstop_${this.viz_id}">${stop}</label>
`;

        start_stop.onchange = () => that.sim_restart();
        
        let form = document.createElement("form");
        form.classList.add("btn-group", "mx-1");
        form.setAttribute("role", "group");
        form.innerHTML = `

  <input id="vizhand_${this.viz_id}" type="radio" class="btn-check" name="pointer_action" value="hand" autocomplete="off">
  <label class="btn btn-secondary-outline" for="vizhand_${this.viz_id}">${hand}</label>
  <input type="radio" class="btn-check" name="pointer_action" id="vizmove_${this.viz_id}" value="move" autocomplete="off" checked>
  <label class="btn btn-secondary-outline" for="vizmove_${this.viz_id}">${move}</label>
`;
        form.onchange = () => that.draw();
        this.pointer_action_form = form;
        let button = document.createElement("button");
        button.setAttribute("id", `vizsvg_${this.viz_id}`);
        button.classList.add("btn", "btn-sm", "btn-outline-secondary");
        button.innerHTML = file_svg;
        button.onclick = function(){
            dl_svg(that.svg.node());
        };

        extra.prepend(linearize);
        extra.prepend(center);
        extra.prepend(rotate);
        extra.prepend(start_stop);
        extra.prepend(button);
        extra.prepend(form);
        this.more_header();
    }

    more_header() {}


    build_svg(){
        if (this.svg != undefined){
            this.g.selectAll("*").remove();
            return
        }
        this.body.innerHTML = "";
        this.svg = d3.select(this.body).append("svg")
            .attr("width", this.width)
            .attr("height", this.height)
            .style("background-color", "rgb(232, 232, 232)");
        this.svg.append("svg:marker")
            .attr("id", "arrow")
            .attr("viewBox", "0 0 10 10")
            .attr('refX', 1)
            .attr('refY', 5)
            .attr("markerWidth", 5)
            .attr("markerHeight", 5)
            .attr("orient", "auto")
            .append("svg:path")
            .attr("d","M 0 0 L 10 5 L 0 10 z");

        let g = this.g = this.svg.append("g");
                //.attr("transform", `translate(${this.init_posX}, ${this.init_posY}) scale(${this.init_scale})`);
        this.reset_zoom();
        this.zoom.translateTo(g, this.init_posX, this.init_posy);
        this.zoom.scaleTo(g, this.init_scale);
    }

    reset_zoom(){
        let g = this.g;
        this.zoom = d3.zoom().scaleExtent([0.01, 10]);
        this.zoom.on("zoom", (event) => { g.attr("transform", event.transform) });
        this.svg.call(this.zoom);
    }


    get pointer_action(){
        return new FormData(this.pointer_action_form).get("pointer_action");
    }

    sim_restart(){
        let start_stop = document.querySelector(`#start_stop_${this.viz_id}`);
        let start = (new FormData(start_stop)).get("start_stop") == "start";
        if (this.simulation != undefined)
            if (start)
                this.simulation.alpha(this.d3_propr.alpha).restart();
            else
                this.simulation.alpha(0).restart();
    }
    handle_selection(element, data){
        let tr = element.attr("transform");
        if (tr)
            tr = remove_translate(element.attr("transform"));
        else
            tr = "";
        let x = (data.px!=undefined) ? data.px :data.x;
        let y = (data.py!=undefined) ? data.py :data.y;
        data.x = x;
        data.y = y;
        element.attr("transform", `translate(${x},${y}) ${tr}`);
    }

    finish(){
    }

    prepare(){
        let that = this;
        this.build_svg();
        this.svg.on(".zoom", null);
        this.svg.style("cursor", ""); 
        this.delete_selection();
        if (this.pointer_action == "move") {
            this.svg.style("cursor", "move"); 
            this.svg.call(this.zoom);
        }
        if (this.pointer_action == "hand"){
            this.selection = {};
            this.build_selection_tool();
        }
    }

    add_node_to_selection(node_list, node_data){
    }

    build_selection_tool(){
        let that = this;
        this.svg.on("click", function(event){
            if (that.selection.g == undefined){
                that.selection.g = that.g.append("g");
            }
            if (that.selection.posX == undefined){
                that.selection.g = that.g.append("g").attr("class", "select_group");
                var xy = d3.pointer(event);
                var transform = d3.zoomTransform(that.svg.node());
                xy = transform.invert(xy);
                that.selection.posX = xy[0];
                that.selection.posY = xy[1];
                that.selection.g.append("circle")
                        .attr("cx", xy[0])
                        .attr("cy", xy[1])
                        .attr("r", 5)
                        .style("fill", "grey");
                that.selection.g.append("rect")
                        .attr("x", xy[0])
                        .attr("y", xy[1])
                        .attr("fill", "blue")
                        .attr("opacity", "0.3")
                        .attr("width", 0)
                        .attr("height", 0);
            }
            else {
                let selected_nodes = []
                for (const data of that.d3_nodes){
                    if ((that.selection.posX < data.x & data.x < that.selection.posX + that.selection.width) &
                       (that.selection.posY  < data.y & data.y < that.selection.posY + that.selection.height))
                        that.add_node_to_selection(selected_nodes, data);
                }
                that.graph.select_nodes(selected_nodes);
                delete that.selection.posX;
                delete that.selection.posY;
            }
        
        });
        that.svg.on("mousemove", function(event){
            if (that.selection.g != undefined){
                var xy = d3.pointer(event);
                var transform = d3.zoomTransform(that.svg.node());
                xy = transform.invert(xy);
                let width  = that.selection.width = xy[0] - that.selection.posX;
                let height = that.selection.height= xy[1] - that.selection.posY;
                that.selection.g.select("rect").attr("width", width)
                                        .attr("height", height);
            }
        });
    }
}


export function drag(graph, data){
    function dragstarted(event) {
        if (graph.pointer_action == "move")
        data.px = data.py = undefined;
    }
    function dragged(event) {
        if (graph.pointer_action == "move"){
            graph.sim_restart();
            data.px = event.x;
            data.py = event.y;
        }
    }
    function dragended(event) {
    }
    return d3.drag().on("start", dragstarted).on("drag", dragged).on("end", dragended);
}
