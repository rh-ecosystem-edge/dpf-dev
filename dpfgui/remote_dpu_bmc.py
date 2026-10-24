# Runs ON THE HYPERVISOR (piped to `python3 -`); standalone, python 3.9 compatible.
#
# Asks a DPU's own BMC (Redfish, as root) what Zero Trust needs from it: whether the root
# password works, the DPU's serial number, and whether rshim runs on the BMC. These are the
# endpoints DPF itself uses (Systems/Bluefield, Managers/Bluefield_BMC/Oem/Nvidia).
# The JSON arguments (base64) are substituted below rather than passed on the command line,
# so the password never shows up in `ps`.
import base64
import json
import socket
import ssl
import urllib.error
import urllib.request

A = json.loads(base64.b64decode("__ARGS__").decode())
CTX = ssl._create_unverified_context()
AUTH = "Basic " + base64.b64encode(("root:%s" % A["password"]).encode()).decode()


def get(path, tries=2):
    # BMCs answer logged-in requests slowly now and then: wait a while, and try twice.
    req = urllib.request.Request("https://%s%s" % (A["bmc"], path), headers={"Authorization": AUTH, "Accept": "application/json"})
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(req, context=CTX, timeout=30) as r:
                return json.load(r)
        except (socket.timeout, urllib.error.URLError) as e:
            if isinstance(e, urllib.error.HTTPError) or attempt == tries - 1:
                raise


out = {"auth": None, "serial": None, "model": None, "rshim": None, "error": None}
try:
    system = get("/redfish/v1/Systems/Bluefield")
    out["auth"] = True
    out["serial"] = (system.get("SerialNumber") or "").strip() or None
    out["model"] = system.get("Model")
    try:
        oem = get("/redfish/v1/Managers/Bluefield_BMC/Oem/Nvidia")
        out["rshim"] = (oem.get("BmcRShim") or {}).get("BmcRShimEnabled")
    except Exception:  # older BMC firmware: can't tell
        pass
except urllib.error.HTTPError as e:
    out["auth"] = False if e.code in (401, 403) else None
    out["error"] = "The BMC refused root's password" if e.code in (401, 403) else (
        "Not a BlueField BMC (no /redfish/v1/Systems/Bluefield)" if e.code == 404 else "BMC answered HTTP %d" % e.code)
except Exception as e:  # unreachable BMC, not Redfish, ...
    out["error"] = str(getattr(e, "reason", e))

print(json.dumps(out))
