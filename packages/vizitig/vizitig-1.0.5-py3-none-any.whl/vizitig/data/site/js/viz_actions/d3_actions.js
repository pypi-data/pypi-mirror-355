import { VizAction } from "./default_actions.js";
import { parallel_path, barycenter_many } from "../geo.js";


export class ShowId extends VizAction {
    transform_node(nodeid, draw_node){

        if (this.check(nodeid)){
            let scale = this.args.get("scale"); 
            draw_node.selectAll(".add_info").append("text")
                     .text(nodeid)
                     .attr("fill", "black")
                     .attr("stroke-width", "0px")
                     .attr("stroke", "black")
                     .attr("x", "-1.6em")
                     .attr("y", "1.35em")
                     .style("font-size", "xx-small")
                     .attr("transform", `scale(${scale} ${scale})`);
        }
        return draw_node;
    }
    static get form_desc() {
        return [
            {
                type: "number", 
                min: "0.1",
                max: "20",
                step: "0.1",
                name: "scale",
                label: "Scale",
                required: "",
                value: "1",
            }
        ];
    }
}


export class Label extends VizAction {
    transform_node(nodeid, draw_node){

        if (this.check(nodeid)){

            let text = this.args.get("label"); 
            let scale= this.args.get("scale"); 
            draw_node.selectAll(".add_info").append("text")
                     .text(text)
                     .attr("fill", this.args.get("color"))
                     .attr("stroke-width", "0px")
                     .attr("stroke", "black")
                     .attr("x", "-1.6em")
                     .attr("y", "1.35em")
                     .style("font-size", "xx-small")
                     .attr("transform", `scale(${scale} ${scale})`);
        }
        return draw_node;
    }
    static get form_desc() {
        return [
            {
                type: "number", 
                min: "0.1",
                max: "20",
                step: "0.1",
                name: "scale",
                label: "Scale",
                required: "",
                value: "1",
            },
            {
                type: "text", 
                name: "label",
                label: "Label",
                required: "true",
            },
            {
                type: "color", 
                name: "color",
                required: "",
                label: "Color"
            }
        ];
    }
}


export class Scale extends VizAction {
    transform_node(nodeid, draw_node){
        if (this.check(nodeid)){
            let tr = draw_node.attr("transform");
            if (tr == null)
                tr = "";
            let scale = this.args.get("scale"); 
            draw_node.attr("transform", `${tr} scale(${scale} ${scale})`);
        }
        return draw_node;
    }

    static get form_desc() {
        return [
            {
                type: "number", 
                min: "0.1",
                max: "20",
                step: "0.1",
                name: "scale",
                label: "Scale",
                required: "",
                value: "1",
            }
        ];
    }
}



export class Transparency extends VizAction{
    transform_node(nodeid, draw_node){
        if (this.check(nodeid)){
            draw_node.attr("fill-opacity", this.args.get("alpha"))
                .attr("stroke-opacity", this.args.get("alpha"));
        }
        return draw_node;
    }

    transform_edge(source, target, draw_edge){
        if (this.check(source) || this.check(target)){
            draw_edge.attr("stroke-opacity", this.args.get("alpha"));
        }
        return draw_edge;
    }

    static get form_desc() {
        return [
            {
                type: "range", 
                min: "0",
                max: "1",
                step: "0.05",
                name: "alpha",
                required: "",
                label: "Transparency"
            }
        ];
    }
}

class DefaultHighlight extends VizAction{
    transform_node(nodeid, draw_node){
        if (this.check(nodeid))
            draw_node.attr("fill", this.args.get("color"));
        return draw_node;
    }

    static get form_desc() {
        return [
            {
                type: "color", 
                name: "color",
                required: "",
                label: "Color"
            }
        ];
    }

}

export class Highlight extends DefaultHighlight {

    transform_edge(source, target, draw_edge){
        if (this.check(source) & this.check(target)){
            draw_edge.attr("stroke", this.args.get("color"))
                .attr("stroke-width", this.args.get("edgew"));
        }

        return draw_edge;
    }

