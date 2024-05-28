import heapq
import process_map_data as pmd


def dijkstra(graph, start, end):
    queue = [(0, start, [])]  # (cost, current_node, path)
    seen = set()
    mins = {start: 0}

    while queue:
        (cost, node, path) = heapq.heappop(queue)
        if node in seen:
            continue

        seen.add(node)
        path = path + [node]

        if node == end:
            return (cost, path)

        for next_node, weight in graph.get(node, ()):
            if next_node in seen:
                continue
            prev = mins.get(next_node, None)
            next_cost = cost + weight
            if prev is None or next_cost < prev:
                mins[next_node] = next_cost
                heapq.heappush(queue, (next_cost, next_node, path))

    return float("inf"), []


if __name__ == "__main__":
    # graph = {
    #     "C": [('D', 3), ('E', 2)],
    #     "E": [("D", 1), ("F", 2), ("G", 3)],
    #     "F": [("H", 1), ("G", 2)],
    #     "D": [("F", 4)],
    #     "G": [("H", 2)]
    # }
    # print(dijkstra(graph, start="C", end="H"))
    reader = pmd.OSMReader.parse('data/turtle_lake_map_region.osm')
    graph = reader.convert_adjacency_matrix_to_dict()
    print("Number of nodes: ", len(reader.index_to_node))
    print("Number of edges: ", len(reader.edges))
    distance, path = dijkstra(graph, start=10, end=40)
    print("Distance: ", distance)
    print("Path: ", path)
