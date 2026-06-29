import sys
import os
import json
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QTextEdit, QListWidget, 
                             QListWidgetItem, QCheckBox, QLabel, QScrollArea,
                             QFrame, QSplitter, QMessageBox, QLineEdit)
from PyQt5.QtCore import Qt, QTimer, QSettings, QPoint, QSize, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont, QPalette, QColor, QIcon
from database import Database
from note_manager import NoteManager
from alarm import AlarmManager

class StickyNote(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.note_manager = NoteManager(self.db)
        self.alarm_manager = AlarmManager()
        self.settings = QSettings('StickyNotes', 'DesktopApp')
        
        # For window dragging
        self.drag_position = None
        
        self.init_ui()
        self.load_notes()
        self.restore_position()
        self.setup_auto_restore()
        
        # Connect alarm signals
        self.alarm_manager.alarm_triggered.connect(self.on_alarm_triggered)
        
        # Timer for auto-refresh
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_notes)
        self.timer.start(30000)  # Refresh every 30 seconds
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Sticky Notes - Desktop")
        self.setWindowFlags(Qt.WindowStaysOnBottomHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Set window size
        self.resize(420, 650)
        
        # Main widget and layout
        main_widget = QWidget()
        main_widget.setObjectName("mainWidget")
        self.setCentralWidget(main_widget)
        
        # Main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        main_widget.setLayout(layout)
        
        # Header - Make it draggable
        header_widget = QWidget()
        header_widget.setObjectName("headerWidget")
        header_widget.mousePressEvent = self.mouse_press_event
        header_widget.mouseMoveEvent = self.mouse_move_event
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(5, 5, 5, 5)
        
        title_label = QLabel("📋 Sticky Notes")
        title_label.setObjectName("titleLabel")
        header_layout.addWidget(title_label)
        
        # Minimize button
        minimize_btn = QPushButton("─")
        minimize_btn.setObjectName("minimizeBtn")
        minimize_btn.setFixedSize(30, 30)
        minimize_btn.clicked.connect(self.showMinimized)
        header_layout.addWidget(minimize_btn)
        
        # Close button
        close_btn = QPushButton("✕")
        close_btn.setObjectName("closeBtn")
        close_btn.setFixedSize(30, 30)
        close_btn.clicked.connect(self.close_app)
        header_layout.addWidget(close_btn)
        
        header_widget.setLayout(header_layout)
        layout.addWidget(header_widget)
        
        # Separator line
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setObjectName("separator")
        layout.addWidget(line)
        
        # Content area - using splitter for resizable sections
        splitter = QSplitter(Qt.Vertical)
        
        # New note section
        note_widget = QWidget()
        note_layout = QVBoxLayout()
        note_layout.setContentsMargins(0, 5, 0, 5)
        
        note_label = QLabel("✏️ New Task")
        note_label.setObjectName("sectionLabel")
        note_layout.addWidget(note_label)
        
        self.note_input = QTextEdit()
        self.note_input.setPlaceholderText("Enter your task here...")
        self.note_input.setMaximumHeight(80)
        self.note_input.setObjectName("noteInput")
        note_layout.addWidget(self.note_input)
        
        # Alarm section
        alarm_layout = QHBoxLayout()
        alarm_label = QLabel("⏰ Alarm (minutes):")
        alarm_label.setObjectName("alarmLabel")
        self.alarm_input = QLineEdit()
        self.alarm_input.setPlaceholderText("5")
        self.alarm_input.setFixedWidth(60)
        self.alarm_input.setText("5")
        alarm_layout.addWidget(alarm_label)
        alarm_layout.addWidget(self.alarm_input)
        alarm_layout.addStretch()
        note_layout.addLayout(alarm_layout)
        
        # Add note button
        add_btn = QPushButton("➕ Add Task")
        add_btn.setObjectName("addBtn")
        add_btn.clicked.connect(self.add_note)
        note_layout.addWidget(add_btn)
        
        note_widget.setLayout(note_layout)
        splitter.addWidget(note_widget)
        
        # Pending tasks section
        pending_widget = QWidget()
        pending_layout = QVBoxLayout()
        pending_layout.setContentsMargins(0, 5, 0, 5)
        
        pending_label = QLabel("📌 Pending Tasks")
        pending_label.setObjectName("sectionLabel")
        pending_layout.addWidget(pending_label)
        
        self.pending_list = QListWidget()
        self.pending_list.setObjectName("taskList")
        self.pending_list.setMinimumHeight(150)
        pending_layout.addWidget(self.pending_list)
        
        pending_widget.setLayout(pending_layout)
        splitter.addWidget(pending_widget)
        
        # Completed tasks section
        completed_widget = QWidget()
        completed_layout = QVBoxLayout()
        completed_layout.setContentsMargins(0, 5, 0, 5)
        
        completed_label = QLabel("✅ Completed Tasks")
        completed_label.setObjectName("sectionLabel")
        completed_layout.addWidget(completed_label)
        
        self.completed_list = QListWidget()
        self.completed_list.setObjectName("taskList")
        self.completed_list.setMinimumHeight(100)
        completed_layout.addWidget(self.completed_list)
        
        completed_widget.setLayout(completed_layout)
        splitter.addWidget(completed_widget)
        
        # Add splitter to main layout
        layout.addWidget(splitter)
        
        # Status bar
        self.status_label = QLabel("Ready")
        self.status_label.setObjectName("statusLabel")
        layout.addWidget(self.status_label)
        
        # Apply stylesheet
        self.apply_styles()
    
    def mouse_press_event(self, event):
        """Handle mouse press for window dragging"""
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouse_move_event(self, event):
        """Handle mouse move for window dragging"""
        if event.buttons() == Qt.LeftButton and self.drag_position is not None:
            self.move(event.globalPos() - self.drag_position)
            event.accept()
    
    def apply_styles(self):
        """Apply modern light theme stylesheet"""
        style = """
        QWidget {
            font-family: 'Segoe UI', Arial, sans-serif;
        }
        
        QMainWindow {
            background-color: transparent;
        }
        
        #mainWidget {
            background-color: #ffffff;
            border-radius: 12px;
            border: 1px solid #e0e0e0;
        }
        
        #headerWidget {
            background-color: #f8f9fa;
            border-top-left-radius: 12px;
            border-top-right-radius: 12px;
            padding: 5px;
        }
        
        #headerWidget:hover {
            background-color: #f0f0f0;
        }
        
        #titleLabel {
            font-size: 16px;
            font-weight: bold;
            color: #2c3e50;
        }
        
        #minimizeBtn {
            background-color: transparent;
            color: #f39c12;
            border: none;
            font-size: 16px;
            font-weight: bold;
            border-radius: 15px;
        }
        
        #minimizeBtn:hover {
            background-color: #f39c12;
            color: white;
        }
        
        #closeBtn {
            background-color: transparent;
            color: #e74c3c;
            border: none;
            font-size: 16px;
            font-weight: bold;
            border-radius: 15px;
        }
        
        #closeBtn:hover {
            background-color: #e74c3c;
            color: white;
        }
        
        #separator {
            background-color: #e0e0e0;
        }
        
        #sectionLabel {
            font-size: 13px;
            font-weight: bold;
            color: #34495e;
            padding: 5px 0;
        }
        
        #noteInput {
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            padding: 8px;
            font-size: 12px;
            background-color: #fafafa;
        }
        
        #noteInput:focus {
            border-color: #3498db;
            background-color: white;
        }
        
        #alarmLabel {
            font-size: 12px;
            color: #7f8c8d;
        }
        
        #alarmInput {
            border: 2px solid #e0e0e0;
            border-radius: 6px;
            padding: 5px;
            font-size: 12px;
            background-color: #fafafa;
        }
        
        #alarmInput:focus {
            border-color: #3498db;
        }
        
        #addBtn {
            background-color: #3498db;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 10px;
            font-size: 13px;
            font-weight: bold;
        }
        
        #addBtn:hover {
            background-color: #2980b9;
        }
        
        #addBtn:pressed {
            background-color: #21618c;
        }
        
        #taskList {
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 5px;
            background-color: #fafafa;
        }
        
        #taskList::item {
            padding: 10px;
            border-bottom: 1px solid #f0f0f0;
            min-height: 50px;
        }
        
        #taskList::item:hover {
            background-color: #f0f7ff;
        }
        
        #statusLabel {
            color: #7f8c8d;
            font-size: 11px;
            padding: 5px 0;
            border-top: 1px solid #f0f0f0;
        }
        
        QCheckBox {
            spacing: 10px;
            font-size: 12px;
            color: #2c3e50;
        }
        
        QCheckBox::indicator {
            width: 18px;
            height: 18px;
            border-radius: 4px;
            border: 2px solid #bdc3c7;
            background-color: white;
        }
        
        QCheckBox::indicator:checked {
            background-color: #27ae60;
            border-color: #27ae60;
        }
        
        QListWidget::item {
            padding: 10px;
        }
        
        QLabel {
            font-size: 12px;
        }
        """
        self.setStyleSheet(style)
    
    def add_note(self):
        """Add a new note/task"""
        text = self.note_input.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "Warning", "Please enter a task description.")
            return
        
        # Get alarm minutes
        try:
            alarm_minutes = int(self.alarm_input.text())
            if alarm_minutes < 0:
                alarm_minutes = 0
        except ValueError:
            alarm_minutes = 0
        
        # Add to database
        note_id = self.note_manager.add_note(text, alarm_minutes)
        
        # Set alarm if needed
        if alarm_minutes > 0:
            self.alarm_manager.set_alarm(note_id, text, alarm_minutes)
        
        # Clear input
        self.note_input.clear()
        self.status_label.setText(f"✅ Task added successfully!")
        
        # Refresh lists
        self.refresh_notes()
    
    def load_notes(self):
        """Load notes from database"""
        self.pending_list.clear()
        self.completed_list.clear()
        
        notes = self.note_manager.get_all_notes()
        
        for note in notes:
            # Create item with proper size - FIXED: Use QSize instead of QPoint
            item = QListWidgetItem()
            item.setSizeHint(QSize(0, 60))  # Set minimum height for each item
            
            # Create widget for the item
            widget = QWidget()
            widget.setMinimumHeight(50)
            
            layout = QHBoxLayout()
            layout.setContentsMargins(10, 5, 10, 5)
            layout.setSpacing(10)
            
            # Checkbox
            checkbox = QCheckBox()
            checkbox.setChecked(note['completed'])
            checkbox.setMinimumWidth(30)
            # Store note ID with the checkbox
            checkbox.note_id = note['id']
            checkbox.stateChanged.connect(lambda state, nid=note['id']: self.toggle_task(nid, state))
            
            # Text label
            text_label = QLabel(note['text'])
            text_label.setWordWrap(True)
            text_label.setMinimumHeight(30)
            text_label.setStyleSheet("font-size: 13px; padding: 5px;")
            
            # Alarm indicator
            if note['alarm_minutes'] > 0:
                alarm_indicator = QLabel("⏰")
                alarm_indicator.setToolTip(f"Alarm set for {note['alarm_minutes']} minutes")
            else:
                alarm_indicator = QLabel("")
            
            # Delete button
            delete_btn = QPushButton("🗑️")
            delete_btn.setFixedSize(30, 30)
            delete_btn.setStyleSheet("""
                QPushButton {
                    font-size: 14px;
                    border: none;
                    border-radius: 5px;
                    padding: 2px;
                }
                QPushButton:hover {
                    background-color: #ff6b6b;
                    color: white;
                }
            """)
            delete_btn.clicked.connect(lambda checked, nid=note['id']: self.delete_task(nid))
            
            # Add widgets to layout
            layout.addWidget(checkbox)
            layout.addWidget(text_label, 1)  # Give text label stretch factor
            if note['alarm_minutes'] > 0:
                layout.addWidget(alarm_indicator)
            layout.addWidget(delete_btn)
            
            widget.setLayout(layout)
            
            # Add to appropriate list
            if note['completed']:
                self.completed_list.addItem(item)
                self.completed_list.setItemWidget(item, widget)
            else:
                self.pending_list.addItem(item)
                self.pending_list.setItemWidget(item, widget)
    
    def refresh_notes(self):
        """Refresh the notes lists"""
        self.load_notes()
    
    def toggle_task(self, note_id, state):
        """Toggle task completion status"""
        completed = state == Qt.Checked
        
        # Get note details from database
        note = self.note_manager.get_note(note_id)
        if not note:
            return
        
        # Update status
        self.note_manager.update_note_status(note_id, completed)
        
        # Handle alarm
        if completed:
            self.alarm_manager.cancel_alarm(note_id)
            self.status_label.setText(f"✅ Task completed")
        else:
            # Re-add alarm if task was uncompleted and has alarm
            if note['alarm_minutes'] > 0:
                self.alarm_manager.set_alarm(note_id, note['text'], note['alarm_minutes'])
        
        self.refresh_notes()
    
    def delete_task(self, note_id):
        """Delete a task"""
        # Get note details
        note = self.note_manager.get_note(note_id)
        if not note:
            return
            
        reply = QMessageBox.question(self, 'Delete Task', 
                                     f'Delete task: "{note["text"][:50]}..."?',
                                     QMessageBox.Yes | QMessageBox.No,
                                     QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.note_manager.delete_note(note_id)
            self.alarm_manager.cancel_alarm(note_id)
            self.status_label.setText(f"🗑️ Task deleted")
            self.refresh_notes()
    
    def on_alarm_triggered(self, note_id, text):
        """Handle alarm triggered event"""
        self.status_label.setText(f"🔔 ALARM: {text[:30]}...")
        # Refresh to show updated status
        self.refresh_notes()
    
    def restore_position(self):
        """Restore window position from settings"""
        if self.settings.contains('pos_x') and self.settings.contains('pos_y'):
            x = self.settings.value('pos_x', type=int)
            y = self.settings.value('pos_y', type=int)
            self.move(x, y)
        else:
            # Center on screen
            screen = QApplication.primaryScreen().availableGeometry()
            x = (screen.width() - self.width()) // 2
            y = (screen.height() - self.height()) // 2
            self.move(x, y)
    
    def save_position(self):
        """Save window position to settings"""
        pos = self.pos()
        self.settings.setValue('pos_x', pos.x())
        self.settings.setValue('pos_y', pos.y())
    
    def setup_auto_restore(self):
        """Setup auto-restore on system restart"""
        # For Windows, create startup shortcut
        if sys.platform == 'win32':
            try:
                import winreg
                key = winreg.HKEY_CURRENT_USER
                subkey = r"Software\Microsoft\Windows\CurrentVersion\Run"
                app_path = os.path.abspath(sys.argv[0])
                with winreg.OpenKey(key, subkey, 0, winreg.KEY_SET_VALUE) as reg_key:
                    winreg.SetValueEx(reg_key, "StickyNotes", 0, winreg.REG_SZ, app_path)
            except Exception as e:
                print(f"Could not set auto-start: {e}")
    
    def close_app(self):
        """Close the application"""
        self.save_position()
        self.alarm_manager.shutdown()
        self.db.close()
        self.close()
    
    def closeEvent(self, event):
        """Handle close event"""
        self.save_position()
        self.alarm_manager.shutdown()
        self.db.close()
        event.accept()

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # Set application icon and metadata
    app.setApplicationName("Sticky Notes")
    app.setOrganizationName("YourOrg")
    
    window = StickyNote()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()