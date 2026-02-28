"""
Registry Loader.

Loads proposer registry manifest and computes registry hash.
"""

import os
from typing import Any, Dict, List, Optional

import yaml

from ..core.errors import RegistryLoadError
from ..core.hashing import hash_registry


class RegistryLoader:
    """Loads and manages the proposer registry.

    Attributes:
        manifest: The loaded manifest data
        registry_hash: Hash of the registry
        proposer_order: Ordered list of proposer IDs
        proposers: Dict of proposer configurations
    """

    def __init__(self, manifest_path: Optional[str] = None):
        """Initialize the registry loader.

        Args:
            manifest_path: Optional path to manifest file. If not provided,
                          uses the default manifest in the registry package.
        """
        self._manifest_path = manifest_path
        self._manifest: Optional[Dict[str, Any]] = None
        self._registry_hash: Optional[str] = None

        # Proposer cache for lazy loading
        self._proposer_cache: Dict[str, Any] = {}

    @property
    def manifest(self) -> Dict[str, Any]:
        """Get the loaded manifest."""
        if self._manifest is None:
            self._load()
        return self._manifest

    @property
    def registry_hash(self) -> str:
        """Get the registry hash."""
        if self._registry_hash is None:
            self._compute_hash()
        return self._registry_hash

    @property
    def spec(self) -> str:
        """Get the manifest spec version."""
        return self.manifest.get("spec", "")

    @property
    def registry_name(self) -> str:
        """Get the registry name."""
        return self.manifest.get("registry_name", "unknown")

    @property
    def registry_version(self) -> int:
        """Get the registry version."""
        return self.manifest.get("registry_version", 0)

    @property
    def proposer_order(self) -> List[str]:
        """Get the ordered list of proposer IDs for the default domain."""
        domain_config = self.manifest.get("domain", {})
        gr_config = domain_config.get("gr", {})
        return gr_config.get("proposer_order", [])

    @property
    def proposers(self) -> Dict[str, Any]:
        """Get all proposer configurations."""
        return self.manifest.get("proposers", {})

    def get_proposer(self, proposer_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific proposer's configuration.

        Args:
            proposer_id: The proposer identifier

        Returns:
            Proposer configuration dict or None
        """
        return self.proposers.get(proposer_id)

    def get_proposer_order(self, domain: str = "gr") -> List[str]:
        """Get the proposer order for a domain.

        Args:
            domain: The domain name

        Returns:
            Ordered list of proposer IDs
        """
        domain_config = self.manifest.get("domain", {})
        domain_data = domain_config.get(domain, {})
        return domain_data.get("proposer_order", [])

    def is_domain_enabled(self, domain: str) -> bool:
        """Check if a domain is enabled.

        Args:
            domain: The domain name

        Returns:
            True if enabled, False otherwise
        """
        domain_config = self.manifest.get("domain", {})
        domain_data = domain_config.get(domain, {})
        return domain_data.get("enabled", False)

    def get_domain_budget(self, domain: str) -> Dict[str, int]:
        """Get budget settings for a domain.

        Args:
            domain: The domain name

        Returns:
            Budget dict with limits
        """
        domain_config = self.manifest.get("domain", {})
        domain_data = domain_config.get(domain, {})
        budgets = domain_data.get("budgets", {})
        return {
            "max_wall_ms": budgets.get("max_wall_ms", 1000),
            "max_candidates": budgets.get("max_candidates", 16),
            "max_evidence_items": budgets.get("max_evidence_items", 100),
            "max_search_expansions": budgets.get("max_search_expansions", 50),
        }

    def _load(self) -> None:
        """Load the manifest from file."""
        if self._manifest_path is None:
            # Use default manifest in the package
            package_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self._manifest_path = os.path.join(package_dir, "registry", "manifest.yaml")

        if not os.path.exists(self._manifest_path):
            raise RegistryLoadError(self._manifest_path, f"File not found: {self._manifest_path}")

        try:
            with open(self._manifest_path, "r", encoding="utf-8") as f:
                content = f.read()
                # Normalize YAML for consistent hashing
                self._manifest = yaml.safe_load(content)
        except yaml.YAMLError as e:
            raise RegistryLoadError(self._manifest_path, f"YAML parse error: {e}")
        except IOError as e:
            raise RegistryLoadError(self._manifest_path, f"IO error: {e}")

    def _compute_hash(self) -> None:
        """Compute the registry hash from normalized manifest."""
        # Sort keys for deterministic hashing
        normalized = self._normalize_manifest(self.manifest)
        self._registry_hash = hash_registry(normalized)

    def _normalize_manifest(self, manifest: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize manifest for consistent hashing.

        Args:
            manifest: The manifest to normalize

        Returns:
            Normalized manifest dict
        """
        normalized = {
            "spec": manifest.get("spec", ""),
            "registry_name": manifest.get("registry_name", ""),
            "registry_version": manifest.get("registry_version", 0),
            "domain": {},
            "proposers": {},
        }

        # Normalize domain section
        for domain, domain_data in manifest.get("domain", {}).items():
            normalized["domain"][domain] = {
                "enabled": domain_data.get("enabled", False),
                "proposer_order": sorted(domain_data.get("proposer_order", [])),
                "budgets": domain_data.get("budgets", {}),
            }

        # Normalize proposers section
        for proposer_id, proposer_data in manifest.get("proposers", {}).items():
            normalized["proposers"][proposer_id] = {
                "module": proposer_data.get("module", ""),
                "entrypoint": proposer_data.get("entrypoint", "propose"),
                "candidate_types": sorted(proposer_data.get("candidate_types", [])),
                "max_outputs": proposer_data.get("max_outputs", 0),
                "budgets": proposer_data.get("budgets", {}),
            }

        return normalized

    def reload(self) -> None:
        """Reload the manifest from file."""
        self._manifest = None
        self._registry_hash = None
        self._proposer_cache = {}
        self._load()
        self._compute_hash()


def load_registry(manifest_path: Optional[str] = None) -> RegistryLoader:
    """Convenience function to load a registry.

    Args:
        manifest_path: Optional path to manifest file

    Returns:
        Loaded RegistryLoader instance
    """
    loader = RegistryLoader(manifest_path)
    # Force loading
    _ = loader.manifest
    _ = loader.registry_hash
    return loader
