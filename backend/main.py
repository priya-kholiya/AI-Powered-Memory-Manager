from flask import Flask, request, jsonify
from algorithms.fifo import fifo
from algorithms.lru import lru
from algorithms.optimal import optimal
from flask_cors import CORS
from flask_pymongo import PyMongo
from hypervisor import Hypervisor
import logging
logging.basicConfig(level=logging.DEBUG)
# -------------------- SETUP --------------------
app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return {"message": "Flask backend is running successfully!"}



hypervisor = Hypervisor(total_frames=100, db=None)

ALGO_MAP = {
    "FIFO": fifo,
    "LRU": lru,
    "OPTIMAL": optimal
}

# -------------------- EXISTING ENDPOINT --------------------
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
    summary = {
        "bestAlgorithm": None,
        "hitRatios": {},
        "faults": {},
        "message": ""
    }

    best_algo = None
    best_hit_ratio = -1
    best_faults = None

    for algo_name in algorithms:
        func = ALGO_MAP.get(algo_name.upper())
        if func:
            result = func(process_id, memory_size, reference_string, frames)
            results[algo_name.upper()] = result

            # Calculate hit ratio
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

    return jsonify({
        "ok": True,
        "results": results,
        "summary": summary
    })





# -------------------- NEW HYPERVISOR ENDPOINTS --------------------

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
        token = hypervisor.vm_login(vm_id, username, password)
        return jsonify({"ok": True, "token": token})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/api/hypervisor/reallocate", methods=["POST"])
def api_reallocate():
    data = request.get_json()
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
