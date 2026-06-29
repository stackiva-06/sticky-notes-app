import threading
import time
import winsound
import sys
from datetime import datetime, timedelta
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QTimer, QObject, pyqtSignal

class AlarmManager(QObject):
    alarm_triggered = pyqtSignal(int, str)  # note_id, text
    
    def __init__(self):
        super().__init__()
        self.alarms = {}
        self.running = True
        self.alarm_thread = None
        self.start_alarm_monitor()
    
    def set_alarm(self, note_id, text, minutes):
        """Set an alarm for a note"""
        alarm_time = datetime.now() + timedelta(minutes=minutes)
        self.alarms[note_id] = {
            'time': alarm_time,
            'text': text,
            'minutes': minutes,
            'triggered': False
        }
        print(f"⏰ Alarm set for '{text[:30]}...' in {minutes} minutes")
    
    def cancel_alarm(self, note_id):
        """Cancel an alarm"""
        if note_id in self.alarms:
            del self.alarms[note_id]
            print(f"🔕 Alarm cancelled for note {note_id}")
    
    def start_alarm_monitor(self):
        """Start the alarm monitoring thread"""
        self.alarm_thread = threading.Thread(target=self.monitor_alarms, daemon=True)
        self.alarm_thread.start()
    
    def monitor_alarms(self):
        """Monitor alarms and trigger when due"""
        while self.running:
            current_time = datetime.now()
            
            for note_id, alarm_info in list(self.alarms.items()):
                if not alarm_info['triggered'] and current_time >= alarm_info['time']:
                    alarm_info['triggered'] = True
                    # Trigger alarm
                    self.trigger_alarm(note_id, alarm_info['text'])
            
            time.sleep(5)  # Check every 5 seconds
    
    def trigger_alarm(self, note_id, text):
        """Trigger an alarm"""
        print(f"🔔 ALARM: {text}")
        
        # Emit signal for GUI
        self.alarm_triggered.emit(note_id, text)
        
        # Play sound (Windows)
        if sys.platform == 'win32':
            try:
                # Play a simple beep sound
                for _ in range(3):
                    winsound.Beep(1000, 500)  # Frequency 1000Hz, duration 500ms
                    time.sleep(0.5)
            except:
                pass
        else:
            # For Mac/Linux, use system bell
            print('\a')  # ASCII bell character
        
        # Show popup
        self.show_alarm_popup(note_id, text)
    
    def show_alarm_popup(self, note_id, text):
        """Show alarm popup"""
        # This will be called from the main thread
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("⏰ Alarm!")
        msg.setText(f"Task Reminder:\n\n{text}")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
        
        # Remove alarm after showing
        if note_id in self.alarms:
            del self.alarms[note_id]
    
    def shutdown(self):
        """Shutdown the alarm manager"""
        self.running = False
        if self.alarm_thread and self.alarm_thread.is_alive():
            self.alarm_thread.join(timeout=2)