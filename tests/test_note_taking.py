import tempfile
import os
from pathlib import Path
import sys

# Add the parent directory to the path so we can import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.assistant import NoteTaking

def test_note_taking_initialization():
    """Test that NoteTaking initializes correctly"""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)
        nt = NoteTaking(str(data_dir))
        expected_notes_dir = data_dir / "notes"
        assert nt.notes_dir == expected_notes_dir
        assert expected_notes_dir.exists()

def test_note_taking_create_note():
    """Test that NoteTaking can create notes"""
    with tempfile.TemporaryDirectory() as tmpdir:
        nt = NoteTaking(tmpdir)

        # Create a note
        title = "Test Note"
        content = "This is a test note."
        file_path = nt.create_note(title, content)

        # Check that file was created
        assert os.path.exists(file_path)
        assert file_path.endswith(".txt")

        # Check file contents
        with open(file_path, 'r', encoding='utf-8') as f:
            content_read = f.read()

        assert f"Title: {title}" in content_read
        assert f"Created:" in content_read
        assert content in content_read

def test_note_taking_list_notes():
    """Test that NoteTaking can list notes"""
    with tempfile.TemporaryDirectory() as tmpdir:
        nt = NoteTaking(tmpdir)

        # Create a couple of notes
        nt.create_note("First Note", "Content of first note")
        nt.create_note("Second Note", "Content of second note")

        # List notes
        notes = nt.list_notes(limit=10)

        # Should have 2 notes
        assert len(notes) == 2

        # Check that notes have expected fields
        for note in notes:
            assert "path" in note
            assert "title" in note
            assert "created" in note
            assert "modified" in note

def test_note_taking_search_notes():
    """Test that NoteTaking can search within notes"""
    with tempfile.TemporaryDirectory() as tmpdir:
        nt = NoteTaking(tmpdir)

        # Create notes with specific content
        nt.create_note("Meeting Notes", "Discussed project timeline")
        nt.create_note("Shopping List", "Buy milk, eggs, and bread")
        nt.create_note("Random Notes", "The quick brown fox jumps over the lazy dog")

        # Search for notes containing "meeting"
        results = nt.search_notes("meeting")
        assert len(results) == 1
        assert results[0]["title"] == "Meeting Notes"

        # Search for notes containing "and" (should match 2 notes)
        results = nt.search_notes("and")
        assert len(results) == 2

        # Search for non-existent term
        results = nt.search_notes("xyz")
        assert len(results) == 0

if __name__ == "__main__":
    test_note_taking_initialization()
    test_note_taking_create_note()
    test_note_taking_list_notes()
    test_note_taking_search_notes()
    print("All note taking tests passed!")