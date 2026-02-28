"""
GraphGML Core Module

Graph container and operations for the GraphGML layer.
Provides the GraphGML class for managing nodes and edges,
and GraphQuery for pattern matching operations.
"""

from typing import Callable, Generator, Optional
from collections import defaultdict

from cnsc.haai.graphgml.types import GraphNode, EdgeType


class GraphGML:
    """
    Graph container for GraphGML traces.

    A directed graph structure that holds nodes and edges representing
    execution traces, proofs, and constraint systems.

    Attributes:
        nodes: Dictionary mapping node IDs to GraphNode instances
        edges: List of tuples (source_id, edge_type, target_id)
        adjacency: Adjacency list for efficient traversal (built on-demand)

    Example:
        >>> graph = GraphGML()
        >>> state = StateNode("s1", "initial")
        >>> candidate = CandidateNode("c1", value=42)
        >>> graph.add_node(state)
        >>> graph.add_node(candidate)
        >>> graph.add_edge("c1", EdgeType.PROPOSED_FROM, "s1")
        >>> neighbors = graph.get_neighbors("c1", EdgeType.PROPOSED_FROM)
    """

    def __init__(self) -> None:
        """Initialize an empty graph."""
        self.nodes: dict[str, GraphNode] = {}
        self.edges: list[tuple[str, str, str]] = []
        self._adjacency: dict[str, dict[str, list[str]]] | None = None

    def _invalidate_cache(self) -> None:
        """Invalidate the adjacency cache after structural changes."""
        self._adjacency = None

    def _build_adjacency(self) -> dict[str, dict[str, list[str]]]:
        """
        Build the adjacency list from edges.

        Returns:
            Dictionary mapping node_id to {edge_type: [target_ids]}
        """
        if self._adjacency is not None:
            return self._adjacency

        self._adjacency = defaultdict(lambda: defaultdict(list))
        for source_id, edge_type, target_id in self.edges:
            # Convert edge_type to string value if it's an enum
            edge_type_str = edge_type.value if hasattr(edge_type, "value") else str(edge_type)
            self._adjacency[source_id][edge_type_str].append(target_id)
            # Build reverse adjacency for reverse traversal
            self._adjacency[target_id][f"rev_{edge_type_str}"].append(source_id)

        return self._adjacency

    def add_node(self, node: GraphNode) -> None:
        """
        Add a node to the graph.

        Args:
            node: GraphNode instance to add

        Raises:
            ValueError: If a node with the same ID already exists
        """
        if node.node_id in self.nodes:
            raise ValueError(f"Node with ID '{node.node_id}' already exists in graph")
        self.nodes[node.node_id] = node
        self._invalidate_cache()

    def add_edge(self, source_id: str, edge_type: str, target_id: str) -> None:
        """
        Add an edge to the graph.

        Args:
            source_id: ID of the source node
            edge_type: Type of the edge (see EdgeType enum)
            target_id: ID of the target node

        Raises:
            ValueError: If source or target node does not exist
        """
        if source_id not in self.nodes:
            raise ValueError(f"Source node '{source_id}' not found in graph")
        if target_id not in self.nodes:
            raise ValueError(f"Target node '{target_id}' not found in graph")
        self.edges.append((source_id, edge_type, target_id))
        self._invalidate_cache()

    def get_node(self, node_id: str) -> Optional[GraphNode]:
        """
        Get a node by ID.

        Args:
            node_id: ID of the node to retrieve

        Returns:
            GraphNode instance or None if not found
        """
        return self.nodes.get(node_id)

    def get_neighbors(self, node_id: str, edge_type: Optional[str] = None) -> list[GraphNode]:
        """
        Get neighboring nodes connected by specified edge type.

        Args:
            node_id: ID of the source node
            edge_type: Optional edge type to filter by

        Returns:
            List of neighboring GraphNode instances
        """
        if node_id not in self.nodes:
            return []

        adjacency = self._build_adjacency()
        neighbors = []

        if edge_type is None:
            # Return all neighbors regardless of edge type
            for edge_type_key, target_ids in adjacency[node_id].items():
                if not edge_type_key.startswith("rev_"):
                    for target_id in target_ids:
                        if target_id in self.nodes:
                            neighbors.append(self.nodes[target_id])
        else:
            # Return only neighbors connected by specified edge type
            target_ids = adjacency[node_id].get(edge_type, [])
            for target_id in target_ids:
                if target_id in self.nodes:
                    neighbors.append(self.nodes[target_id])

        return neighbors

    def find_nodes(self, predicate: Callable[[GraphNode], bool]) -> list[GraphNode]:
        """
        Find all nodes matching a predicate function.

        Args:
            predicate: Function that takes a node and returns bool

        Returns:
            List of matching GraphNode instances
        """
        return [node for node in self.nodes.values() if predicate(node)]

    def find_nodes_by_type(self, node_type: str) -> list[GraphNode]:
        """
        Find all nodes of a specific type.

        Args:
            node_type: Type string to filter by

        Returns:
            List of matching GraphNode instances
        """
        return self.find_nodes(lambda n: n.node_type == node_type)

    def traverse(self, start_node_id: str, edge_type: str) -> Generator[GraphNode, None, None]:
        """
        Traverse the graph following edges of a specific type.

        Args:
            start_node_id: ID of the starting node
            edge_type: Type of edges to follow

        Yields:
            GraphNode instances along the traversal path
        """
        if start_node_id not in self.nodes:
            return

        adjacency = self._build_adjacency()
        visited = set()
        queue = [start_node_id]

        while queue:
            current_id = queue.pop(0)
            if current_id in visited:
                continue
            visited.add(current_id)

            current_node = self.nodes.get(current_id)
            if current_node:
                yield current_node

            target_ids = adjacency[current_id].get(edge_type, [])
            for target_id in target_ids:
                if target_id not in visited:
                    queue.append(target_id)

    def reverse_traverse(
        self, start_node_id: str, edge_type: str
    ) -> Generator[GraphNode, None, None]:
        """
        Traverse the graph in reverse direction following edges.

        Args:
            start_node_id: ID of the starting node
            edge_type: Type of edges to traverse in reverse

        Yields:
            GraphNode instances along the reverse traversal path
        """
        if start_node_id not in self.nodes:
            return

        adjacency = self._build_adjacency()
        visited = set()
        queue = [start_node_id]

        while queue:
            current_id = queue.pop(0)
            if current_id in visited:
                continue
            visited.add(current_id)

            current_node = self.nodes.get(current_id)
            if current_node:
                yield current_node

            reverse_key = f"rev_{edge_type}"
            source_ids = adjacency[current_id].get(reverse_key, [])
            for source_id in source_ids:
                if source_id not in visited:
                    queue.append(source_id)

    def validate_invariants(self, allow_orphaned: bool = True) -> list[str]:
        """
        Validate graph structure invariants.

        Args:
            allow_orphaned: If True, nodes without edges are allowed (warn only).
                           If False, they cause validation failure.

        Returns:
            List of invariant violation messages (empty if valid)
        """
        violations = []
        warnings = []

        # Check for orphaned nodes (nodes with no edges)
        connected_nodes = set()
        for source_id, _, target_id in self.edges:
            connected_nodes.add(source_id)
            connected_nodes.add(target_id)

        for node_id, node in self.nodes.items():
            if node_id not in connected_nodes:
                if allow_orphaned:
                    warnings.append(f"Node '{node_id}' is orphaned (no edges)")
                else:
                    violations.append(f"Node '{node_id}' is orphaned (no edges)")

        # Check for duplicate edges
        edge_set = set()
        for source_id, edge_type, target_id in self.edges:
            edge_key = (source_id, edge_type, target_id)
            if edge_key in edge_set:
                violations.append(f"Duplicate edge: {source_id} -> {target_id} ({edge_type})")
            edge_set.add(edge_key)

        # Check edge type validity
        valid_types = {e.value for e in EdgeType}
        for source_id, edge_type, target_id in self.edges:
            if edge_type not in valid_types:
                violations.append(
                    f"Invalid edge type '{edge_type}' on edge {source_id} -> {target_id}"
                )

        return violations

    def node_count(self) -> int:
        """Return the number of nodes in the graph."""
        return len(self.nodes)

    def edge_count(self) -> int:
        """Return the number of edges in the graph."""
        return len(self.edges)

    def clear(self) -> None:
        """Remove all nodes and edges from the graph."""
        self.nodes.clear()
        self.edges.clear()
        self._adjacency = None

    def copy(self) -> "GraphGML":
        """
        Create a deep copy of the graph.

        Returns:
            New GraphGML instance with copied nodes and edges
        """
        new_graph = GraphGML()
        for node in self.nodes.values():
            # Create a copy of the node's data
            new_node = GraphNode(
                node_id=node.node_id,
                node_type=node.node_type,
                properties=node.properties.copy(),
                metadata=node.metadata.copy(),
            )
            new_graph.add_node(new_node)
        for source_id, edge_type, target_id in self.edges:
            new_graph.add_edge(source_id, edge_type, target_id)
        return new_graph


