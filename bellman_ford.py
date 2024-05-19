from typing import Dict, List, Tuple

class Graph:
    def __init__(self, vertices):
        self.vertices = vertices
        self.edges = []

    def add_edge(self, u, v, weight):
        self.edges.append((u, v, weight))


class BellmanFord:
    def __init__(self, graph, source):
        self.graph = graph
        self.source = source
        self.distances = {vertex: float('inf') for vertex in graph.vertices}
        self.distances[source] = 0
        self.predecessors = {vertex: None for vertex in graph.vertices}

    def run(self):
        for i in range(len(self.graph.vertices) - 1):
            for u, v, weight in self.graph.edges:
                if self.distances[u] + weight < self.distances[v]:
                    self.distances[v] = self.distances[u] + weight
                    self.predecessors[v] = u

        for u, v, weight in self.graph.edges:
            if self.distances[u] + weight < self.distances[v]:
                print("Negative cycle detected")
                return

        print("Shortest distances:", self.distances)

    def get_shortest_path(self, destination):
        path = []
        while destination != self.source:
            path.append(destination)
            destination = self.predecessors[destination]
        path.append(self.source)
        return path[::-1]


def bellman_ford(graph: Dict[str, List[Tuple[str, int]]], start: str, end: str) -> Tuple[List[str], int]:
    vertices = list(graph.keys())
    distances = {vertex: float('inf') for vertex in vertices}
    distances[start] = 0
    predecessors = {vertex: None for vertex in vertices}

    edges = [(u, v, weight) for u, adjacent_nodes in graph.items() for v, weight in adjacent_nodes]

    for _ in range(len(vertices) - 1):
        for u, v, weight in edges:
            if distances[u] + weight < distances[v]:
                distances[v] = distances[u] + weight
                predecessors[v] = u

    for u, v, weight in edges:
        if distances[u] + weight < distances[v]:
            raise ValueError("Negative cycle detected")

    shortest_paths = {}
    for destination in vertices:
        if destination == start:
            continue
        path = []
        node = destination
        while node != start:
            path.append(node)
            node = predecessors[node]
        path.append(start)
        shortest_paths[destination] = path[::-1]

    return shortest_paths[end], distances[end]
    # return distances, predecessors


if __name__ == "__main__":
    graph = {
        'A': [('B', 20), ('G', 15)],
        'B': [('A', 20), ('C', 8), ('D', 9)],
        'C': [('B', 8), ('D', 6), ('E', 15), ('H', 10)],
        'D': [('B', 9), ('C', 6), ('E', 7)],
        'E': [('C', 15), ('D', 7), ('F', 22), ('G', 18)],
        'F': [('E', 22)],
        'G': [('A', 15), ('E', 18)],
        'H': [('C', 10)]
    }
    print(bellman_ford(graph, "F", "H"))

# if __name__ == '__main__':
#     vertices = ['A', 'B', 'C', 'D', 'E']
#     graph = Graph(vertices)
#     graph.add_edge('A', 'B', 4)
#     graph.add_edge('A', 'C', 2)
#     graph.add_edge('B', 'C', 3)
#     graph.add_edge('B', 'D', 2)
#     graph.add_edge('B', 'E', 3)
#     graph.add_edge('C', 'B', 1)
#     graph.add_edge('C', 'D', 4)
#     graph.add_edge('C', 'E', 5)
#     graph.add_edge('E', 'D', 1)

#     bf = BellmanFord(graph, 'A')
#     bf.run()
#     print("Shortest path from A to D:", bf.get_shortest_path('D'))
