"""จัดการรายการเพลง — ห้าม import PyQt ในไฟล์นี้"""


class Playlist:
    def __init__(self):
        self.songs: list[str] = []
        self.current = -1  # -1 = ยังไม่ได้เลือกเพลง

    def add(self, paths) -> list[str]:
        """เพิ่มเพลง ข้ามตัวที่ซ้ำ คืนเฉพาะ path ที่เพิ่มเข้าไปจริง"""
        added = []
        for path in paths:
            if path not in self.songs:
                self.songs.append(path)
                added.append(path)
        return added

    def remove(self, index):
        if not 0 <= index < len(self.songs):
            return
        del self.songs[index]
        if index == self.current:
            self.current = -1  # ponytail: ลบเพลงที่เลือกอยู่ = ไม่มีเพลงเลือก, ค่อยทำ auto-next ถ้าต้องการ
        elif index < self.current:
            self.current -= 1

    def clear(self):
        self.songs.clear()
        self.current = -1

    def select(self, index):
        self.current = index if 0 <= index < len(self.songs) else -1

    def current_path(self):
        return self.songs[self.current] if 0 <= self.current < len(self.songs) else None

    def next_path(self):
        """เพลงถัดไป ถึงท้าย list แล้วคืน None (ไม่วนกลับต้น)"""
        nxt = self.current + 1
        return self.songs[nxt] if 0 <= nxt < len(self.songs) else None

    def is_empty(self) -> bool:
        return not self.songs


if __name__ == "__main__":
    p = Playlist()
    assert p.is_empty() and p.current_path() is None and p.next_path() is None

    assert p.add(["a.mp3", "b.mp3", "a.mp3"]) == ["a.mp3", "b.mp3"]  # ข้ามซ้ำ
    p.select(0)
    assert p.current_path() == "a.mp3" and p.next_path() == "b.mp3"
    p.select(1)
    assert p.next_path() is None  # ท้าย list
    p.select(99)
    assert p.current_path() is None  # index นอกช่วง

    p.add(["c.mp3"])
    p.select(2)
    p.remove(0)  # ลบตัวก่อนหน้า current -> index ต้องเลื่อนตาม
    assert p.current_path() == "c.mp3", p.current_path()
    p.remove(1)  # ลบตัวที่เลือกอยู่
    assert p.current == -1 and p.songs == ["b.mp3"]

    p.clear()
    assert p.is_empty() and p.current == -1
    print("playlist ok")
