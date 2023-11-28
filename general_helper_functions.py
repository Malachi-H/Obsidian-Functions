import fnmatch
from pprint import pprint
import re
from typing import List
import glob
import os
from pathlib import Path
from time import time


def terminal_link(uri, label=None):
    if label is None:
        label = uri
    parameters = ""

    # OSC 8 ; params ; URI ST <name> OSC 8 ;; ST
    escape_mask = "\033]8;{};{}\033\\{}\033]8;;\033\\"

    return escape_mask.format(parameters, uri, label)


def get_input_directory(DEFAULT_DIRECTORY: str) -> str:
    ValidInput = False
    while not ValidInput:
        proposed_input_directory = input(
            rf"Please Enter INPUT Directory or enter nothing for default ({DEFAULT_DIRECTORY}): "
        )
        if proposed_input_directory == "":
            # Leave as input directory as default
            ValidInput = True
        else:
            if os.path.exists(proposed_input_directory) == True:
                ValidInput = True
                return proposed_input_directory
            else:
                print("INPUT directory not found")
                print(proposed_input_directory)
    return DEFAULT_DIRECTORY


def get_output_directory(default_directory: str) -> str:
    ValidInput = False
    while not ValidInput:
        proposed_output_directory = input(
            "Please Enter OUTPUT Directory or nothing for default ({INPUT_DIRECTORY}_comments_removed): "
        )
        if proposed_output_directory == "":
            ValidInput = True
            proposed_output_directory = default_directory
        elif proposed_output_directory[0] in ['"', "'"]:
            # Check if wrapped in quotes and remove them
            proposed_output_directory = proposed_output_directory[1:-1]
            ValidInput = True
        if os.path.exists(proposed_output_directory) == False:
            # make directory if it doesn't exist
            os.makedirs(proposed_output_directory)
            return proposed_output_directory
    return default_directory


def get_start_file(DEFAULT_START_FILE: str) -> str:
    ValidInput = False
    while not ValidInput:
        proposed_start_file = input(
            rf"Please Enter START FILE or enter nothing for default ({DEFAULT_START_FILE}): "
        )
        if proposed_start_file == "":
            # Leave as input directory as default
            ValidInput = True
        elif proposed_start_file[0] in ['"', "'"]:
            # Check if wrapped in quotes and remove them
            proposed_start_file = proposed_start_file[1:-1]
            if os.path.exists(proposed_start_file) == True:
                ValidInput = True
                return proposed_start_file
            else:
                print("START FILE not found")
                print(proposed_start_file)
    return DEFAULT_START_FILE


def return_all_full_file_paths(INPUT_DIRECTORY):
    """Returns all the full file paths (absolute paths instead of relative) of all the files in the input directory."""
    all_file_paths_from_input = [
        entry.path
        for entry in os.scandir(INPUT_DIRECTORY)
        if entry.is_file() and entry.name.endswith(".md")
    ]
    return all_file_paths_from_input


def return_all_paths_in_directory_as_dictionary(
    INPUT_DIRECTORY: Path, file_type: str | None = None
) -> dict[str, Path]:
    """Returns a dictionary of all the files in the input directory.
    key = file name
    value = full path to file

    If file_type is specified, only files of that type will be returned.
    file_type should be a string with the period included (e.g. ".md")
    """
    all_files_in_base_directory = {
        Path(file).name: Path(root) / file
        for root, dirs, files in os.walk(INPUT_DIRECTORY)
        for file in files
    }
    # Optionally filter by file type
    if file_type != None:
        all_files_in_base_directory = {
            name: path
            for (name, path) in all_files_in_base_directory.items()
            if path.suffix == f"{file_type}"
        }
    return all_files_in_base_directory


def find_file_path(directory: str, base_name: str) -> str | None:
    if "/" in base_name:
        # for use with Obsidian, the base_name can sometime be a file path relative to the vault root
        # this occurs when there are multiple files with the same basename, requiring a more specific pointer to the file.
        segments = base_name.split("/")
        real_base_name = segments[-1]
        relative_path = "\\".join(segments[:-1])
        more_specific_path = os.path.join(directory, relative_path)
        directory = more_specific_path
        base_name = real_base_name
    for current_folder, subfolders, filenames in os.walk(directory):
        for filename in fnmatch.filter(filenames, f"{base_name}.*"):
            return os.path.join(current_folder, str(filename))
    return None


def convert_file_base_names_to_full_path(
    linked_file_base_names: list[str], root_directory: str
) -> tuple[list[str], list[str]]:
    """Converts a list of file base names to a list of full paths."""
    linked_files = []
    un_finable_files = []
    for linked_file_base_name in linked_file_base_names:
        # convert to full path
        linked_file = find_file_path(root_directory, linked_file_base_name)
        if linked_file != None:
            linked_files.append(linked_file)
        else:
            print(f"Linked file not found: {linked_file_base_name}\n")
            if linked_file_base_name[-1] == " ":
                print(
                    "Looks like there is a trailing space at the end of the file name!"
                )
            un_finable_files.append(linked_file_base_name)
    return linked_files, un_finable_files


def convert_file_base_names_to_full_path_V2(
    linked_file_base_names: list[str],
    all_files_in_base_directory: dict[str, Path],
    root_directory: str | Path,
) -> tuple[list[Path], list[str]]:
    """This function needs refactoring but im too lazy to do so now.
    Here's what is does:
    1. Checks if the input file base name is a file path relative to the vault root (this is caused by duplicate file names)
    2. If it is, it checks to see if the file exists in the vault root by searching with the more specific path instead of just the base name

    3. If the input file base name is not a file path relative to the vault root, it checks to see if the file exists in the vault root by searching with just the base name
    4. if it can't find it, it lowers its own value and all of the dictionary keys and searches again (time consuming)
    5. if it still can't find it, it prints a message to the terminal (would be better to raise an error with a logging module)
    """
    linked_files: list[Path] = []
    un_finable_files: list[str] = []
    for linked_file_base_name in linked_file_base_names:
        if "/" in linked_file_base_name:
            all_file_paths_in_root_directory = [
                file for file in all_files_in_base_directory.values()
            ]
            path_of_linked_file = Path(root_directory) / Path(
                f"{linked_file_base_name}.md"
            )
            if path_of_linked_file in all_file_paths_in_root_directory:
                linked_files.append(path_of_linked_file)
            else:
                print(f"Linked file not found: {linked_file_base_name}\n")
                if linked_file_base_name[-1] == " ":
                    print(
                        "Looks like there is a trailing space at the end of the file name!"
                    )
                un_finable_files.append(linked_file_base_name)
        else:
            linked_file_base_name = f"{linked_file_base_name}.md"  # assuming that the file is a markdown file
            if linked_file_base_name in all_files_in_base_directory.keys():
                linked_files.append(all_files_in_base_directory[linked_file_base_name])
            else:
                lowered_all_files_in_base_directory = {
                    key.lower(): value
                    for key, value in all_files_in_base_directory.items()
                }
                if (
                    linked_file_base_name.lower()
                    in lowered_all_files_in_base_directory.keys()
                ):
                    linked_files.append(
                        lowered_all_files_in_base_directory[
                            linked_file_base_name.lower()
                        ]
                    )
                else:
                    print(f"Linked file not found: {linked_file_base_name}\n")
                    if linked_file_base_name[-1] == " ":
                        print(
                            "Looks like there is a trailing space at the end of the file name!"
                        )
                    un_finable_files.append(linked_file_base_name)

    return linked_files, un_finable_files
