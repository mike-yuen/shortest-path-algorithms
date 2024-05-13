import typing as tp
import osmium
import math
import numpy as np
import matplotlib.pyplot as plt


__all__ = ['get_adjacency_matrix_from_osm_file']

R = 6371  # Earth's radius in kilometers


class Node(tp.NamedTuple):
    id: int
    lon: float
    lat: float

    # Function to convert latitude and longitude to Cartesian coordinates
    def to_cartesian(self):
        x = R * math.cos(self.lat) * math.cos(self.lon)
        y = R * math.cos(self.lat) * math.sin(self.lon)
        z = R * math.sin(self.lat)
        return x, y, z

    def __eq__(self, other):
        return self.id == other.id


class Edge(tp.NamedTuple):
    id: str
    nodes: tp.Tuple[Node, Node]
    name: str
    merged_length: tp.Union[float, None] = None

    def merge_with(self, other):
        if self == other:
            return self
        assert self.nodes[1] == other.nodes[0]
        return Edge(
            id=self.id, nodes=(self.nodes[0], other.nodes[1]),
            name=self.name, merged_length=self.distance() + other.distance())

    def distance(self) -> float:
        node1, node2 = self.nodes
        lat1 = node1.lat
        lat2 = node2.lat
        lon1 = node1.lon
        lon2 = node2.lon
        delta_lat = abs(lat2 - lat1)
        delta_lon = abs(lon2 - lon1)
        a = np.sin(delta_lat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(delta_lon / 2) ** 2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
        d = R * c
        return d

    def __eq__(self, other):
        return self.id == other.id and self.nodes == other.nodes


class EdgeGroup(tp.NamedTuple):
    edges: tp.List[Edge]

    @staticmethod
    def merge_edges(edges: tp.List[Edge]):
        new_edge = edges[0]
        for edge in edges:
            new_edge = new_edge.merge_with(edge)
        return new_edge


class OSMProcessHandler(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.edge_groups = []
        self.id_to_node = {}
        self.edge_node_ids = []

    def node(self, n):
        # Define your filtering criteria here
        self.id_to_node[n.id] = Node(
            id=n.id, lon=np.radians(n.location.lon),
            lat=np.radians(n.location.lat))

    def way(self, way):
        node_refs = way.nodes
        node_ref0 = node_refs[0]
        node_ref1 = node_refs[-1]
        if node_ref0.ref == node_ref1.ref:
            # self-loop node
            return None
        street_name = way.tags.get('addr:street', None)
        if street_name is None:
            street_name = way.tags.get('name', '')
        self.edge_node_ids.extend([n.ref for n in node_refs])
        edges = []
        for i in range(len(node_refs) - 1):
            nd0 = node_refs[i]
            nd1 = np.roll(node_refs, -1)[i]
            node0 = Node(
                id=nd0.ref, lon=self.id_to_node[nd0.ref].lon,
                lat=self.id_to_node[nd0.ref].lat)
            node1 = Node(
                id=nd1.ref, lon=self.id_to_node[nd1.ref].lon,
                lat=self.id_to_node[nd1.ref].lat)
            edge = Edge(id=way.id, name=street_name, nodes=(node0, node1))
            edges.append(edge)
        self.edge_groups.append(EdgeGroup(edges=edges))

    def clean(self) -> tp.Tuple[tp.List[Edge], dict]:
        clean_edges = []
        id_to_node_index = {}
        for edge_group in self.edge_groups:
            edge_merge_queue = []
            for edge in edge_group.edges:
                if edge.id == 609435533:
                    print()
                edge_nodes =  edge.nodes
                if self.edge_node_ids.count(edge_nodes[0].id) < 2:
                    if not len(edge_merge_queue):
                        # no connection with any edges -> isolated component
                        continue
                if self.edge_node_ids.count(edge_nodes[1].id) > 1:
                    if len(edge_merge_queue):
                        new_edge = EdgeGroup.merge_edges([*edge_merge_queue, edge])
                    else:
                        new_edge = edge
                    for node in new_edge.nodes:
                        if node.id not in id_to_node_index:
                            id_to_node_index[node.id] = len(id_to_node_index)
                    clean_edges.append(new_edge)
                    edge_merge_queue.clear()
                else:
                    edge_merge_queue.append(edge)
        return clean_edges, id_to_node_index


def get_adjacency_matrix_from_osm_file(filename: str) -> np.ndarray:
    # Parse .osm file and apply filters
    osm_handler = OSMProcessHandler()
    osm_handler.apply_file(filename)
    edges, id_to_node_index = osm_handler.clean()
    # node_coordinates = []
    # pair_coordinates = []
    # for node_id in id_to_node_index:
    #     node_coordinates.append(list(osm_handler.id_to_node[node_id].to_cartesian())[:-1])
    # node_coordinates = np.array(node_coordinates)
    # plt.figure(figsize=(8, 6))
    # plt.scatter(node_coordinates[:, 0], node_coordinates[:, 1], color='blue', label='Random Data')
    # plt.grid(True)
    num_node = len(id_to_node_index)
    adjacency_matrix = np.zeros((num_node, num_node))
    print('number of edges', len(edges))
    print('number of nodes', num_node)
    for edge in edges:
        nodes = edge.nodes
        # pair_coordinates.append([list(nodes[0].to_cartesian())[:-1], list(nodes[1].to_cartesian())[:-1]])
        node0_id = nodes[0].id
        node1_id = nodes[1].id
        node0_idx = id_to_node_index[node0_id]
        node1_idx = id_to_node_index[node1_id]
        adjacency_matrix[node0_idx, node1_idx] = edge.distance() \
            if edge.merged_length is None else edge.merged_length
    # print(np.where(adjacency_matrix[148, :] != 0.0))
    # for idx, pair in enumerate(np.array(pair_coordinates)):
    #     plt.plot(
    #         pair[:, 0], pair[:, 1],
    #         color='red', label='Sine Curve', linestyle='-')
    # plt.show()
    return adjacency_matrix

# a = get_adjacency_matrix_from_osm_file('data/exported_map.osm')
# print(a.shape)