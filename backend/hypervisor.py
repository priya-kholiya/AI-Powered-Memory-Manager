# backend/hypervisor.py

import bcrypt
import uuid
import time
from algorithms.fifo import fifo
from algorithms.lru import lru
from algorithms.optimal import optimal

ALGO_MAP = {
    "FIFO": fifo,
    "LRU": lru,
    "OPTIMAL": optimal
}

class Hypervisor:
    def __init__(self, total_frames=100, db=None):
        self.total_frames = total_frames
        self.db = db
        self.vms = {}  # store all VM objects

    # ---------- INTERNAL UTIL ----------
    def _allocated_frames(self):
        return sum(vm["frames"] for vm in self.vms.values())

    # ---------- VM MANAGEMENT ----------
    def create_vm(self, vm_id, os_name, algorithm, frames, users):
        if vm_id in self.vms:
            raise ValueError("VM already exists")

        if self._allocated_frames() + frames > self.total_frames:
            raise ValueError("Not enough frames available")

        # Hash user passwords
        for user in users:
            user["password_hash"] = bcrypt.hashpw(
                user["password"].encode(), bcrypt.gensalt()
            ).decode()
            del user["password"]  # remove raw password

        self.vms[vm_id] = {
            "vmId": vm_id,
            "osName": os_name,
            "algorithm": algorithm.upper(),
            "frames": frames,
            "users": users,
            "active_tokens": {}
        }

        return self.vms[vm_id]

    def list_vms(self):
        return list(self.vms.values())

    def delete_vm(self, vm_id):
        if vm_id not in self.vms:
            raise ValueError("VM not found")
        deleted = self.vms[vm_id]
        del self.vms[vm_id]
        return deleted

    # ---------- VM LOGIN ----------
    def login(self, vm_id: str, username: str, password: str):
        vm = self.vms.get(vm_id)
        if not vm:
            raise ValueError("VM not found")
        for u in vm["users"]:
            if u["username"] == username:
                if bcrypt.checkpw(password.encode(), u["password_hash"].encode()):
                    token = str(uuid.uuid4())
                    vm["active_tokens"][token] = {
                        "username": username,
                        "role": u["role"],
                        "login_time": time.time()
                        }
                    return {
                        "token": token,
                        "username": username,
                        "vmId": vm_id,
                        "role": u["role"]
                        }
                else:
                    raise ValueError("Invalid password")

            raise ValueError("Invalid username")
        # ---------- VM LOGOUT ----------
    def logout(self, vm_id: str, username: str, token: str):
        vm = self.vms.get(vm_id)
        if not vm:
            raise ValueError("VM not found")

        # Token must exist
        if token not in vm["active_tokens"]:
            raise ValueError("Invalid token")

        # Token must belong to this user
        if vm["active_tokens"][token]["username"] != username:
            raise ValueError("Token does not belong to user")

        # Remove token (logout)
        del vm["active_tokens"][token]

        return {"message": "Logout successful", "vmId": vm_id, "username": username}


    # ---------- RUN VM ----------
    def run_vm(self, vm_id, reference_string, user=None):
        vm = self.vms.get(vm_id)
        if not vm:
            raise ValueError("VM not found")
        # Validate session token
        if user:
            token = user.get("token")
            username = user.get("username")
            if token not in vm["active_tokens"]:
                raise ValueError("Invalid or expired session token")

        # Get role
            user_role = vm["active_tokens"][token]["role"]

        # Restrict guest: only allow reference strings <= 5
            if user_role == "guest" and len(reference_string) > 5:
                raise ValueError("Guests can only run short simulations (<= 5 length)")

    # Run algorithm
        algo = vm["algorithm"]
        func = ALGO_MAP.get(algo)
        
        return func(
            process_id=vm_id,
            memory_size=vm["frames"],
            reference_string=reference_string,
            frames=vm["frames"]
            )


    # ---------- REALLOCATE FRAMES ----------
    def reallocate_frames(self, from_vm, to_vm, frames):
        if from_vm not in self.vms or to_vm not in self.vms:
            raise ValueError("VM not found")

        if self.vms[from_vm]["frames"] < frames:
            raise ValueError("Not enough frames to move")

        self.vms[from_vm]["frames"] -= frames
        self.vms[to_vm]["frames"] += frames

        return {
            "from": self.vms[from_vm],
            "to": self.vms[to_vm]
        }
