"""Semiotic Table Engine implementation.

This module defines the :class:`SemioticTable` used across the
EchoThreads ecosystem for binding symbolic units to memory constructs.
"""

from typing import Dict, Any


class SemioticTable:
    """Central registry for Red Stones, Echo Nodes and Orbs."""

    def __init__(self) -> None:
        self.red_stones: Dict[str, Any] = {}
        self.echo_nodes: Dict[str, Any] = {}
        self.orbs: Dict[str, Any] = {}
        self.fractal_schema: Dict[str, Any] = {}

    def register_red_stone(self, key: str, payload: Any) -> None:
        """Store a Red Stone payload by key."""
        self.red_stones[key] = payload

    def attach_orb(self, red_stone_key: str, orb: Any) -> None:
        """Bind an Orb instance to a Red Stone anchor."""
        if red_stone_key in self.red_stones:
            self.orbs[getattr(orb, "id", red_stone_key)] = {
                "anchor": red_stone_key,
                "orb": orb,
            }

    def sync_echo_node(self, node_id: str, memory: Any) -> None:
        """Synchronize an Echo Node with provided memory."""
        self.echo_nodes[node_id] = memory

    def load_fractal_schema(self, schema: Dict[str, Any]) -> None:
        """Load a fractal schema for system-wide indexing."""
        self.fractal_schema = schema
