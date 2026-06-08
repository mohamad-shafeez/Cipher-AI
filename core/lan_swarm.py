import subprocess
import requests
import config

class LANSwarm:
    # List of fallback secondary IP nodes on your local Wi-Fi/Ethernet network running Ollama
    # You can customize these IPs to match your secondary devices (e.g., 192.168.1.50)
    SWARM_NODES = [
        "http://192.168.1.15:11434",
        "http://192.168.1.20:11434"
    ]

    @classmethod
    def get_active_node(cls) -> str:
        """
        Dynamically pings local LAN nodes to find an available secondary device.
        Falls back to local host if no network swarm nodes respond within 1.5 seconds.
        """
        for node in cls.SWARM_NODES:
            try:
                # Lightweight handshake to check if the secondary node's Ollama engine is alive
                response = requests.get(f"{node}/api/tags", timeout=1.5)
                if response.status_code == 200:
                    print(f"📡 [LAN SWARM]: Secondary cluster node detected active at {node}!")
                    return node
            except Exception:
                continue
        
        # If no cluster nodes respond, return native local target
        return getattr(config, "OLLAMA_URL", "http://localhost:11434")

    @classmethod
    def dispatch_inference(cls, target_endpoint: str, payload: dict, local_timeout: int = 120) -> dict:
        """
        Routes an AI task (embeddings or vision) to the optimal network node.
        """
        base_node = cls.get_active_node()
        full_url = f"{base_node}{target_endpoint}"
        
        if "localhost" not in base_node:
            print(f"🔀 [COMPUTE OFFLOAD]: Offloading operational load to cluster target -> {full_url}")
        else:
            print(f"💻 [LOCAL COMPUTE]: Processing task natively on local hardware host...")

        response = requests.post(full_url, json=payload, timeout=local_timeout)
        return response
