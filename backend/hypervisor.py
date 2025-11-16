# backend/hypervisor.py

import bcrypt
import uuid
import time
from werkzeug.security import check_password_hash  # supports pbkdf2, scrypt, etc.

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
        self.vms = {}

    # ---------- INTERNAL UTIL ----------
    def _allocated_frames(self):
        return sum(vm["frames"] for vm in self.vms.values())

    # ---------- VM MANAGEMENT ----------
    def create_vm(self, vm_id, os_name, algorithm, frames, users):
        if vm_id in self.vms:
            raise ValueError("VM already exists")

        if self._allocated_frames() + frames > self.total_frames:
            raise ValueError("Not enough frames available")

        # TRUST loader to give password_hash
        for user in users:
            if "password_hash" not in user:
                raise ValueError("User must contain password_hash")

        self.vms[vm_id] = {
            "vmId": vm_id,
            "osName": os_name,
            "algorithm": algorithm.upper(),
            "frames": frames,
            "users": users,
            "active_tokens": {}
        }

        return self.vms[vm_id]

    # ---------- VM LOGIN ----------
    def login(self, vm_id: str, username: str, password: str):
        vm = self.vms.get(vm_id)
        if not vm:
            raise ValueError("VM not found")

        for u in vm["users"]:
            if u["username"] == username:

                stored_hash = u["password_hash"]

                # SUPPORT BOTH bcrypt and Werkzeug hashes
                try:
                    # Check werkzeug style (pbkdf2:sha256)
                    if ":" in stored_hash:
                        valid = check_password_hash(stored_hash, password)
                    else:
                        # bcrypt
                        valid = bcrypt.checkpw(password.encode(), stored_hash.encode())
                except Exception:
                    valid = False

                if valid:
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

                raise ValueError("Invalid password")

        raise ValueError("Invalid username")

    # ---------- VM LOGOUT ----------
    def logout(self, vm_id: str, username: str, token: str):
        vm = self.vms.get(vm_id)
        if not vm:
            raise ValueError("VM not found")

        if token not in vm["active_tokens"]:
            raise ValueError("Invalid token")

        if vm["active_tokens"][token]["username"] != username:
            raise ValueError("Token does not belong to user")

        del vm["active_tokens"][token]
        return {"message": "Logout successful", "vmId": vm_id, "username": username}

    # ---------- RUN VM ----------
    def run_vm(self, vm_id, reference_string, user=None):
        vm = self.vms.get(vm_id)
        if not vm:
            raise ValueError("VM not found")

        if user:
            token = user.get("token")
            username = user.get("username")
            if token not in vm["active_tokens"]:
                raise ValueError("Invalid or expired session token")

            user_role = vm["active_tokens"][token]["role"]
            if user_role == "guest" and len(reference_string) > 5:
                raise ValueError("Guests can only run short simulations (<= 5 length)")

        algo = vm["algorithm"]
        func = ALGO_MAP.get(algo)

        return func(
            process_id=vm_id,
            memory_size=vm["frames"],
            reference_string=reference_string,
            frames=vm["frames"]
        )
