import tempfile
import os
from pathlib import Path
import sys

# Add the parent directory to the path so we can import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.assistant import FileSearch

def test_file_search_initialization():
    """Test that FileSearch initializes correctly"""
    with tempfile.TemporaryDirectory() as tmpdir:
        fs = FileSearch(tmpdir)
        assert fs.data_dir == Path(tmpdir)
        assert fs.data_dir.exists()

def test_file_search_search_files():
    """Test that FileSearch can find files"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create some test files
        test_dir = Path(tmpdir)
        (test_dir / "document.txt").write_text("This is a test document")
        (test_dir / "another_doc.pdf").write_text("PDF content")
        (test_dir / "image.jpg").write_text("Image data")

        # Create a subdirectory
        subdir = test_dir / "subdir"
        subdir.mkdir()
        (subdir / "hidden.txt").write_text("Hidden file")

        fs = FileSearch(str(test_dir))

        # Search for files containing "document"
        results = fs.search_files("document")
        assert len(results) == 1
        assert results[0]["name"] == "document.txt"
        assert "path" in results[0]
        assert "size" in results[0]
        assert "modified" in results[0]

        # Search for files with .txt extension
        results = fs.search_files("", file_types=[".txt"])
        assert len(results) == 2  # document.txt and subdir/hidden.txt
        filenames = [r["name"] for r in results]
        assert "document.txt" in filenames
        assert "hidden.txt" in filenames

        # Search for non-existent file
        results = fs.search_files("nonexistent")
        assert len(results) == 0

def test_file_search_search_in_file():
    """Test that FileSearch can search within files"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a test file with known content
        test_file = Path(tmpdir) / "sample.txt"
        content = """This is line one
This is line two with keyword
This is line three
Another keyword here
Final line"""
        test_file.write_text(content)

        fs = FileSearch(str(tmpdir))

        # Search for "keyword"
        matches = fs.search_in_file(str(test_file), "keyword")
        assert len(matches) == 2
        assert matches[0]["line"] == 2
        assert "keyword" in matches[0]["text"]
        assert matches[1]["line"] == 4
        assert "keyword" in matches[1]["text"]

        # Search for case-insensitive match
        matches = fs.search_in_file(str(test_file), "KEYWORD")
        assert len(matches) == 2  # Should still find matches due to lower() in implementation

        # Search for non-existent term
        matches = fs.search_in_file(str(test_file), "nonexistent")
        assert len(matches) == 0

if __name__ == "__main__":
    test_file_search_initialization()
    test_file_search_search_files()
    test_file_search_search_in_file()
    print("All file search tests passed!")