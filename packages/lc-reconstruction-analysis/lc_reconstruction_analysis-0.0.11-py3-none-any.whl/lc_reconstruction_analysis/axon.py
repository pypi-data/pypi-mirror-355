"""
    Adds wire length computation
"""

import queue


def add_all_wire_lengths(dataDF, graphs):
    """
    compute wire length for all cells
    """
    for name in dataDF["Graph"]:
        graphs[name] = add_wire_length(graphs[name])
    return graphs


def add_wire_length(graph):
    """
    Add wire length calculation to each node
    graph = axon.add_wire_length(graph)
    """
    graph.nodes[1]["wire_length"] = 0
    node_queue = queue.Queue()
    node_queue.put(1)
    while not node_queue.empty():
        node = node_queue.get()
        edges = dict(graph[node])
        for k in edges.keys():
            graph.nodes[k]["wire_length"] = (
                graph.nodes[node]["wire_length"] + edges[k]["weight"]
            )
            node_queue.put(k)
    return graph