    static get form_desc() {
        let T = super.form_desc;
        T.push({
            type: "number", 
            min: "1",
            max: "40",
            value:"10",
            name: "edgew",
            label: "Edge width"
        });
        return T;
    }
}

export class BandHighlight extends DefaultHighlight {
    transform_node(node_id, draw_node){
        if (this.check(node_id))
            draw_node.select(".main_path").attr("stroke", this.args.get("color"))
            .attr("stroke-width", this.args.get("width"))
            .attr("opacity", this.args.get("opacity"));
        return draw_node;
    }

    static get form_desc(){
        let T = super.form_desc;
        T.push({
            type: "number", 
            min: "1",
            max: "40",
            name: "width",
            label: "Width",
            value: 10
        });
        T.push({
            type: "range", 
            min: "0",
            max: "1",
            step: "0.05",
            name: "opacity",
            required: "",
            label: "Opacity"
        });
        return T;
    }
}

export class Center extends VizAction {
    finish(){
        let barycenter_pt = barycenter_many(this.viz.d3_nodes); 
        this.viz.svg.call(this.viz.zoom.translateTo, barycenter_pt.x, barycenter_pt.y);
    }

    get one_shot(){
        return true;
    }
}

export class Rotate extends VizAction {
    finish(){
        for (let node of this.viz.d3_nodes){
            let x = node.x;
            node.x = node.y;
            node.y = x;
            let px = node.px;
            node.px = node.py;
            node.py = px;
        }
    }

    get one_shot(){
        return true;
    }
}

export class Sashimi extends DefaultHighlight {

    transform_edge(source, target, draw_edge){
        return draw_edge;
    }
    
    transform_node(source, draw_node){
        const abundanceFrom = this.args.get("abundancefrom");
        let abundance_source;
        let meta;
        let target_meta;
        if (this.graph && this.graph.node_data(source).metadatas) {
            const sourceHasColor = this.graph.node_data(source).metadatas.some(item => {
                meta = item[0];
                const abundance = parseInt(item[1]);
                if (meta.type == "Color" && meta.id == abundanceFrom && abundance != -1) {
                    abundance_source = abundance;
                    target_meta = item;
                }
            });
        }
        if (abundance_source && this.args.get("maxabundance") != "") {
            let colors = new Array();
            this.graph.node_data(source).metadatas.forEach(item => {
                if(item[0] && typeof item[0] === 'object' && item[0].type === "Color")
                    colors.push(item);
            })

            let targetMetaOfset = colors.indexOf(target_meta);

            let tag_size = 10 * (Math.log((abundance_source) / Math.log(this.args.get("maxabundance"))));
            
            if (tag_size < (this.args.get("maxabundance") / 20)) {
                tag_size = (this.args.get("maxabundance") / 20);
            }

            let barWidth = 4;
            draw_node.select(".add_info")
                .append("rect")
                .attr("width", barWidth)
                .attr("height", tag_size)
                .attr("rx", 1) 
                .attr("fill", this.args.get("color"))
                .attr("transform", `translate(${(barWidth * targetMetaOfset) - 5} , 0)`);
                    }
        return draw_node;
    }


    static get form_desc() {
        let T = super.form_desc;
        T.push({
            type: "text", 
            name: "abundancefrom",
            label: "Abundance from"
        });
        T.push({
            type: "int",
            min: 1,
            max: 10000000, 
            value: 100,
            name: "maxabundance",
            label: "Max abundance"
        });
        return T;
        
    }
}


const line = d3.line()
  .x(d => d.x)
  .y(d => d.y)
  .curve(d3.curveCatmullRom);


