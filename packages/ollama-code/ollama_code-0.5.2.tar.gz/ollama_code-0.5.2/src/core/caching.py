#!/usr/bin/env python3
"""
Caching-Modul für Atlas Code
Verwaltet Session-Cache, Context-Snapshots und Token-Zählung.
"""

import json
import re
import uuid
import hashlib
import threading
import time
from pathlib import Path
from datetime import datetime
from functools import lru_cache
from typing import Dict, List, Any

from src.config import CACHE_DIR, SESSIONS_DIR, CONTEXT_CACHE_DIR, MODEL_CACHE_DIR, MODEL_NAME, MAX_CONVERSATION_LENGTH

# Globale Cache-Variablen
conversation_cache: List[Dict[str, Any]] = []
cache_lock = threading.RLock()
current_session_id = str(uuid.uuid4())
cache_metadata = {}

def initialize_cache():
    """Initialisiert den Cache und die Metadaten für eine neue Session."""
    global current_session_id, cache_metadata, conversation_cache
    
    current_session_id = str(uuid.uuid4())
    conversation_cache = []
    
    cache_metadata = {
        "session_id": current_session_id,
        "created_at": datetime.now().isoformat(),
        "model_name": MODEL_NAME,
        "version": "2.1_modular", # Neue Version
        "context_windows": [],
        "performance_stats": {},
        "cache_hits": 0,
    }
    
    for cache_dir in [CACHE_DIR, SESSIONS_DIR, CONTEXT_CACHE_DIR, MODEL_CACHE_DIR]:
        cache_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"📝 Neue Session initialisiert: {current_session_id[:8]}")

def realistic_token_count(text: str) -> int:
    """Realistische Token-Zählung basierend auf GPT-ähnlicher Tokenisierung."""
    if not isinstance(text, str):
        text = str(text)
    if not text.strip():
        return 0
    
    token_pattern = r'''[a-zA-ZäöüÄÖÜß]+(?:'[a-zA-Z]+)?|\d+(?:\.\d+)?|[^\w\s]|\s+'''
    tokens = re.findall(token_pattern, text, re.VERBOSE)
    tokens = [t for t in tokens if t.strip()]
    
    token_count = 0
    for token in tokens:
        if len(token) > 8 and token.isalpha():
            token_count += max(1, len(token) // 4)
        elif token.strip():
            token_count += 1
    
    min_tokens = max(1, len(text) // 4)
    return max(token_count, min_tokens)

@lru_cache(maxsize=1)
def get_cache_hash(content: str) -> str:
    """Erstellt eindeutigen Hash für Cache-Keys"""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]

def save_session_cache(token_start_time, total_tokens):
    """Speichert den aktuellen Session-Cache."""
    with cache_lock:
        try:
            session_file = SESSIONS_DIR / f"session_{current_session_id}.json"
            current_session_file = CACHE_DIR / "current_session.json"
            
            performance_stats = {
                "total_tokens": total_tokens,
                "conversation_length": len(conversation_cache),
                "session_duration": time.time() - (token_start_time or time.time())
            }
            
            session_data = {
                "session_id": current_session_id,
                "created_at": cache_metadata["created_at"],
                "updated_at": datetime.now().isoformat(),
                "model_name": cache_metadata["model_name"],
                "version": cache_metadata["version"],
                "conversation_cache": conversation_cache,
                "performance_stats": performance_stats
            }
            
            temp_file = session_file.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)
            temp_file.replace(session_file)
            
            current_session_ref = {
                "current_session_id": current_session_id,
                "session_file": str(session_file),
                "last_updated": datetime.now().isoformat()
            }
            with open(current_session_file, 'w', encoding='utf-8') as f:
                json.dump(current_session_ref, f, indent=2)

            print(f"💾 Session gespeichert: {len(conversation_cache)} Nachrichten, ID: {current_session_id[:8]}")
        except Exception as e:
            print(f"⚠️ Cache-Speicherung fehlgeschlagen: {e}")

def load_session_cache(session_id: str = None) -> bool:
    """Lädt einen Session-Cache."""
    global conversation_cache, current_session_id, cache_metadata
    
    with cache_lock:
        target_session_id = session_id or get_last_session_id()
        if not target_session_id:
            initialize_cache()
            return False
            
        session_file = SESSIONS_DIR / f"session_{target_session_id}.json"
        if not session_file.exists():
            print(f"⚠️ Session-Datei nicht gefunden: {target_session_id[:8]}")
            initialize_cache()
            return False
            
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            # Reset und lade Daten
            initialize_cache()
            current_session_id = session_data.get("session_id", current_session_id)
            conversation_cache = session_data.get("conversation_cache", [])
            cache_metadata.update(session_data)
            
            print(f"🔄 Session geladen: {len(conversation_cache)} Nachrichten, ID: {current_session_id[:8]}")
            return True
        except Exception as e:
            print(f"⚠️ Cache-Laden fehlgeschlagen: {e}")
            initialize_cache()
            return False

def get_last_session_id() -> str:
    """Ermittelt die letzte Session-ID."""
    current_session_file = CACHE_DIR / "current_session.json"
    try:
        if current_session_file.exists():
            with open(current_session_file, 'r', encoding='utf-8') as f:
                return json.load(f).get("current_session_id")
    except Exception:
        return None
    return None

def clear_session_cache(all_sessions: bool = False):
    """Löscht den Session-Cache."""
    with cache_lock:
        if all_sessions:
            for f in SESSIONS_DIR.glob("*.json"):
                f.unlink()
            for f in CONTEXT_CACHE_DIR.glob("*.json"):
                f.unlink()
            current_session_file = CACHE_DIR / "current_session.json"
            if current_session_file.exists():
                current_session_file.unlink()
            print("🗑️ Alle Session-Caches geleert")
        else:
            session_file = SESSIONS_DIR / f"session_{current_session_id}.json"
            if session_file.exists():
                session_file.unlink()
            print(f"🗑️ Aktuelle Session geleert: {current_session_id[:8]}")
        
        # Initialisiere eine saubere, neue Session
        initialize_cache()
        return True

def get_cache_stats() -> dict:
    """Gibt erweiterte Cache-Statistiken zurück."""
    try:
        return {
            "session_id": current_session_id,
            "total_sessions": len(list(SESSIONS_DIR.glob("session_*.json"))),
            "current_conversation_length": len(conversation_cache),
            "total_cache_size_mb": round(sum(f.stat().st_size for f in CACHE_DIR.rglob("*.json")) / 1024 / 1024, 2),
            "model_name": MODEL_NAME
        }
    except Exception as e:
        print(f"⚠️ Cache-Stats-Fehler: {e}")
        return {}