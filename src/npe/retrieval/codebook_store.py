"""
Codebook Store.

Loads and manages YAML codebooks for rulepacks, repair maps, and plan templates.
"""

import os
from typing import Any, Dict, List, Optional

import yaml


class CodebookStore:
    """Stores and manages codebooks loaded from YAML files.

    Attributes:
        repair_maps: Dict of repair maps by domain
        plan_templates: Dict of plan templates
        rulepacks: Dict of rulepacks by domain
    """

    def __init__(self):
        self.repair_maps: Dict[str, Dict[str, Any]] = {}
        self.plan_templates: Dict[str, Dict[str, Any]] = {}
        self.rulepacks: Dict[str, Dict[str, Any]] = {}

    def load_repair_map(self, path: str) -> Dict[str, Any]:
        """Load a repair map from YAML.

        Args:
            path: Path to repair map YAML

        Returns:
            Repair map data
        """
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        domain = data.get("domain", "gr")
        self.repair_maps[domain] = data
        return data

    def load_plan_templates(self, path: str) -> Dict[str, Any]:
        """Load plan templates from YAML.

        Args:
            path: Path to plan templates YAML

        Returns:
            Plan templates data
        """
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        self.plan_templates = data
        return data

    def load_rulepacks(self, path: str) -> Dict[str, Any]:
        """Load rulepacks from YAML.

        Args:
            path: Path to rulepacks YAML

        Returns:
            Rulepacks data
        """
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        domain = data.get("domain", "gr")
        self.rulepacks[domain] = data
        return data

    def load_directory(self, dir_path: str) -> None:
        """Load all codebooks from a directory.

        Args:
            dir_path: Path to codebooks directory
        """
        for filename in os.listdir(dir_path):
            filepath = os.path.join(dir_path, filename)
            if not os.path.isfile(filepath):
                continue

            try:
                if filename.endswith(".yaml") or filename.endswith(".yml"):
                    with open(filepath, "r", encoding="utf-8") as f:
                        data = yaml.safe_load(f)

                    codebook_type = data.get("type", "")

                    if codebook_type == "repair_map":
                        self.load_repair_map(filepath)
                    elif codebook_type == "plan_templates":
                        self.load_plan_templates(filepath)
                    elif codebook_type == "rulepacks":
                        self.load_rulepacks(filepath)
                    elif "repair" in filename.lower():
                        self.load_repair_map(filepath)
                    elif "plan" in filename.lower():
                        self.load_plan_templates(filepath)
                    elif "rule" in filename.lower():
                        self.load_rulepacks(filepath)
            except (yaml.YAMLError, IOError) as e:
                print(f"Warning: Could not load {filepath}: {e}")

    def get_repair_actions(self, domain: str, gate_type: str) -> List[Dict[str, Any]]:
        """Get repair actions for a gate type.

        Args:
            domain: The domain
            gate_type: Type of gate

        Returns:
            List of repair actions
        """
        repair_map = self.repair_maps.get(domain, {})
        gate_repairs = repair_map.get("repairs", {}).get(gate_type, [])
        return gate_repairs

    def get_plan_templates(self, goal_type: str) -> List[Dict[str, Any]]:
        """Get plan templates for a goal type.

        Args:
            goal_type: Type of goal

        Returns:
            List of matching templates
        """
        templates = self.plan_templates.get("templates", [])
        return [
            t
            for t in templates
            if t.get("goal_type") == goal_type or goal_type in t.get("tags", [])
        ]

    def get_rules(self, domain: str, rule_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get rules from rulepacks.

        Args:
            domain: The domain
            rule_type: Optional rule type filter

        Returns:
            List of matching rules
        """
        rulepacks = self.rulepacks.get(domain, {})
        rules = rulepacks.get("rules", [])

        if rule_type:
            rules = [r for r in rules if r.get("type") == rule_type]

        return rules

    def get_conservative_knobs(self, domain: str) -> Dict[str, Any]:
        """Get conservative/safe configuration knobs.

        Args:
            domain: The domain

        Returns:
            Dict of conservative knob settings
        """
        rulepacks = self.rulepacks.get(domain, {})
        return rulepacks.get("conservative_knobs", {})


def load_codebooks(codebooks_path: str) -> CodebookStore:
    """Load all codebooks from a directory.

    Args:
        codebooks_path: Path to codebooks directory

    Returns:
        Loaded CodebookStore
    """
    store = CodebookStore()

    if os.path.isdir(codebooks_path):
        store.load_directory(codebooks_path)
    elif os.path.isfile(codebooks_path):
        if "repair" in codebooks_path.lower():
            store.load_repair_map(codebooks_path)
        elif "plan" in codebooks_path.lower():
            store.load_plan_templates(codebooks_path)
        elif "rule" in codebooks_path.lower():
            store.load_rulepacks(codebooks_path)

    return store
