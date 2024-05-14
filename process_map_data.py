import typing as tp
import math
import numpy as np

from xml.etree import ElementTree

__all__ = ['OSMReader']


R = 6371 * 1000  # Earth's radius in kilometers


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


class OSMReader:
    def __init__(self, edges, adjacency_matrix, index_to_node, bounds):
        self.edges = edges
        self.index_to_node = index_to_node
        self.adjacency_matrix = adjacency_matrix
        self.bounds = bounds

    @staticmethod
    def parse_node(root) -> tp.Tuple[dict, dict]:
        id_to_node = {}
        bounds = None
        for element in root:
            if element.tag == 'node':
                node_id = int(element.attrib['id'])
                lat = float(element.attrib['lat'])
                lon = float(element.attrib['lon'])
                id_to_node[node_id] = Node(
                    id=node_id, lon=np.radians(lon), lat=np.radians(lat))
            if element.tag == 'bounds':
                bounds = element.attrib
        return id_to_node, bounds

    @staticmethod
    def parse_edge(root, id_to_node: dict) -> tp.Tuple[list, list]:
        edge_node_ids = []
        edge_groups = []
        for element in root:
            if element.tag == 'way':
                way_id = element.attrib['id']
                node_refs = element.findall('nd')
                node_ref0 = node_refs[0]
                node_ref1 = node_refs[-1]
                if node_ref0.attrib['ref'] == node_ref1.attrib['ref']:
                    # self-loop node
                    continue
                edge_node_ids.extend([int(n.attrib['ref']) for n in node_refs])
                edges = []
                for i in range(len(node_refs) - 1):
                    nd0 = node_refs[i]
                    nd1 = node_refs[i + 1]
                    node0 = Node(
                        id=int(nd0.attrib['ref']), lon=id_to_node[int(nd0.attrib['ref'])].lon,
                        lat=id_to_node[int(nd0.attrib['ref'])].lat)
                    node1 = Node(
                        id=int(nd1.attrib['ref']), lon=id_to_node[int(nd1.attrib['ref'])].lon,
                        lat=id_to_node[int(nd1.attrib['ref'])].lat)
                    edge = Edge(id=way_id, name='', nodes=(node0, node1))
                    edges.append(edge)
                edge_groups.append(EdgeGroup(edges=edges))

        return edge_node_ids, edge_groups

    @staticmethod
    def clean(edge_node_ids: list, edge_groups: list) -> tp.Tuple[tp.List[Edge], dict]:
        clean_edges = []
        id_to_node_index = {}
        for edge_group in edge_groups:
            edge_merge_queue = []
            for edge in edge_group.edges:
                edge_nodes = edge.nodes
                if edge_node_ids.count(edge_nodes[0].id) < 2:
                    if not len(edge_merge_queue):
                        # no connection with any edges -> isolated component
                        continue
                if edge_node_ids.count(edge_nodes[1].id) > 1:
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

    @staticmethod
    def parse(filename: str):
        tree = ElementTree.parse(filename)
        root = tree.getroot()
        id_to_node, bounds = OSMReader.parse_node(root)
        edge_node_ids, edge_groups = OSMReader.parse_edge(root, id_to_node)
        clean_edges, id_to_node_index = OSMReader.clean(edge_node_ids, edge_groups)
        num_node = len(id_to_node_index)
        adjacency_matrix = np.zeros((num_node, num_node))
        for edge in clean_edges:
            nodes = edge.nodes
            node0_id = nodes[0].id
            node1_id = nodes[1].id
            node0_idx = id_to_node_index[node0_id]
            node1_idx = id_to_node_index[node1_id]
            adjacency_matrix[node0_idx, node1_idx] = edge.distance() \
                if edge.merged_length is None else edge.merged_length
        index_to_node = [id_to_node[_id] for _id in id_to_node_index]
        return OSMReader(
            index_to_node=index_to_node, edges=clean_edges,
            adjacency_matrix=adjacency_matrix, bounds=bounds)

    def get_coords_for_chart(self):
        node_coords = []
        for edge in self.edges:
            temp = []
            for node in edge.nodes:
                temp.append(list(node.to_cartesian())[:-1])
            node_coords.append(temp)
        return node_coords

    def get_array_bounds(self):
        return [[float(self.bounds['minlat']), float(self.bounds['minlon'])],
                [float(self.bounds['maxlat']), float(self.bounds['maxlon'])]]
