from .lakehouse import LakehouseSource
from .warehouse import WarehouseSource
from .base import BaseSource

_TYPE_MAP = {
    "lakehouse_tables": LakehouseSource,
    "data_warehouse": WarehouseSource,  # TODO: Add KQL and DAX support
}


def make_source(cfg: dict) -> BaseSource:
    """
    Build a concrete Source object from a Fabric datasource configuration.
    `cfg` must have at least keys: 'type', 'display_name'.
    """
    if "type" not in cfg or "display_name" not in cfg:
        raise ValueError("cfg must contain 'type' and 'display_name'")

    try:
        cls = _TYPE_MAP[cfg["type"]]
    except KeyError as exc:
        raise ValueError(f"Unsupported datasource type '{cfg['type']}'") from exc

    return cls(
        artifact_id_or_name = cfg.get("id") or cfg["display_name"], 
        workspace_id_or_name=cfg.get("workspace_id") or cfg.get("workspace_name"),
    )  # TODO:Pass the entire config for flexibility
