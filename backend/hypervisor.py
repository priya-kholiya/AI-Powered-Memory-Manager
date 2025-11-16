# backend/hypervisor.py
import bcrypt
import uuid
import time
from werkzeug.security import check_password_hash

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

    def _allocated_frames(self):
        return sum(vm["frames"] for vm in self.vms.values())

    def create_vm(self, vm_id, os_name, algorithm, frames, users):
        if vm_id in self.vms:
            raise ValueError("VM already exists")

        if self._allocated_frames() + frames > self.total_frames:
            raise ValueError("Not enough frames available")

        # ensure loader passed password_hash for each user
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

    def _check_password_compat(self, stored_hash, password):
        """
        Unified password check helper:
         - If stored_hash looks like werkzeug pbkdf2 (contains 'pbkdf2'), use check_password_hash.
         - Else try bcrypt (stored as string).
         - Returns True/False.
        """
        if not stored_hash:
            return False

        # If it's not a string, try to decode bytes
        if isinstance(stored_hash, bytes):
            stored_hash = stored_hash.decode()

        try:
            if isinstance(stored_hash, str) and "pbkdf2" in stored_hash:
                return check_password_hash(stored_hash, password)
            else:
                # assume bcrypt stored hash: bcrypt wants bytes
                try:
                    return bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8"))
                except Exception:
                    # if stored_hash is already bytes
                    return bcrypt.checkpw(password.encode("utf-8"), stored_hash)
        except Exception:
            return False

    def login(self, vm_id: str, username: str, password: str):
        vm = self.vms.get(vm_id)
        if not vm:
            raise ValueError("VM not found")

        for u in vm["users"]:
            if u["username"] == username:
                stored_hash = u.get("password_hash")
                valid = self._check_password_compat(stored_hash, password)
                if valid:
                    token = str(uuid.uuid4())
                    vm["active_tokens"][token] = {
                        "username": username,
                        "role": u.get("role"),
                        "login_time": time.time()
                    }
                    return {
                        "token": token,
                        "username": username,
                        "vmId": vm_id,
                        "role": u.get("role")
                    }
                raise ValueError("Invalid password")

        raise ValueError("Invalid username")

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
        if not func:
            raise ValueError("Unsupported algorithm: " + str(algo))

        return func(
            process_id=vm_id,
            memory_size=vm["frames"],
            reference_string=reference_string,
            frames=vm["frames"]
        )
        
        
    def list_vms(self):
        """
        Return a list of all VM dicts.
        """
        return list(self.vms.values())