#!/usr/bin/env python3
"""
Context Cache System - GPU-optimierter Cache für KI-Kontext
Kombiniert Performance-UI mit vollständigem KI-Kontext
"""

import json
import sqlite3
import hashlib
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from src import config

class ContextCache:
    def __init__(self):
        self.db_path = config.CACHE_DIR / "context_cache.db"
        self.session_id = None
        self.init_database()
        
    def init_database(self):
        """Initialisiert SQLite-Datenbank für Context-Cache"""
        config.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            # Erstelle Tabellen
            conn.execute("""
                CREATE TABLE IF NOT EXISTS context_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    message_id TEXT UNIQUE NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    ui_content TEXT NOT NULL,
                    token_count INTEGER DEFAULT 0,
                    timestamp REAL NOT NULL,
                    viewport_priority INTEGER DEFAULT 0
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS session_metadata (
                    session_id TEXT PRIMARY KEY,
                    total_tokens INTEGER DEFAULT 0,
                    message_count INTEGER DEFAULT 0,
                    last_updated REAL NOT NULL
                )
            """)
            
            # Erstelle Indizes separat
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_session_timestamp 
                ON context_messages (session_id, timestamp)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_session_priority 
                ON context_messages (session_id, viewport_priority)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_content_hash 
                ON context_messages (content_hash)
            """)
            
    def set_session(self, session_id: str):
        """Setzt aktuelle Session"""
        self.session_id = session_id
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO session_metadata 
                (session_id, total_tokens, message_count, last_updated)
                VALUES (?, 0, 0, ?)
            """, (session_id, time.time()))
            
    def add_message(self, message_id: str, role: str, content: str, 
                   ui_content: str, token_count: int = 0) -> bool:
        """Fügt Nachricht zum Context-Cache hinzu"""
        if not self.session_id:
            return False
            
        content_hash = hashlib.md5(content.encode()).hexdigest()
        timestamp = time.time()
        
        with sqlite3.connect(self.db_path) as conn:
            try:
                conn.execute("""
                    INSERT OR REPLACE INTO context_messages
                    (session_id, message_id, role, content, content_hash, 
                     ui_content, token_count, timestamp, viewport_priority)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
                """, (self.session_id, message_id, role, content, 
                      content_hash, ui_content, token_count, timestamp))
                
                # Update session metadata
                conn.execute("""
                    UPDATE session_metadata 
                    SET message_count = message_count + 1,
                        total_tokens = total_tokens + ?,
                        last_updated = ?
                    WHERE session_id = ?
                """, (token_count, timestamp, self.session_id))
                
                return True
            except Exception as e:
                print(f"❌ Context-Cache-Fehler: {e}")
                return False
                
    def get_ai_context(self, max_tokens: int = 120000) -> List[Dict[str, Any]]:
        """Holt vollständigen KI-Kontext (für AI-Anfragen)"""
        if not self.session_id:
            return []
            
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT role, content, token_count, timestamp
                FROM context_messages 
                WHERE session_id = ?
                ORDER BY timestamp ASC
            """, (self.session_id,))
            
            messages = []
            total_tokens = 0
            
            # Rückwärts durch Messages gehen (neueste zuerst)
            all_messages = list(cursor.fetchall())
            for row in reversed(all_messages):
                if total_tokens + row['token_count'] > max_tokens:
                    break
                    
                messages.insert(0, {
                    'role': row['role'],
                    'content': row['content'],
                    'token_count': row['token_count'],
                    'timestamp': row['timestamp']
                })
                total_tokens += row['token_count']
                
            print(f"🧠 AI-Context: {len(messages)} Nachrichten, {total_tokens} Tokens")
            return messages
            
    def get_viewport_messages(self, viewport_start: int, viewport_end: int, 
                            buffer_size: int = 5) -> List[Dict[str, Any]]:
        """Holt Nachrichten für Viewport + Buffer (für UI)"""
        if not self.session_id:
            return []
            
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # Berechne Sichtbarkeits-Range mit Buffer
            start_idx = max(0, viewport_start - buffer_size)
            end_idx = viewport_end + buffer_size
            
            cursor = conn.execute("""
                SELECT message_id, role, content, ui_content, viewport_priority, timestamp
                FROM context_messages 
                WHERE session_id = ?
                ORDER BY timestamp ASC
                LIMIT ? OFFSET ?
            """, (self.session_id, end_idx - start_idx, start_idx))
            
            messages = []
            for i, row in enumerate(cursor.fetchall()):
                actual_idx = start_idx + i
                
                # Bestimme ob vollständig oder komprimiert laden
                in_viewport = viewport_start <= actual_idx <= viewport_end
                in_buffer = (viewport_start - buffer_size <= actual_idx < viewport_start or 
                           viewport_end < actual_idx <= viewport_end + buffer_size)
                
                content = row['content'] if (in_viewport or in_buffer) else row['ui_content']
                priority = 100 if in_viewport else (50 if in_buffer else 0)
                
                messages.append({
                    'message_id': row['message_id'],
                    'role': row['role'],
                    'content': content,
                    'ui_content': row['ui_content'],
                    'priority': priority,
                    'compressed': not (in_viewport or in_buffer),
                    'timestamp': row['timestamp']
                })
                
            print(f"👁️ Viewport: {len(messages)} Nachrichten, Buffer: {buffer_size}")
            return messages
            
    def update_viewport_priorities(self, visible_message_ids: List[str]):
        """Aktualisiert Viewport-Prioritäten basierend auf Sichtbarkeit"""
        if not self.session_id:
            return
            
        with sqlite3.connect(self.db_path) as conn:
            # Reset alle Prioritäten
            conn.execute("""
                UPDATE context_messages 
                SET viewport_priority = 0 
                WHERE session_id = ?
            """, (self.session_id,))
            
            # Setze hohe Priorität für sichtbare Messages
            if visible_message_ids:
                placeholders = ','.join('?' * len(visible_message_ids))
                conn.execute(f"""
                    UPDATE context_messages 
                    SET viewport_priority = 100 
                    WHERE session_id = ? AND message_id IN ({placeholders})
                """, [self.session_id] + visible_message_ids)
                
    def compress_old_messages(self, keep_recent: int = 50):
        """Komprimiert alte Nachrichten für Performance"""
        if not self.session_id:
            return
            
        with sqlite3.connect(self.db_path) as conn:
            # Finde alte Nachrichten (außer letzten N)
            cursor = conn.execute("""
                SELECT message_id, content, ui_content
                FROM context_messages 
                WHERE session_id = ? AND viewport_priority = 0
                ORDER BY timestamp DESC
                OFFSET ?
            """, (self.session_id, keep_recent))
            
            compressed_count = 0
            for row in cursor.fetchall():
                # Erstelle komprimierte Version falls noch nicht vorhanden
                if len(row['ui_content']) > 100:
                    compressed = self._compress_content(row['content'])
                    conn.execute("""
                        UPDATE context_messages 
                        SET ui_content = ?
                        WHERE message_id = ?
                    """, (compressed, row['message_id']))
                    compressed_count += 1
                    
            print(f"🗜️ {compressed_count} Nachrichten komprimiert")
            
    def _compress_content(self, content: str) -> str:
        """Komprimiert Nachrichteninhalt für UI"""
        # Entferne HTML-Tags für Preview
        import re
        text = re.sub(r'<[^>]+>', '', content)
        
        # Erste Zeile oder erste 100 Zeichen
        lines = text.split('\n')
        first_line = lines[0] if lines else text
        
        preview = first_line[:100]
        if len(first_line) > 100:
            preview += '...'
            
        return f'<div class="compressed-message" title="Klicken zum Erweitern">{preview}</div>'
        
    def get_session_stats(self) -> Dict[str, Any]:
        """Gibt Session-Statistiken zurück"""
        if not self.session_id:
            return {}
            
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT total_tokens, message_count, last_updated
                FROM session_metadata 
                WHERE session_id = ?
            """, (self.session_id,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'session_id': self.session_id,
                    'total_tokens': row['total_tokens'],
                    'message_count': row['message_count'],
                    'last_updated': row['last_updated'],
                    'context_usage': min(100, (row['total_tokens'] / config.MAX_CONTEXT_TOKENS) * 100)
                }
            return {}

# Globale Instance
context_cache = ContextCache()