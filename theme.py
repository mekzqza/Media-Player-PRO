"""สีและหน้าตาทั้งหมดอยู่ไฟล์นี้ที่เดียว — แก้ที่ COLORS พอ ไม่ต้องแตะ main.py"""

from string import Template

COLORS = {
    "window": "#d6d6d6",        # พื้นหลังนอกสุด
    "panel": "#ffffff",         # พื้นที่เนื้อหา / การ์ด
    "panel_border": "#c9c9c9",
    "text": "#1c1c1c",
    "text_muted": "#6e6e6e",
    "accent": "#cc1111",        # แดงหลัก: แถวเพลง + ปุ่ม play
    "accent_hover": "#e02323",
    "accent_dark": "#8f0c0c",   # แถวเพลงที่เลือกอยู่
    "on_accent": "#ffffff",     # ตัวหนังสือบนพื้นแดง
    "track": "#c4c4c4",         # รางสไลเดอร์ส่วนที่ยังไม่เล่น
    "track_fill": "#2b2b2b",    # รางส่วนที่เล่นไปแล้ว
    "button": "#efefef",
    "button_hover": "#e4e4e4",
    "scrollbar": "#a99ab3",
}

FONT = "Segoe UI"
ICON_FONT = "Segoe MDL2 Assets"  # ฟอนต์ไอคอนที่ติดมากับ Windows ทุกเครื่อง
RADIUS = "10px"

# อยากได้ไอคอนอื่นเพิ่ม: เปิด charmap.exe เลือกฟอนต์ Segoe MDL2 Assets
# หรือเสิร์ช "Segoe MDL2 Assets icon list" แล้วเอารหัส U+Exxx มาใส่เป็น chr(0xExxx)
ICONS = {
    "home": chr(0xE80F),
    "prev": chr(0xE892),
    "play": chr(0xF5B0),   # PlaySolid — ปุ่มหลัก เอาแบบทึบให้เด่น
    "pause": chr(0xE769),
    "stop": chr(0xE71A),
    "next": chr(0xE893),
    "volume": chr(0xE767),
    "edit": chr(0xE70F),
    "add": chr(0xE710),
    "search": chr(0xE721),
    "songs": chr(0xE8FD),
    "delete": chr(0xE74D),
}

