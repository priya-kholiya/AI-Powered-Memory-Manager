from flask import Flask, request, jsonify
from algorithms.fifo import fifo
from algorithms.lru import lru
from algorithms.optimal import optimal
from flask_cors import CORS
from hypervisor import Hypervisor
import random,time
import logging
import json
import os

logging.basicConfig(level=logging.DEBUG)

# -------------------- SETUP --------------------
app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return {"message": "Flask backend is running successfully!"}

if not os.path.exists("vm_users.json"):
    with open("vm_users.json", "w") as f:
        json.dump([], f)   # create empty JSON list
        print("Created new vm_users.json")

with open("vm_users.json", "r") as f:
    vm_data = json.load(f)


# Initialize hypervisor
hypervisor = Hypervisor(total_frames=100, db=None)

for vm in vm_data:
    hypervisor.create_vm(
        vm_id=vm["vmId"],
        os_name=vm.get("osName", "SimOS"),
        algorithm=vm.get("algorithm", "FIFO"),
        frames=vm.get("frames", 1),
        users=vm.get("users", [])
    )
ALGO_MAP = {
    "FIFO": fifo,
    "LRU": lru,
    "OPTIMAL": optimal
}

# -------------------- MEMORY MANAGEMENT ENDPOINT --------------------
@app.route("/api/run", methods=["POST"])
def run_algorithms():
    data = request.get_json()
    app.logger.info(f"Received request: {data}")

    process_id = data.get("processId")
    memory_size = data.get("memorySize")
    reference_string = data.get("referenceString")
    frames = data.get("frames")
    algorithms = data.get("algorithms", [])

    results = {}
    summary = {"bestAlgorithm": None, "hitRatios": {}, "faults": {}, "message": ""}
    best_algo = None
    best_hit_ratio = -1
    best_faults = None

    for algo_name in algorithms:
        func = ALGO_MAP.get(algo_name.upper())
        if func:
            result = func(process_id, memory_size, reference_string, frames)
            results[algo_name.upper()] = result

            total_accesses = len(reference_string)
            hit_ratio = result["hits"] / total_accesses if total_accesses > 0 else 0
            summary["hitRatios"][algo_name.upper()] = round(hit_ratio * 100, 2)
            summary["faults"][algo_name.upper()] = result["pageFaults"]

            if hit_ratio > best_hit_ratio:
                best_hit_ratio = hit_ratio
                best_algo = algo_name.upper()
                best_faults = result["pageFaults"]
        else:
            results[algo_name.upper()] = {"error": "Algorithm not found"}

    if best_algo:
        summary["bestAlgorithm"] = best_algo
        summary["message"] = (
            f"{best_algo} performed best with a hit ratio of "
            f"{round(best_hit_ratio * 100, 2)}% and only {best_faults} page faults."
        )
    else:
        summary["message"] = "No valid algorithms were provided."

    return jsonify({"ok": True, "results": results, "summary": summary})


cpu_history = [
    {"time": "00:00:01", "usage": 40},
    {"time": "00:00:02", "usage": 42},
    {"time": "00:00:03", "usage": 41},
]

last_update = time.time()

@app.route("/api/vitals", methods=["GET"])
def vitals():
    global cpu_history, last_update

    # --- CPU HISTORY UPDATE ---
    if time.time() - last_update >= 3:
        last_update = time.time()
        cpu_history = cpu_history[1:] + [{
            "time": time.strftime("%H:%M:%S"),
            "usage": random.randint(30, 90)
        }]

    # --- BUILD VM LIST FROM HYPERVISOR ---
    vm_list = []
    for vm_id, vm in hypervisor.vms.items():
        vm_list.append({
            "id": vm_id,
            "name": vm_id,
            "os": vm["osName"],
            "user": vm["users"][0]["username"] if vm["users"] else "-",
            "cpu": random.uniform(5, 95),
            "memory": random.uniform(1, vm["frames"]),
            "status": "Running"
        })

    # --- SUMMARY ---
    summary = {
        "activeVMs": len(vm_list),
        "totalVMs": len(vm_list),
        "totalUsers": sum(len(vm["users"]) for vm in hypervisor.vms.values()),
        "overallCpuUsage": cpu_history[-1]["usage"],
        "overallMemoryUsageGB": sum(vm["frames"] for vm in hypervisor.vms.values()),
        "totalMemoryGB": hypervisor.total_frames,
    }

    return jsonify({
        "summary": summary,
        "vmList": vm_list,
        "cpuHistory": cpu_history
    })

# -------------------- HYPERVISOR / VM ENDPOINTS --------------------
@app.route("/api/vm/create", methods=["POST"])
def api_create_vm():
    data = request.get_json()
    try:
        vm = hypervisor.create_vm(
            vm_id=data["vmId"],
            os_name=data.get("osName", "SimOS"),
            algorithm=data.get("algorithm", "FIFO"),
            frames=int(data.get("frames", 1)),
            users=data.get("users", [])
        )
        app.logger.info(f"Created VM: {vm}")
        return jsonify({"ok": True, "vm": vm})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400

@app.route("/api/vm/list", methods=["GET"])
def api_list_vms():
    return jsonify({"vms": hypervisor.list_vms()})

@app.route("/api/vm/delete", methods=["POST"])
def api_delete_vm():
    data = request.get_json()
    try:
        vm = hypervisor.delete_vm(data["vmId"])
        app.logger.info(f"Deleted VM: {vm}")
        return jsonify({"ok": True, "vm": vm})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400

@app.route("/api/vm/run", methods=["POST"])
def api_run_vm():
    data = request.get_json()
    try:
        vm_id = data["vmId"]
        reference_string = data["referenceString"]
        user = data.get("user")
        result = hypervisor.run_vm(vm_id, reference_string, user=user)
        return jsonify({"ok": True, "result": result})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400

@app.route("/api/vm/login", methods=["POST"])
def api_vm_login():
    data = request.get_json()
    try:
        vm_id = data["vmId"]
        username = data["username"]
        password = data["password"]

        result = hypervisor.login(vm_id, username, password)
        return jsonify({"ok": True, "result": result})

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400
    
@app.route("/api/vm/logout", methods=["POST"])
def api_vm_logout():
    data = request.get_json()
    try:
        result = hypervisor.logout(
            vm_id=data["vmId"],
            username=data["username"],
            token=data["token"]
        )
        return jsonify({"ok": True, "result": result})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/api/hypervisor/reallocate", methods=["POST"])
def api_reallocate():
    data = request.get_json()

    vm_id = data.get("vmId")
    user = data.get("user")

    # Validate admin
    vm = hypervisor.vms.get(vm_id)
    token = user.get("token")

    if token not in vm["active_tokens"]:
        return jsonify({"ok": False, "error": "Invalid token"}), 403

    role = vm["active_tokens"][token]["role"]
    if role != "admin":
        return jsonify({"ok": False, "error": "Only admin can reallocate frames"}), 403

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
        "vms": hypervisor.list_vms()
    }
    return jsonify(stats)

# -------------------- RUN APP --------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
