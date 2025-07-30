#!/usr/bin/env python3
"""
Session Manager & Intelligente Context-Rotation
(Früher: session_continuity.py)
"""

import sqlite3
import json
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import hashlib
import re
import requests

from src import config
from src.core.caching import realistic_token_count

class SessionManager:
    def __init__(self):
        self.db_path = config.CACHE_DIR / "session_continuity.db"
        self.lock = threading.RLock()
        self.context_limit = 75000
        self.rotation_threshold = 0.85
        self.min_rotation_interval = 600
        
        self.current_session_id = None
        self.last_rotation_time = 0
        self.rotation_in_progress = False
        
        self.conversation_cache: Optional[List[Dict]] = None
        
        self.performance_stats = {
            "total_rotations": 0,
            "avg_rotation_time": 0,
            "compression_ratios": [],
        }
        
        self._init_database()
        
    def set_conversation_cache_reference(self, cache_ref: List[Dict]):
        """Setzt die Referenz auf den globalen conversation_cache."""
        self.conversation_cache = cache_ref
        
    def _init_database(self):
        """Initialisiert die Session-Continuity-Database."""
        try:
            with sqlite3.connect(self.db_path, check_same_thread=False) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS session_continuity (
                        session_id TEXT PRIMARY KEY,
                        intelligent_summary TEXT,
                        current_context_version INTEGER DEFAULT 1,
                        last_rotation_timestamp TIMESTAMP,
                        total_rotations INTEGER DEFAULT 0,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS context_snapshots (
                        snapshot_id TEXT PRIMARY KEY,
                        session_id TEXT,
                        snapshot_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        conversation_before_rotation TEXT,
                        conversation_after_rotation TEXT,
                        compression_ratio REAL,
                        rotation_duration_ms INTEGER
                    )
                """)
                conn.commit()
        except Exception as e:
            print(f"❌ Database-Initialisierung fehlgeschlagen: {e}")
            raise
    
    def register_session(self, session_id: str):
        """Registriert eine neue oder fortgesetzte Session."""
        with self.lock:
            self.current_session_id = session_id
            try:
                with sqlite3.connect(self.db_path, check_same_thread=False) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT session_id FROM session_continuity WHERE session_id = ?", (session_id,))
                    if not cursor.fetchone():
                        cursor.execute("INSERT INTO session_continuity (session_id) VALUES (?)", (session_id,))
                        conn.commit()
                        print(f"🆕 Session in DB registriert: {session_id[:8]}")
                    else:
                        print(f"🔄 Session in DB fortgesetzt: {session_id[:8]}")
            except Exception as e:
                print(f"❌ Session-DB-Registrierung fehlgeschlagen: {e}")

    def should_rotate_context(self) -> Tuple[bool, str]:
        """Prüft, ob der Kontext rotiert werden sollte."""
        if self.rotation_in_progress or not self.conversation_cache:
            return False, "Nicht bereit für Rotation"
        
        if time.time() - self.last_rotation_time < self.min_rotation_interval:
            return False, f"Min-Intervall ({self.min_rotation_interval}s) nicht erreicht"
        
        current_context_length = sum(len(msg.get('content', '')) for msg in self.conversation_cache)
        usage_percentage = current_context_length / self.context_limit
        
        if usage_percentage >= self.rotation_threshold:
            return True, f"Context-Limit erreicht: {usage_percentage:.1%}"
        
        return False, f"Context-Nutzung: {usage_percentage:.1%}"

    def analyze_message_importance(self, message: Dict[str, Any]) -> float:
        """Bewertet die Wichtigkeit einer Nachricht."""
        content = message.get('content', '').lower()
        role = message.get('role', '')
        score = 0.0
        if role == 'user': score += 0.3
        if '```' in message.get('content', ''): score += 0.3
        if any(k in content for k in ['error', 'fehler', 'problem']): score += 0.25
        if any(k in content for k in ['erstelle', 'create', 'fix']): score += 0.2
        if len(content) > 200: score += 0.1
        return min(1.0, max(0.0, score))

    def create_intelligent_summary(self, conversation_history: List[Dict]) -> str:
        """Erstellt eine intelligente Zusammenfassung mit Ollama."""
        print("🧠 Erstelle intelligente Zusammenfassung...")
        preview = "\n".join([f"[{m.get('role', '?')}] {m.get('content', '')[:150]}..." for m in conversation_history[-15:]])
        prompt = f"Erstelle eine kompakte, technische Zusammenfassung der folgenden Konversation für den weiteren Kontext:\n\n{preview}"
        
        try:
            response_data = requests.post(
                f"{OLLAMA_URL}/api/generate",
                json={"model": MODEL_NAME, "prompt": prompt, "stream": False},
                timeout=30
            ).json()
            summary = response_data.get('response', '').strip()
            return summary if summary else self._create_fallback_summary(conversation_history)
        except Exception as e:
            print(f"⚠️ Ollama-Zusammenfassung fehlgeschlagen: {e}")
            return self._create_fallback_summary(conversation_history)

    def _create_fallback_summary(self, conversation_history: List[Dict]) -> str:
        """Erstellt eine regelbasierte Fallback-Zusammenfassung."""
        keywords = set()
        for msg in conversation_history:
            content = msg.get('content', '')
            keywords.update(re.findall(r'\b\w{5,}\b', content.lower()))
        return f"Zusammenfassung: Wichtige Themen waren {', '.join(list(keywords)[:10])}."

    def select_important_messages(self, conversation_history: List[Dict], target_count: int = 10) -> List[Dict]:
        """Wählt die wichtigsten Nachrichten für den neuen Kontext aus."""
        scored = sorted(
            [(self.analyze_message_importance(msg), i, msg) for i, msg in enumerate(conversation_history)],
            key=lambda x: x[0],
            reverse=True
        )
        
        # Nimm die wichtigsten, aber behalte die letzten 5 für den unmittelbaren Kontext
        important_indices = {item[1] for item in scored[:target_count]}
        recent_indices = set(range(len(conversation_history) - 5, len(conversation_history)))
        final_indices = sorted(list(important_indices | recent_indices))
        
        return [conversation_history[i] for i in final_indices]

    def perform_context_rotation(self) -> bool:
        """Führt die vollständige Kontext-Rotation durch."""
        if self.rotation_in_progress or not self.conversation_cache:
            return False
        
        self.rotation_in_progress = True
        rotation_start = time.time()
        
        try:
            print("🔄 Starte Context-Rotation...")
            conversation_before = list(self.conversation_cache)
            chars_before = sum(len(msg.get('content', '')) for msg in conversation_before)

            summary = self.create_intelligent_summary(conversation_before)
            important_messages = self.select_important_messages(conversation_before, target_count=8)

            new_context = [{
                "role": "system",
                "content": f"SESSION-ZUSAMMENFASSUNG:\n{summary}",
                "type": "context_summary"
            }]
            new_context.extend(important_messages)
            
            # Atomares Update des Caches
            self.conversation_cache.clear()
            self.conversation_cache.extend(new_context)

            chars_after = sum(len(msg.get('content', '')) for msg in self.conversation_cache)
            compression_ratio = chars_after / chars_before if chars_before > 0 else 1.0
            duration = time.time() - rotation_start

            self._save_rotation_to_db(conversation_before, self.conversation_cache, compression_ratio, duration)
            self.last_rotation_time = time.time()

            print(f"✅ Context-Rotation abgeschlossen in {duration:.2f}s")
            return True
        except Exception as e:
            print(f"❌ Context-Rotation fehlgeschlagen: {e}")
            # Rollback zum Zustand vor der Rotation
            self.conversation_cache.clear()
            self.conversation_cache.extend(conversation_before)
            return False
        finally:
            self.rotation_in_progress = False

    def _save_rotation_to_db(self, before: list, after: list, ratio: float, duration: float):
        """Speichert die Rotationsdaten in der Datenbank."""
        with self.lock, sqlite3.connect(self.db_path, check_same_thread=False) as conn:
            cursor = conn.cursor()
            snapshot_id = hashlib.md5(f"{self.current_session_id}_{time.time()}".encode()).hexdigest()
            cursor.execute("""
                INSERT INTO context_snapshots (snapshot_id, session_id, conversation_before_rotation, conversation_after_rotation, compression_ratio, rotation_duration_ms)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (snapshot_id, self.current_session_id, json.dumps(before), json.dumps(after), ratio, int(duration * 1000)))
            
            cursor.execute("""
                UPDATE session_continuity SET total_rotations = total_rotations + 1, current_context_version = current_context_version + 1, last_rotation_timestamp = CURRENT_TIMESTAMP WHERE session_id = ?
            """, (self.current_session_id,))
            conn.commit()

    def get_session_stats(self) -> Dict[str, Any]:
        """Gibt Statistiken zur aktuellen Session aus der DB zurück."""
        if not self.current_session_id: return {"available": False}
        with self.lock, sqlite3.connect(self.db_path, check_same_thread=False) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT total_rotations, current_context_version, last_rotation_timestamp FROM session_continuity WHERE session_id = ?", (self.current_session_id,))
            data = cursor.fetchone()
            if not data: return {"available": False}
            
            current_percentage = (sum(len(m['content']) for m in self.conversation_cache) / self.context_limit * 100) if self.conversation_cache else 0
            
            return {
                "available": True,
                "total_rotations": data[0],
                "context_version": data[1],
                "last_rotation": data[2],
                "current_percentage": current_percentage,
                "rotation_threshold": self.rotation_threshold * 100,
            }

    def cleanup_old_data(self, days_to_keep: int = 7):
        """Bereinigt alte DB-Einträge."""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        with self.lock, sqlite3.connect(self.db_path, check_same_thread=False) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM context_snapshots WHERE snapshot_timestamp < ?", (cutoff_date,))
            deleted_count = cursor.rowcount
            conn.commit()
            if deleted_count > 0:
                print(f"🧹 DB Cleanup: {deleted_count} alte Snapshots entfernt.")