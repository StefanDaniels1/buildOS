"""
Custom Tools Loader

Loads enabled custom tools from SQLite database.
"""

import json
import sqlite3
from pathlib import Path
from typing import Dict, Any, List, Optional


def get_db_path() -> Path:
    """Get the path to the SQLite database."""
    # Database is in apps/server/events.db
    current_dir = Path(__file__).parent.parent
    db_path = current_dir / "apps" / "server" / "events.db"

    # Fallback to current working directory
    if not db_path.exists():
        db_path = Path.cwd() / "apps" / "server" / "events.db"

    # Docker path fallback
    if not db_path.exists():
        db_path = Path("/app/apps/server/events.db")

    return db_path


def load_enabled_tools() -> List[Dict[str, Any]]:
    """Load all enabled custom tools from database."""
    db_path = get_db_path()

    if not db_path.exists():
        print(f"Database not found at {db_path}, no custom tools loaded")
        return []

    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.execute("""
            SELECT id, name, description, input_schema, handler_code, enabled, env_vars, created_at, updated_at
            FROM custom_tools
            WHERE enabled = 1
            ORDER BY name
        """)

        tools = []
        for row in cursor.fetchall():
            tools.append({
                "id": row[0],
                "name": row[1],
                "description": row[2],
                "input_schema": json.loads(row[3]),
                "handler_code": row[4],
                "enabled": row[5] == 1,
                "env_vars": json.loads(row[6]) if row[6] else {},
                "created_at": row[7],
                "updated_at": row[8]
            })

        conn.close()
        return tools

    except sqlite3.Error as e:
        print(f"Database error loading custom tools: {e}")
        return []
    except Exception as e:
        print(f"Error loading custom tools: {e}")
        return []


def load_tool_by_name(name: str) -> Optional[Dict[str, Any]]:
    """Load a specific tool by name."""
    db_path = get_db_path()

    if not db_path.exists():
        return None

    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.execute("""
            SELECT id, name, description, input_schema, handler_code, enabled, env_vars, created_at, updated_at
            FROM custom_tools
            WHERE name = ?
        """, (name,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return {
            "id": row[0],
            "name": row[1],
            "description": row[2],
            "input_schema": json.loads(row[3]),
            "handler_code": row[4],
            "enabled": row[5] == 1,
            "env_vars": json.loads(row[6]) if row[6] else {},
            "created_at": row[7],
            "updated_at": row[8]
        }

    except Exception as e:
        print(f"Error loading tool {name}: {e}")
        return None
