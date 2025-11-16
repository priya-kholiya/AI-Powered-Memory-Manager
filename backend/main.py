# backend/main.py
import time
import random
import logging
import json
import subprocess
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from werkzeug.security import check_password_hash, generate_password_hash

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
CORS(app, resources={r"/api/*": {"origins": "*"}})

# ---- Instantiate hypervisor ----
hypervisor = Hypervisor(total_frames=100, db=None)


def load_vm_users():
    """
    Loads VM definitions from vm_users.json and creates VMs in hypervisor.
    Accepts either:
      - a list of VM objects (legacy)
      - or an object with key "vms": [...]
    Each user entry should contain either:
      - password_hash (Werkzeug pbkdf2 or bcrypt string)
      - or password (raw) -> we will hash with werkzeug PBKDF2
    """
    json_path = os.path.join(os.path.dirname(__file__), "vm_users.json")
    logger.info("===== VM LOADER =====")
    logger.info("Looking for vm_users.json at: %s", json_path)

    if not os.path.exists(json_path):
        logger.error("vm_users.json NOT FOUND!")
        return

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            content = json.load(f)
    except Exception as e:
        logger.exception("Error reading vm_users.json: %s", e)
        return

    # Accept either a list or an object with "vms" key for flexibility
    if isinstance(content, list):
        vm_list = content
    elif isinstance(content, dict) and "vms" in content:
        vm_list = content["vms"]
    else:
        logger.error("vm_users.json must be a list or an object with key 'vms'")
        return

    for vm in vm_list:
        try:
            processed_users = []

            for user in vm.get("users", []):
                username = user.get("username")
                if not username:
                    raise ValueError("Each user must have a username")

                # Prefer an explicit password_hash field
                if "password_hash" in user and user["password_hash"]:
                    hashed = user["password_hash"]
                # If raw password provided (dev only), hash with werkzeug PBKDF2
                elif "password" in user and user["password"]:
                    hashed = generate_password_hash(user["password"], method="pbkdf2:sha256")
                    logger.info("Generated PBKDF2 hash for user %s (dev-only flow)", username)
                else:
                    raise ValueError("User must contain 'password_hash' or 'password'")

                processed_users.append({
                    "username": username,
                    "role": user.get("role", "user"),
                    "password_hash": hashed
                })

            hypervisor.create_vm(
                vm_id=vm["vmId"],
                os_name=vm.get("osName", "SimOS"),
                algorithm=vm.get("algorithm", "FIFO"),
                frames=int(vm.get("frames", 1)),
                users=processed_users,
            )
            logger.info("✔ Loaded VM: %s with %d users", vm["vmId"], len(processed_users))

        except Exception as e:
            logger.exception("Error loading VM %s: %s", vm.get("vmId", "<unknown>"), e)

    logger.info("===== LOADED VMs =====")
    logger.info("%s", json.dumps(hypervisor.vms, indent=2))


# Load on startup
load_vm_users()


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


@app.route("/")
def home():
    return {"message": "Flask backend is running successfully!"}


@app.route("/api/vitals", methods=["GET"])
def vitals():
    global cpu_history, last_cpu_update

    if time.time() - last_cpu_update >= 3:
        last_cpu_update = time.time()
        cpu_history = cpu_history[1:] + [
            {"time": datetime.now().strftime("%H:%M:%S"), "usage": random.randint(20, 90)}
        ]

    vm_list = []
    for vm in hypervisor.list_vms():
        vm_list.append(
            {
                "id": vm["vmId"],
                "name": vm.get("osName", vm.get("vmId", "vm")),
                "os": vm.get("osName", "SimOS"),
                "user": vm.get("users", [{}])[0].get("username", "-") if vm.get("users") else "-",
                "cpu": round(random.uniform(5, 95), 1),
                "memory": round(random.uniform(1, float(vm.get("frames", 1))), 2),
                "status": vm.get("status", "Running"),
            }
        )

    summary = {
        "activeVMs": len([v for v in vm_list if v["status"] == "Running"]),
        "totalVMs": len(vm_list),
        "totalUsers": sum(len(vm.get("users", [])) for vm in hypervisor.list_vms()),
        "overallCpuUsage": cpu_history[-1]["usage"] if cpu_history else 0,
        "overallMemoryUsageGB": sum(vm.get("frames", 0) for vm in hypervisor.list_vms()),
        "totalMemoryGB": hypervisor.total_frames,
    }

    return jsonify({"summary": summary, "vmList": vm_list, "cpuHistory": cpu_history})


