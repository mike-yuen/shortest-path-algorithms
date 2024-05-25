import shortestpaths as sp
import networkx as nx
import dijkstra


def remove_edges_from_graph(graph, start, end_nodes):
    graph = graph.copy()
    new_edges = []
    for node, cost in graph.get(start, ()):
        if node not in end_nodes:
            new_edges.append((node, cost))
    graph[start] = new_edges
    return graph


def get_removed_share_same_root_nodes_from_paths(paths, root_path):
    removed_nodes = set()
    if not len(root_path):
        return removed_nodes
    for path, _ in paths:
        if root_path == path[: len(root_path)]:
            removed_nodes.add(path[len(root_path)])
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
    best_cost, shortest_path = dijkstra.dijkstra(graph, source, target)
    shortest_paths = [(tuple(shortest_path), best_cost)]
    candidate_path_to_cost = {}

    for k in range(top - 1):
        for i, node in enumerate(shortest_paths[k][0][:-1]):
            spur_node = node
            root_path = shortest_paths[k][0][:i]
            removed_nodes = get_removed_share_same_root_nodes_from_paths(
                shortest_paths, root_path + (spur_node,))
            new_graph = remove_edges_from_graph(graph, spur_node, removed_nodes)
            cost, spur_path = dijkstra.dijkstra(new_graph, spur_node, target)
            if not len(spur_path):
                continue
            total_path = root_path + tuple(spur_path)
            root_cost = get_cost_from_path(graph, root_path + tuple(spur_path)[:1])
            if tuple(total_path) not in candidate_path_to_cost.keys():
                candidate_path_to_cost[tuple(total_path)] = cost + root_cost
        if not len(candidate_path_to_cost.keys()):
            continue
        best_path = sorted(list(candidate_path_to_cost.items()), key=lambda item: item[1])[0]
        same_cost_best_paths = list(filter(
            lambda item: item[1] == best_path[1], candidate_path_to_cost.items()))
        best_paths = min(same_cost_best_paths, key=lambda item: len(item[0]))
        shortest_paths.append(best_path)  # TODO: get path with less number of nodes
        candidate_path_to_cost.pop(best_paths[0])

    return tuple(zip(*shortest_paths[: top]))


if __name__ == '__main__':
    # Example usage
    Graph = {
        "C": [('D', 3), ('E', 2)],
        "E": [("D", 1), ("F", 2), ("G", 3)],
        "F": [("H", 1), ("G", 2)],
        "D": [("F", 4)],
        "G": [("H", 2)]
    }
    G = nx.DiGraph()
    for s, neighbors in Graph.items():
        for neighbor, weight in neighbors:
            G.add_edge(s, neighbor, weight=weight)
    ref_s_paths, ref_best_costs = zip(*sp.k_shortest_paths(G, "C", "H", k=3, method='y'))
    s_paths, best_costs = yen(Graph, source="C", target="H", top=3)
    assert ref_s_paths == tuple(list(s) for s in s_paths)
    assert ref_best_costs == best_costs

