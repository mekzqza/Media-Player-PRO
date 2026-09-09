"""จัดการรายการเพลง — ห้าม import PyQt ในไฟล์นี้"""

import json
import os


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


class Library:
    """เพลย์ลิสต์หลายอัน เก็บลง json ไฟล์เดียว {ชื่อ: [path, ...]}"""

    def __init__(self, path):
        self.path = path
        self.playlists: dict[str, Playlist] = {}  # dict รักษาลำดับที่สร้างไว้ให้เอง

    def load(self):
        if not os.path.exists(self.path):
            return
        try:
            with open(self.path, encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                raise ValueError("รูปแบบไฟล์ไม่ถูกต้อง")
        except (ValueError, OSError) as exc:
            # ไฟล์พัง: สำรองไว้ก่อนแล้วค่อยเริ่มใหม่ ห้ามทับทิ้งเงียบๆ
            backup = self.path + ".bak"
            os.replace(self.path, backup)
            raise ValueError(f"อ่าน {os.path.basename(self.path)} ไม่ได้ ({exc})\nสำรองไว้ที่ {backup} แล้ว")

        self.playlists = {}
        for name, songs in data.items():
            playlist = Playlist()
            playlist.add(songs)
            self.playlists[name] = playlist

    def save(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump({n: p.songs for n, p in self.playlists.items()}, f, ensure_ascii=False, indent=2)

    def create(self, name) -> str:
        name = self._unique(name)
        self.playlists[name] = Playlist()
        self.save()
        return name

    def rename(self, old, new) -> str:
        if old not in self.playlists or new.strip() in ("", old):
            return old
        new = self._unique(new)
        self.playlists = {(new if k == old else k): v for k, v in self.playlists.items()}
        self.save()
        return new

    def delete(self, name):
        self.playlists.pop(name, None)
        self.save()

    def _unique(self, name):
        """กันชื่อซ้ำ: ต่อท้ายด้วย (2), (3), ..."""
        name = (name or "").strip() or "เพลย์ลิสต์ใหม่"
        candidate, n = name, 2
        while candidate in self.playlists:
            candidate = f"{name} ({n})"
            n += 1
        return candidate


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

    # ---------- Library ----------
    import tempfile

    tmp = os.path.join(tempfile.mkdtemp(), "playlists.json")
    lib = Library(tmp)
    lib.load()  # ไฟล์ยังไม่มี ต้องไม่พัง
    assert lib.playlists == {}

    first = lib.create("ชิลๆ")
    dup = lib.create("ชิลๆ")
    assert (first, dup) == ("ชิลๆ", "ชิลๆ (2)"), (first, dup)
    assert lib.create("") == "เพลย์ลิสต์ใหม่"

    lib.playlists[first].add(["x.mp3", "y.mp3"])
    lib.save()

    again = Library(tmp)
    again.load()
    assert list(again.playlists) == [first, dup, "เพลย์ลิสต์ใหม่"]  # ลำดับต้องคงเดิม
    assert again.playlists[first].songs == ["x.mp3", "y.mp3"]

    assert again.rename(first, "ชิลๆ") == first  # ชื่อเดิม ไม่ต้องทำอะไร
    renamed = again.rename(first, "ตอนเช้า")
    assert list(again.playlists)[0] == "ตอนเช้า" == renamed
    again.delete(dup)
    assert dup not in again.playlists

    with open(tmp, "w", encoding="utf-8") as f:
        f.write("{ พัง ]")
    broken = Library(tmp)
    try:
        broken.load()
        raise AssertionError("ไฟล์พังต้อง raise")
    except ValueError:
        assert os.path.exists(tmp + ".bak")  # ต้องสำรองไว้ ไม่ใช่ทับทิ้ง

    print("playlist ok")
