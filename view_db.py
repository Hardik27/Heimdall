#!/usr/bin/env python
"""
Database viewer for Tofia Voice Assistant.
Simple script to display database tables and their contents.
"""
import sqlite3
import json
from datetime import datetime
from tabulate import tabulate as tabulate_func

def view_database():
    """View the contents of the Tofia database."""
    conn = sqlite3.connect('tofia.db')
    cursor = conn.cursor()
    
    # List all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("\n=== TABLES IN DATABASE ===")
    for table in tables:
        print(f"- {table[0]}")
    
    # View callers table
    cursor.execute("SELECT * FROM callers;")
    callers = cursor.fetchall()
    
    # Get column names
    cursor.execute("PRAGMA table_info(callers);")
    caller_columns = [col[1] for col in cursor.fetchall()]
    
    print("\n=== CALLERS TABLE ===")
    if callers:
        print(tabulate_func(callers, headers=caller_columns, tablefmt="grid"))
    else:
        print("No callers found")
    
    # View call records table
    cursor.execute("SELECT id, caller_id, call_type, call_sid, start_time, end_time, status, appointment_date, appointment_time, doctor_name FROM call_records;")
    call_records = cursor.fetchall()
    
    # Get column names for the selected columns
    columns = ["id", "caller_id", "call_type", "call_sid", "start_time", "end_time", "status", "appointment_date", "appointment_time", "doctor_name"]
    
    print("\n=== CALL RECORDS TABLE ===")
    if call_records:
        print(tabulate_func(call_records, headers=columns, tablefmt="grid"))
    else:
        print("No call records found")
    
    # View conversation histories
    cursor.execute("SELECT id, call_sid FROM call_records;")
    record_ids = cursor.fetchall()
    
    print("\n=== CONVERSATION HISTORIES ===")
    for record_id, call_sid in record_ids:
        cursor.execute("SELECT summary FROM call_records WHERE id = ?;", (record_id,))
        summary = cursor.fetchone()[0]
        
        cursor.execute("SELECT conversation_json FROM call_records WHERE id = ?;", (record_id,))
        json_data = cursor.fetchone()[0]
        
        print(f"\nRecord ID: {record_id} (Call SID: {call_sid})")
        print("-" * 50)
        
        if summary:
            print("Text Summary:")
            print(summary[:500] + "..." if len(summary) > 500 else summary)
        else:
            print("No text summary available")
        
        print("\nJSON Conversation Data:")
        if json_data:
            try:
                parsed = json.loads(json_data)
                print(f"Found {len(parsed)} conversation entries")
                for i, entry in enumerate(parsed[:3]):
                    print(f"\nEntry {i+1}:")
                    print(f"  Timestamp: {entry.get('timestamp')}")
                    print(f"  Type: {entry.get('type')}")
                    print(f"  User: {entry.get('user_message')}")
                    print(f"  Assistant: {entry.get('assistant_response')}")
                
                if len(parsed) > 3:
                    print(f"\n...and {len(parsed) - 3} more entries")
            except:
                print("Error parsing JSON data")
        else:
            print("No structured JSON data available")
        
        print("-" * 50)
    
    conn.close()

if __name__ == "__main__":
    try:
        from tabulate import tabulate
    except ImportError:
        print("Missing dependency. Installing tabulate...")
        import subprocess
        subprocess.call(["pip", "install", "tabulate"])
        from tabulate import tabulate
    
    view_database()