//export class SashimiLine extends DefaultHighlight {
//
//    transform_edge(source, target, draw_edge){
//        return draw_edge;
//    }
//    
//    transform_node(source, draw_node){
//        const abundanceFrom = this.args.get("abundancefrom");
//        let abundance_source;
//        let meta;
//        let target_meta;
//        if (this.graph && this.graph.node_data(source).metadatas) {
//            const sourceHasColor = this.graph.node_data(source).metadatas.some(item => {
//                meta = item[0];
//                const abundance = parseInt(item[1]);
//                if (meta.type == "Color" && meta.id == abundanceFrom && abundance != -1) {
//                    abundance_source = abundance;
//                    target_meta = item;
//                }
//            });
//        }
//
//        if (draw_node != undefined) {
//            if (draw_node.line_slots == undefined)
//                draw_node.line_slots = 12;
//            if (draw_node.data.tagline_map == undefined)
//                draw_node.data.tagline_map = new Map();
//
//            if (abundance_source && this.args.get("maxabundance") != "") {
//                let colors = new Array();
//                this.graph.node_data(source).metadatas.forEach(item => {
//                    if(item[0] && typeof item[0] === 'object' && item[0].type === "Color")
//                        colors.push(item);
//                })
//
//                let tag_size = 10 * (Math.log((abundance_source) / Math.log(this.args.get("maxabundance"))));
//                
//                if (tag_size < (this.args.get("maxabundance") / 20)) {
//                    tag_size = (this.args.get("maxabundance") / 20);
//                }
//
//                let size = this.args.get("tag_size");
//
//                let amplitude = (draw_node.line_slots+size/2);
//                draw_node.line_slots += amplitude/2;
//                draw_node.data.tagline_map.set(this.id, amplitude);
//                draw_node.selectAll(`.tagline_${this.id}`).remove();
//                draw_node.append("path")
//                            .attr("stroke",this.args.get("color"))
//                            .attr("fill", "none")
//                            .attr("stroke-width", tag_size)
//                            .attr("amplitude", amplitude)
//                            .attr("class", `tagline_${this.id}`);
//        };
//
//        return draw_node;
//    }}
//
//    static get form_desc() {
//        let T = super.form_desc;
//        T.push({
//            type: "text", 
//            name: "abundancefrom",
//            label: "Abundance from"
//        });
//        T.push({
//            type: "int",
//            min: 1,
//            max: 10000000, 
//            value: 100,
//            name: "maxabundance",
//            label: "Max abundance"
//        });
//        return T;
//        
//    }
//
//    get at_update(){
//        return true;
//    }
//
//    update_node(nodeid, draw_node){
//        if (this.check(nodeid)){
//            let base_path = this.viz.path(draw_node.data); 
//            let path = parallel_path(base_path, draw_node.data.tagline_map.get(this.id));
//            draw_node.select(`.tagline_${this.id}`)
//                    .datum(path).attr("d", line);
//        }
//    }
//}


export class Loop extends DefaultHighlight {
    transform_node(nodeid, draw_node){
        if (this.check(nodeid)){
            draw_node.append("path")
            .attr("stroke", this.args.get("color"))
            .attr("fill", "transparent")
            .attr("stroke-width", "1pt")
            .attr('marker-end', "url(#arrow)")
            .attr('d', "M -5 4 C -10 20, 10 20, 6 11");
        }
        return draw_node;
    }

}

export class Tag extends DefaultHighlight {
    transform_node(nodeid, draw_node){
        let tag_size = parseInt(this.args.get("tag_size"));
        if (this.check(nodeid)){
            if (draw_node.tag_left == undefined)
                draw_node.tag_left = 0;
            draw_node.selectAll(".add_info").append("circle")
                     .attr("r", tag_size)
                     .attr("fill",this.args.get("color"))
                     .attr("transform", `translate(${tag_size + draw_node.tag_left}, 0)`);
            draw_node.tag_left += tag_size; 
        }
        return draw_node;
    }

    static get form_desc() {
        let T = super.form_desc;
        T.push({
            type: "number", 
            min: "4",
            max: "40",
            name: "tag_size",
            label: "Size",
            value: "6",
            required: "",
        });
        return T;
    }
}


export class UnderLine extends Tag {
    get at_update(){
        return true;
    }

