import os
import sys

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

import theme
from playlist import Playlist


def _fmt(ms):
    seconds = max(0, ms) // 1000
    return f"{seconds // 60}:{seconds % 60:02d}"


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Media Player PRO")
        self.resize(940, 580)
        self.setMinimumSize(720, 460)

        self.playlist = Playlist()
        self.player = QMediaPlayer()
        # ต้องเก็บ QAudioOutput ไว้เป็น attribute ไม่งั้นโดน GC แล้วเสียงเงียบแบบไม่มี error
        self.audio_output = QAudioOutput()
        self.audio_output.setVolume(0.5)
        self.player.setAudioOutput(self.audio_output)
        self.player.errorOccurred.connect(self.on_player_error)

        self._build_ui()

    def _build_ui(self):
        # ---------- แถบบน ----------
        self.home_button = QPushButton("⌂")
        self.home_button.setObjectName("IconButton")
        self.home_button.setEnabled(False)
        self.home_button.setToolTip("หน้า Library — ยังไม่ได้ทำ")

        title = QLabel("Media Player PRO")
        title.setObjectName("Title")

        self.add_button = QPushButton("+  Add Songs")
        self.add_button.setObjectName("AddButton")
        self.add_button.clicked.connect(self.on_add_songs)

        top_bar = QHBoxLayout()
        top_bar.addWidget(self.home_button)
        top_bar.addWidget(title)
        top_bar.addStretch()
        top_bar.addWidget(self.add_button)

        # ---------- รายการเพลง + ข้อมูลเพลง ----------
        self.list_widget = QListWidget()
        self.list_widget.setObjectName("Playlist")
        self.list_widget.itemDoubleClicked.connect(self.on_item_double_clicked)

        self.now_playing = QLabel("ยังไม่มีเพลงเล่นอยู่")
        self.now_playing.setObjectName("InfoPanel")
        self.now_playing.setWordWrap(True)
        self.now_playing.setAlignment(Qt.AlignmentFlag.AlignCenter)

        content = QHBoxLayout()
        content.setSpacing(14)
        content.addWidget(self.list_widget, 2)
        content.addWidget(self.now_playing, 3)

        # ---------- เวลา + progress ----------
        self.time_current = QLabel("0:00")
        self.time_current.setObjectName("TimeLabel")
        self.time_total = QLabel("0:00")
        self.time_total.setObjectName("TimeLabel")

        time_row = QHBoxLayout()
        time_row.addWidget(self.time_current)
        time_row.addStretch()
        time_row.addWidget(self.time_total)

        self.progress = QSlider(Qt.Orientation.Horizontal)
        self.progress.setObjectName("Progress")
        self.progress.sliderMoved.connect(self.player.setPosition)  # sliderMoved = ผู้ใช้ลากเท่านั้น
        self.player.durationChanged.connect(self.on_duration_changed)
        self.player.positionChanged.connect(self.on_position_changed)

        # ---------- ปุ่มควบคุม + volume ----------
        transport = QHBoxLayout()
        transport.addSpacing(160)  # ponytail: ถ่วงซ้ายให้ปุ่มอยู่กลางจริง เพราะขวามี volume กินที่
        transport.addStretch()
        for glyph, tooltip, slot, name in (
            ("◀◀", "เพลงก่อนหน้า", self.on_prev, "Transport"),
            ("▶", "เล่น", self.on_play, "PlayButton"),
            ("❚❚", "หยุดชั่วคราว", self.on_pause, "Transport"),
            ("■", "หยุด", self.on_stop, "Transport"),
            ("▶▶", "เพลงถัดไป", self.on_next, "Transport"),
        ):
            button = QPushButton(glyph)
            button.setObjectName(name)
            button.setToolTip(tooltip)
            button.clicked.connect(slot)
            transport.addWidget(button)
        transport.addStretch()

        volume_icon = QLabel(chr(0xE767))  # ไอคอนลำโพง Segoe MDL2 Assets
        volume_icon.setObjectName("VolumeIcon")
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setObjectName("Volume")
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.setFixedWidth(120)
        self.volume_slider.valueChanged.connect(self.on_volume_changed)
        transport.addWidget(volume_icon)
        transport.addWidget(self.volume_slider)

        root = QVBoxLayout()
        root.setContentsMargins(18, 16, 18, 16)
        root.setSpacing(12)
        root.addLayout(top_bar)
        root.addLayout(content, 1)
        root.addLayout(time_row)
        root.addWidget(self.progress)
        root.addLayout(transport)

        central = QWidget()
        central.setLayout(root)
        self.setCentralWidget(central)

    def on_add_songs(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Add Songs", "", "MP3 Files (*.mp3)")
        for path in self.playlist.add(paths):
            item = QListWidgetItem(os.path.basename(path))
            item.setData(Qt.ItemDataRole.UserRole, path)
            self.list_widget.addItem(item)

    def on_item_double_clicked(self, item):
        self._play_index(self.list_widget.row(item))

    def on_play(self):
        if self.playlist.is_empty():
            QMessageBox.information(
                self, "Playlist ว่าง", "ยังไม่มีเพลงใน playlist กด Add Songs ก่อน"
            )
            return

        state = self.player.playbackState()
        if state == QMediaPlayer.PlaybackState.PausedState:
            self.player.play()  # เล่นต่อจากตำแหน่งเดิม ห้าม setSource ใหม่
            return
        if state == QMediaPlayer.PlaybackState.PlayingState:
            return  # เล่นอยู่แล้ว ไม่ต้องเริ่มใหม่

        self._play_index(self.playlist.current if self.playlist.current >= 0 else 0)

    def on_pause(self):
        self.player.pause()

    def on_stop(self):
        self.player.stop()

    def on_prev(self):
        self._play_index(self.playlist.current - 1)  # index ไม่ถูกต้อง -> _play_index เมิน

    def on_next(self):
        self._play_index(self.playlist.current + 1)

    def on_duration_changed(self, duration):
        self.progress.setRange(0, duration)
        self._update_time()

    def on_position_changed(self, position):
        if not self.progress.isSliderDown():  # ตอนผู้ใช้ลากอยู่ ห้ามเขียนทับ ไม่งั้นสไลเดอร์กระตุก
            self.progress.setValue(position)
        self._update_time()

    def _update_time(self):
        self.time_current.setText(_fmt(self.player.position()))
        self.time_total.setText(_fmt(self.player.duration()))

    def on_volume_changed(self, value):
        # ponytail: linear พอสำหรับตอนนี้ อยากได้สเกลตามหูค่อยใช้ QtAudio.convertVolume
        self.audio_output.setVolume(value / 100)

    def _play_index(self, index):
        item = self.list_widget.item(index)
        if item is None:
            return

        path = item.data(Qt.ItemDataRole.UserRole)
        if not os.path.exists(path):
            # QMediaPlayer ไม่ throw ตอนไฟล์หาย มันเงียบ เลยต้องเช็คเอง
            QMessageBox.critical(self, "หาไฟล์ไม่เจอ", f"ไฟล์ถูกลบหรือย้ายไปแล้ว:\n{path}")
            return

        self.playlist.select(index)
        self.list_widget.setCurrentRow(index)
        self.player.setSource(QUrl.fromLocalFile(path))  # fromLocalFile: กัน "C:" โดนอ่านเป็น URL scheme
        self.player.play()
        self.now_playing.setText(f"กำลังเล่น\n\n{os.path.basename(path)}")

    def on_player_error(self, error, error_string):
        if error == QMediaPlayer.Error.NoError:
            return
        QMessageBox.critical(self, "เล่นไฟล์ไม่ได้", error_string or str(error))
        self.now_playing.setText("ยังไม่มีเพลงเล่นอยู่")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(theme.stylesheet())
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
