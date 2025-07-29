import pytest
from gitanalytics.complexity_analyzer import ComplexityAnalyzer
import tempfile
from pathlib import Path

def test_complexity_analyzer_simple_file():
    """
    Tests that the ComplexityAnalyzer correctly calculates the complexity of a simple file.
    """
    # Create a temporary python file with known complexity
    py_content = """
def func_a(x):
    if x > 10: # +1
        return 1
    return 2

def func_b(y, z):
    if y and z: # +2 (1 for `if`, 1 for `and`)
        for i in range(y): # +1
            if i == z: # +1
                return True
    return False
"""
    # Expected complexities: func_a = 2, func_b = 4. Average = (2+4)/2 = 3

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        file_path = temp_path / "test_file.py"
        file_path.write_text(py_content)

        analyzer = ComplexityAnalyzer()
        complexity_data = analyzer.analyze_files(temp_dir, ["test_file.py"])

        assert "test_file.py" in complexity_data
        assert complexity_data["test_file.py"] == 3.5

def test_complexity_analyzer_empty_file():
    """
    Tests that the analyzer handles empty files gracefully.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        file_path = temp_path / "empty.py"
        file_path.write_text("")

        analyzer = ComplexityAnalyzer()
        complexity_data = analyzer.analyze_files(temp_dir, ["empty.py"])

        assert "empty.py" in complexity_data
        assert complexity_data["empty.py"] == 0

def test_complexity_analyzer_nonexistent_file():
    """
    Tests that the analyzer handles non-existent files gracefully.
    """
    analyzer = ComplexityAnalyzer()
    complexity_data = analyzer.analyze_files("/tmp", ["nonexistent123.py"])
    assert "nonexistent123.py" in complexity_data
    assert complexity_data["nonexistent123.py"] == 0