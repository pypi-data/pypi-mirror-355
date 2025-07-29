import os
from datetime import datetime
import shutil


def _get_file_modified_date(file_path: str) -> datetime:
    """
    Returns the last modified datetime of a file.

    Args:
        file_path (str): Full path to the file.

    Returns:
        datetime: Datetime object representing the last modification time.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File does not exist: {file_path}")
    return datetime.fromtimestamp(os.stat(file_path).st_mtime)


def _get_subdirectories_names(
    folder_path: str, ignore_dir: list[str] = None
) -> list[str]:
    if ignore_dir is None:
        ignore_dir = []
    sub_dir_list = [
        name
        for name in os.listdir(folder_path)
        if os.path.isdir(os.path.join(folder_path, name)) and name not in ignore_dir
    ]
    return sub_dir_list


def flatten_dir(
    folder_path: str,
    dest_folder_path: str,
    ignore_dir: list[str] = None,
    rm_subdir: bool = False,
) -> None:
    """
    Moves all files from subdirectories of a given folder into a destination folder.

    This is useful for flattening a directory structure by collecting all files
    from nested folders and moving them into one target folder.

    Args:
        folder_path (str): Path to the root folder containing subdirectories with files.
        dest_folder_path (str): Path to the folder where all files should be moved.
        ignore_dir (list[str]): Names of subdirectories within `folder_path` that should be ignored during processing.
        rm_subdir (bool): If True, subdirectories will be removed after moving their contents.

    Raises:
        FileNotFoundError: If the root folder (`folder_path`) does not exist.

    Notes:

        - Any errors encountered while moving files or removing subdirectories are
          caught and printed, but not raised.
        - Fails silently (with printed messages) on permission issues, missing files, or non-empty directories during deletion.
    """
    if not os.path.exists(folder_path):
        raise FileNotFoundError(f"The folder path '{folder_path}' does not exist.")

    if not os.path.exists(dest_folder_path):
        os.makedirs(dest_folder_path)

    try:
        # Get name of the sub directories ignoring the one in ignore_dir list.
        sub_dir_list = _get_subdirectories_names(folder_path, ignore_dir)

        # Get the list of files to be moved.
        file_list = [
            name
            for name in os.listdir(folder_path)
            if os.path.isfile(os.path.join(folder_path, name))
            and name not in (ignore_dir or [])
        ]

        # If file_list empty then then return the function for sub_dir.
        if sub_dir_list and not file_list:
            for sub_dir_name in sub_dir_list:
                flatten_dir(
                    os.path.join(folder_path, sub_dir_name),
                    dest_folder_path,
                    ignore_dir,
                )

        # Move the files in the file_list to the dest_folder and check for folder in sub_dir_list.
        elif file_list:
            for name in file_list:
                source_item = os.path.join(folder_path, name)
                dest_item = os.path.join(dest_folder_path, name)
                try:
                    shutil.move(source_item, dest_item)
                except Exception as e:
                    print(f"Failed to move '{source_item}' to '{dest_item}': {e}")
            if sub_dir_list:
                for sub_dir_name in sub_dir_list:
                    flatten_dir(
                        os.path.join(folder_path, sub_dir_name),
                        dest_folder_path,
                        ignore_dir,
                    )

                # Remove the sub directories if rm_subdir is True.
                if rm_subdir:
                    for sub_dir_name in sub_dir_list:
                        sub_dir_path = os.path.join(folder_path, sub_dir_name)
                        try:
                            shutil.rmtree(sub_dir_path)
                        except Exception as e:
                            print(f"Failed to remove directory '{sub_dir_path}': {e}")

    except Exception as e:
        print(f"Error occurred while cleaning up folders: {e}")
