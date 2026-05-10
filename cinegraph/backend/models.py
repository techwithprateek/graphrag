from pydantic import BaseModel
from typing import Any


class QueryRequest(BaseModel):
    question: str


class GraphNode(BaseModel):
    id: str
    label: str          # Movie | Person | Genre | Studio
    properties: dict[str, Any] = {}


class GraphEdge(BaseModel):
    source: str
    target: str
    type: str


class GraphData(BaseModel):
    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []


class Meta(BaseModel):
    node_count: int
    edge_count: int
    query_ms: int


class QueryResponse(BaseModel):
    answer: str
    cypher: str
    hop_count: int
    graph_data: GraphData
    meta: Meta