    transform_node(nodeid, draw_node){
        let tag_size = parseInt(this.args.get("tag_size"));
        if (this.check(nodeid)){
            if (draw_node.line_slots == undefined)
                draw_node.line_slots = 14;
            let size = this.args.get("tag_size");
            let amplitude = draw_node.line_slots+size*2;
            draw_node.line_slots = amplitude;
            draw_node.selectAll(`.tagline_${this.id}`).remove();
            draw_node.append("path")
                        .lower()
                        .attr("stroke",this.args.get("color"))
                        .attr("fill", "none")
                        .attr("stroke-width", amplitude+"px")
                        .attr("class", `tagline_${this.id}`);
                        
        }
        return draw_node;
    }

    update_node(nodeid, draw_node){
        if (this.check(nodeid)){
            let base_path = this.viz.path(draw_node.data); 
            //let path = parallel_path(base_path, draw_node.data.tagline_map.get(this.id));
            draw_node.select(`.tagline_${this.id}`)
                    .datum(base_path).attr("d", line);
        }
        return draw_node;
    }

}


export class TagLine extends DefaultHighlight {

    get at_update(){
        return true;
    }

    compute_size(nodeid){
        return parseInt(this.args.get("tag_size"));
    }

    transform_node(nodeid, draw_node){
        if (this.check(nodeid)){
            let size = this.compute_size(nodeid);
            if (size == undefined)
                return draw_node;
            if (draw_node.line_slots == undefined){
                draw_node.line_slots = 10;
            }
            if (draw_node.tag_line_shift == undefined){
                draw_node.tag_line_shift = [];
            }
            draw_node.tag_line_shift.push([this.id, size]);
            draw_node.selectAll(`.tagline_${this.id}`).remove();
            draw_node.append("path")
                        .lower()
                        .attr("stroke",this.args.get("color"))
                        .attr("fill", "none")
                        .attr("stroke-width", size+"px")
                        .attr("class", `tagline_${this.id}`);
        }
        return draw_node;
    }

    update_node(nodeid, draw_node){
        if (this.check(nodeid)){
            if (this.compute_size(nodeid) == undefined)
                return draw_node;
            let base_path = this.viz.path(draw_node.data); 
            let amplitude = draw_node.line_slots/2;
            for (const [id, size] of draw_node.tag_line_shift){
                amplitude += size + 4;
                if (id == this.id) break
            }
            let path = parallel_path(base_path, amplitude);
            let chunk_line = path.map(e => `M ${e[0].x} ${e[0].y} L ${e[1].x} ${e[1].y}`).join(" ");
            draw_node.select(`.tagline_${this.id}`)
                    .datum(path).attr("d", chunk_line);
        }
        return draw_node;
    }
    static get form_desc() {
        let T = super.form_desc;
        T.push({
            type: "number", 
            min: "4",
            max: "40",
            name: "tag_size",
            label: "Size",
            value: "6",
            required: "",
        });
        return T;
    }
}

export class SashimiLine extends TagLine {

    compute_size(nodeid){
        const abundanceFrom = this.args.get("abundancefrom");
        let abundance_source;
        let size;
        if (this.graph && this.graph.node_data(nodeid).metadatas) {
            for (const item of this.graph.node_data(nodeid).metadatas){
                let meta = item[0];
                const abundance = parseInt(item[1]);
                if (meta.type == "Color" && meta.id == abundanceFrom && abundance != -1) {
                    abundance_source = abundance;
                    break;
                }
            };
            if (abundance_source == undefined)
                return;
            size = 10 * (Math.log((abundance_source) / Math.log(this.args.get("maxabundance"))));
               
            if (size < (this.args.get("maxabundance") / 20)) {
                size = (this.args.get("maxabundance") / 20);
            }
        }
        return size;
    }


    static get form_desc() {
       let T = Object.getPrototypeOf(Object.getPrototypeOf(this)).form_desc;
       T.push({
           type: "text", 
           name: "abundancefrom",
           label: "Abundance from"
       });
       T.push({
           type: "int",
           min: 1,
           max: 10000000, 
           value: 100,
           name: "maxabundance",
           label: "Max abundance"
       });
       return T;
   }

}
