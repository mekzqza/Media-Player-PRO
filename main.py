import os
import sys

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QIcon
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSlider,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

import theme
from playlist import Library, Playlist

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# ตอนเป็น .exe: ข้อมูลผู้ใช้เซฟข้างตัว exe (โฟลเดอร์ชั่วคราวโดนลบทุกครั้งที่ปิด)
# ส่วนไฟล์แนบอย่างไอคอนอยู่ใน _MEIPASS ที่ PyInstaller แตกไว้ให้
BASE_DIR = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else SCRIPT_DIR
RES_DIR = getattr(sys, "_MEIPASS", SCRIPT_DIR)
PLAYLISTS_FILE = os.path.join(BASE_DIR, "playlists.json")
ICON_FILE = os.path.join(RES_DIR, "assets", "app-c.ico")
CARDS_PER_ROW = 3


def _fmt(ms):
    seconds = max(0, ms) // 1000
    return f"{seconds // 60}:{seconds % 60:02d}"


def _song_item(path):
    """แถวใน list: โชว์แค่ชื่อไฟล์ แต่เก็บ path เต็มไว้ใน UserRole"""
    item = QListWidgetItem(os.path.basename(path))
    item.setData(Qt.ItemDataRole.UserRole, path)
    return item


class PlaylistDialog(QDialog):
    """แก้ไขเพลย์ลิสต์: เปลี่ยนชื่อ / เพิ่มเพลง / ลบเพลง / ลบทั้งเพลย์ลิสต์"""

    def __init__(self, parent, name, playlist):
        super().__init__(parent)
        self.playlist = playlist
        self.deleted = False
        self.setWindowTitle(f"แก้ไข — {name}")
        self.resize(480, 460)

        self.name_edit = QLineEdit(name)

        self.songs = QListWidget()
        self.songs.setObjectName("Playlist")
        for path in playlist.songs:
            self.songs.addItem(_song_item(path))

        add_button = QPushButton("+  เพิ่มเพลง")
        add_button.setObjectName("AddButton")
        add_button.clicked.connect(self.on_add)

        remove_button = QPushButton("ลบเพลงที่เลือก")
        remove_button.clicked.connect(self.on_remove)

        delete_button = QPushButton("ลบเพลย์ลิสต์นี้")
        delete_button.setObjectName("Danger")
        delete_button.clicked.connect(self.on_delete_playlist)

        done_button = QPushButton("เสร็จ")
        done_button.clicked.connect(self.accept)

        song_buttons = QHBoxLayout()
        song_buttons.addWidget(add_button)
        song_buttons.addWidget(remove_button)
        song_buttons.addStretch()

        bottom = QHBoxLayout()
        bottom.addWidget(delete_button)
        bottom.addStretch()
        bottom.addWidget(done_button)

        root = QVBoxLayout()
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(10)
        root.addWidget(QLabel("ชื่อเพลย์ลิสต์"))
        root.addWidget(self.name_edit)
        root.addWidget(self.songs, 1)
        root.addLayout(song_buttons)
        root.addLayout(bottom)
        self.setLayout(root)

    def on_add(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Add Songs", "", "MP3 Files (*.mp3)")
        for path in self.playlist.add(paths):
            self.songs.addItem(_song_item(path))

    def on_remove(self):
        row = self.songs.currentRow()
        if row < 0:
            QMessageBox.information(self, "ยังไม่ได้เลือก", "เลือกเพลงที่จะลบก่อน")
            return
        self.playlist.remove(row)
        self.songs.takeItem(row)

    def on_delete_playlist(self):
        answer = QMessageBox.question(
            self, "ลบเพลย์ลิสต์", f"ลบ \"{self.name_edit.text()}\" ทั้งอันเลยไหม"
        )
        if answer == QMessageBox.StandardButton.Yes:
            self.deleted = True
            self.accept()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Media Player PRO")
        self.resize(940, 620)
        self.setMinimumSize(760, 520)

        self.library = Library(PLAYLISTS_FILE)
        self.playlist = Playlist()  # เพลย์ลิสต์ที่เปิดอยู่ในหน้าเล่นเพลง
        self.current_name = None

        self.player = QMediaPlayer()
        # ต้องเก็บ QAudioOutput ไว้เป็น attribute ไม่งั้นโดน GC แล้วเสียงเงียบแบบไม่มี error
        self.audio_output = QAudioOutput()
        self.audio_output.setVolume(0.5)
        self.player.setAudioOutput(self.audio_output)
        self.player.errorOccurred.connect(self.on_player_error)

        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_library_page())
        self.stack.addWidget(self._build_player_page())
        self.setCentralWidget(self.stack)

        try:
            self.library.load()
        except ValueError as exc:
            QMessageBox.warning(self, "ไฟล์เพลย์ลิสต์มีปัญหา", str(exc))
        self.refresh_library()

    # ---------------------------------------------------------------- library

    def _build_library_page(self):
        title = QLabel("เพลย์ลิสต์ของฉัน")
        title.setObjectName("Title")

        self.search_edit = QLineEdit()
        self.search_edit.setObjectName("Search")
        self.search_edit.setPlaceholderText("ค้นหา เพลย์ลิสต์")
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.textChanged.connect(lambda _: self.refresh_library())

        search_icon = QLabel(theme.ICONS["search"])
        search_icon.setObjectName("SearchIcon")
        search_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # ปุ่มพวกนี้ใช้ฟอนต์ปกติ (มีตัวหนังสือไทย) เลยใช้ + ธรรมดา ไม่ใช่ไอคอน MDL2
        new_button = QPushButton("+  สร้างเพลย์ลิสต์ใหม่")
        new_button.setObjectName("AddButton")
        new_button.clicked.connect(self.on_new_playlist)

        header = QHBoxLayout()
        header.addWidget(title)
        header.addSpacing(12)
        header.addWidget(self.search_edit, 1)
        header.addWidget(search_icon)
        header.addSpacing(12)
        header.addWidget(new_button)

        self.cards = QGridLayout()
        self.cards.setSpacing(14)
        self.cards.setAlignment(Qt.AlignmentFlag.AlignTop)

        holder = QWidget()
        holder.setLayout(self.cards)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(holder)

        root = QVBoxLayout()
        root.setContentsMargins(18, 16, 18, 16)
        root.setSpacing(14)
        root.addLayout(header)
        root.addWidget(scroll, 1)

        page = QWidget()
        page.setLayout(root)
        return page

    def refresh_library(self):
        """สร้างการ์ดใหม่ทั้งกริด — ponytail: เพลย์ลิสต์หลักสิบอัน วาดใหม่ทั้งหมดเร็วพอ"""
        while self.cards.count():
            widget = self.cards.takeAt(0).widget()
            if widget is not None:
                widget.setParent(None)  # ต้องตัด parent ทันที ไม่งั้นค้างบนจอจนกว่า deleteLater จะทำงาน
                widget.deleteLater()

        keyword = self.search_edit.text().strip().lower()
        names = [n for n in self.library.playlists if keyword in n.lower()]

        if not names:
            message = "ไม่เจอเพลย์ลิสต์ที่ค้นหา" if keyword else "ยังไม่มีเพลย์ลิสต์ — กดสร้างเพลย์ลิสต์ใหม่ได้เลย"
            empty = QLabel(message)
            empty.setObjectName("Empty")
            self.cards.addWidget(empty, 0, 0)
            return

        for i, name in enumerate(names):
            self.cards.addWidget(self._make_card(name), i // CARDS_PER_ROW, i % CARDS_PER_ROW)

    def _make_card(self, name):
        playlist = self.library.playlists[name]

        edit_button = QPushButton(theme.ICONS["edit"])
        edit_button.setObjectName("CardIcon")
        edit_button.setToolTip("แก้ไขเพลย์ลิสต์")
        edit_button.clicked.connect(lambda _, n=name: self.on_edit_playlist(n))

        play_button = QPushButton(theme.ICONS["play"])
        play_button.setObjectName("CardPlay")
        play_button.setToolTip("เปิดเพลย์ลิสต์นี้")
        play_button.clicked.connect(lambda _, n=name: self.open_playlist(n))

        count = QLabel(f"{theme.ICONS['songs']}  {len(playlist.songs)}")
        count.setObjectName("CardCount")

        card_name = QLabel(name)
        card_name.setObjectName("CardName")
        card_name.setWordWrap(True)
        card_name.setAlignment(Qt.AlignmentFlag.AlignCenter)

        top = QHBoxLayout()
        top.addStretch()
        top.addWidget(edit_button)

        bottom = QHBoxLayout()
        bottom.addWidget(count)
        bottom.addStretch()
        bottom.addWidget(play_button)

        inner = QVBoxLayout()
        inner.setContentsMargins(12, 8, 12, 10)
        inner.addLayout(top)
        inner.addWidget(card_name, 1)
        inner.addLayout(bottom)

        card = QFrame()
        card.setObjectName("Card")
        card.setMinimumHeight(150)
        card.setLayout(inner)
        return card

    def on_new_playlist(self):
        name = self.library.create("เพลย์ลิสต์ใหม่")
        self.refresh_library()
        self.on_edit_playlist(name)  # เปิดให้ตั้งชื่อ + ใส่เพลงต่อทันที

    def on_edit_playlist(self, name):
        playlist = self.library.playlists[name]
        dialog = PlaylistDialog(self, name, playlist)
        dialog.exec()

        if dialog.deleted:
            self.library.delete(name)
            if self.current_name == name:  # อันที่เปิดค้างอยู่ในหน้าเล่นเพลงถูกลบ
                self.player.stop()
                self.playlist = Playlist()
                self.current_name = None
                self._populate_songs()
        else:
            name = self.library.rename(name, dialog.name_edit.text())
            self.library.save()
            if self.current_name is not None and self.playlist is playlist:
                self.current_name = name
                self._populate_songs()

        self.refresh_library()

    def open_playlist(self, name):
        self.player.stop()
        self.current_name = name
        self.playlist = self.library.playlists[name]
        self._populate_songs()
        self.stack.setCurrentIndex(1)
        if not self.playlist.is_empty():
            self._play_index(0)

    def _populate_songs(self):
        self.list_widget.clear()
        for path in self.playlist.songs:
            self.list_widget.addItem(_song_item(path))
        self.playlist_label.setText(self.current_name or "ยังไม่ได้เลือกเพลย์ลิสต์")
        self.now_playing.setText("ยังไม่มีเพลงเล่นอยู่")

    # ----------------------------------------------------------------- player

    def _build_player_page(self):
        self.home_button = QPushButton(theme.ICONS["home"])
        self.home_button.setObjectName("IconButton")
        self.home_button.setToolTip("กลับหน้าเพลย์ลิสต์")
        self.home_button.clicked.connect(self.on_home)

        self.playlist_label = QLabel("ยังไม่ได้เลือกเพลย์ลิสต์")
        self.playlist_label.setObjectName("Title")

        self.add_button = QPushButton("+  Add Songs")
        self.add_button.setObjectName("AddButton")
        self.add_button.clicked.connect(self.on_add_songs)

        top_bar = QHBoxLayout()
        top_bar.addWidget(self.home_button)
        top_bar.addWidget(self.playlist_label)
        top_bar.addStretch()
        top_bar.addWidget(self.add_button)

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

        transport = QHBoxLayout()
        transport.addSpacing(160)  # ponytail: ถ่วงซ้ายให้ปุ่มอยู่กลางจริง เพราะขวามี volume กินที่
        transport.addStretch()
        for icon, tooltip, slot, name in (
            ("prev", "เพลงก่อนหน้า", self.on_prev, "Transport"),
            ("play", "เล่น", self.on_play, "PlayButton"),
            ("pause", "หยุดชั่วคราว", self.on_pause, "Transport"),
            ("stop", "หยุด", self.on_stop, "Transport"),
            ("next", "เพลงถัดไป", self.on_next, "Transport"),
        ):
            button = QPushButton(theme.ICONS[icon])
            button.setObjectName(name)
            button.setToolTip(tooltip)
            button.clicked.connect(slot)
            transport.addWidget(button)
        transport.addStretch()

        volume_icon = QLabel(theme.ICONS["volume"])
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

        page = QWidget()
        page.setLayout(root)
        return page

    def on_home(self):
        self.refresh_library()
        self.stack.setCurrentIndex(0)

    def on_add_songs(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Add Songs", "", "MP3 Files (*.mp3)")
        for path in self.playlist.add(paths):
            self.list_widget.addItem(_song_item(path))
        if self.current_name is not None:
            self.library.save()

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
    app.setWindowIcon(QIcon(ICON_FILE))
    app.setStyleSheet(theme.stylesheet())
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
