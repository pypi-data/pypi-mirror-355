import datetime
import psutil

def get_memory_payload():
    process = psutil.Process()
    mem = process.memory_info()
    return {
        "status": "ok",
        "message": "Ping successful",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "memory": {
            "rss": round(mem.rss / 1024 / 1024, 2),
            "heapUsed": round(mem.vms / 1024 / 1024, 2)
        }
    }

# Used across all frameworks
heimdall_ping_point = "__ping__/"
