"""Main window for Live Captions Companion."""
import ctypes
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QStandardPaths, QUrl
from PySide6.QtGui import QTextCursor
from capture.worker import CaptureWorker
from PySide6.QtWidgets import (
    QInputDialog,
    QComboBox,
    QFileDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QDialog,
    QWidget,
    QLineEdit,
)

from capture.history import SessionHistory
from capture.export import export_session


class MainWindow(QMainWindow):
    """Main application window for browsing captured sessions."""

    def __init__(self) -> None:
        super().__init__()

        self.history = SessionHistory()
        # At startup, no capture worker from a previous process can still be
        # running. Mark any sessions left open by a crash as interrupted.
        self.recovered_session_ids = self.history.recover_interrupted_sessions()
        self.sessions: list[dict] = []
        self.current_session_id: str | None = None
        self.saved_transcript = ""
        self.capture_worker: CaptureWorker | None = None
        self.active_capture_session_id: str | None = None

        self.setWindowTitle("Live Captions Companion")
        self.resize(1100, 700)
        self.setMinimumSize(800, 500)

        self._build_ui()
        self.refresh_sessions()
        if self.recovered_session_ids:
            count = len(self.recovered_session_ids)
            self.statusBar().showMessage(
                f"Recovered {count} interrupted recording session(s). "
                "Their captured transcripts have been preserved.",
                10000,
            )

    def _build_ui(self) -> None:
        """Build the polished, three-part desktop interface."""
        self.setObjectName("mainWindow")
        self.setStyleSheet("""
            QMainWindow#mainWindow {
                background: #F5F7FA;
            }
            QWidget {
                font-family: "Segoe UI";
                font-size: 10pt;
                color: #202938;
            }
            QFrame#sidebar {
                background: #FFFFFF;
                border: 1px solid #E3E8EF;
                border-radius: 12px;
            }
            QFrame#workspace {
                background: #FFFFFF;
                border: 1px solid #E3E8EF;
                border-radius: 12px;
            }
            QLabel#appTitle {
                font-size: 16pt;
                font-weight: 700;
                color: #17243A;
            }
            QLabel#appSubtitle, QLabel#mutedText {
                color: #697586;
            }
            QLabel#sectionTitle {
                font-size: 10pt;
                font-weight: 700;
                color: #344054;
            }
            QLabel#sessionTitle {
                font-size: 18pt;
                font-weight: 700;
                color: #17243A;
            }
            QLabel#recordingIndicator {
                padding: 7px 11px;
                border-radius: 9px;
                background: #EEF2F6;
                color: #475467;
                font-weight: 600;
            }
            QLineEdit {
                background: #F8FAFC;
                border: 1px solid #D8E0EA;
                border-radius: 8px;
                padding: 9px 11px;
                selection-background-color: #2F65B0;
            }
            QLineEdit:focus, QTextEdit:focus {
                border: 1px solid #4B83D1;
            }
            QListWidget {
                background: transparent;
                border: none;
                outline: none;
                padding: 3px;
            }
            QListWidget::item {
                padding: 11px 10px;
                margin: 2px 0;
                border-radius: 7px;
            }
            QListWidget::item:hover {
                background: #F1F5FA;
            }
            QListWidget::item:selected {
                background: #E8F0FC;
                color: #174A8B;
                font-weight: 600;
            }
            QTextEdit {
                background: #FCFDFE;
                border: 1px solid #E1E7EF;
                border-radius: 9px;
                padding: 12px;
                font-size: 11pt;
                selection-background-color: #CFE0F8;
            }
            QPushButton {
                background: #F1F4F8;
                border: 1px solid #DCE3EB;
                border-radius: 8px;
                padding: 9px 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #E8EDF4;
            }
            QPushButton:pressed {
                background: #DCE5F0;
            }
            QPushButton:disabled {
                color: #98A2B3;
                background: #F5F6F8;
                border-color: #E8EBEF;
            }
            QPushButton#primaryButton {
                background: #245FA8;
                color: white;
                border: 1px solid #245FA8;
            }
            QPushButton#primaryButton:hover {
                background: #1D508F;
            }
            QPushButton#dangerButton {
                color: #A52B32;
                background: #FFF5F5;
                border-color: #F1D1D3;
            }
            QPushButton#dangerButton:hover {
                background: #FDEBEC;
            }
            QStatusBar {
                background: #FFFFFF;
                color: #667085;
                border-top: 1px solid #E6EAF0;
            }
            QSplitter::handle {
                background: transparent;
                width: 8px;
            }
        """)

        # Application header
        app_icon = QLabel("CC")
        app_icon.setObjectName("appMark")
        app_icon.setFixedSize(42, 42)
        app_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        app_icon.setStyleSheet(
            "background:#245FA8; color:white; border-radius:10px;"
            "font-size:15pt; font-weight:800;"
        )

        title_block = QWidget()
        title_layout = QVBoxLayout(title_block)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(1)
        app_title = QLabel("Live Captions Companion")
        app_title.setObjectName("appTitle")
        app_subtitle = QLabel("An independent companion for Windows Live Captions")
        app_subtitle.setObjectName("appSubtitle")
        title_layout.addWidget(app_title)
        title_layout.addWidget(app_subtitle)

        header = QHBoxLayout()
        header.setContentsMargins(2, 0, 2, 8)
        header.addWidget(app_icon)
        header.addWidget(title_block)
        header.addStretch(1)

        self.recording_indicator = QLabel("●  Ready to capture")
        self.recording_indicator.setObjectName("recordingIndicator")
        self.recording_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.addWidget(self.recording_indicator)

        # Sidebar: capture actions and searchable session history
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search sessions and transcripts…")
        self.search_input.textChanged.connect(self.filter_sessions)

        self.refresh_button = QPushButton("Refresh sessions")
        self.refresh_button.clicked.connect(self.refresh_sessions)

        self.start_button = QPushButton("▶   Start capture")
        self.start_button.setObjectName("primaryButton")
        self.start_button.clicked.connect(self.start_recording)

        self.stop_button = QPushButton("■   Stop capture")
        self.stop_button.setObjectName("dangerButton")
        self.stop_button.clicked.connect(self.stop_recording)
        self.stop_button.setEnabled(False)

        self.rename_button = QPushButton("Rename")
        self.rename_button.clicked.connect(self.rename_selected_session)

        self.delete_button = QPushButton("Delete")
        self.delete_button.setObjectName("dangerButton")
        self.delete_button.clicked.connect(self.delete_selected_session)

        self.export_button = QPushButton("Export transcript")
        self.export_button.clicked.connect(self.export_selected_session)

        self.session_list = QListWidget()
        self.session_list.currentItemChanged.connect(self.on_session_selected)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(16, 16, 16, 16)
        sidebar_layout.setSpacing(9)

        sessions_heading = QLabel("SESSION LIBRARY")
        sessions_heading.setObjectName("sectionTitle")
        sidebar_layout.addWidget(self.start_button)
        sidebar_layout.addWidget(self.stop_button)
        sidebar_layout.addSpacing(8)
        sidebar_layout.addWidget(sessions_heading)
        sidebar_layout.addWidget(self.search_input)
        sidebar_layout.addWidget(self.refresh_button)
        sidebar_layout.addWidget(self.session_list, 1)

        session_actions = QHBoxLayout()
        session_actions.addWidget(self.rename_button)
        session_actions.addWidget(self.delete_button)
        sidebar_layout.addLayout(session_actions)
        sidebar_layout.addWidget(self.export_button)

        # Main workspace: selected session information and transcript editor
        self.session_title = QLabel("Welcome")
        self.session_title.setObjectName("sessionTitle")

        self.session_details = QLabel(
            "Select a saved session to review its transcript, or start a new capture."
        )
        self.session_details.setObjectName("mutedText")
        self.session_details.setWordWrap(True)

        workspace_header = QHBoxLayout()
        workspace_header.addWidget(self.session_title, 1)

        self.transcript_viewer = QTextEdit()
        self.transcript_viewer.setReadOnly(False)
        self.transcript_viewer.setPlaceholderText(
            "Your selected transcript will appear here. Start a capture to collect "
            "Windows Live Captions, or select a previous session."
        )
        self.transcript_viewer.textChanged.connect(self.update_editor_state)

        self.save_button = QPushButton("Save changes")
        self.save_button.setObjectName("primaryButton")
        self.save_button.clicked.connect(self.save_transcript)

        self.discard_button = QPushButton("Discard changes")
        self.discard_button.clicked.connect(self.discard_transcript_changes)

        editor_footer = QHBoxLayout()
        editor_footer.addStretch(1)
        editor_footer.addWidget(self.discard_button)
        editor_footer.addWidget(self.save_button)

        workspace = QFrame()
        workspace.setObjectName("workspace")
        workspace_layout = QVBoxLayout(workspace)
        workspace_layout.setContentsMargins(20, 18, 20, 18)
        workspace_layout.setSpacing(12)
        workspace_layout.addLayout(workspace_header)
        workspace_layout.addWidget(self.session_details)
        workspace_layout.addWidget(self.transcript_viewer, 1)
        workspace_layout.addLayout(editor_footer)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(sidebar)
        splitter.addWidget(workspace)
        splitter.setSizes([310, 790])

        central = QWidget()
        central_layout = QVBoxLayout(central)
        central_layout.setContentsMargins(18, 16, 18, 10)
        central_layout.setSpacing(12)
        central_layout.addLayout(header)
        central_layout.addWidget(splitter, 1)
        self.setCentralWidget(central)

        self.statusBar().showMessage("Ready")
        self.update_editor_state()

    def start_recording(self) -> None:
        """Start caption capture in a background thread."""
        if self.capture_worker is not None and self.capture_worker.isRunning():
            return

        # Avoid starting a capture while there are unsaved manual edits.
        if not self.confirm_unsaved_changes():
            return

        self.capture_worker = CaptureWorker()
        self.capture_worker.recording_started.connect(self.on_recording_started)
        self.capture_worker.capture_error.connect(self.on_capture_error)
        self.capture_worker.status_update.connect(self.statusBar().showMessage)
        self.capture_worker.recording_finished.connect(self.on_recording_finished)
        self.capture_worker.transcript_update.connect(self.on_transcript_update)

        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.transcript_viewer.setReadOnly(True)
        self.rename_button.setEnabled(False)
        self.delete_button.setEnabled(False)
        self.export_button.setEnabled(False)
        self.session_list.setEnabled(False)
        self.recording_indicator.setText("●  Starting capture…")
        self.recording_indicator.setStyleSheet("background:#FFF4E5; color:#9A5B13; padding:7px 11px; border-radius:9px; font-weight:600;")
        self.statusBar().showMessage("Starting caption capture...")

        self.capture_worker.start()

    def stop_recording(self) -> None:
        """Request that the active capture worker stop."""
        if self.capture_worker is None or not self.capture_worker.isRunning():
            return

        self.stop_button.setEnabled(False)
        self.recording_indicator.setText("●  Stopping capture…")
        self.recording_indicator.setStyleSheet(
            "background:#FFF4E5; color:#9A5B13; padding:7px 11px; border-radius:9px; font-weight:600;"
        )
        self.statusBar().showMessage("Stopping caption capture...")
        self.capture_worker.stop()

    def on_recording_started(self, session_id: str, session_path: str) -> None:
        """Show the new session in the list as soon as recording starts."""
        self.active_capture_session_id = session_id
        self.refresh_sessions()

        # Select the newly created session so its live transcript is visible.
        for row in range(self.session_list.count()):
            item = self.session_list.item(row)
            if item.data(Qt.ItemDataRole.UserRole) == session_id:
                self.session_list.setCurrentItem(item)
                break

        self.recording_indicator.setText("●  Recording")
        self.recording_indicator.setStyleSheet("background:#FDEBEC; color:#B4232C; padding:7px 11px; border-radius:9px; font-weight:700;")
        self.statusBar().showMessage(f"Recording captions: {session_path}")

    def on_transcript_update(self, transcript: str) -> None:
        """Display live text for the currently recording session."""
        if not self.active_capture_session_id:
            return
        if self.current_session_id != self.active_capture_session_id:
            return

        self.transcript_viewer.blockSignals(True)
        self.transcript_viewer.setPlainText(transcript)
        self.transcript_viewer.moveCursor(QTextCursor.MoveOperation.End)
        self.transcript_viewer.blockSignals(False)
        # Live capture updates are not manual edits and should not be marked dirty.
        self.saved_transcript = transcript
        self.update_editor_state()

    @staticmethod
    def _apply_light_title_bar_to(widget: QWidget) -> None:
        """Request a light native title bar for a top-level Qt window."""
        if sys.platform != "win32":
            return

        try:
            hwnd = int(widget.winId())
            dwmapi = ctypes.WinDLL("dwmapi")
            value = ctypes.c_int(0)  # Light title-bar appearance
            for attribute in (20, 19):
                result = dwmapi.DwmSetWindowAttribute(
                    ctypes.c_void_p(hwnd),
                    ctypes.c_uint(attribute),
                    ctypes.byref(value),
                    ctypes.sizeof(value),
                )
                if result == 0:
                    break
        except (AttributeError, OSError, TypeError, ValueError):
            # Fall back to the platform's default title bar if unavailable.
            pass

    def _ask_text(
        self,
        title: str,
        prompt: str,
        initial_text: str = "",
    ) -> tuple[str, bool]:
        """Show a compact, light-themed text input dialog."""
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setModal(True)
        self._apply_light_title_bar_to(dialog)
        dialog.setStyleSheet("""
            QDialog { background: #FFFFFF; }
            QLabel {
                color: #344054;
                background: transparent;
                font-family: "Segoe UI";
                font-size: 10pt;
            }
            QLineEdit {
                background: #FFFFFF;
                color: #202938;
                border: 1px solid #B8C7D9;
                border-radius: 7px;
                padding: 8px 10px;
                selection-background-color: #CFE0F8;
                font-family: "Segoe UI";
                font-size: 10pt;
            }
            QLineEdit:focus { border: 1px solid #4B83D1; }
            QPushButton {
                background: #F1F4F8;
                color: #202938;
                border: 1px solid #DCE3EB;
                border-radius: 7px;
                padding: 7px 18px;
                min-width: 64px;
                font-family: "Segoe UI";
                font-size: 10pt;
                font-weight: 600;
            }
            QPushButton:hover { background: #E8EDF4; }
            QPushButton#primaryButton {
                background: #245FA8;
                color: #FFFFFF;
                border-color: #245FA8;
            }
            QPushButton#primaryButton:hover { background: #1D508F; }
        """)

        prompt_label = QLabel(prompt)
        prompt_label.setWordWrap(True)
        text_input = QLineEdit(initial_text)
        text_input.selectAll()

        ok_button = QPushButton("OK")
        ok_button.setObjectName("primaryButton")
        cancel_button = QPushButton("Cancel")
        ok_button.clicked.connect(dialog.accept)
        cancel_button.clicked.connect(dialog.reject)
        text_input.returnPressed.connect(dialog.accept)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        buttons.addWidget(ok_button)
        buttons.addWidget(cancel_button)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)
        layout.addWidget(prompt_label)
        layout.addWidget(text_input)
        layout.addLayout(buttons)

        dialog.setFixedWidth(400)
        text_input.setFocus()
        accepted = dialog.exec() == QDialog.DialogCode.Accepted
        return text_input.text(), accepted

    def _choose_item(
        self,
        title: str,
        prompt: str,
        items: list[str],
        initial_index: int = 0,
    ) -> tuple[str, bool]:
        """Show a compact, light-themed selection dialog."""
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setModal(True)
        self._apply_light_title_bar_to(dialog)
        dialog.setStyleSheet("""
            QDialog { background: #FFFFFF; }
            QLabel {
                color: #344054;
                background: transparent;
                font-family: "Segoe UI";
                font-size: 10pt;
            }
            QComboBox {
                background: #FFFFFF;
                color: #202938;
                border: 1px solid #B8C7D9;
                border-radius: 7px;
                padding: 8px 10px;
                font-family: "Segoe UI";
                font-size: 10pt;
            }
            QPushButton {
                background: #F1F4F8;
                color: #202938;
                border: 1px solid #DCE3EB;
                border-radius: 7px;
                padding: 7px 18px;
                min-width: 64px;
                font-family: "Segoe UI";
                font-size: 10pt;
                font-weight: 600;
            }
            QPushButton:hover { background: #E8EDF4; }
            QPushButton#primaryButton {
                background: #245FA8;
                color: #FFFFFF;
                border-color: #245FA8;
            }
        """)

        prompt_label = QLabel(prompt)
        combo = QComboBox()
        combo.addItems(items)
        if items:
            combo.setCurrentIndex(max(0, min(initial_index, len(items) - 1)))

        ok_button = QPushButton("OK")
        ok_button.setObjectName("primaryButton")
        cancel_button = QPushButton("Cancel")
        ok_button.clicked.connect(dialog.accept)
        cancel_button.clicked.connect(dialog.reject)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        buttons.addWidget(ok_button)
        buttons.addWidget(cancel_button)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)
        layout.addWidget(prompt_label)
        layout.addWidget(combo)
        layout.addLayout(buttons)

        dialog.setFixedWidth(400)
        accepted = dialog.exec() == QDialog.DialogCode.Accepted
        return combo.currentText(), accepted

    def _show_message(
        self,
        icon: QMessageBox.Icon,
        title: str,
        message: str,
        buttons: QMessageBox.StandardButton = QMessageBox.StandardButton.Ok,
        default_button: QMessageBox.StandardButton = QMessageBox.StandardButton.Ok,
    ) -> QMessageBox.StandardButton:
        """Show a compact custom dialog with controlled spacing and contrast."""
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setModal(True)
        self._apply_light_title_bar_to(dialog)
        dialog.setMinimumWidth(0)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #FFFFFF;
            }
            QLabel#dialogMessage {
                color: #202938;
                background: transparent;
                font-family: "Segoe UI";
                font-size: 10pt;
            }
            QLabel#dialogIcon {
                font-family: "Segoe UI Symbol";
                font-size: 22pt;
                font-weight: 700;
                border-radius: 20px;
                min-width: 40px;
                max-width: 40px;
                min-height: 40px;
                max-height: 40px;
            }
            QPushButton {
                background: #F1F4F8;
                color: #202938;
                border: 1px solid #DCE3EB;
                border-radius: 7px;
                padding: 7px 18px;
                min-width: 64px;
                font-family: "Segoe UI";
                font-size: 10pt;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #E8EDF4;
            }
            QPushButton:default {
                background: #245FA8;
                color: #FFFFFF;
                border-color: #245FA8;
            }
            QPushButton:default:hover {
                background: #1D508F;
            }
        """)

        if icon == QMessageBox.Icon.Warning:
            symbol, icon_style = "!", "background:#FFF0C2; color:#9A6700;"
        elif icon == QMessageBox.Icon.Question:
            symbol, icon_style = "?", "background:#E5F2FF; color:#1769AA;"
        elif icon == QMessageBox.Icon.Critical:
            symbol, icon_style = "×", "background:#FDEBEC; color:#B4232C;"
        else:
            symbol, icon_style = "i", "background:#E8F0FC; color:#245FA8;"

        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(14)

        icon_label = QLabel(symbol)
        icon_label.setObjectName("dialogIcon")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet(icon_style)
        content_layout.addWidget(
            icon_label, 0, Qt.AlignmentFlag.AlignTop
        )

        message_label = QLabel(message)
        message_label.setObjectName("dialogMessage")
        message_label.setWordWrap(True)
        message_label.setMaximumWidth(390)
        content_layout.addWidget(message_label, 1)

        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 8, 0, 0)
        button_layout.setSpacing(8)
        button_layout.addStretch(1)

        button_labels = (
            (QMessageBox.StandardButton.Yes, "Yes"),
            (QMessageBox.StandardButton.No, "No"),
            (QMessageBox.StandardButton.Save, "Save"),
            (QMessageBox.StandardButton.Discard, "Discard"),
            (QMessageBox.StandardButton.Cancel, "Cancel"),
            (QMessageBox.StandardButton.Ok, "OK"),
            (QMessageBox.StandardButton.Close, "Close"),
        )
        for standard_button, label in button_labels:
            if buttons & standard_button:
                button = QPushButton(label)
                button.setDefault(standard_button == default_button)
                button.clicked.connect(
                    lambda checked=False, result=standard_button: dialog.done(int(result))
                )
                button_layout.addWidget(button)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 18, 20, 16)
        layout.setSpacing(4)
        layout.addLayout(content_layout)
        layout.addLayout(button_layout)

        dialog.adjustSize()
        dialog.setFixedWidth(max(360, min(dialog.sizeHint().width(), 520)))
        return QMessageBox.StandardButton(dialog.exec())

    def on_capture_error(self, message: str) -> None:
        """Display a capture error reported by the worker."""
        self.recording_indicator.setText("●  Capture issue")
        self.recording_indicator.setStyleSheet(
            "background:#FFF4E5; color:#9A5B13; padding:7px 11px; border-radius:9px; font-weight:600;"
        )
        self.statusBar().showMessage(message)
        self._show_message(QMessageBox.Icon.Warning, "Caption capture", message)

    def on_recording_finished(self, session_id: str, status: str) -> None:
        """Restore controls and refresh history after capture ends."""
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.transcript_viewer.setReadOnly(False)
        self.rename_button.setEnabled(True)
        self.delete_button.setEnabled(True)
        self.export_button.setEnabled(self.current_session_id is not None)
        self.session_list.setEnabled(True)
        self.active_capture_session_id = None

        if status == "completed":
            self.recording_indicator.setText("●  Ready to capture")
            self.recording_indicator.setStyleSheet(
                "background:#EEF2F6; color:#475467; padding:7px 11px; border-radius:9px; font-weight:600;"
            )
        elif status == "interrupted":
            self.recording_indicator.setText("●  Capture ended")
            self.recording_indicator.setStyleSheet(
                "background:#FFF4E5; color:#9A5B13; padding:7px 11px; border-radius:9px; font-weight:600;"
            )
        else:
            self.recording_indicator.setText("●  Capture issue")
            self.recording_indicator.setStyleSheet(
                "background:#FFF4E5; color:#9A5B13; padding:7px 11px; border-radius:9px; font-weight:600;"
            )

        # The worker has finished writing files, so it is now safe to reload.
        self.refresh_sessions()

        if session_id:
            for row in range(self.session_list.count()):
                item = self.session_list.item(row)
                if item.data(Qt.ItemDataRole.UserRole) == session_id:
                    self.session_list.setCurrentItem(item)
                    break

        self.statusBar().showMessage(
            "Recording finished." if status == "completed"
            else f"Recording ended with status: {status}"
        )

    def update_editor_state(self) -> None:
        """Enable or disable editor controls according to unsaved changes."""
        has_session = self.current_session_id is not None
        is_dirty = (
            self.transcript_viewer.toPlainText() != self.saved_transcript
        )

        self.save_button.setEnabled(has_session and is_dirty)
        self.discard_button.setEnabled(has_session and is_dirty)
        recording = self.capture_worker is not None and self.capture_worker.isRunning()
        self.export_button.setEnabled(has_session and not recording)

        if has_session and is_dirty:
            self.session_title.setText(
                f"{self._current_session_name()} *"
            )

    def _current_session_name(self) -> str:
        """Return the current session's display name."""
        if not self.current_session_id:
            return "No session selected"

        session = self.history.get_session(self.current_session_id)
        if session is None:
            return self.current_session_id

        return session.get("name") or self.current_session_id

    def confirm_unsaved_changes(self) -> bool:
        """Ask how to handle unsaved changes before switching sessions."""
        current_text = self.transcript_viewer.toPlainText()

        if current_text == self.saved_transcript:
            return True

        answer = self._show_message(QMessageBox.Icon.Question, "Unsaved Changes",
            "You have unsaved transcript changes. Save them before "
            "continuing?",
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Save,
        )

        if answer == QMessageBox.StandardButton.Save:
            return self.save_transcript()

        if answer == QMessageBox.StandardButton.Discard:
            return True

        return False

    def refresh_sessions(self) -> None:
        """Reload saved sessions from disk."""
        if hasattr(self, "transcript_viewer"):
            if not self.confirm_unsaved_changes():
                return

        previous_id = self.current_session_id
        self.sessions = self.history.list_sessions()

        self.session_list.blockSignals(True)
        self.session_list.clear()

        selected_item = None

        for session in self.sessions:
            session_id = session.get("session_id", "")
            display_name = session.get("name") or session_id

            item = QListWidgetItem(display_name)
            item.setData(Qt.ItemDataRole.UserRole, session_id)
            self.session_list.addItem(item)

            if session_id == previous_id:
                selected_item = item

        self.session_list.blockSignals(False)

        if selected_item:
            self.session_list.setCurrentItem(selected_item)
            self.load_session(selected_item)
        elif self.session_list.count():
            self.session_list.setCurrentRow(0)
        else:
            self.current_session_id = None
            self.clear_selected_session()

        self.filter_sessions(self.search_input.text())

        self.statusBar().showMessage(
            f"{len(self.sessions)} saved session(s)"
        )

    def filter_sessions(self, query: str) -> None:
        """Filter the session list by metadata or transcript content."""
        query = query.strip().casefold()
        selected_id = self.current_session_id

        self.session_list.blockSignals(True)
        self.session_list.clear()

        first_match = None
        selected_match = None

        for session in self.sessions:
            session_id = session.get("session_id", "")
            name = session.get("name") or session_id
            started_at = session.get("started_at", "")
            status = session.get("status", "")

            searchable = f"{name} {session_id} {started_at} {status}"
            matches = not query or query in searchable.casefold()

            if query and not matches:
                try:
                    transcript = self.history.read_transcript(session_id)
                    matches = query in transcript.casefold()
                except (OSError, ValueError):
                    matches = False

            if not matches:
                continue

            item = QListWidgetItem(name)
            item.setData(Qt.ItemDataRole.UserRole, session_id)
            self.session_list.addItem(item)

            if first_match is None:
                first_match = item

            if session_id == selected_id:
                selected_match = item

        self.session_list.blockSignals(False)

        item_to_select = selected_match or first_match

        if item_to_select:
            self.session_list.setCurrentItem(item_to_select)
            if item_to_select.data(Qt.ItemDataRole.UserRole) != selected_id:
                self.load_session(item_to_select)
        else:
            self.current_session_id = None
            self.clear_selected_session()

    def on_session_selected(
        self,
        current: QListWidgetItem | None,
        previous: QListWidgetItem | None,
    ) -> None:
        """Handle session selection changes safely."""
        if current is None:
            return

        if not self.confirm_unsaved_changes():
            self.session_list.blockSignals(True)
            if previous is not None:
                self.session_list.setCurrentItem(previous)
            self.session_list.blockSignals(False)
            return

        self.load_session(current)

    def load_session(self, item: QListWidgetItem) -> None:
        """Load a session's metadata and transcript."""
        session_id = item.data(Qt.ItemDataRole.UserRole)
        session = self.history.get_session(session_id)

        if session is None:
            self.clear_selected_session()
            return

        try:
            transcript = self.history.read_transcript(session_id)
        except (OSError, ValueError) as exc:
            self._show_message(QMessageBox.Icon.Warning, "Unable to open transcript",
                f"Could not read this transcript:\n{exc}",
            )
            return

        self.current_session_id = session_id
        self.saved_transcript = transcript

        self.transcript_viewer.blockSignals(True)
        self.transcript_viewer.setPlainText(transcript)
        self.transcript_viewer.blockSignals(False)

        name = session.get("name") or session_id
        duration = session.get("duration_seconds")

        if duration is None:
            duration_text = "Not available"
        else:
            total_seconds = int(duration)
            minutes, seconds = divmod(total_seconds, 60)
            hours, minutes = divmod(minutes, 60)
            duration_text = (
                f"{hours}h {minutes}m {seconds}s"
                if hours
                else f"{minutes}m {seconds}s"
            )

        self.session_title.setText(name)
        self.session_details.setText(
            f"Started: {session.get('started_at', 'Unknown')}\n"
            f"Ended: {session.get('ended_at') or 'In progress'}\n"
            f"Duration: {duration_text}\n"
            f"Status: {session.get('status', 'unknown')}"
        )

        self.update_editor_state()
        self.statusBar().showMessage(f"Opened: {name}")

    def save_transcript(self) -> bool:
        """Save the edited transcript to its session file."""
        if not self.current_session_id:
            return False

        transcript = self.transcript_viewer.toPlainText()

        session = self.history.get_session(self.current_session_id)
        if session is None:
            self._show_message(QMessageBox.Icon.Warning, "Session not found",
                "The selected session no longer exists.",
            )
            return False

        session_dir = Path(session["_directory"])
        transcript_name = session.get("transcript_file", "transcript.txt")
        transcript_path = session_dir / transcript_name

        try:
            if transcript_path.resolve().parent != session_dir.resolve():
                raise ValueError("Invalid transcript path.")

            transcript_path.write_text(transcript, encoding="utf-8")
        except (OSError, ValueError) as exc:
            self._show_message(QMessageBox.Icon.Warning, "Save failed",
                f"Could not save the transcript:\n{exc}",
            )
            return False

        self.saved_transcript = transcript
        self.update_editor_state()
        self.statusBar().showMessage("Transcript saved successfully")
        return True

    def export_selected_session(self) -> None:
        """Export the selected transcript to a user-chosen file."""
        if not self.current_session_id:
            self._show_message(QMessageBox.Icon.Information, "No session selected", "Select a session before exporting."
            )
            return

        if self.capture_worker is not None and self.capture_worker.isRunning():
            self._show_message(QMessageBox.Icon.Information, "Recording in progress",
                "Stop the recording before exporting this session."
            )
            return

        session = self.history.get_session(self.current_session_id)
        if session is None:
            self._show_message(QMessageBox.Icon.Warning, "Session not found", "This session could not be found.")
            return

        formats = ["Plain text (*.txt)", "Markdown (*.md)", "JSON (*.json)", "SubRip subtitles (*.srt)"]
        selected, accepted = self._choose_item(
            "Export Transcript", "Choose an export format:", formats, 0
        )
        if not accepted:
            return

        extensions = {formats[0]: "txt", formats[1]: "md", formats[2]: "json", formats[3]: "srt"}
        extension = extensions[selected]
        session_name = session.get("name") or session.get("session_id", "transcript")
        safe_name = "".join(char if char.isalnum() or char in " -_" else "_" for char in session_name).strip()
        default_path = str(Path.home() / "Documents" / f"{safe_name or 'transcript'}.{extension}")
        # Use Qt's non-native file dialog to avoid OLE/COM conflicts with
        # pywinauto, and style it to match the rest of the application.
        dialog = QFileDialog(self, "Save Export", default_path)
        dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
        dialog.setFileMode(QFileDialog.FileMode.AnyFile)
        dialog.setNameFilters([selected, "All files (*)"])
        dialog.selectNameFilter(selected)
        dialog.setDefaultSuffix(extension)
        dialog.setOption(QFileDialog.Option.DontUseNativeDialog, True)

        # Keep Qt's default locations (including My Computer) and add useful
        # Windows folder shortcuts to the navigation sidebar.
        sidebar_urls = list(dialog.sidebarUrls())
        known_urls = {url.toString() for url in sidebar_urls}
        shortcut_locations = (
            QStandardPaths.StandardLocation.DesktopLocation,
            QStandardPaths.StandardLocation.DocumentsLocation,
            QStandardPaths.StandardLocation.DownloadLocation,
            QStandardPaths.StandardLocation.PicturesLocation,
        )
        for location in shortcut_locations:
            folder = QStandardPaths.writableLocation(location)
            if folder and Path(folder).is_dir():
                url = QUrl.fromLocalFile(folder)
                if url.toString() not in known_urls:
                    sidebar_urls.append(url)
                    known_urls.add(url.toString())
        dialog.setSidebarUrls(sidebar_urls)

        self._apply_light_title_bar_to(dialog)
        dialog.resize(860, 560)
        dialog.setStyleSheet("""
            QFileDialog {
                background: #F5F7FA;
                color: #202938;
                font-family: "Segoe UI";
                font-size: 10pt;
            }
            QFileDialog QWidget {
                font-family: "Segoe UI";
                font-size: 10pt;
            }
            QLabel {
                color: #344054;
                background: transparent;
            }
            QLineEdit {
                background: #FFFFFF;
                color: #202938;
                border: 1px solid #B8C7D9;
                border-radius: 6px;
                padding: 6px 8px;
                selection-background-color: #245FA8;
                selection-color: #FFFFFF;
            }
            QLineEdit:focus { border: 1px solid #4B83D1; }
            QTreeView, QListView {
                background: #FFFFFF;
                alternate-background-color: #F7F9FC;
                color: #202938;
                border: 1px solid #DCE3EB;
                border-radius: 6px;
                outline: 0;
                selection-background-color: #245FA8;
                selection-color: #FFFFFF;
            }
            QTreeView::item, QListView::item {
                padding: 5px;
                border-radius: 3px;
            }
            QTreeView::item:hover, QListView::item:hover {
                background: #EAF1FA;
                color: #202938;
            }
            /* Keep the entire file-list header area light, including unused
               space to the right of the final column and the corner button. */
            QHeaderView {
                background-color: #F1F4F8;
                color: #475467;
                border: none;
            }
            QHeaderView::section {
                background-color: #F1F4F8;
                color: #475467;
                border: none;
                border-bottom: 1px solid #DCE3EB;
                padding: 7px 8px;
                font-weight: 600;
            }
            QTableCornerButton::section {
                background-color: #F1F4F8;
                border: none;
                border-bottom: 1px solid #DCE3EB;
            }
            QComboBox {
                background: #FFFFFF;
                color: #202938;
                border: 1px solid #B8C7D9;
                border-radius: 6px;
                padding: 6px 8px;
                min-height: 20px;
            }
            QComboBox QAbstractItemView {
                background: #FFFFFF;
                color: #202938;
                selection-background-color: #245FA8;
                selection-color: #FFFFFF;
                border: 1px solid #DCE3EB;
            }
            QPushButton, QToolButton {
                background: #FFFFFF;
                color: #344054;
                border: 1px solid #D0D9E4;
                border-radius: 6px;
                padding: 6px 11px;
            }
            QPushButton:hover, QToolButton:hover {
                background: #EAF1FA;
                border-color: #B8C7D9;
            }
            QPushButton:pressed, QToolButton:pressed { background: #DCE8F7; }
            QPushButton:default {
                background: #245FA8;
                color: #FFFFFF;
                border-color: #245FA8;
                font-weight: 600;
            }
            QDialogButtonBox QPushButton {
                min-width: 76px;
                padding: 7px 14px;
            }
            QScrollBar:vertical {
                background: #F5F7FA;
                width: 12px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #C5CFDB;
                border-radius: 5px;
                min-height: 24px;
            }
            QScrollBar::handle:vertical:hover { background: #AAB8C8; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }
            QSplitter::handle { background: #E4EAF1; }
        """)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        selected_files = dialog.selectedFiles()
        destination = selected_files[0] if selected_files else ""
        if not destination:
            return

        if Path(destination).suffix.lower() != f".{extension}":
            destination = f"{destination}.{extension}"

        try:
            session_dir = Path(session["_directory"])
            timestamped_name = session.get(
                "timestamped_transcript_file", "timestamped_transcript.txt"
            )
            timestamped_path = session_dir / timestamped_name
            if timestamped_path.resolve().parent != session_dir.resolve():
                raise ValueError("Invalid timestamped transcript path in session metadata.")

            export_session(
                destination=destination,
                file_format=extension,
                transcript=self.transcript_viewer.toPlainText(),
                metadata=session,
                timestamped_transcript_path=timestamped_path,
            )
        except (OSError, ValueError) as exc:
            self._show_message(QMessageBox.Icon.Warning, "Export failed", f"Could not export the transcript:\n{exc}")
            return

        self.statusBar().showMessage(f"Transcript exported: {destination}")
        self._show_message(QMessageBox.Icon.Information, "Export complete", f"Transcript exported successfully:\n{destination}")

    def discard_transcript_changes(self) -> None:
        """Restore the last saved transcript."""
        self.transcript_viewer.blockSignals(True)
        self.transcript_viewer.setPlainText(self.saved_transcript)
        self.transcript_viewer.blockSignals(False)
        self.update_editor_state()

        self.statusBar().showMessage("Unsaved changes discarded")

    def rename_selected_session(self) -> None:
        """Rename the currently selected session."""
        item = self.session_list.currentItem()

        if item is None:
            self._show_message(QMessageBox.Icon.Information, "No session selected",
                "Select a session before renaming it.",
            )
            return

        if not self.confirm_unsaved_changes():
            return

        session_id = item.data(Qt.ItemDataRole.UserRole)
        session = self.history.get_session(session_id)

        if session is None:
            self._show_message(QMessageBox.Icon.Warning, "Session not found",
                "This session could not be found. Try refreshing the list.",
            )
            return

        current_name = session.get("name") or session_id
        new_name, accepted = self._ask_text(
            "Rename Session",
            "Enter a name for this recording:",
            current_name,
        )

        if not accepted:
            return

        new_name = new_name.strip()

        if not new_name:
            self._show_message(QMessageBox.Icon.Warning, "Invalid name",
                "The session name cannot be empty.",
            )
            return

        try:
            self.history.rename_session(session_id, new_name)
        except (OSError, ValueError) as exc:
            self._show_message(QMessageBox.Icon.Warning, "Rename failed",
                f"Could not rename this session:\n{exc}",
            )
            return

        self.refresh_sessions()
        self.statusBar().showMessage(f"Session renamed to: {new_name}")

    def delete_selected_session(self) -> None:
        """Delete the selected session after explicit confirmation."""
        item = self.session_list.currentItem()

        if item is None:
            self._show_message(QMessageBox.Icon.Information, "No session selected",
                "Select a session before deleting it.",
            )
            return

        if not self.confirm_unsaved_changes():
            return

        session_id = item.data(Qt.ItemDataRole.UserRole)
        session = self.history.get_session(session_id)

        if session is None:
            self._show_message(QMessageBox.Icon.Warning, "Session not found",
                "This session could not be found. Try refreshing the list.",
            )
            return

        session_name = session.get("name") or session_id

        answer = self._show_message(QMessageBox.Icon.Question, "Delete Session",
            f"Permanently delete '{session_name}' and all its files?\n\n"
            "This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        try:
            self.history.delete_session(session_id)
        except (OSError, ValueError) as exc:
            self._show_message(QMessageBox.Icon.Warning, "Delete failed",
                f"Could not delete this session:\n{exc}",
            )
            return

        # Clear the deleted session before refreshing the list.
        self.session_list.blockSignals(True)
        self.session_list.clearSelection()
        self.session_list.setCurrentRow(-1)
        self.session_list.blockSignals(False)

        self.clear_selected_session()
        self.refresh_sessions()
        self.statusBar().showMessage(f"Deleted session: {session_name}")

    def clear_selected_session(self) -> None:
        """Clear the transcript panel when no session is selected."""
        self.current_session_id = None
        self.saved_transcript = ""

        self.transcript_viewer.blockSignals(True)
        self.transcript_viewer.clear()
        self.transcript_viewer.blockSignals(False)

        self.session_title.setText("No session selected")
        self.session_details.setText(
            "Select a recording from the session list."
        )

        self.update_editor_state()

    def showEvent(self, event) -> None:
        """Apply a light native Windows title bar when the window is shown."""
        super().showEvent(event)
        self._set_light_title_bar()

    def _set_light_title_bar(self) -> None:
        """Request a light native title bar for the main application window."""
        self._apply_light_title_bar_to(self)

    def closeEvent(self, event) -> None:
        """Stop active capture safely before closing the application."""
        if not self.confirm_unsaved_changes():
            event.ignore()
            return

        if self.capture_worker is not None and self.capture_worker.isRunning():
            answer = self._show_message(QMessageBox.Icon.Question, "Recording in progress",
                "A recording is in progress. Stop it and close the application?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )
            if answer != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
            self.capture_worker.stop()
            self.capture_worker.wait(3000)
            if self.capture_worker.isRunning():
                self._show_message(QMessageBox.Icon.Warning, "Capture still stopping",
                    "Caption capture is still stopping. Please try closing again.",
                )
                event.ignore()
                return

        event.accept()
