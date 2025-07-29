import { Layouts as BaseLayout} from "./layout_actions.js";


export class Layouts extends BaseLayout {

    transform_node(nodeid, draw_node){
        let data = draw_node.data;
        if (this.check(nodeid)){
            for (let i = 0; i < data.internal.length; i++){
                let node_intern = data.internal[i];
                this.nodes.set(node_intern.id, node_intern);
                if (i > 0)
                    this.edges.set([data.internal[i-1].id, node_intern.id], {});
            }
            this.nodes.set(data.first.id, data.first);
            this.nodes.set(data.last.id, data.last);
            this.edges.set([data.first.id, data.internal[0].id], {});
            this.edges.set([data.internal[data.internal.length-1].id, data.last.id], {});
        }
        return draw_node;
    }

    transform_edge(source, target, draw_edge){
        return draw_edge;
    }
}
