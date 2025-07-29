import os
import shutil
import tempfile
import pytest
from sortium.file_utils import flatten_dir


def create_temp_file(directory, name, content="test"):
    path = os.path.join(directory, name)
    with open(path, "w") as f:
        f.write(content)
    return path


@pytest.fixture
def setup_test_dirs():
    base = tempfile.mkdtemp()
    dest = tempfile.mkdtemp()
    dest_test = os.path.join(dest, "dest_test")

    sub1 = os.path.join(base, "sub1")
    sub2 = os.path.join(base, "sub2")
    os.mkdir(sub1)
    os.mkdir(sub2)

    sub_sub1 = os.path.join(sub1, "sub_sub1")
    sub_sub2 = os.path.join(sub2, "sub_sub2")
    os.mkdir(sub_sub1)
    os.mkdir(sub_sub2)

    # Ignored dir
    ignored = os.path.join(base, "ignoreme")
    os.mkdir(ignored)

    file1 = create_temp_file(sub_sub1, "file1.txt", "data1")
    file2 = create_temp_file(sub_sub2, "file2.txt", "data2")
    file_outer = create_temp_file(sub1, "file_outer.txt", "outer_file")
    ignored_file = create_temp_file(ignored, "ignored.txt", "ignored")

    yield {
        "base": base,
        "dest": dest,
        "dest_test": dest_test,
        "files": [file1, file2, file_outer],
        "ignored": ignored,
        "ignored_file": ignored_file,
    }

    shutil.rmtree(base)


def test_flatten_dir_moves_files(setup_test_dirs):
    flatten_dir(
        setup_test_dirs["base"], setup_test_dirs["dest"], ignore_dir=["ignoreme"]
    )

    dest_files = os.listdir(setup_test_dirs["dest"])
    assert "file1.txt" in dest_files
    assert "file2.txt" in dest_files
    assert "file_outer.txt" in dest_files

    # Ignored file should still exist
    assert os.path.exists(setup_test_dirs["ignored_file"])


def test_flatten_dir_create_dest_dir(setup_test_dirs):
    flatten_dir(
        setup_test_dirs["base"], setup_test_dirs["dest_test"], ignore_dir=["ignoreme"]
    )

    assert os.path.exists(setup_test_dirs["dest_test"])