# ponytail: string.Template เพราะ QSS เต็มไปด้วย {} ถ้าใช้ .format จะพังทันที
_QSS = Template("""
QWidget {
    background: $window;
    color: $text;
    font-family: "$font";
    font-size: 13px;
}

QLabel#Title {
    font-size: 16px;
    font-weight: 600;
    padding-left: 6px;
}

QLabel#TimeLabel {
    color: $text_muted;
    font-size: 12px;
    background: transparent;
}

QLabel#VolumeIcon {
    font-family: "$icon_font";
    font-size: 15px;
    color: $text;
    background: transparent;
    padding-right: 6px;
}

/* ---------- รายการเพลง ---------- */
QListWidget#Playlist {
    background: $panel;
    border: 1px solid $panel_border;
    border-radius: $radius;
    padding: 8px;
    outline: 0;
}
QListWidget#Playlist::item {
    background: $accent;
    color: $on_accent;
    border-radius: 5px;
    padding: 11px 12px;
    margin: 3px 2px;
}
QListWidget#Playlist::item:hover { background: $accent_hover; }
QListWidget#Playlist::item:selected { background: $accent_dark; }

QScrollBar:vertical {
    background: transparent;
    width: 10px;
    margin: 6px 2px;
}
QScrollBar::handle:vertical {
    background: $scrollbar;
    border-radius: 5px;
    min-height: 34px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }

/* ---------- แผงข้อมูลเพลง ---------- */
QLabel#InfoPanel {
    background: $panel;
    border: 1px solid $panel_border;
    border-radius: $radius;
    color: $text_muted;
    font-size: 15px;
    padding: 24px;
}

/* ---------- สไลเดอร์ ---------- */
QSlider::groove:horizontal {
    background: $track;
    height: 10px;
    border-radius: 5px;
}
QSlider::sub-page:horizontal {
    background: $track_fill;
    border-radius: 5px;
}
QSlider::handle:horizontal {
    background: $panel;
    border: 2px solid $track_fill;
    width: 13px;
    margin: -3px 0;
    border-radius: 8px;
}
QSlider#Volume::groove:horizontal { height: 6px; border-radius: 3px; }
QSlider#Volume::handle:horizontal { width: 9px; margin: -4px 0; border-radius: 7px; }

/* ---------- ปุ่ม ---------- */
QPushButton {
    background: $button;
    border: 1px solid $panel_border;
    border-radius: 6px;
    padding: 8px 16px;
}
QPushButton:hover { background: $button_hover; }
QPushButton:pressed { background: $panel_border; }

QPushButton#AddButton {
    background: $accent;
    color: $on_accent;
    border: none;
    border-radius: 6px;
    padding: 9px 18px;
    font-weight: 600;
}
QPushButton#AddButton:hover { background: $accent_hover; }

QPushButton#IconButton {
    background: $panel;
    border: 2px solid $text;
    border-radius: 10px;
    font-family: "$icon_font";
    font-size: 15px;
    min-width: 36px;
    min-height: 32px;
    padding: 0;
}
QPushButton#IconButton:disabled {
    color: $text_muted;
    border-color: $panel_border;
}

QPushButton#Transport, QPushButton#PlayButton {
    background: transparent;
    border: none;
    min-width: 46px;
    padding: 6px;
    font-family: "$icon_font";
    font-size: 16px;
}
QPushButton#Transport:hover, QPushButton#PlayButton:hover { color: $accent_hover; }
QPushButton#PlayButton { color: $accent; font-size: 21px; }

/* ---------- หน้า Library ---------- */
QLineEdit#Search {
    background: $panel;
    border: 1px solid $panel_border;
    border-radius: 19px;
    padding: 9px 16px;
    font-size: 14px;
}
QLineEdit#Search:focus { border-color: $accent; }

QLabel#SearchIcon {
    font-family: "$icon_font";
    font-size: 15px;
    color: $on_accent;
    background: $accent_dark;
    border-radius: 17px;
    min-width: 34px;
    max-width: 34px;
    min-height: 34px;
    max-height: 34px;
}

QScrollArea, QScrollArea > QWidget > QWidget { background: transparent; border: none; }

QFrame#Card {
    background: $panel;
    border: 1px solid $panel_border;
    border-radius: $radius;
}
QFrame#Card:hover { border: 1px solid $accent; }

QLabel#CardName {
    font-size: 14px;
    font-weight: 600;
    background: transparent;
}
QLabel#CardCount {
    color: $text_muted;
    font-size: 12px;
    font-family: "$icon_font";
    background: transparent;
}
QLabel#Empty {
    color: $text_muted;
    font-size: 14px;
    background: transparent;
}

QPushButton#CardIcon {
    background: transparent;
    border: none;
    font-family: "$icon_font";
    font-size: 14px;
    min-width: 24px;
    padding: 2px;
}
QPushButton#CardIcon:hover { color: $accent; }
QPushButton#CardPlay {
    background: transparent;
    border: none;
    font-family: "$icon_font";
    font-size: 18px;
    color: $accent;
    min-width: 26px;
    padding: 2px;
}
QPushButton#CardPlay:hover { color: $accent_hover; }

/* ---------- หน้าต่างแก้ไขเพลย์ลิสต์ ---------- */
QDialog { background: $window; }
QLineEdit {
    background: $panel;
    border: 1px solid $panel_border;
    border-radius: 6px;
    padding: 8px 10px;
    font-size: 14px;
}
QLineEdit:focus { border-color: $accent; }
QPushButton#Danger {
    background: transparent;
    border: 1px solid $accent;
    color: $accent;
    border-radius: 6px;
    padding: 8px 14px;
}
QPushButton#Danger:hover { background: $accent; color: $on_accent; }
""")


def stylesheet() -> str:
    return _QSS.substitute(COLORS, font=FONT, icon_font=ICON_FONT, radius=RADIUS)


if __name__ == "__main__":
    qss = stylesheet()
    assert "$" not in qss, "ยังมีตัวแปรที่แทนค่าไม่ครบ"
    assert COLORS["accent"] in qss
    print("theme ok:", len(qss), "chars")
