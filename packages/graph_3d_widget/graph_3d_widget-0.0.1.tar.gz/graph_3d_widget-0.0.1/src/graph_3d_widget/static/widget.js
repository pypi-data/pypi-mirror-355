import ForceGraph3D from "https://esm.sh/3d-force-graph";
import { forceManyBody } from "https://esm.sh/d3-force-3d";

let plot;
let default_repulsion = 1;
let default_node_scale = 1;
let node_size = 5;
// let selectedNodes = new Set();
let selected_ids = new Set();
let default_width = 600;
let default_height = 600;

function render({ model, el }) {
    const create_plot = (data) => {
        return ForceGraph3D()(el)
            .width(width)
            .height(height)
            .graphData(data)
            .showNavInfo(false)
            .nodeColor(() =>"grey")
            // .nodeColor(node => selectedNodes.has(node) ? 'yellow' : 'grey')
            // .nodeColor(node => selected_ids.has(node.id) ? 'yellow' : 'green')
            .onNodeClick((node, event) => {
                if (event.ctrlKey || event.shiftKey || event.altKey) { // multi-selection
                    // selectedNodes.has(node) ? selectedNodes.delete(node) : selectedNodes.add(node);
                    selected_ids.has(node.id) ? selected_ids.delete(node.id) : selected_ids.add(node.id);
                } else { // single-selection
                    // const untoggle = selectedNodes.has(node) && selectedNodes.size === 1;
                    // selectedNodes.clear();
                    // !untoggle && selectedNodes.add(node);
                    const untoggle = selected_ids.has(node.id) && selected_ids.size === 1;
                    selected_ids.clear();
                    !untoggle && selected_ids.add(node.id);
                }
                console.log("selected_ids", selected_ids);
                model.set("selected_ids", [...selected_ids]);
                model.save_changes();
                // plot.nodeColor(node => selectedNodes.has(node) ? 'yellow' : 'grey');
            })
            .onNodeDrag((node, translate) => {
                // if (selectedNodes.has(node)) { // moving a selected node
                //     [...selectedNodes]
                //     .filter(selNode => selNode !== node) // don't touch node being dragged
                //     .forEach(node => ['x', 'y', 'z'].forEach(coord => node[`f${coord}`] = node[coord] + translate[coord])); // translate other nodes by same amount
                // }
                if ( selected_ids.has(node.id) ) { // moving a selected node
                    [...selected_ids]
                    .filter(selNodeId => selNodeId !== node.id) // don't touch node being dragged
                    .forEach(selNodeId => {
                        const selNode = plot.nodeById(selNodeId);
                        ['x', 'y', 'z'].forEach(coord => selNode[`f${coord}`] = selNode[coord] + translate[coord]);
                    }); // translate other nodes by same amount
                }
            })
            .onNodeDragEnd(node => {
                // if (selectedNodes.has(node)) { // finished moving a selected node
                //     [...selectedNodes]
                //     .filter(selNode => selNode !== node) // don't touch node being dragged
                //     .forEach(node => ['x', 'y', 'z'].forEach(coord => node[`f${coord}`] = undefined)); // unfix controlled nodes
                // }
                if ( selected_ids.has(node.id) ) { // finished moving a selected node
                    [...selected_ids]
                    .filter(selNodeId => selNodeId !== node.id) // don't touch node being dragged
                    .forEach(selNodeId => {
                        const selNode = plot.nodeById(selNodeId);
                        ['x', 'y', 'z'].forEach(coord => selNode[`f${coord}`] = undefined); // unfix controlled nodes
                    });
                }
            })
            .onEngineStop(() => {
                plot.zoomToFit(400);
            })
    }

    const data = model.get("data");
    let repulsion = model.get("repulsion") || default_repulsion;
    let node_size = model.get("node_scale") || default_node_scale;
    let node_scale = model.get("node_scale") || default_node_scale;
    let width = model.get("width") || default_width;
    let height = model.get("height") || default_height;

    plot = create_plot(data)

    model.on("change:repulsion", () => {
        repulsion = model.get("repulsion");
        plot.d3Force('charge', forceManyBody().strength(-repulsion));
        plot.d3ReheatSimulation();
    });
    model.on("change:node_scale", () => {
        node_size = model.get("node_scale");
        plot.nodeRelSize(node_size * node_scale)
        plot.d3ReheatSimulation();
    });
    model.on("change:selected_ids", () => {
        // local_selected_ids = model.get("selected_ids");
        selected_ids = new Set(model.get("selected_ids"));
        plot.nodeColor(node => selected_ids.has(node.id) ? 'yellow' : 'grey');
    });
}

export default { render };