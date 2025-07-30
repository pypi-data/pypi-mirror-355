import marimo

__generated_with = "0.13.15"
app = marimo.App(width="full")


@app.cell
def _():
    import graph_3d_widget
    import marimo as mo
    import json
    return graph_3d_widget, json, mo


@app.cell
def _(json):
    with open('my_graph.json', 'r') as f:
        data = json.load(f)
    return (data,)


@app.cell
def _(data, graph_3d_widget, mo):
    data_graph = mo.ui.anywidget(
        graph_3d_widget.ForceGraph3DWidget(
            data=data,
            node_scale=5,
            repulsion=50,
            width=800,
            height=400
        )
    )
    return (data_graph,)


@app.cell
def _(mo):
    repulsion_slider = mo.ui.slider(start=1,stop=100,step=1,value=3, label="repulsion")
    node_scale_slider = mo.ui.slider(start=1,stop=20,step=1,value=3, label="node scale")
    return node_scale_slider, repulsion_slider


@app.cell
def _(data_graph, node_scale_slider, repulsion_slider):
    data_graph.widget.node_scale = node_scale_slider.value
    data_graph.widget.repulsion = repulsion_slider.value
    return


@app.cell
def _(data_graph, mo, node_scale_slider, repulsion_slider):
    mo.hstack([data_graph,mo.vstack([repulsion_slider, node_scale_slider])],justify="start")
    return


@app.cell
def _(data_graph):
    data_graph.selected_ids
    return


@app.cell
def _():
    # data_graph.selected_ids = [1,2,3]
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
