import os

from bobleesj.utils.io.folder import contains_file_type, get_file_paths


def test_get_file_paths_with_matching_files(tmp_path):
    # Create dummy .cif files
    file1 = tmp_path / "a.cif"
    file2 = tmp_path / "b.cif"
    file1.write_text("data")
    file2.write_text("data")
    # Create a non-matching file
    (tmp_path / "readme.txt").write_text("not a cif")
    result = get_file_paths(str(tmp_path), ext=".cif")
    expected = sorted([str(file1), str(file2)])
    assert sorted(result) == expected


def test_get_file_paths_with_no_matches(tmp_path):
    (tmp_path / "file1.txt").write_text("irrelevant")
    (tmp_path / "file2.log").write_text("still irrelevant")

    result = get_file_paths(str(tmp_path), ext=".cif")
    assert result == []


def test_contains_file_type_with_no_matches(tmp_path):
    (tmp_path / "test.txt").write_text("text")
    assert contains_file_type(str(tmp_path), ext=".cif") is False


def test_contains_file_type_with_match(tmp_path):
    (tmp_path / "test.cif").write_text("text")
    assert contains_file_type(str(tmp_path), ext=".cif") is True


def test_contains_file_type_ignores_dirs(tmp_path):
    os.mkdir(tmp_path / "test.cif")
    assert contains_file_type(str(tmp_path), ext=".cif") is False
