import {is_d3, is_svg} from "../utils.js";
import { rand_str } from "../utils.js";

export class VizAction{
    constructor(graph, args, viz){
        // if args is not a formData, it is considered as an object and we build a formData for it.
        this.graph = graph;
        this.viz = viz;
        if (args.constructor != FormData){
            let F = new FormData();
            for (const [key, value] of Object.entries(args))
                F.set(key, value);
            this.args = F;
        }
        else 
            this.args = args;
    } 

    get_state(){
        let args = {}
        this.args.forEach((value, key) => args[key] = value);
        return {
            type: this.constructor.name,
            args: args
        }
    }

    get at_update(){
        return false;
    }

    get filter_key(){
        return this.args.get("filter");
    }
    prepare() {}
    filter(e){return true}
    transform_node(e, draw_node){return draw_node} 
    update_node(e, draw_node){return draw_node} 
    transform_edge(source, target, draw_edge){return draw_edge} 
    update_edge(source, target, draw_edge){return draw_edge} 
    get one_shot(){
        return false;
    }
    finish(){}

    // This should return a list of object representing the form element to add.
    // e.g { type: "number", min:0, max:10, label:"foo" };
    // value are all attributes of an input type.
    // Default tag is "input" except if tag is a value of the object.
    // mandatory key: "name" and "label"

    static get form_desc(){
        return [];
    };
    static form(holder){
        let form_desc = this.form_desc;
        let last_child = holder.children[holder.children.length-1];
        for (const obj of form_desc){
            let col = document.createElement("div");
            holder.insertBefore(col, last_child);
            col.classList.add("col-2", "extra_form", "my-auto"); 
            let bid = rand_str();
            let label = obj.label;
            let tag_name = "input";
            if (obj.tag) tag_name = obj.tag;
            let class_name = "form-control";
            if (obj.class_name != undefined) class_name = obj.class_name;
            let content = "";
            if (obj.content) content = obj.content;
            let container_class = "form-floating";
            if (obj.container_class != undefined) container_class=obj.container_class;
            col.innerHTML = `<div class="${container_class} extra_form">
                <${tag_name} id="${bid}" class="${class_name}" name="${obj.name}">${content}</${tag_name}>
                <label for="${bid}" class="form-label">${label}</label>
            </div>`;
            let tag = col.querySelector(tag_name);
            for (const [key, value] of Object.entries(obj)){
                if (key == "label" || key == "tag") continue;
                tag.setAttribute(key, value); 
            }
        }
    }
    check(e){
        let sat = this.graph.node_satisfy(this.filter_key, e); 
        if (this.args.has("not")) return !sat;
        return sat;
    }
}

export class Hide extends VizAction {
    filter(e){
        return !this.check(e); 
    }
}


export class Highlight extends VizAction{
    transform_node(nodeid, draw_node){
        if (this.check(nodeid)){
            if (draw_node.tagNAME = "TR")
                draw_node.classList.add("table-active");
            else
                draw_node.classList.add("bg-primary");
        }
        return draw_node;
    }
}
