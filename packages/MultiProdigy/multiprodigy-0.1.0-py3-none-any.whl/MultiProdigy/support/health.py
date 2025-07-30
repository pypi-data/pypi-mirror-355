def health_check() -> dict:
    return {
        "status": "ok",
        "agents_loaded": True,
        "memory_available": True,
        "ollama_installed": True  # You can later replace with a real check
    }
