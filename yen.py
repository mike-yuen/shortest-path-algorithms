import numpy as np
import dijkstra


def remove_edges_from_graph(graph, start, end_nodes):
    graph = graph.copy()
    new_edges = []
    for node, cost in graph.get(start, ()):
        if node not in end_nodes:
            new_edges.append((node, cost))
    graph[start] = new_edges
    return graph


def get_removed_nodes_from_paths(paths, source):
    removed_nodes = set()
    for path in paths:
        indices = np.where(np.array(path, dtype=type(path[0])) == source)[0]
        if len(indices) != 1:
            continue
        removed_nodes.add(path[indices[0] + 1])
    return removed_nodes


def get_cost_from_path(graph, path):
    cost = 0.
    if len(path) == 0:
        return cost
    for i, node in enumerate(path[:-1]):
        edges = graph[node]
        for second_node, c in edges:
            if second_node == path[i + 1]:
                cost += c
    return cost


def yen(graph, source, target, top=3):
    """
    Finds k shortest loopless paths from source to target in a graph,
    including their costs.

    Args:
        graph: A dictionary representing the graph. Keys are nodes, values are dictionaries
               mapping neighbors to their edge costs.
        source: The starting node.
        target: The destination node.
        top: The number of shortest paths to find.

    Returns:
        A list of tuples containing (cost, path) for k shortest paths.
    """
    best_cost, shortest_path = dijkstra.dijkstra1(graph, source, target)
    best_shortest_paths = [(tuple(shortest_path), best_cost)]
    traversed_paths = [shortest_path]

    for k in range(top):
        candidate_path_to_cost = {}
        for i, node in enumerate(best_shortest_paths[k][0][:-1]):
            spur_node = node
            root_path = best_shortest_paths[k][0][:i]
            removed_nodes = get_removed_nodes_from_paths(traversed_paths, spur_node)
            new_graph = remove_edges_from_graph(graph, spur_node, removed_nodes)
            cost, spur_path = dijkstra.dijkstra1(new_graph, spur_node, target)
            if not len(spur_path):
                continue
            total_path = root_path + tuple(spur_path)
            traversed_paths.append(total_path)
            root_cost = get_cost_from_path(graph, root_path + tuple(spur_path)[:1])
            candidate_path_to_cost[tuple(total_path)] = cost + root_cost
        if not len(candidate_path_to_cost.keys()):
            continue
        best_path = sorted(list(candidate_path_to_cost.items()), key=lambda item: item[0])[-1]
        best_shortest_paths.append(best_path)  # TODO: get path with less number of nodes

    return tuple(zip(*best_shortest_paths[: top]))


if __name__ == '__main__':
    # Example usage
    Graph = {
        "C": [('D', 3), ('E', 2)],
        "E": [("D", 1), ("F", 2), ("G", 3)],
        "F": [("H", 1), ("G", 2)],
        "D": [("F", 4)],
        "G": [("H", 2)]
    }

    shortest_paths = yen(Graph, source="C", target="H", top=3)
    print(shortest_paths)
