import { MetaViz } from "./metadata.js";
import { FiltersManager, filter_instances } from "./filters.js";
import {Hide} from "./viz_actions/default_actions.js";
import { chunkArray } from "./utils.js";

let default_viz_open = new Map();
default_viz_open.set("bands_graph", 
{
    "style": {width: "66vw", height: "85vh"},
    "actions": []
}
    );
default_viz_open.set("table", {
    "style": {width: "32vw", height: "85vh"},
    "actions":
        [
            (graph) => new Hide(graph, {filter: "selection", not: true})
        ]
}
);

let loading_spin = document.getElementById("loading");
let main_ctl = document.getElementById("main_ctl");
function loading(){
    loading_spin.classList.remove("d-none");
    main_ctl.classList.add("d-none");
}

function end_loading(){
    loading_spin.classList.add("d-none");
    main_ctl.classList.remove("d-none");
}

export function set_page(G, load_default_viz){
    refresh.href = `graph.html?graph=${G.gname}`;
    refresh.innerHTML = G.gname;
    document.title = `Vizitig: ${G.gname}`;
    total_size.innerHTML = G.total_size;

    //Add data injection here
    G.add_onready_callback(async function(){
        fetched_nodes.innerHTML = G.fully_loaded_nodes.length;
        discovered.innerHTML = G.nodes.length;
    });
    

    G.api.get.load_viz().then(async function(vizlist){
            for (const vizname of vizlist.sort().reverse()){
                let li = document.createElement("li");
                li.innerHTML = `<a class="dropdown-item href="#">${vizname.replace("_", " ")}</a>`;
                li.onclick = () => G.add_viz(vizname);
                vizlist_holder.appendChild(li);
                if (default_viz_open.has(vizname) && load_default_viz){
                    let viz = await G.add_viz(vizname)
                    for (const [key, value] of Object.entries(default_viz_open.get(vizname).style))
                        viz.holder.style[key] = value;
                    for (const act of default_viz_open.get(vizname).actions)
                        viz.add_action(act(G)); 
                    G.state_in_url();
                }
            }
    });
    fetch_node.addEventListener("submit", async function(event){
        event.preventDefault();
        const formData = new FormData(this);
        let query_str = formData.get("query");
        let action = event.submitter.value;
        //fetch_node.querySelector("button[type=submit]").setAttribute("disable");
        if (action == "fetch"){
            loading();
            G.fetch_nodes(query_str).finally(end_loading);
        }
    });

    export_form.addEventListener("submit", async function(event){
        event.preventDefault(); 
        const formData = new FormData(this);
        let filter = formData.get("filter");
        G.api.post.export_nodes(G.gname, formData.get("format"), G.all_nodes_satisfying(filter)).then(function(url){
            /// shameless stolen from https://stackoverflow.com/a/23013574
            var link = document.createElement("a");
            link.setAttribute("target", "_blank");
            link.setAttribute("download", "");
            link.href = url;
            document.body.appendChild(link);
            link.click();
            link.remove();
        })
    });


    const metadataselector = document.getElementById("metadata_manager_button");
    metadataselector.onclick = () => (new MetaViz(G)).build();

    const filtermanager = document.getElementById("filter_manager_button");
    filtermanager.onclick = () => (new FiltersManager(G)).build();

    const savestate = document.getElementById("save_state"); 
    savestate.onsubmit = async function(e){
        e.preventDefault();
        let data = new FormData(this);
        let state_name = data.get("save");
        await G.api.post.save_state(G.gname, state_name, G.get_enc_state());
        let url = new URL(window.location.href);
        window.history.replaceState(null, null, `graph.html?graph=${G.gname}&state=${state_name}`);
        document.title = `Vizitig:${G.gname} -- ${state_name}`;
    }


    G.add_onupdate_filter_callback(function () {
        let select_form = document.getElementById("select_expand_filter");
        select_form.innerHTML = "";
        let front_only = G.front_only_filters.map(e => e[1]);
        for (const filter of G.filters) {
            if (front_only.includes(filter)) continue;
            let option_elem = document.createElement("option");
            option_elem.value = filter;
            option_elem.innerHTML = filter;
            if (filter == "all") {
                option_elem.setAttribute("default", "true")
            }
            select_form.appendChild(option_elem);
        }
    })


    const expand_button = document.getElementById("expand_button");
    expand_button.onclick = async function(){
        let expand_nb = document.getElementById("expand_nb").value;  
        let selonly = document.getElementById("expand_selection_only");  
        let partial_nodes_init = new Set(G.partially_loaded_nodes);
        let to_expand = partial_nodes_init;

        let base_query = "";
        let select_form = document.getElementById("select_expand_filter");
        if (select_form.value != "all") {
            let filters_list = await G.api.get.list_filters(G.gname);
            base_query = filters_list.filter((filter) => filter[0] == select_form.value)[0][1];
        }

        if (selonly.checked){
            let res = new Set();
            G.selection.forEach((node) => {
                Object.keys(G.node_data(node).neighbors).forEach((nid, _) => {
                    res.add(parseInt(nid));
                })
            });

            to_expand = new Set(to_expand.intersection(res));
        }
        while (expand_nb > 0 && to_expand.size > 0){
            let query_str;
            if (base_query != "") {
                query_str = base_query + ' and ' + `NodeId(${[...to_expand].slice(0, expand_nb).join(",")})`; 
            }
            else {
                query_str = `NodeId(${[...to_expand].slice(0, expand_nb).join(",")})`; 
          
            }

            await G.fetch_nodes(query_str);
            expand_nb -= to_expand.size;
            to_expand = (new Set(G.partially_loaded_nodes)).difference(partial_nodes_init); 
        }
    }
    add_filter_button.addEventListener("click", function() {
        G.add_filter_str(filterName.value, queryField.value.trim());
        G.api.post.add_filter(G.gname, filterName.value, queryField.value);
        filternameinput.classList.remove("show");
        filter_instances.forEach(element => {
            element.refresh_table();
        });
    })        


}


export function setUpDSLButtonFunctions() {
    queryField = document.querySelector("#queryField");
    for (const button in Object.entries(document.querySelector(".DSLButton"))){
        button.addEventListener('click', () => function() {
            queryField.value += button.valueOf})
        }
    }


function addMetadataToQuery(element) {
    queryField = document.querySelector('#queryField');
    var str = element.type + '(' + element.id + ') ';
    queryField.value += str;
}

// create a meta element from a DOM detached element
export function modal(content){
    // TODO
}

export function autoResizeQueryField() {
    queryField.style.height = "auto";
    queryField.style.height = queryField.scrollHeight + 'px';
}

