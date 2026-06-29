import sqlite3
import os
from datetime import datetime

class Database:
    def __init__(self, db_path='notes.db'):
        self.db_path = db_path
        self.connection = None
        self.cursor = None
        self.init_database()
    
    def init_database(self):
        """Initialize the database and create table if it doesn't exist"""
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.cursor = self.connection.cursor()
            
            # Create notes table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    text TEXT NOT NULL,
                    completed INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    alarm_minutes INTEGER DEFAULT 0,
                    alarm_set INTEGER DEFAULT 0
                )
            ''')
            
            self.connection.commit()
        except Exception as e:
            print(f"Database initialization error: {e}")
    
    def execute_query(self, query, params=()):
        """Execute a query and return results"""
        try:
            if self.connection is None:
                self.init_database()
            
            self.cursor.execute(query, params)
            self.connection.commit()
            
            if query.strip().upper().startswith('SELECT'):
                return self.cursor.fetchall()
            return self.cursor.lastrowid
        except Exception as e:
            print(f"Query execution error: {e}")
            return None
    
    def add_note(self, text, alarm_minutes=0):
        """Add a new note"""
        query = "INSERT INTO notes (text, alarm_minutes) VALUES (?, ?)"
        return self.execute_query(query, (text, alarm_minutes))
    
    def get_all_notes(self):
        """Get all notes"""
        query = "SELECT id, text, completed, created_at, alarm_minutes FROM notes ORDER BY created_at DESC"
        result = self.execute_query(query)
        
        if result:
            notes = []
            for row in result:
                notes.append({
                    'id': row[0],
                    'text': row[1],
                    'completed': bool(row[2]),
                    'created_at': row[3],
                    'alarm_minutes': row[4]
                })
            return notes
        return []
    
    def update_note_status(self, note_id, completed):
        """Update note completion status"""
        query = "UPDATE notes SET completed = ? WHERE id = ?"
        return self.execute_query(query, (1 if completed else 0, note_id))
    
    def delete_note(self, note_id):
        """Delete a note"""
        query = "DELETE FROM notes WHERE id = ?"
        return self.execute_query(query, (note_id,))
    
    def get_note(self, note_id):
        """Get a single note by ID"""
        query = "SELECT id, text, completed, alarm_minutes FROM notes WHERE id = ?"
        result = self.execute_query(query, (note_id,))
        
        if result and len(result) > 0:
            row = result[0]
            return {
                'id': row[0],
                'text': row[1],
                'completed': bool(row[2]),
                'alarm_minutes': row[3]
            }
        return None
    
    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()