"""Tests for memory file parsing and writing."""

from pathlib import Path

from infodeck.data.memory_files import (
    MemoryEntry,
    MemoryFile,
    add_entry,
    delete_entry,
    parse_memory_file,
    update_entry,
    write_memory_file,
)


class TestParseMemoryFile:
    def test_parse_entries(self, tmp_path):
        filepath = tmp_path / "MEMORY.md"
        filepath.write_text("Entry one\n§\nEntry two\n§\nEntry three\n")

        result = parse_memory_file(filepath, "memory")
        assert len(result.entries) == 3
        assert result.entries[0].content == "Entry one"
        assert result.entries[0].index == 0
        assert result.entries[1].content == "Entry two"
        assert result.entries[2].content == "Entry three"

    def test_empty_file(self, tmp_path):
        filepath = tmp_path / "MEMORY.md"
        filepath.write_text("")

        result = parse_memory_file(filepath, "memory")
        assert result.entries == []

    def test_nonexistent_file(self, tmp_path):
        filepath = tmp_path / "nonexistent.md"
        result = parse_memory_file(filepath, "memory")
        assert result.entries == []
        assert result.path == filepath

    def test_single_entry_no_delimiter(self, tmp_path):
        filepath = tmp_path / "MEMORY.md"
        filepath.write_text("Just one entry, no delimiter.")

        result = parse_memory_file(filepath, "memory")
        assert len(result.entries) == 1
        assert result.entries[0].content == "Just one entry, no delimiter."

    def test_skips_empty_entries(self, tmp_path):
        filepath = tmp_path / "MEMORY.md"
        filepath.write_text("First\n§\n\n§\nThird\n")

        result = parse_memory_file(filepath, "memory")
        assert len(result.entries) == 2
        assert result.entries[0].content == "First"
        assert result.entries[1].content == "Third"

    def test_preview_truncation(self, tmp_path):
        long_text = "x" * 100
        filepath = tmp_path / "MEMORY.md"
        filepath.write_text(long_text)

        result = parse_memory_file(filepath, "memory")
        assert len(result.entries[0].preview) <= 83  # 80 chars + "…"

    def test_multiline_entries(self, tmp_path):
        filepath = tmp_path / "MEMORY.md"
        filepath.write_text("Line 1\nLine 2\n§\nLine 3\nLine 4\n")

        result = parse_memory_file(filepath, "memory")
        assert len(result.entries) == 2
        assert result.entries[0].content == "Line 1\nLine 2"
        assert result.entries[1].content == "Line 3\nLine 4"


class TestWriteMemoryFile:
    def test_write_and_reread(self, tmp_path):
        filepath = tmp_path / "MEMORY.md"
        memfile = MemoryFile(path=filepath, source="memory")
        memfile.entries = [
            MemoryEntry(source="memory", index=0, content="Entry A", preview="Entry A"),
            MemoryEntry(source="memory", index=1, content="Entry B", preview="Entry B"),
        ]

        error = write_memory_file(memfile, backup=False)
        assert error is None
        assert filepath.exists()

        content = filepath.read_text()
        assert "Entry A" in content
        assert "Entry B" in content
        assert "\n§\n" in content

    def test_backup_created(self, tmp_path):
        filepath = tmp_path / "MEMORY.md"
        filepath.write_text("original\n")
        memfile = parse_memory_file(filepath, "memory")
        memfile.entries[0].content = "modified"

        error = write_memory_file(memfile, backup=True)
        assert error is None

        bak = tmp_path / "MEMORY.md.bak"
        assert bak.exists()
        assert bak.read_text() == "original\n"

    def test_write_to_new_file(self, tmp_path):
        filepath = tmp_path / "new_file.md"
        memfile = MemoryFile(path=filepath, source="memory")
        memfile.entries = [
            MemoryEntry(source="memory", index=0, content="New content", preview="New")
        ]

        error = write_memory_file(memfile, backup=False)
        assert error is None
        assert filepath.read_text().strip() == "New content"


class TestCrud:
    def test_add_entry(self):
        memfile = MemoryFile(path=Path("/tmp/test.md"), source="memory")
        idx = add_entry(memfile, "New entry")
        assert idx == 0
        assert len(memfile.entries) == 1
        assert memfile.entries[0].content == "New entry"

    def test_delete_entry(self):
        memfile = MemoryFile(path=Path("/tmp/test.md"), source="memory")
        add_entry(memfile, "First")
        add_entry(memfile, "Second")
        add_entry(memfile, "Third")

        assert delete_entry(memfile, 1) is True
        assert len(memfile.entries) == 2
        assert memfile.entries[0].content == "First"
        assert memfile.entries[1].content == "Third"
        assert memfile.entries[0].index == 0
        assert memfile.entries[1].index == 1

    def test_delete_invalid_index(self):
        memfile = MemoryFile(path=Path("/tmp/test.md"), source="memory")
        assert delete_entry(memfile, 0) is False
        assert delete_entry(memfile, -1) is False

    def test_update_entry(self):
        memfile = MemoryFile(path=Path("/tmp/test.md"), source="memory")
        add_entry(memfile, "Original")

        assert update_entry(memfile, 0, "Updated") is True
        assert memfile.entries[0].content == "Updated"
        assert "Updated" in memfile.entries[0].preview

    def test_update_invalid_index(self):
        memfile = MemoryFile(path=Path("/tmp/test.md"), source="memory")
        assert update_entry(memfile, 0, "X") is False
