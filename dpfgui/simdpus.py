"""Simulated DPUs from dpusimaas, for when you have no BlueField of your own.

A lease is a simulated DPU host on the lab LAN, with BMCs on an address of its own. Zero Trust: its
DPU's BMC (Redfish) and its host's (IPMI). Host-trusted: a host VM and its BMC (Redfish with
virtual media, and IPMI), which the cluster installs as a worker. Once DPF installs an OS on the
DPU, an aarch64 VM boots as it. To a deployment it looks like a lab DPU host. DPFGUI_DPUSIMAAS_URL
points elsewhere.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

URL = os.environ.get("DPFGUI_DPUSIMAAS_URL", "http://dpusimaas.tuchfeld.dev").rstrip("/")


class SimError(RuntimeError):
    pass


def _call(method: str, path: str, body: dict | None = None, timeout: float = 30):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(URL + path, data=data, method=method, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        try:
            msg = json.loads(e.read()).get("error")
        except ValueError:
            msg = None
        raise SimError(msg or f"dpusimaas answered HTTP {e.code}") from e
    except (urllib.error.URLError, OSError) as e:
        raise SimError(f"Can't reach dpusimaas at {URL}: {getattr(e, 'reason', e)}") from e


def info() -> dict:
    return _call("GET", "/v1/info")


def leases(owner: str) -> list[dict]:
    return _call("GET", f"/v1/dpus?owner={urllib.request.quote(owner)}")


def lease(owner: str, mode: str, bmc_password: str) -> dict:
    """A new simulated DPU (getting its address from DHCP takes a few seconds)."""
    return _call("POST", "/v1/dpus", {"owner": owner, "mode": mode, "bmc_password": bmc_password}, timeout=120)


def release(lease_id: str) -> None:
    _call("DELETE", f"/v1/dpus/{urllib.request.quote(lease_id)}", timeout=120)


def node_name(lease_id: str) -> str:
    """The WORKER_<n>_NAME of a simulated DPU host."""
    return f"sim-{lease_id}"
