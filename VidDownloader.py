import sys
import threading
from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QLineEdit, QCheckBox, QPushButton, QLabel, QWidget, QApplication, QFileDialog, QScrollArea, QMessageBox
from PyQt5.QtCore import Qt, QObject, pyqtSignal
from qt_material import apply_stylesheet
from googleapiclient.discovery import build
from pytube import YouTube

class Worker(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(str)
    progress = pyqtSignal(str)
    video_details = pyqtSignal(str)

    def __init__(self, parent=None):
        super(Worker, self).__init__(parent)
        self.error_emitted = False

    def fetch_video_details(self, video_title):
        try:
            youtube = build('youtube', 'v3', developerKey='AIzaSyCie1TuXNEYfA4V8YeLtlOqcWQ0NbeZYrM')
            request = youtube.search().list(
                part="snippet",
                q=video_title,
                maxResults=1,
                type="video"
            )
            response = request.execute()
            
            if 'items' in response and response['items']:
                video_id = response['items'][0]['id']['videoId']
                video_link = f"https://www.youtube.com/watch?v={video_id}"
                video = YouTube(video_link)
                video_details = f"Title: {video.title}\nViews: {video.views}\nLength: {video.length} seconds\nDescription: {video.description}"
                self.video_details.emit(video_details)
            else:
                if not self.error_emitted:
                    self.error_emitted = True
                    self.error.emit("No video found for the given query.")
        except Exception as e:
            self.error.emit(str(e))

    def download_video(self, save_location, video_title):
        try:
            youtube = build('youtube', 'v3', developerKey='AIzaSyCie1TuXNEYfA4V8YeLtlOqcWQ0NbeZYrM')
            request = youtube.search().list(
                part="snippet",
                q=video_title,
                maxResults=1,
                type="video"
            )
            response = request.execute()
            
            if 'items' in response and response['items']:
                video_id = response['items'][0]['id']['videoId']
                video_link = f"https://www.youtube.com/watch?v={video_id}"
                video = YouTube(video_link)
                stream = video.streams.get_highest_resolution()
                self.progress.emit("Downloading...") 
                stream.download(save_location)
                self.finished.emit()
            else:
                if not self.error_emitted:
                    self.error_emitted = True
                    self.error.emit("No video found for the given query.")
        except Exception as e:
            self.error.emit(str(e))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YTDownloader")
        self.setFixedSize(300, 400)
        self.worker = Worker()

        self.la = QVBoxLayout()
        self.title_label = QLabel("Enter the video title:")
        self.text = QLineEdit()
        self.che1 = QCheckBox("Video")
        self.che1.setChecked(True)
        self.che2 = QCheckBox("audio only")
        self.button = QPushButton("Download")

        self.labi = QLabel()
        self.labi.setAlignment(Qt.AlignTop)
        self.labi.setFixedWidth(250)
        self.labi.setMinimumHeight(150)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_content = QWidget(self.scroll_area)
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_area.setWidget(self.scroll_content)

        self.labi.setWordWrap(True)
        self.la.addWidget(self.title_label)
        self.la.addWidget(self.text)
        self.la.addWidget(self.button)
        self.la.addWidget(self.che1)
        self.la.addWidget(self.che2)
        self.labi.setStyleSheet("border:1px solid yellow")

        widget = QWidget()
        widget.setLayout(self.la)
        self.setCentralWidget(widget)
        self.la.addWidget(self.scroll_area)
        self.scroll_layout.addWidget(self.labi)

        self.worker.finished.connect(self.download_finished)
        self.worker.error.connect(self.show_error)
        self.worker.progress.connect(self.update_progress)
        self.worker.video_details.connect(self.show_video_details)

        self.button.clicked.connect(self.open_file)

    def open_file(self):
        self.labi.clear()
        self.labi.setText("Working on it......")
        save_location = QFileDialog.getExistingDirectory(self, "Select location")
        if save_location:
            video_title = self.text.text()
            self.button.setText("Downloading.....")
            self.button.setEnabled(False)
            threading.Thread(target=self.worker.fetch_video_details, args=(video_title,)).start()
            threading.Thread(target=self.worker.download_video, args=(save_location, video_title)).start()
        else:
            temp = self.labi.text()
            temp += "\n Downloading Stopped!"
            self.labi.setText(temp)

    def download_finished(self):
        QMessageBox().about(self, 'Success', 'Downloading Complete')
        self.button.setEnabled(True)
        self.button.setText("Download")
        self.text.clear()

    def show_error(self, message):
        QMessageBox.critical(self, "Error", message, QMessageBox.Ok)
        self.labi.clear()
        self.button.setEnabled(True)
        self.button.setText("Download")

    def update_progress(self, message):
        temp = self.labi.text()
        temp += f"\n{message}"
        self.labi.setText(temp)
        if message == "Download Success":
            self.button.setEnabled(True)

    def show_video_details(self, details):
        temp = self.labi.text()
        temp += f"\n\n{details}"
        self.labi.setText(temp)


if __name__ == "__main__":
    app = QApplication([])
    apply_stylesheet(app, theme='dark_amber.xml')
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
