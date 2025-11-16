# backend/main.py
import time
import random
import logging
import json
import subprocess
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

# Algorithms (your existing modules)
from algorithms.fifo import fifo
from algorithms.lru import lru
from algorithms.optimal import optimal

# Hypervisor class (your existing file)
from hypervisor import Hypervisor

# ---- Logging ----
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("backend")

# ---- Flask app ----
app = Flask(__name__)
CORS(app)

# ---- Instantiate hypervisor ----
hypervisor = Hypervisor(total_frames=100, db=None)

# Try to load vm_users.json (optional)
try:
    with open("vm_users.json", "r") as f:
        vm_defs = json.load(f)
    for vm in vm_defs:
        try:
            hypervisor.create_vm(
                vm_id=vm["vmId"],
                os_name=vm.get("osName", "SimOS"),
                algorithm=vm.get("algorithm", "FIFO"),
                frames=int(vm.get("frames", 1)),
                users=vm.get("users", []),
            )
            logger.info(f"Loaded VM from vm_users.json: {vm['vmId']}")
        except Exception as e:
            logger.warning(f"Skipping VM {vm.get('vmId')}: {e}")
except FileNotFoundError:
    logger.info("vm_users.json not found, continuing without it.")
except Exception as e:
    logger.exception("Error loading vm_users.json: %s", e)

# ---- CPU history (rolling) ----
cpu_history = [
    {"time": datetime.now().strftime("%H:%M:%S"), "usage": random.randint(20, 70)}
    for _ in range(5)
]
last_cpu_update = time.time()


# ---- Helper to get logged-in users (uses 'who') ----
def get_logged_in_users():
    try:
        out = subprocess.getoutput("who")
        users = [line.split()[0] for line in out.splitlines() if line.strip()]
        return list(sorted(set(users)))
    except Exception:
        return []


# ---- Endpoint: basic check ----
@app.route("/")
def home():
    return {"message": "Flask backend is running successfully!"}


# ---- Endpoint: vitals (single unified) ----
@app.route("/api/vitals", methods=["GET"])
def vitals():
    global cpu_history, last_cpu_update

    # update rolling CPU history every ~3 seconds
    if time.time() - last_cpu_update >= 3:
        last_cpu_update = time.time()
        cpu_history = cpu_history[1:] + [
            {"time": datetime.now().strftime("%H:%M:%S"), "usage": random.randint(20, 90)}
        ]

    # Build vm_list from hypervisor internal state (with simulated metrics)
    vm_list = []
    for vm in hypervisor.list_vms():
        vm_list.append(
            {
                "id": vm["vm_id"] if "vm_id" in vm else vm.get("vmId", "unknown"),
                "name": vm.get("vm_id", vm.get("vmId", "vm")),
                "os": vm.get("os_name", vm.get("osName", vm.get("os", "SimOS"))),
                "user": vm.get("users", [{}])[0].get("username", "-") if vm.get("users") else "-",
                "cpu": round(random.uniform(5, 95), 1),
                "memory": round(random.uniform(1, float(vm.get("frames", 1))), 2),
                "status": vm.get("status", "Running"),
            }
        )

    # Summary: aggregate
    summary = {
        "activeVMs": len([v for v in vm_list if v["status"] == "Running"]),
        "totalVMs": len(vm_list),
        "totalUsers": sum(len(vm.get("users", [])) for vm in hypervisor.list_vms()),
        "overallCpuUsage": cpu_history[-1]["usage"] if cpu_history else 0,
        # Using frames to approximate memory used on hypervisor demo
        "overallMemoryUsageGB": sum(vm.get("frames", 0) for vm in hypervisor.list_vms()),
        "totalMemoryGB": hypervisor.total_frames,
    }

    return jsonify({"summary": summary, "vmList": vm_list, "cpuHistory": cpu_history})


# ---- Algorithm runner endpoint (Option A: backend runs algorithms) ----
ALGO_MAP = {
    "FIFO": fifo,
    "LRU": lru,
    "OPTIMAL": optimal,
    # you can add more: "CLOCK": clock_func, ...
}


@app.route("/api/algorithm/run", methods=["POST"])
def run_algorithm():
    data = request.get_json()
    algo = data.get("algorithm", "FIFO").upper()
    frames = int(data.get("frames", 3))
    reference_string = list(map(int, data.get("referenceString", "").split()))
    process_id = data.get("processId", "process-1")

    if algo == "FIFO":
        result = fifo(process_id, frames, reference_string, frames)
    elif algo == "LRU":
        result = lru(process_id, frames, reference_string, frames)
    elif algo == "OPTIMAL":
        result = optimal(process_id, frames, reference_string, frames)
    else:
        return jsonify({"ok": False, "error": "Invalid algorithm"})

    return jsonify({"ok": True, "result": result})


# ---- VM / Hypervisor management endpoints (re-using hypervisor object) ----
@app.route("/api/vm/create", methods=["POST"])
def api_create_vm():
    data = request.get_json() or {}
    try:
        vm = hypervisor.create_vm(
            vm_id=data["vmId"],
            os_name=data.get("osName", "SimOS"),
            algorithm=data.get("algorithm", "FIFO"),
            frames=int(data.get("frames", 1)),
            users=data.get("users", []),
        )
        return jsonify({"ok": True, "vm": vm})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/api/vm/list", methods=["GET"])
def api_list_vms():
    return jsonify({"vms": hypervisor.list_vms()})


@app.route("/api/vm/delete", methods=["POST"])
def api_delete_vm():
    data = request.get_json() or {}
    try:
        vm = hypervisor.delete_vm(data["vmId"])
        return jsonify({"ok": True, "vm": vm})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/api/vm/run", methods=["POST"])
def api_run_vm():
    data = request.get_json() or {}
    try:
        vm_id = data["vmId"]
        reference_string = data["referenceString"]
        user = data.get("user")
        result = hypervisor.run_vm(vm_id, reference_string, user=user)
        return jsonify({"ok": True, "result": result})
    except Exception as e:
        logger.exception("vm_run failed")
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/api/vm/login", methods=["POST"])
def api_vm_login():
    data = request.get_json() or {}
    try:
        vm_id = data["vmId"]
        username = data["username"]
        password = data["password"]
        token = hypervisor.vm_login(vm_id, username, password)
        return jsonify({"ok": True, "result": token})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/api/hypervisor/reallocate", methods=["POST"])
def api_reallocate():
    data = request.get_json() or {}
    try:
        res = hypervisor.reallocate_frames(data["fromVm"], data["toVm"], int(data["frames"]))
        return jsonify({"ok": True, "result": res})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/api/hypervisor/stats", methods=["GET"])
def api_stats():
    stats = {
        "total_frames": hypervisor.total_frames,
        "allocated_frames": hypervisor._allocated_frames(),
        "vms": hypervisor.list_vms(),
    }
    return jsonify(stats)


# ---- Run app ----
if __name__ == "__main__":
    logger.info("Starting Flask backend on 0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
