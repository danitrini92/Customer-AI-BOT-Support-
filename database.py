"""
database.py — SupportAI Pro
SQLite database for persistent storage of chats, tickets, and escalations.
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = "supportai.db"


def get_connection():
    """Get database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create all tables if they don't exist."""
    conn = get_connection()
    c = conn.cursor()

    # Chat messages table
    c.execute("""
        CREATE TABLE IF NOT EXISTS chat_messages (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id  TEXT NOT NULL,
            timestamp   TEXT NOT NULL,
            role        TEXT NOT NULL,
            message     TEXT NOT NULL,
            intent      TEXT,
            department  TEXT,
            priority    TEXT,
            urgency     TEXT,
            issue_type  TEXT,
            summary     TEXT,
            sentiment   TEXT,
            time_sec    REAL
        )
    """)

    # Tickets table
    c.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id    TEXT UNIQUE NOT NULL,
            session_id   TEXT NOT NULL,
            timestamp    TEXT NOT NULL,
            issue        TEXT NOT NULL,
            department   TEXT,
            priority     TEXT,
            urgency      TEXT,
            issue_type   TEXT,
            summary      TEXT,
            resolution   TEXT,
            action       TEXT,
            status       TEXT DEFAULT 'OPEN',
            sentiment    TEXT
        )
    """)

    # Escalations table
    c.execute("""
        CREATE TABLE IF NOT EXISTS escalations (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            ref_id       TEXT UNIQUE NOT NULL,
            session_id   TEXT NOT NULL,
            timestamp    TEXT NOT NULL,
            issue        TEXT NOT NULL,
            department   TEXT,
            priority     TEXT,
            urgency      TEXT,
            issue_type   TEXT,
            summary      TEXT,
            status       TEXT DEFAULT 'OPEN',
            sentiment    TEXT
        )
    """)

    conn.commit()
    conn.close()
    print("✅ Database initialized!")


def save_message(session_id, role, message, meta={}):
    """Save a chat message to database."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO chat_messages
        (session_id, timestamp, role, message, intent, department,
         priority, urgency, issue_type, summary, sentiment, time_sec)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        session_id,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        role,
        message,
        meta.get("intent"),
        meta.get("department"),
        meta.get("priority"),
        meta.get("urgency"),
        meta.get("issue_type"),
        meta.get("summary"),
        meta.get("sentiment"),
        meta.get("time_sec"),
    ))
    conn.commit()
    conn.close()


def save_ticket(session_id, ticket_id, issue, meta={}):
    """Save a ticket to database."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT OR IGNORE INTO tickets
        (ticket_id, session_id, timestamp, issue, department,
         priority, urgency, issue_type, summary, resolution, action, sentiment)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        ticket_id,
        session_id,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        issue,
        meta.get("department"),
        meta.get("priority"),
        meta.get("urgency"),
        meta.get("issue_type"),
        meta.get("summary"),
        meta.get("estimated_resolution"),
        meta.get("suggested_action"),
        meta.get("sentiment"),
    ))
    conn.commit()
    conn.close()


def save_escalation(session_id, ref_id, issue, meta={}):
    """Save an escalation to database."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT OR IGNORE INTO escalations
        (ref_id, session_id, timestamp, issue, department,
         priority, urgency, issue_type, summary, sentiment)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        ref_id,
        session_id,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        issue,
        meta.get("department"),
        meta.get("priority"),
        meta.get("urgency"),
        meta.get("issue_type"),
        meta.get("summary"),
        meta.get("sentiment"),
    ))
    conn.commit()
    conn.close()


def get_all_messages():
    """Get all chat messages."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM chat_messages ORDER BY timestamp DESC")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def get_all_tickets():
    """Get all tickets."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM tickets ORDER BY timestamp DESC")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def get_all_escalations():
    """Get all escalations."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM escalations ORDER BY timestamp DESC")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def get_stats():
    """Get summary statistics."""
    conn = get_connection()
    c = conn.cursor()

    c.execute("SELECT COUNT(*) as total FROM chat_messages WHERE role='user'")
    total_queries = c.fetchone()["total"]

    c.execute("SELECT COUNT(*) as total FROM tickets")
    total_tickets = c.fetchone()["total"]

    c.execute("SELECT COUNT(*) as total FROM escalations")
    total_escalations = c.fetchone()["total"]

    c.execute("""
        SELECT intent, COUNT(*) as count
        FROM chat_messages WHERE role='user' AND intent IS NOT NULL
        GROUP BY intent
    """)
    intent_counts = {r["intent"]: r["count"] for r in c.fetchall()}

    c.execute("""
        SELECT department, COUNT(*) as count
        FROM tickets WHERE department IS NOT NULL
        GROUP BY department
    """)
    dept_counts = {r["department"]: r["count"] for r in c.fetchall()}

    c.execute("""
        SELECT priority, COUNT(*) as count
        FROM tickets WHERE priority IS NOT NULL
        GROUP BY priority
    """)
    prio_counts = {r["priority"]: r["count"] for r in c.fetchall()}

    c.execute("""
        SELECT AVG(time_sec) as avg_time
        FROM chat_messages WHERE time_sec IS NOT NULL
    """)
    avg_time = c.fetchone()["avg_time"] or 0

    conn.close()
    return {
        "total_queries":    total_queries,
        "total_tickets":    total_tickets,
        "total_escalations":total_escalations,
        "intent_counts":    intent_counts,
        "dept_counts":      dept_counts,
        "prio_counts":      prio_counts,
        "avg_time":         round(avg_time, 2),
    }


def update_ticket_status(ticket_id, status):
    """Update ticket status — OPEN, IN_PROGRESS, RESOLVED."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE tickets SET status=? WHERE ticket_id=?", (status, ticket_id))
    conn.commit()
    conn.close()


def clear_all_data():
    """Clear all data from database."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM chat_messages")
    c.execute("DELETE FROM tickets")
    c.execute("DELETE FROM escalations")
    conn.commit()
    conn.close()


# Initialize database on import
init_db()
