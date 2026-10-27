"""Тесты этапа 3: загрузка VFS."""

import json
import os
import tempfile
import unittest

from emulator import ShellError, count_nodes, execute, load_vfs, tree_lines

SAMPLE = {
    "type": "dir",
    "children": {
        "a.txt": {"type": "file", "content": "привет"},
        "b.bin": {"type": "file", "encoding": "base64", "content": "SGVsbG8="},
        "sub": {
            "type": "dir",
            "children": {"c.txt": {"type": "file", "content": "x"}},
        },
    },
}


class LoadVfsTest(unittest.TestCase):
    """Проверка загрузки VFS из JSON."""

    def setUp(self):
        """Создать временную папку для JSON-файлов."""
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.folder = tmp.name

    def write(self, text):
        """Записать текст во временный JSON-файл и вернуть путь."""
        path = os.path.join(self.folder, "vfs.json")
        with open(path, "w", encoding="utf-8") as file:
            file.write(text)
        return path

    def load_sample(self):
        """Загрузить образец VFS."""
        return load_vfs(self.write(json.dumps(SAMPLE)))

    def test_text_and_binary(self):
        """Текст кодируется в UTF-8, base64 декодируется в байты."""
        files = self.load_sample()["children"]
        self.assertEqual(files["a.txt"]["data"], "привет".encode("utf-8"))
        self.assertEqual(files["b.bin"]["data"], b"Hello")
        self.assertTrue(files["b.bin"]["binary"])

    def test_count_nodes(self):
        """Подсчёт папок и файлов."""
        self.assertEqual(count_nodes(self.load_sample()), (1, 3))

    def test_tree_lines(self):
        """Дерево выводится с отступами и размерами."""
        self.assertEqual(
            tree_lines(self.load_sample()),
            [
                "a.txt (текст, 12 байт)",
                "b.bin (двоичный, 5 байт)",
                "sub/",
                "  c.txt (текст, 1 байт)",
            ],
        )

    def test_vfs_command(self):
        """Команда vfs печатает дерево, а без VFS даёт ошибку."""
        vfs = self.load_sample()
        self.assertTrue(execute("vfs", vfs).startswith("/\n"))
        with self.assertRaises(ShellError):
            execute("vfs")
        with self.assertRaises(ShellError):
            execute("vfs лишний", vfs)

    def test_missing_file(self):
        """Несуществующий файл даёт ошибку."""
        with self.assertRaises(ShellError):
            load_vfs(os.path.join(self.folder, "no.json"))

    def test_bad_json(self):
        """Битый JSON даёт ошибку."""
        with self.assertRaises(ShellError):
            load_vfs(self.write("{"))

    def test_bad_base64(self):
        """Неверный base64 даёт ошибку."""
        bad = {"type": "file", "encoding": "base64", "content": "!!!"}
        data = {"type": "dir", "children": {"x": bad}}
        with self.assertRaises(ShellError):
            load_vfs(self.write(json.dumps(data)))

    def test_unknown_type(self):
        """Неизвестный тип узла даёт ошибку."""
        with self.assertRaises(ShellError):
            load_vfs(self.write(json.dumps({"type": "link"})))

    def test_root_must_be_dir(self):
        """Корень-файл не допускается."""
        with self.assertRaises(ShellError):
            load_vfs(self.write(json.dumps({"type": "file"})))


if __name__ == "__main__":
    unittest.main()