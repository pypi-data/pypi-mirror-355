import("./libs/graphviz/graphviz.js");
//export const graphviz = await Graphviz.load();

onmessage = function(e){
    console.log("prout", graphviz);
    postMessage("prout");
 // postMessage(graphviz.layout(e[0], "json0", e[1]));

};
