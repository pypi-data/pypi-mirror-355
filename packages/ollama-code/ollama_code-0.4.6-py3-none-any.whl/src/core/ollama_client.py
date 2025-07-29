#!/usr/bin/env python3
"""
Ollama Client Modul
Verwaltet die Kommunikation mit dem Ollama-Backend.
"""

import requests
from typing import Any
from src.config import OLLAMA_URL, MODEL_NAME

def call_ollama(prompt: str, stream: bool = True) -> Any:
    """Ruft das Ollama-Modell auf"""
    try:
        payload = {
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": 0.6,
                "top_p": 0.85,
                "max_tokens": 4096,
                "num_predict": -1,
                "repeat_penalty": 1.15,
                "typical_p": 1.0,
                "tfs_z": 1.0,
                "num_ctx": 8192,
                "num_batch": 512,
                "num_thread": 8
            },
            "keep_alive": "5m"
        }
        
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json=payload,
            stream=stream,
            timeout=None
        )
        
        response.raise_for_status() # Löst einen Fehler bei 4xx/5xx aus
        
        if stream:
            return response
        else:
            return response.json()
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Ollama-Verbindung fehlgeschlagen: {str(e)}")
        return {"error": f"Ollama-Verbindung fehlgeschlagen: {str(e)}"}