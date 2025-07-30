# OrKa: Orchestrator Kit Agents
# Copyright © 2025 Marco Somma
#
# This file is part of OrKa – https://github.com/marcosomma/orka-resoning
#
# Licensed under the Apache License, Version 2.0 (Apache 2.0).
# You may not use this file for commercial purposes without explicit permission.
#
# Full license: https://www.apache.org/licenses/LICENSE-2.0
# For commercial use, contact: marcosomma.work@gmail.com
#
# Required attribution: OrKa by Marco Somma – https://github.com/marcosomma/orka-resoning

from .base_node import BaseNode


class RouterNode(BaseNode):
    """
    A node that routes the workflow based on a decision value from previous outputs.
    Supports flexible matching of decision values and routing maps.
    """

    def __init__(self, node_id, params=None, **kwargs):
        """
        Initialize the router node.

        Args:
            node_id (str): Unique identifier for the node.
            params (dict): Parameters containing decision_key and routing_map.
            **kwargs: Additional configuration parameters.

        Raises:
            ValueError: If required parameters are missing.
        """
        queue = kwargs.pop("queue", None)
        super().__init__(node_id=node_id, prompt=None, queue=None, **kwargs)
        if params is None:
            raise ValueError(
                "RouterAgent requires 'params' with 'decision_key' and 'routing_map'."
            )
        self.params = params

    def run(self, input_data):
        """
        Route the workflow based on the decision value.

        Args:
            input_data (dict): Input data containing previous outputs.

        Returns:
            list: List of next nodes to execute based on routing decision.
        """
        # Get decision value from previous outputs
        previous_outputs = input_data.get("previous_outputs", {})
        decision_key = self.params.get("decision_key")
        routing_map = self.params.get("routing_map", {})

        decision_value = previous_outputs.get(decision_key)

        # Normalize decision value for flexible matching
        decision_value_str = str(decision_value).strip().lower()

        # Try different matching strategies in order of preference
        route = (
            routing_map.get(decision_value)  # literal (True, False)
            or routing_map.get(decision_value_str)  # string "true"/"false"
            or routing_map.get(self._bool_key(decision_value_str))  # normalized boolean
            or []  # default empty list
        )

        return route

    def _bool_key(self, val):
        """
        Convert string values to boolean for routing.

        Args:
            val (str): String value to convert.

        Returns:
            bool or str: Boolean value if recognized, original string otherwise.
        """
        if val in ("true", "yes", "1"):
            return True
        if val in ("false", "no", "0"):
            return False
        return val
