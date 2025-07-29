import {Graph}      from "./application.js";
import {Logger}     from "./logger.js";
import {set_page}   from "./ui.js";
const url = new URL(window.location.href);
const params = new URLSearchParams(url.search);
const logger = new Logger();
let G;

if (params.has("vizonly"))
    document.body.classList.add("vizonly");

if (params.has("noheader"))
    document.body.classList.add("noheader");

if (!params.has("graph")){
    window.location.href = "/";
}
const gname = params.get("graph");
window.onload = async function(){
    G = new Graph(gname, logger);
    await G.build();
    let load_default = true;
    if (params.has("state")){
        await G.from_state(params.get("state"));
        load_default = false;

    } 
    set_page(G, load_default);
    G.onready();
    G.onupdate_filter();

}
