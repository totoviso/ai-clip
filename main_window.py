"""
Main window for the ClipMaster application.
"""
import sys
import os
from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QLineEdit, QProgressBar,
    QTabWidget, QFileDialog, QMessageBox, QComboBox,
    QSlider, QSpinBox, QCheckBox, QGroupBox, QScrollArea,
    QSplitter, QTextEdit
)
from PyQt6.QtCore import Qt, QSize, QUrl, QThread, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QIcon, QPixmap, QFont, QAction
from qt_material import apply_stylesheet

# Import our backend services
# These will be implemented later
from src.backend.services.youtube_service import YouTubeService
from src.backend.services.transcription_service import TranscriptionService
from src.backend.services.clip_detection_service import ClipDetectionService
from src.backend.services.video_processing_service import VideoProcessingService


class MainWindow(QMainWindow):
    """Main window for the ClipMaster application."""
    
    def __init__(self):
        super().__init__()
        
        # Initialize services
        self.youtube_service = YouTubeService()
        self.transcription_service = TranscriptionService()
        self.clip_detection_service = ClipDetectionService()
        self.video_processing_service = VideoProcessingService()
        
        # Set up the UI
        self.init_ui()
        
        # Apply material design theme
        apply_stylesheet(self, theme='dark_teal.xml')
        
    def init_ui(self):
        """Initialize the user interface."""
        # Set window properties
        self.setWindowTitle("ClipMaster - Video Clipping Software")
        self.setMinimumSize(1200, 800)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Create the header section
        self.create_header_section(main_layout)
        
        # Create the main content area with tabs
        self.create_tabs(main_layout)
        
        # Create the status bar
        self.statusBar().showMessage("Ready")
        
        # Create menu bar
        self.create_menu_bar()
        
    def create_header_section(self, parent_layout):
        """Create the header section with URL input and download button."""
        header_layout = QHBoxLayout()
        
        # URL input field
        url_label = QLabel("YouTube URL:")
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Enter YouTube URL here...")
        
        # Download button
        self.download_btn = QPushButton("Download && Process")
        self.download_btn.clicked.connect(self.on_download_clicked)
        
        # Add widgets to header layout
        header_layout.addWidget(url_label)
        header_layout.addWidget(self.url_input, 1)  # 1 is the stretch factor
        header_layout.addWidget(self.download_btn)
        
        # Add header layout to parent layout
        parent_layout.addLayout(header_layout)
        
        # Add progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        parent_layout.addWidget(self.progress_bar)
        
    def create_tabs(self, parent_layout):
        """Create the main tab widget with different sections."""
        self.tabs = QTabWidget()
        
        # Create tabs
        self.video_tab = QWidget()
        self.transcription_tab = QWidget()
        self.clip_detection_tab = QWidget()
        self.editing_tab = QWidget()
        self.export_tab = QWidget()
        
        # Set up each tab's content
        self.setup_video_tab()
        self.setup_transcription_tab()
        self.setup_clip_detection_tab()
        self.setup_editing_tab()
        self.setup_export_tab()
        
        # Add tabs to tab widget
        self.tabs.addTab(self.video_tab, "Video")
        self.tabs.addTab(self.transcription_tab, "Transcription")
        self.tabs.addTab(self.clip_detection_tab, "Clip Detection")
        self.tabs.addTab(self.editing_tab, "Editing")
        self.tabs.addTab(self.export_tab, "Export")
        
        # Add tab widget to parent layout
        parent_layout.addWidget(self.tabs, 1)  # 1 is the stretch factor
        
    def setup_video_tab(self):
        """Set up the video tab content."""
        layout = QVBoxLayout(self.video_tab)
        
        # Video preview section
        preview_label = QLabel("Video Preview")
        preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_label.setFont(QFont("Arial", 14))
        
        # Placeholder for video preview
        self.video_preview = QLabel("No video loaded")
        self.video_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_preview.setStyleSheet("background-color: #1e1e1e; min-height: 400px;")
        
        # Video info section
        info_group = QGroupBox("Video Information")
        info_layout = QVBoxLayout(info_group)
        
        self.video_title_label = QLabel("Title: ")
        self.video_duration_label = QLabel("Duration: ")
        self.video_resolution_label = QLabel("Resolution: ")
        
        info_layout.addWidget(self.video_title_label)
        info_layout.addWidget(self.video_duration_label)
        info_layout.addWidget(self.video_resolution_label)
        
        # Add widgets to layout
        layout.addWidget(preview_label)
        layout.addWidget(self.video_preview, 1)
        layout.addWidget(info_group)
        
    def setup_transcription_tab(self):
        """Set up the transcription tab content."""
        layout = QVBoxLayout(self.transcription_tab)
        
        # Transcription options
        options_group = QGroupBox("Transcription Options")
        options_layout = QHBoxLayout(options_group)
        
        self.language_combo = QComboBox()
        self.language_combo.addItems(["Auto-detect", "English", "Spanish", "French", "German"])
        
        self.transcribe_btn = QPushButton("Transcribe")
        self.transcribe_btn.clicked.connect(self.on_transcribe_clicked)
        
        options_layout.addWidget(QLabel("Language:"))
        options_layout.addWidget(self.language_combo)
        options_layout.addStretch(1)
        options_layout.addWidget(self.transcribe_btn)
        
        # Transcription text area
        self.transcription_text = QTextEdit()
        self.transcription_text.setPlaceholderText("Transcription will appear here...")
        self.transcription_text.setReadOnly(False)  # Allow editing for corrections
        
        # Add widgets to layout
        layout.addWidget(options_group)
        layout.addWidget(QLabel("Transcription:"))
        layout.addWidget(self.transcription_text, 1)
        
    def setup_clip_detection_tab(self):
        """Set up the clip detection tab content."""
        layout = QVBoxLayout(self.clip_detection_tab)
        
        # Detection options
        options_group = QGroupBox("Detection Options")
        options_layout = QHBoxLayout(options_group)
        
        self.clip_length_spin = QSpinBox()
        self.clip_length_spin.setRange(15, 180)
        self.clip_length_spin.setValue(60)
        self.clip_length_spin.setSuffix(" seconds")
        
        self.detect_btn = QPushButton("Detect Viral Clips")
        self.detect_btn.clicked.connect(self.on_detect_clips_clicked)
        
        options_layout.addWidget(QLabel("Target Clip Length:"))
        options_layout.addWidget(self.clip_length_spin)
        options_layout.addStretch(1)
        options_layout.addWidget(self.detect_btn)
        
        # Detected clips list
        clips_group = QGroupBox("Detected Clips")
        clips_layout = QVBoxLayout(clips_group)
        
        self.clips_list = QTextEdit()
        self.clips_list.setPlaceholderText("Detected clips will appear here...")
        self.clips_list.setReadOnly(True)
        
        clips_layout.addWidget(self.clips_list)
        
        # Add widgets to layout
        layout.addWidget(options_group)
        layout.addWidget(clips_group, 1)
        
    def setup_editing_tab(self):
        """Set up the editing tab content."""
        layout = QVBoxLayout(self.editing_tab)
        
        # Split into two panels
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel - clip preview
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        preview_label = QLabel("Clip Preview")
        preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_label.setFont(QFont("Arial", 14))
        
        self.clip_preview = QLabel("No clip selected")
        self.clip_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.clip_preview.setStyleSheet("background-color: #1e1e1e; min-height: 400px;")
        
        left_layout.addWidget(preview_label)
        left_layout.addWidget(self.clip_preview, 1)
        
        # Right panel - editing options
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Aspect ratio selection
        aspect_group = QGroupBox("Aspect Ratio")
        aspect_layout = QHBoxLayout(aspect_group)
        
        self.aspect_combo = QComboBox()
        self.aspect_combo.addItems(["9:16 (Vertical)", "1:1 (Square)", "16:9 (Horizontal)"])
        
        aspect_layout.addWidget(self.aspect_combo)
        
        # Face tracking options
        tracking_group = QGroupBox("Face Tracking")
        tracking_layout = QVBoxLayout(tracking_group)
        
        self.enable_tracking_check = QCheckBox("Enable Face Tracking")
        self.enable_tracking_check.setChecked(True)
        
        tracking_layout.addWidget(self.enable_tracking_check)
        
        # Caption options
        caption_group = QGroupBox("Captions")
        caption_layout = QVBoxLayout(caption_group)
        
        self.enable_captions_check = QCheckBox("Enable Captions")
        self.enable_captions_check.setChecked(True)
        
        self.caption_font_combo = QComboBox()
        self.caption_font_combo.addItems(["Arial", "Helvetica", "Impact", "Comic Sans MS"])
        
        self.caption_size_spin = QSpinBox()
        self.caption_size_spin.setRange(12, 72)
        self.caption_size_spin.setValue(24)
        
        caption_layout.addWidget(self.enable_captions_check)
        caption_layout.addWidget(QLabel("Font:"))
        caption_layout.addWidget(self.caption_font_combo)
        caption_layout.addWidget(QLabel("Size:"))
        caption_layout.addWidget(self.caption_size_spin)
        
        # Apply button
        self.apply_edits_btn = QPushButton("Apply Edits")
        self.apply_edits_btn.clicked.connect(self.on_apply_edits_clicked)
        
        # Add widgets to right layout
        right_layout.addWidget(aspect_group)
        right_layout.addWidget(tracking_group)
        right_layout.addWidget(caption_group)
        right_layout.addStretch(1)
        right_layout.addWidget(self.apply_edits_btn)
        
        # Add panels to splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([600, 600])  # Equal initial sizes
        
        # Add splitter to main layout
        layout.addWidget(splitter)
        
    def setup_export_tab(self):
        """Set up the export tab content."""
        layout = QVBoxLayout(self.export_tab)
        
        # Export options
        options_group = QGroupBox("Export Options")
        options_layout = QVBoxLayout(options_group)
        
        # Resolution selection
        resolution_layout = QHBoxLayout()
        resolution_layout.addWidget(QLabel("Resolution:"))
        
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems(["1080p", "720p", "480p", "360p"])
        
        resolution_layout.addWidget(self.resolution_combo)
        resolution_layout.addStretch(1)
        
        # Format selection
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Format:"))
        
        self.format_combo = QComboBox()
        self.format_combo.addItems(["MP4", "MOV", "WebM"])
        
        format_layout.addWidget(self.format_combo)
        format_layout.addStretch(1)
        
        # Output path selection
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("Output Path:"))
        
        self.output_path = QLineEdit()
        self.output_path.setReadOnly(True)
        
        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self.on_browse_clicked)
        
        path_layout.addWidget(self.output_path, 1)
        path_layout.addWidget(self.browse_btn)
        
        # Add layouts to options group
        options_layout.addLayout(resolution_layout)
        options_layout.addLayout(format_layout)
        options_layout.addLayout(path_layout)
        
        # Export button
        self.export_btn = QPushButton("Export Clip")
        self.export_btn.clicked.connect(self.on_export_clicked)
        self.export_btn.setStyleSheet("font-size: 16px; padding: 10px;")
        
        # Add widgets to main layout
        layout.addWidget(options_group)
        layout.addStretch(1)
        layout.addWidget(self.export_btn)
        
    def create_menu_bar(self):
        """Create the application menu bar."""
        menu_bar = self.menuBar()
        
        # File menu
        file_menu = menu_bar.addMenu("File")
        
        open_action = QAction("Open Video...", self)
        open_action.triggered.connect(self.on_open_video)
        file_menu.addAction(open_action)
        
        save_project_action = QAction("Save Project", self)
        save_project_action.triggered.connect(self.on_save_project)
        file_menu.addAction(save_project_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Help menu
        help_menu = menu_bar.addMenu("Help")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self.on_about)
        help_menu.addAction(about_action)
        
    # Event handlers
    def on_download_clicked(self):
        """Handle download button click."""
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Input Error", "Please enter a valid YouTube URL.")
            return
            
        self.statusBar().showMessage("Downloading video...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # TODO: Implement actual download logic with the YouTube service
        # For now, just simulate progress
        for i in range(101):
            self.progress_bar.setValue(i)
            # In a real implementation, we would use QThread and signals
            # to update the progress bar without blocking the UI
        
        self.statusBar().showMessage("Download complete")
        QMessageBox.information(self, "Success", "Video downloaded successfully!")
        
    def on_transcribe_clicked(self):
        """Handle transcribe button click."""
        self.statusBar().showMessage("Transcribing video...")
        # TODO: Implement actual transcription logic
        self.statusBar().showMessage("Transcription complete")
        
    def on_detect_clips_clicked(self):
        """Handle detect clips button click."""
        self.statusBar().showMessage("Detecting viral clips...")
        # TODO: Implement actual clip detection logic
        self.statusBar().showMessage("Clip detection complete")
        
    def on_apply_edits_clicked(self):
        """Handle apply edits button click."""
        self.statusBar().showMessage("Applying edits...")
        # TODO: Implement actual editing logic
        self.statusBar().showMessage("Edits applied")
        
    def on_browse_clicked(self):
        """Handle browse button click for output path selection."""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Output Directory", os.path.expanduser("~")
        )
        if directory:
            self.output_path.setText(directory)
            
    def on_export_clicked(self):
        """Handle export button click."""
        if not self.output_path.text():
            QMessageBox.warning(self, "Export Error", "Please select an output directory.")
            return
            
        self.statusBar().showMessage("Exporting clip...")
        # TODO: Implement actual export logic
        self.statusBar().showMessage("Export complete")
        QMessageBox.information(self, "Success", "Clip exported successfully!")
        
    def on_open_video(self):
        """Handle open video menu action."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Video", os.path.expanduser("~"),
            "Video Files (*.mp4 *.avi *.mov *.mkv *.webm)"
        )
        if file_path:
            self.statusBar().showMessage(f"Opening {file_path}...")
            # TODO: Implement actual video opening logic
            self.statusBar().showMessage(f"Opened {os.path.basename(file_path)}")
            
    def on_save_project(self):
        """Handle save project menu action."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Project", os.path.expanduser("~"),
            "ClipMaster Projects (*.cmp)"
        )
        if file_path:
            self.statusBar().showMessage(f"Saving project to {file_path}...")
            # TODO: Implement actual project saving logic
            self.statusBar().showMessage("Project saved")
            
    def on_about(self):
        """Handle about menu action."""
        QMessageBox.about(
            self, "About ClipMaster",
            "ClipMaster 1.0.0\n\n"
            "A self-hosted video clipping software with YouTube integration.\n\n"
            "© 2025 ClipMaster Team"
        )
