from datetime import datetime
import threading
import time

class NoteManager:
    def __init__(self, database):
        self.db = database
        self.alarms = {}
    
    def add_note(self, text, alarm_minutes=0):
        """Add a new note"""
        return self.db.add_note(text, alarm_minutes)
    
    def get_all_notes(self):
        """Get all notes"""
        return self.db.get_all_notes()
    
    def update_note_status(self, note_id, completed):
        """Update note completion status"""
        return self.db.update_note_status(note_id, completed)
    
    def delete_note(self, note_id):
        """Delete a note"""
        return self.db.delete_note(note_id)
    
    def get_note(self, note_id):
        """Get a single note"""
        return self.db.get_note(note_id)