ALGO_MAP = {
    "FIFO": fifo,
    "LRU": lru,
    "OPTIMAL": optimal,
}


@app.route("/api/algorithm/run", methods=["POST"])
def run_algorithm():
    data = request.get_json() or {}
    algo = data.get("algorithm", "FIFO").upper()
    frames = int(data.get("frames", 3))
    ref_str_raw = data.get("referenceString", "")
    reference_string = []
    if isinstance(ref_str_raw, str) and ref_str_raw.strip():
        reference_string = list(map(int, ref_str_raw.split()))
    elif isinstance(ref_str_raw, list):
        reference_string = list(map(int, ref_str_raw))

    process_id = data.get("processId", "process-1")

    func = ALGO_MAP.get(algo)
    if not func:
        return jsonify({"ok": False, "error": "Invalid algorithm"}), 400

    result = func(process_id, frames, reference_string, frames)
    return jsonify({"ok": True, "result": result})


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    print("\n=== LOGIN ATTEMPT ===")
    print("Username from client:", repr(username))
    print("Password from client:", repr(password))

    user_found = False

    for vm_id, vm in hypervisor.vms.items():
        print(f"\nChecking VM: {vm_id}")

        for user in vm["users"]:
            print("  → Comparing with user:", user["username"])

            if user["username"] == username:
                user_found = True
                stored = user["password_hash"]

                print("    Stored hash:", stored)
                print("    Hash type:", "pbkdf2" if stored.startswith("pbkdf2") else "UNKNOWN")
                print("    Attempting hash verify...")

                try:
                    ok = check_password_hash(stored, password)
                except Exception as e:
                    print("    ERROR while verifying hash:", e)
                    ok = False

                print("    Hash match result:", ok)

                if ok:
                    print("✔ SUCCESS — password correct")
                    return jsonify({
                        "ok": True,
                        "user": {
                            "username": username,
                            "role": user["role"],
                            "vmId": vm_id
                        }
                    })

    if user_found:
        print("❌ PASSWORD MISMATCH for:", username)
        return jsonify({"ok": False, "error": "Invalid password"}), 401

    print("❌ USER NOT FOUND:", username)
    return jsonify({"ok": False, "error": "User not found"}), 401



# Additional endpoints re-used from your original file (unchanged):
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
        logger.exception("api_create_vm failed")
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
        token = hypervisor.login(vm_id, username, password)
        return jsonify({"ok": True, "result": token})
    except Exception as e:
        logger.exception("api_vm_login failed")
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


# small debug helper: verify an arbitrary hash vs password (dev only)
@app.route("/api/debug/hashcheck", methods=["POST"])
def debug_hashcheck():
    data = request.get_json() or {}
    hash_val = data.get("hash")
    pwd = data.get("password")
    if not hash_val or pwd is None:
        return jsonify({"ok": False, "error": "hash and password required"}), 400
    try:
        # try werkzeug first
        if isinstance(hash_val, str) and "pbkdf2" in hash_val:
            ok = check_password_hash(hash_val, pwd)
        else:
            ok = hypervisor._check_password_compat(hash_val, pwd)
        return jsonify({"ok": True, "match": bool(ok)})
    except Exception as e:
        logger.exception("debug hashcheck error")
        return jsonify({"ok": False, "error": str(e)}), 500


if __name__ == "__main__":
    logger.info("Starting Flask backend on 0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
