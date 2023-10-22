import fnmatch
from typing import List
import glob
import os


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
    all_file_paths_from_input = glob.glob(
        os.path.join(INPUT_DIRECTORY, "**/*.md"), recursive=True
    )  # get all .md files in the input directory
    all_files_full_paths = []
    for file_path in all_file_paths_from_input:
        all_files_full_paths.append(os.path.join(INPUT_DIRECTORY, file_path))
    return all_files_full_paths


def find_file_path(directory, base_name):
    for root, dirnames, filenames in os.walk(directory):
        for filename in fnmatch.filter(filenames, f"{base_name}.*"):
            return os.path.join(root, str(filename))
    return None
