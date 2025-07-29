from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict, Optional

if TYPE_CHECKING:
    from kubernetes.client import V1PodSpec


_PRIMARY_CONTAINER_NAME_FIELD = "primary_container_name"
_PRIMARY_CONTAINER_DEFAULT_NAME = "primary"


@dataclass(init=True, repr=True, eq=True, frozen=False)
class PodTemplate(object):
    """Custom PodTemplate specification for a Task."""

    pod_spec: Optional["V1PodSpec"] = field(default_factory=lambda: V1PodSpec())
    primary_container_name: str = _PRIMARY_CONTAINER_DEFAULT_NAME
    labels: Optional[Dict[str, str]] = None
    annotations: Optional[Dict[str, str]] = None