class GraphQuery:
    """
    Query interface for pattern matching on GraphGML graphs.

    Provides methods for finding paths and subgraphs that match
    specified patterns.

    Example:
        >>> query = GraphQuery(graph)
        >>> paths = query.find_path("c1", "s3", [EdgeType.PROPOSED_FROM])
        >>> subgraph = query.find_subgraph({"node_type": "commit"})
    """

    def __init__(self, graph: GraphGML) -> None:
        """
        Initialize the query interface.

        Args:
            graph: GraphGML instance to query
        """
        self.graph = graph

    def find_path(self, start: str, end: str, edge_types: list[str]) -> list[list[str]]:
        """
        Find all paths from start node to end node following edge types.

        Uses BFS to find all simple paths (no cycles).

        Args:
            start: Starting node ID
            end: Ending node ID
            edge_types: List of allowed edge types in order

        Returns:
            List of paths, where each path is a list of node IDs
        """
        if start not in self.graph.nodes or end not in self.graph.nodes:
            return []

        paths: list[list[str]] = []
        adjacency = self.graph._build_adjacency()

        def dfs(current_id: str, path: list[str], edge_index: int) -> None:
            if current_id == end:
                paths.append(path.copy())
                return

            if edge_index >= len(edge_types):
                return

            edge_type = edge_types[edge_index]
            target_ids = adjacency[current_id].get(edge_type, [])

            for target_id in target_ids:
                if target_id not in path:  # Prevent cycles
                    path.append(target_id)
                    dfs(target_id, path, edge_index + 1)
                    path.pop()

        dfs(start, [start], 0)
        return paths

    def find_subgraph(self, pattern: dict) -> GraphGML:
        """
        Find a subgraph matching a pattern.

        Args:
            pattern: Dictionary with node_type and/or property filters

        Returns:
            New GraphGML containing matching nodes and their connections
        """
        matching_nodes = self.graph.find_nodes(
            lambda n: all(
                getattr(n, key) == value for key, value in pattern.items() if hasattr(n, key)
            )
        )

        result = GraphGML()
        for node in matching_nodes:
            # Copy node to result graph
            new_node = GraphNode(
                node_id=node.node_id,
                node_type=node.node_type,
                properties=node.properties.copy(),
                metadata=node.metadata.copy(),
            )
            result.add_node(new_node)

        # Add edges between matching nodes
        for source_id, edge_type, target_id in self.graph.edges:
            if source_id in result.nodes and target_id in result.nodes:
                result.add_edge(source_id, edge_type, target_id)

        return result

    def find_upstream(
        self, node_id: str, edge_types: list[str], max_depth: int = 10
    ) -> list[GraphNode]:
        """
        Find all nodes upstream (ancestors) of a given node.

        Args:
            node_id: Target node ID
            edge_types: Edge types to traverse in reverse
            max_depth: Maximum traversal depth

        Returns:
            List of upstream nodes in dependency order
        """
        results: list[GraphNode] = []
        visited = set()

        for node in self.graph.reverse_traverse(node_id, edge_types[0] if edge_types else ""):
            if node.node_id in visited:
                continue
            visited.add(node.node_id)
            results.append(node)

        return results

    def find_downstream(
        self, node_id: str, edge_types: list[str], max_depth: int = 10
    ) -> list[GraphNode]:
        """
        Find all nodes downstream (descendants) of a given node.

        Args:
            node_id: Source node ID
            edge_types: Edge types to traverse
            max_depth: Maximum traversal depth

        Returns:
            List of downstream nodes in execution order
        """
        results: list[GraphNode] = []
        visited = set()

        for node in self.graph.traverse(node_id, edge_types[0] if edge_types else ""):
            if node.node_id in visited:
                continue
            visited.add(node.node_id)
            results.append(node)

        return results

    def get_dependency_order(self) -> list[str]:
        """
        Get nodes in topological dependency order.

        Returns:
            List of node IDs in topological order

        Raises:
            ValueError: If graph contains cycles
        """
        in_degree: dict[str, int] = defaultdict(int)
        adjacency = self.graph._build_adjacency()

        # Calculate in-degrees
        for node_id in self.graph.nodes:
            for edge_type, targets in adjacency[node_id].items():
                if not edge_type.startswith("rev_"):
                    for target_id in targets:
                        in_degree[target_id] += 1

        # Start with nodes that have no dependencies
        queue = [node_id for node_id in self.graph.nodes if in_degree[node_id] == 0]
        order = []

        while queue:
            current = queue.pop(0)
            order.append(current)

            for edge_type, targets in adjacency[current].items():
                if not edge_type.startswith("rev_"):
                    for target_id in targets:
                        in_degree[target_id] -= 1
                        if in_degree[target_id] == 0:
                            queue.append(target_id)

        if len(order) != len(self.graph.nodes):
            remaining = set(self.graph.nodes) - set(order)
            raise ValueError(f"Cycle detected involving nodes: {remaining}")

        return order


__all__ = ["GraphGML", "GraphQuery"]
