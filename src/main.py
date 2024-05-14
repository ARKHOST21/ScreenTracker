import sys
import os
import datetime
import json
import shutil
import time
import psutil
from PyQt5.QtWidgets import (QApplication, QMenu, qApp, QSystemTrayIcon, QGroupBox, QWidget, QVBoxLayout, QPushButton, QFileDialog, QLabel, QLineEdit, QMessageBox, QComboBox, QCheckBox, QDialog, QListWidget, QListWidgetItem, QAbstractItemView, QDialogButtonBox, QScrollArea)
from PyQt5.QtCore import QTimer, QDateTime, Qt
from PyQt5.QtGui import QIcon, QPixmap
from mss import mss
from PIL import Image, ImageChops
from dateutil.relativedelta import relativedelta

# Determine if the app is frozen using PyInstaller
if getattr(sys, 'frozen', False):
    current_path = sys._MEIPASS
else:
    current_path = os.path.abspath(os.path.dirname(__file__))

icon_folder_path = os.path.join(current_path, 'icons')
icon_path = os.path.join(icon_folder_path, 'app_icon.ico')

def load_translations(language_code):
    translation_file = os.path.join(current_path, 'lang', f'{language_code}.json')
    try:
        with open(translation_file, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        QMessageBox.warning(None, "Translation Error", f"Translation file for language '{language_code}' not found.")
        return {}

class ScreenshotViewer(QDialog):
    def __init__(self, screenshot_folder, tr):
        super().__init__()
        self.tr = tr
        self.setWindowTitle(tr("screenshot_viewer"))
        self.setGeometry(100, 100, 800, 600)
        self.screenshot_folder = screenshot_folder
        self.current_folder = screenshot_folder

        self.layout = QVBoxLayout(self)
        
        self.backButton = QPushButton(tr("back"))
        self.backButton.clicked.connect(self.navigate_up)
        self.layout.addWidget(self.backButton)
        
        self.scrollArea = QScrollArea(self)
        self.imageLabel = QLabel(self)
        self.imageLabel.setScaledContents(True)
        self.scrollArea.setWidget(self.imageLabel)
        self.layout.addWidget(self.scrollArea)
        
        self.screenshotList = QListWidget(self)
        self.screenshotList.setSelectionMode(QAbstractItemView.SingleSelection)
        self.screenshotList.itemDoubleClicked.connect(self.navigate_down)
        self.screenshotList.itemSelectionChanged.connect(self.load_selected_image)
        self.layout.addWidget(self.screenshotList)
        
        self.load_screenshots(self.current_folder)
        
    def load_screenshots(self, folder):
        self.screenshotList.clear()
        self.imageLabel.clear()
        self.current_folder = folder
        if self.current_folder != self.screenshot_folder:
            self.backButton.setEnabled(True)
        else:
            self.backButton.setEnabled(False)
        for item_name in os.listdir(folder):
            item_path = os.path.join(folder, item_name)
            if os.path.isdir(item_path):
                item = QListWidgetItem(f"[{self.tr('folder')}] {item_name}")
            elif item_name.endswith(('.png', '.jpeg', '.jpg')):
                item = QListWidgetItem(item_name)
            else:
                continue
            item.setData(Qt.UserRole, item_path)
            self.screenshotList.addItem(item)
                
    def load_selected_image(self):
        selected_item = self.screenshotList.currentItem()
        if selected_item and not selected_item.text().startswith(f"[{self.tr('folder')}]"):
            image_path = selected_item.data(Qt.UserRole)
            pixmap = QPixmap(image_path)
            self.imageLabel.setPixmap(pixmap)
            self.imageLabel.adjustSize()

    def navigate_up(self):
        parent_folder = os.path.dirname(self.current_folder)
        if parent_folder and os.path.isdir(parent_folder):
            self.load_screenshots(parent_folder)
        
    def navigate_down(self, item):
        if item.text().startswith(f"[{self.tr('folder')}]"):
            folder_path = item.data(Qt.UserRole)
            if os.path.isdir(folder_path):
                self.load_screenshots(folder_path)

class WorkTrackerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.language_code = 'english'  # Default language
        self.translations = load_translations(self.language_code)
        self.tr = lambda key: self.translations.get(key, key)
        self.setWindowTitle(self.tr("app_title"))
        self.setGeometry(100, 100, 320, 400)
        self.setWindowIcon(QIcon(icon_path))
        self.screenshots_folder = None
        self.settings_file = 'app_settings.json'
        self.max_folder_age = relativedelta(weeks=13)
        self.dark_mode_enabled = False
        self.screenshot_format = 'PNG'
        self.monitor_selection = []
        self.retention_period_days = 30  # Default retention period
        self.initUI()
        self.load_settings()
        self.timer = QTimer()
        self.timer.timeout.connect(self.take_and_save_screenshots)
        # System Tray Icon Setup
        self.trayIcon = QSystemTrayIcon(self)
        self.trayIcon.setIcon(QIcon(icon_path))
        self.trayIcon.setToolTip(self.tr("app_title"))

        # Right-click Menu for Tray Icon
        trayMenu = QMenu()
        openAction = trayMenu.addAction(self.tr("open"))
        openAction.triggered.connect(self.showNormal)
        exitAction = trayMenu.addAction(self.tr("exit"))
        exitAction.triggered.connect(qApp.quit)

        self.trayIcon.setContextMenu(trayMenu)
        self.trayIcon.show()

        # Automatic cleanup timer
        self.cleanup_timer = QTimer()
        self.cleanup_timer.timeout.connect(self.automatic_cleanup)
        self.cleanup_timer.start(86400000)  # Run cleanup every 24 hours

    def closeEvent(self, event):
        """Override the close event to minimize to system tray."""
        event.ignore()
        self.hide()
        self.trayIcon.showMessage(self.tr("app_title"), 
                                  self.tr("minimized_to_tray"),
                                  QSystemTrayIcon.Information,
                                  2000)

    def initUI(self):
        self.layout = QVBoxLayout(self)

        # Language Selection
        self.languageComboBox = QComboBox()
        self.languageComboBox.addItems(["English", "Dutch", "Spanish", "Russian", "Italian", "German", "French", "Armenian", "Georgian", "Bulgarian", "Polish"])
        self.languageComboBox.currentIndexChanged.connect(self.change_language)
        self.languageLabel = QLabel("Select Language:")
        self.layout.addWidget(self.languageLabel)
        self.layout.addWidget(self.languageComboBox)

        # General Settings Section
        generalSettingsGroup = QGroupBox(self.tr("general_settings"))
        generalLayout = QVBoxLayout()

        self.folderLabel = QLabel(self.tr("output_folder_not_set"))
        generalLayout.addWidget(self.folderLabel)

        self.browseButton = QPushButton(self.tr("set_output_folder"))
        self.browseButton.clicked.connect(self.set_output_folder)
        generalLayout.addWidget(self.browseButton)

        self.intervalInput = QLineEdit("5")
        self.intervalLabel = QLabel(self.tr("screenshot_interval"))
        generalLayout.addWidget(self.intervalLabel)
        generalLayout.addWidget(self.intervalInput)

        self.formatComboBox = QComboBox()
        self.formatComboBox.addItems(["PNG", "JPEG"])
        self.formatLabel = QLabel(self.tr("screenshot_format"))
        generalLayout.addWidget(self.formatLabel)
        generalLayout.addWidget(self.formatComboBox)

        self.retentionInput = QLineEdit(str(self.retention_period_days))
        self.retentionLabel = QLabel(self.tr("retention_period"))
        generalLayout.addWidget(self.retentionLabel)
        generalLayout.addWidget(self.retentionInput)

        generalSettingsGroup.setLayout(generalLayout)
        self.layout.addWidget(generalSettingsGroup)

        # Monitor Selection Section
        monitorSelectionGroup = QGroupBox(self.tr("monitor_selection"))
        monitorLayout = QVBoxLayout()
        self.monitorCheckboxes = QVBoxLayout()
        self.populateMonitorCheckboxes()
        monitorLayout.addLayout(self.monitorCheckboxes)
        monitorSelectionGroup.setLayout(monitorLayout)
        self.layout.addWidget(monitorSelectionGroup)

        # Control and Management Section
        controlGroup = QGroupBox(self.tr("control_management"))
        controlLayout = QVBoxLayout()

        self.startButton = QPushButton(self.tr("start"))
        self.startButton.clicked.connect(self.start_capture)
        controlLayout.addWidget(self.startButton)

        self.stopButton = QPushButton(self.tr("stop"))
        self.stopButton.clicked.connect(self.stop_capture)
        controlLayout.addWidget(self.stopButton)

        self.statusIndicator = QLabel(self.tr("stopped"))
        controlLayout.addWidget(self.statusIndicator)

        self.toggleDarkModeButton = QPushButton(self.tr("enable_dark_mode"))
        self.toggleDarkModeButton.clicked.connect(self.toggle_dark_mode)
        controlLayout.addWidget(self.toggleDarkModeButton)

        self.exportSettingsButton = QPushButton(self.tr("export_settings"))
        self.exportSettingsButton.clicked.connect(self.export_settings)
        controlLayout.addWidget(self.exportSettingsButton)

        self.importSettingsButton = QPushButton(self.tr("import_settings"))
        self.importSettingsButton.clicked.connect(self.import_settings)
        controlLayout.addWidget(self.importSettingsButton)

        self.viewScreenshotsButton = QPushButton(self.tr("view_screenshots"))
        self.viewScreenshotsButton.clicked.connect(self.open_screenshot_viewer)
        controlLayout.addWidget(self.viewScreenshotsButton)

        self.diskSpaceButton = QPushButton(self.tr("disk_space_info"))
        self.diskSpaceButton.clicked.connect(self.show_disk_space_info)
        controlLayout.addWidget(self.diskSpaceButton)

        self.cleanFoldersButton = QPushButton(self.tr("clean_folders"))
        self.cleanFoldersButton.clicked.connect(self.clean_folders)
        controlLayout.addWidget(self.cleanFoldersButton)

        # System Status Monitoring
        self.cpu_label = QLabel(self.tr("cpu_usage") + ": 0%")
        self.memory_label = QLabel(self.tr("memory_usage") + ": 0%")
        controlLayout.addWidget(self.cpu_label)
        controlLayout.addWidget(self.memory_label)

        self.system_status_timer = QTimer()
        self.system_status_timer.timeout.connect(self.update_system_status)
        self.system_status_timer.start(1000)  # Update every second

        controlGroup.setLayout(controlLayout)
        self.layout.addWidget(controlGroup)

    def change_language(self):
        language_map = {
            "English": "english",
            "Dutch": "dutch",
            "Spanish": "spanish",
            "Russian": "russian",
            "Italian": "italian",
            "German": "german",
            "French": "french",
            "Armenian": "armenian",
            "Georgian": "georgian",
            "Bulgarian": "bulgarian",
            "Polish": "polish"
        }
        selected_language = self.languageComboBox.currentText()
        self.language_code = language_map.get(selected_language, "english")
        self.translations = load_translations(self.language_code)
        self.tr = lambda key: self.translations.get(key, key)
        self.update_ui_texts()

    def update_ui_texts(self):
        self.setWindowTitle(self.tr("app_title"))
        self.languageLabel.setText(self.tr("select_language"))
        self.folderLabel.setText(self.tr("output_folder_not_set"))
        self.browseButton.setText(self.tr("set_output_folder"))
        self.intervalLabel.setText(self.tr("screenshot_interval"))
        self.formatLabel.setText(self.tr("screenshot_format"))
        self.retentionLabel.setText(self.tr("retention_period"))
        self.startButton.setText(self.tr("start"))
        self.stopButton.setText(self.tr("stop"))
        self.statusIndicator.setText(self.tr("stopped"))
        self.toggleDarkModeButton.setText(self.tr("enable_dark_mode") if not self.dark_mode_enabled else self.tr("enable_light_mode"))
        self.exportSettingsButton.setText(self.tr("export_settings"))
        self.importSettingsButton.setText(self.tr("import_settings"))
        self.viewScreenshotsButton.setText(self.tr("view_screenshots"))
        self.diskSpaceButton.setText(self.tr("disk_space_info"))
        self.cleanFoldersButton.setText(self.tr("clean_folders"))
        self.cpu_label.setText(self.tr("cpu_usage") + ": 0%")
        self.memory_label.setText(self.tr("memory_usage") + ": 0%")
        
        # Update group box titles
        self.layout.itemAt(2).widget().setTitle(self.tr("general_settings"))
        self.layout.itemAt(3).widget().setTitle(self.tr("monitor_selection"))
        self.layout.itemAt(4).widget().setTitle(self.tr("control_management"))
        
        # Update monitor checkboxes
        for i in range(self.monitorCheckboxes.count()):
            self.monitorCheckboxes.itemAt(i).widget().setText(f"{self.tr('monitor')} {i+1}")

    def populateMonitorCheckboxes(self):
        with mss() as sct:
            for i, monitor in enumerate(sct.monitors[1:], start=1):
                checkbox = QCheckBox(f"{self.tr('monitor')} {i}")
                checkbox.setChecked(True)  # Default to checked
                self.monitorCheckboxes.addWidget(checkbox)

    def set_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, self.tr("select_folder"))
        if folder:
            self.screenshots_folder = folder
            self.folderLabel.setText(f"{self.tr('output_folder')}: {self.screenshots_folder}")
            self.save_settings()

    def start_capture(self):
        if not self.screenshots_folder:
            QMessageBox.warning(self, self.tr("output_folder_not_set"), self.tr("please_set_output_folder"))
            return
        try:
            interval_minutes = int(self.intervalInput.text())
            if interval_minutes <= 0:
                raise ValueError(self.tr("interval_positive_integer"))
            interval_milliseconds = interval_minutes * 60 * 1000
            self.timer.start(interval_milliseconds)
            self.update_status_indicator(True)
        except ValueError:
            QMessageBox.warning(self, self.tr("invalid_input"), self.tr("please_enter_valid_integer"))

    def stop_capture(self):
        self.timer.stop()
        self.update_status_indicator(False)

    def take_and_save_screenshots(self):
        if self.screenshots_folder:
            todays_folder = self.create_todays_folder()
            now = datetime.datetime.now()

            with mss() as sct:
                for i, monitor in enumerate(sct.monitors[1:], start=1):
                    if not self.monitorCheckboxes.layout().itemAt(i-1).widget().isChecked():
                        continue
                    screenshot_file = f"screen_{i}_{now.strftime('%Y-%m-%d_%H-%M-%S')}.{self.formatComboBox.currentText().lower()}"
                    screenshot_path = os.path.join(todays_folder, screenshot_file)

                    sct_img = sct.grab(monitor)
                    img = Image.frombytes("RGB", sct_img.size, sct_img.rgb)

                    if not self.is_black_image(img):
                        img.save(screenshot_path)

            self.update_status_indicator(True)

    def is_black_image(self, img):
        black = Image.new('RGB', img.size, (0, 0, 0))
        difference = ImageChops.difference(img, black)
        return not difference.getbbox()

    def update_status_indicator(self, is_capturing):
        if is_capturing:
            next_capture_time = QDateTime.currentDateTime().addSecs(int(self.intervalInput.text()) * 60)
            self.statusIndicator.setText(f'{self.tr("active")} - {self.tr("next_capture_at")}: {next_capture_time.toString("hh:mm:ss")}')
        else:
            self.statusIndicator.setText(self.tr("stopped"))
        self.statusIndicator.setStyleSheet('color: green;' if is_capturing else 'color: red;')
        self.statusIndicator.adjustSize()

    def create_todays_folder(self):
        today = datetime.date.today()
        todays_folder = os.path.join(self.screenshots_folder, today.strftime("%Y-%m-%d"))
        os.makedirs(todays_folder, exist_ok=True)
        return todays_folder

    def toggle_dark_mode(self):
        self.dark_mode_enabled = not self.dark_mode_enabled
        self.update_dark_mode()

    def update_dark_mode(self):
        if self.dark_mode_enabled:
            self.setStyleSheet("QWidget { background-color: #353535; color: #FFFFFF; }")
            self.toggleDarkModeButton.setText(self.tr("enable_light_mode"))
        else:
            self.setStyleSheet("")
            self.toggleDarkModeButton.setText(self.tr("enable_dark_mode"))
        self.save_settings()

    def save_settings(self):
        settings = {
            'screenshots_folder': self.screenshots_folder,
            'dark_mode_enabled': self.dark_mode_enabled,
            'interval_minutes': self.intervalInput.text(),
            'screenshot_format': self.formatComboBox.currentText(),
            'retention_period_days': self.retentionInput.text(),
            'selected_monitors': [self.monitorCheckboxes.layout().itemAt(i).widget().isChecked() for i in range(self.monitorCheckboxes.layout().count())]
        }
        with open(self.settings_file, 'w') as f:
            json.dump(settings, f)

    def load_settings(self):
        try:
            with open(self.settings_file) as f:
                settings = json.load(f)
                self.screenshots_folder = settings.get('screenshots_folder')
                self.dark_mode_enabled = settings.get('dark_mode_enabled', False)
                self.intervalInput.setText(str(settings.get('interval_minutes', 5)))
                self.formatComboBox.setCurrentText(settings.get('screenshot_format', 'PNG'))
                self.retention_period_days = int(settings.get('retention_period_days', 30))
                self.retentionInput.setText(str(self.retention_period_days))
                for i, checked in enumerate(settings.get('selected_monitors', [])):
                    if i < self.monitorCheckboxes.layout().count():
                        self.monitorCheckboxes.layout().itemAt(i).widget().setChecked(checked)
                self.update_dark_mode()
                self.folderLabel.setText(f"{self.tr('output_folder')}: {self.screenshots_folder if self.screenshots_folder else self.tr('output_folder_not_set')}")
        except FileNotFoundError:
            pass

    def export_settings(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getSaveFileName(self, self.tr("export_settings"), "", "JSON Files (*.json)", options=options)
        if fileName:
            settings = {
                'screenshots_folder': self.screenshots_folder,
                'dark_mode_enabled': self.dark_mode_enabled,
                'interval_minutes': self.intervalInput.text(),
                'screenshot_format': self.formatComboBox.currentText(),
                'retention_period_days': self.retentionInput.text(),
                'selected_monitors': [self.monitorCheckboxes.layout().itemAt(i).widget().isChecked() for i in range(self.monitorCheckboxes.layout().count())]
            }
            with open(fileName, 'w') as file:
                json.dump(settings, file)
            QMessageBox.information(self, self.tr("export_successful"), self.tr("settings_exported_successfully"))

    def import_settings(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(self, self.tr("import_settings"), "", "JSON Files (*.json)", options=options)
        if fileName:
            with open(fileName, 'r') as file:
                settings = json.load(file)
                self.apply_settings(settings)
            QMessageBox.information(self, self.tr("import_successful"), self.tr("settings_imported_successfully"))
            self.load_settings()

    def apply_settings(self, settings):
        self.screenshots_folder = settings.get('screenshots_folder')
        self.dark_mode_enabled = settings.get('dark_mode_enabled', False)
        self.intervalInput.setText(str(settings.get('interval_minutes', 5)))
        self.formatComboBox.setCurrentText(settings.get('screenshot_format', 'PNG'))
        self.retention_period_days = int(settings.get('retention_period_days', 30))
        self.retentionInput.setText(str(self.retention_period_days))
        for i, checked in enumerate(settings.get('selected_monitors', [])):
            if i < self.monitorCheckboxes.layout().count():
                self.monitorCheckboxes.layout().itemAt(i).widget().setChecked(checked)
        self.update_dark_mode()
        if self.screenshots_folder:
            self.folderLabel.setText(f"{self.tr('output_folder')}: {self.screenshots_folder}")
        else:
            self.folderLabel.setText(self.tr("output_folder_not_set"))
        self.save_settings()

    def open_screenshot_viewer(self):
        if not self.screenshots_folder:
            QMessageBox.warning(self, self.tr("output_folder_not_set"), self.tr("please_set_output_folder"))
            return    
        if self.screenshots_folder:
            viewer = ScreenshotViewer(self.screenshots_folder, self.tr)
            viewer.exec_()

    def show_disk_space_info(self):
        if self.screenshots_folder:
            total, used, free = shutil.disk_usage(self.screenshots_folder)
            total_gb = total / (1024 ** 3)
            used_gb = used / (1024 ** 3)
            free_gb = free / (1024 ** 3)
            QMessageBox.information(self, self.tr("disk_space_info"), 
                                    f"{self.tr('total')}: {total_gb:.2f} GB\n{self.tr('used')}: {used_gb:.2f} GB\n{self.tr('free')}: {free_gb:.2f} GB")
        else:
            QMessageBox.warning(self, self.tr("output_folder_not_set"), self.tr("please_set_output_folder"))

    def clean_folders(self):
        if not self.screenshots_folder:
            QMessageBox.warning(self, self.tr("output_folder_not_set"), self.tr("please_set_output_folder"))
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(self.tr("clean_folders"))
        dialog.setGeometry(100, 100, 300, 400)

        layout = QVBoxLayout(dialog)

        self.folderListWidget = QListWidget()
        self.folderListWidget.setSelectionMode(QAbstractItemView.MultiSelection)
        layout.addWidget(self.folderListWidget)

        buttonBox = QDialogButtonBox()
        deleteButton = buttonBox.addButton(self.tr("delete"), QDialogButtonBox.AcceptRole)
        closeButton = buttonBox.addButton(self.tr("close"), QDialogButtonBox.RejectRole)
        deleteButton.setEnabled(False)
        buttonBox.accepted.connect(dialog.accept)
        buttonBox.rejected.connect(dialog.reject)
        layout.addWidget(buttonBox)

        self.folderListWidget.itemSelectionChanged.connect(lambda: deleteButton.setEnabled(bool(self.folderListWidget.selectedItems())))

        self.load_folders()

        if dialog.exec_() == QDialog.Accepted:
            selected_folders = [item.text() for item in self.folderListWidget.selectedItems()]
            if selected_folders:
                reply = QMessageBox.question(self, self.tr("confirm_deletion"), self.tr("confirm_delete_folders"),
                                             QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply == QMessageBox.Yes:
                    self.delete_selected_folders(selected_folders)

    def load_folders(self):
        self.folderListWidget.clear()
        if self.screenshots_folder:
            folders = [f for f in os.listdir(self.screenshots_folder) if os.path.isdir(os.path.join(self.screenshots_folder, f))]
            self.folderListWidget.addItems(folders)

    def delete_selected_folders(self, selected_folders):
        for folder in selected_folders:
            folder_path = os.path.join(self.screenshots_folder, folder)
            if os.path.isdir(folder_path):
                try:
                    for root, dirs, files in os.walk(folder_path, topdown=False):
                        for name in files:
                            os.remove(os.path.join(root, name))
                        for name in dirs:
                            os.rmdir(os.path.join(root, name))
                    os.rmdir(folder_path)
                except Exception as e:
                    QMessageBox.warning(self, self.tr("error_deleting_folder"), f"{self.tr('error_deleting_folder')}: {folder} - {e}")

    def automatic_cleanup(self):
        if self.screenshots_folder:
            now = time.time()
            retention_time = self.retention_period_days * 86400  # Convert days to seconds
            for root, dirs, files in os.walk(self.screenshots_folder):
                for name in files:
                    file_path = os.path.join(root, name)
                    if os.stat(file_path).st_mtime < now - retention_time:
                        os.remove(file_path)
                for name in dirs:
                    dir_path = os.path.join(root, name)
                    if os.stat(dir_path).st_mtime < now - retention_time:
                        shutil.rmtree(dir_path)

    def update_system_status(self):
        cpu_usage = psutil.cpu_percent()
        memory_usage = psutil.virtual_memory().percent
        self.cpu_label.setText(f"{self.tr('cpu_usage')}: {cpu_usage}%")
        self.memory_label.setText(f"{self.tr('memory_usage')}: {memory_usage}%")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    # Use icon_path for consistency
    app.setWindowIcon(QIcon(icon_path))
    ex = WorkTrackerApp()
    ex.show()
    sys.exit(app.exec_())
