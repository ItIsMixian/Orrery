"""Platform-neutral Project Orrery contracts."""

from .manifests import ReleaseContract, build_project_manifest, default_release_contract, read_json_object
from .schema import DOCUMENT_SCHEMA, PROJECT_MANIFEST_FORMAT, REQUIRED_SCAFFOLD_FILES
from .templates import authority_template_root, iter_authority_assets, rendered_bytes, rendered_content

__version__ = "0.1.9"
CORE_API_VERSION = 1

__all__ = [
    "CORE_API_VERSION",
    "DOCUMENT_SCHEMA",
    "PROJECT_MANIFEST_FORMAT",
    "REQUIRED_SCAFFOLD_FILES",
    "ReleaseContract",
    "authority_template_root",
    "build_project_manifest",
    "default_release_contract",
    "iter_authority_assets",
    "read_json_object",
    "rendered_bytes",
    "rendered_content",
]
