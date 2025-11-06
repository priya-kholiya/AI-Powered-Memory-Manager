# backend/hypervisor.py
import time
from typing import Dict, Any
from algorithms.fifo import fifo
from algorithms.lru import lru
from algorithms.optimal import optimal
import bcrypt

ALGO_MAP = {
    "FIFO": fifo,
    "LRU": lru,
    "OPTIMAL": optimal
}

class Hypervisor:
    def __init__(self, total_frames: int = 100, db=None):
        """
        total_frames: total physical frames available on the host
        db: optional MongoDB client (flask_pymongo) to persist VMs and simulations
        """
        self.total_frames = total_frames
        self.db = db
        self.vms: Dict[str, Dict[str, Any]] = {}   # vm_id -> vm object

    # ---------------- VM lifecycle ----------------
    def create_vm(self, vm_id: str, os_name: str, algorithm: str, frames: int, users: list = None):
        if vm_id in self.vms:
            raise ValueError(f"VM {vm_id} already exists")

        if self._allocated_frames() + frames > self.total_frames:
            raise ValueError("Not enough free frames to allocate to this VM")

        users = users or []
        # hash passwords before storing
        stored_users = []
        for u in users:
            pw = u.get("password", "")
            pw_hash = bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()
            stored_users.append({"username": u["username"], "password_hash": pw_hash})

        vm = {
            "vm_id": vm_id,
            "os_name": os_name,
            "algorithm": algorithm.upper(),
            "frames": int(frames),
            "users": stored_users,
            "status": "idle",
            "last_result": None,
            "created_at": time.time()
        }
        self.vms[vm_id] = vm

        if self.db:
            # persist VM config
            self.db.db.vms.update_one({"vm_id": vm_id}, {"$set": vm}, upsert=True)

        return vm

    def delete_vm(self, vm_id: str):
        if vm_id not in self.vms:
            raise ValueError("VM not found")
        vm = self.vms.pop(vm_id)
        if self.db:
            self.db.db.vms.delete_one({"vm_id": vm_id})
            self.db.db.simulations.delete_many({"vm_id": vm_id})
        return vm

    def list_vms(self):
        return list(self.vms.values())

    def get_vm(self, vm_id: str):
        return self.vms.get(vm_id)

    def _allocated_frames(self):
        return sum(vm["frames"] for vm in self.vms.values())

    # ---------------- VM runtime operations ----------------
    def run_vm(self, vm_id: str, reference_string: list, user: str = None):
        """
        Runs the configured algorithm for vm_id on the given reference string.
        Stores results in vm['last_result'] and optionally in DB.simulations
        """
        vm = self.vms.get(vm_id)
        if not vm:
            raise ValueError("VM not found")

        algo_name = vm.get("algorithm", "FIFO")
        func = ALGO_MAP.get(algo_name)
        if not func:
            raise ValueError(f"Algorithm {algo_name} not supported")

        vm["status"] = "running"
        result = func(vm_id, None, reference_string, vm["frames"])  # memory_size not needed
        vm["last_result"] = result
        vm["status"] = "idle"

        # persist simulation if db present
        if self.db:
            sim_doc = {
                "vm_id": vm_id,
                "user": user,
                "reference_string": reference_string,
                "algorithm": algo_name,
                "frames": vm["frames"],
                "pageFaults": result.get("pageFaults"),
                "hits": result.get("hits"),
                "timestamp": time.time()
            }
            self.db.db.simulations.insert_one(sim_doc)

        return result

    # ---------------- simple reallocation ----------------
    def reallocate_frames(self, from_vm: str, to_vm: str, frames: int):
        if from_vm not in self.vms or to_vm not in self.vms:
            raise ValueError("One of the VMs not found")
        if frames <= 0:
            raise ValueError("frames must be > 0")

        if self.vms[from_vm]["frames"] < frames:
            raise ValueError("Not enough frames to remove from from_vm")

        self.vms[from_vm]["frames"] -= frames
        self.vms[to_vm]["frames"] += frames

        if self.db:
            self.db.db.vms.update_one({"vm_id": from_vm}, {"$set": {"frames": self.vms[from_vm]["frames"]}})
            self.db.db.vms.update_one({"vm_id": to_vm}, {"$set": {"frames": self.vms[to_vm]["frames"]}})

        return {"from": self.vms[from_vm], "to": self.vms[to_vm]}

    # ---------------- login helper ----------------
    def vm_login(self, vm_id: str, username: str, password: str):
        vm = self.vms.get(vm_id)
        if not vm:
            raise ValueError("VM not found")
        for u in vm["users"]:
            if u["username"] == username:
                if bcrypt.checkpw(password.encode(), u["password_hash"].encode()):
                    # produce a simple session token (for demo only)
                    token = bcrypt.hashpw(f"{vm_id}:{username}:{time.time()}".encode(), bcrypt.gensalt()).decode()
                    return {"token": token, "username": username, "vm_id": vm_id}
                else:
                    raise ValueError("Invalid password")
        raise ValueError("User not found")
