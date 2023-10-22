from enum import Enum
import glob
import os
from pathlib import Path
from pprint import pprint
import re
import shutil
from typing import List, Tuple
import general_helper_functions as help_funcs


def has_yaml_tag(tag: str, all_file_lines: List[str]) -> bool:
    """Returns True if the file has the appropriate yaml tag. False otherwise.
    tag: The tag to search for in the yaml section of the file.
    all_file_lines: All the lines of the file.
    """
    yaml_line = "---\n"
    tags_line = "tags:\n"

    in_yaml_section = False
    in_tags_section = False
    has_tag = False
    for line in all_file_lines:
        if line == yaml_line:
            in_yaml_section = True
        if line == tags_line and in_yaml_section:
            in_tags_section = True
        if (
            re.search(rf"\s*{re.escape(tag)}", line) != None
            and in_tags_section
            and in_yaml_section
        ):
            has_tag = True

    if has_tag:
        return True
    return False


def line_contains_comment(line: str) -> bool:
    if re.search(r"<!--.*-->", line) != None:
        return True
    return False


def remove_flashcard_metadata(all_file_lines: List[str]) -> List[str]:
    """Removes all flashcard_metadata comments from the file, line by line.
    all_file_lines: All the lines of the file.

    Returns a list of all the lines of the file with the flashcard_metadata comments removed.
    """
    changed_file = []
    for line in all_file_lines:
        if line_contains_comment(line):
            print("found comment")
            old_line = line
            line = re.sub("<!--.*-->", "", line)
            if old_line != line:
                print("removed comment")
        changed_file.append(line)
    return changed_file


def copy_attachments_to_new_directory(
    linked_attachments_path, input_directory, output_directory_for_attachments
) -> None:
    """Copies all attachments to a new directory.
    linked_attachments: A list of all the attachments to copy as paths.
    input_directory: The directory to search for the attachments.
    output_directory_for_attachments: The directory to copy the attachments to.
    """
    all_files = glob.glob(
        os.path.join(input_directory, "**/*"), recursive=True
    )  # get all files in the input directory
    for attachment_basename in linked_attachments_path:
        for file_path in all_files:
            if attachment_basename in file_path:
                if os.path.exists(file_path):
                    print("copying attachment")
                    if os.path.exists(output_directory_for_attachments) == False:
                        os.makedirs(output_directory_for_attachments)
                    shutil.copy2(file_path, output_directory_for_attachments)
                else:
                    print("Attachment not found")
                    print(file_path)


def return_linked_files(all_file_lines: List[str], file_extension=r"\..+") -> List[str]:
    """Returns a list of all the linked attachments in the file as paths.
    Links must follow the [[{attachment_path-name}.{file_extension}]] format.

    all_file_lines: All the lines of the file as a list of strings.
    file_extension: The file extension of the attachments to search for in the format r"\.{file_extension}". eg. file_extension = r"\.pdf" for pdf files.

    To ignore extension (return regardless of ext or lack there of) use file_extension = r""
    """
    all_linked_wikilink_attachment_paths = []
    for line in all_file_lines:
        wikilink_attachment_MatchGroup = re.search(
            rf"\[\[(.*{file_extension})\]\]", line
        )  # must follow [[{attachment_path-name}.{file_extension}]] format
        if wikilink_attachment_MatchGroup != None:
            wikilink_attachment_path = wikilink_attachment_MatchGroup.group(1)
            all_linked_wikilink_attachment_paths.append(wikilink_attachment_path)
    return all_linked_wikilink_attachment_paths


def return_linked_files_with_recursion_depth(
    start_file_path,
    start_file_directory,
    recursion_depth=0,
    _recursion_depth_current=-1,
    _all_linked_files: List[str] | None = None,
):
    if _recursion_depth_current == -1:
        _all_linked_files = []
        return_linked_files_with_recursion_depth(
            start_file_path,
            start_file_directory,
            recursion_depth,
            _recursion_depth_current + 1,
            _all_linked_files,
        )

    else:
        current_file_contains_links = True
        while (
            _recursion_depth_current < recursion_depth and current_file_contains_links
        ):
            with open(start_file_path, "r", encoding="utf8") as f:
                all_file_lines = f.readlines()

            linked_files = return_linked_files(all_file_lines, file_extension=r"")
            print("Current depth:\n", _recursion_depth_current, sep="")
            print("Current File:\n", start_file_path, sep="")
            print("linked files:\n", linked_files, "\n", sep="")
            _all_linked_files.extend(linked_files)  # type: ignore
            _recursion_depth_current += 1

            for linked_file in linked_files:
                linked_file_path = help_funcs.find_file_path(
                    start_file_directory, linked_file
                )
                if linked_file_path != None and current_file_contains_links:
                    return_linked_files_with_recursion_depth(
                        linked_file_path,
                        start_file_directory,
                        recursion_depth,
                        _recursion_depth_current,
                        _all_linked_files,
                    )
                else:
                    current_file_contains_links = False

        return _all_linked_files


def return_linked_files_with_recursion_depth__V2(
    start_file_path,
    start_file_directory,
    recursion_depth_max,
    _recursion_depth_current=0,
    _recursion_location_history: None | List[Tuple[int, str]] = None,
):
    print("Started New Instance")
    print("Current depth:\n", _recursion_depth_current, sep="")
    print("Current File:\n", start_file_path, sep="")
    print("")

    if _recursion_depth_current == 0:
        _recursion_location_history = [(_recursion_depth_current, start_file_path)]
    elif _recursion_location_history != None:
        _recursion_location_history.append((_recursion_depth_current, start_file_path))
    else:
        raise ValueError("Recursion location history is None")

    with open(start_file_path, "r", encoding="utf8") as f:
        all_file_lines = f.readlines()

    linked_files = return_linked_files(all_file_lines, file_extension=r"")

    combined_files = linked_files
    if linked_files != []:
        for linked_file in linked_files:
            linked_files_in_linked_file = []
            linked_file_path = help_funcs.find_file_path(
                start_file_directory, linked_file
            )
            if start_file_path != None:
                linked_files_in_linked_file = (
                    return_linked_files_with_recursion_depth__V2(
                        linked_file_path,
                        start_file_directory,
                        recursion_depth_max,
                        _recursion_depth_current + 1,
                        _recursion_location_history,
                    )
                )
            if linked_files_in_linked_file != []:
                combined_files.append(linked_files_in_linked_file)

    return combined_files


class File_Group:
    def __init__(self, file_path: str, child_file_groups: list):
        self.file_path = Path(file_path)
        self._child_file_groups = child_file_groups
        self.number_of_child_file_groups = len(child_file_groups)
        for index, child_group in enumerate(self._child_file_groups):
            setattr(self, f"child_file_group_{index}", child_group)

    def __repr__(self) -> str:
        return f"File_Group({self.file_path}, {self._child_file_groups})"

    def __str__(self) -> str:
        display_text = f"{self.file_path}"
        for index, group in enumerate([x for x in self._child_file_groups]):
            display_text += f"\n{'  '*(index+1)}-{index+1}- {group}"
        return display_text


def return_linked_files_V3(
    current_file, max_link_depth, root_directory, parent_file=None
):
    if parent_file == None:
        parent_file = current_file

    with open(current_file, "r", encoding="utf8") as f:
        all_file_lines = f.readlines()

    linked_files = return_linked_files(all_file_lines, file_extension=r"")

    if max_link_depth == 0:
        # Just return current file in group without going deeper
        file_group = File_Group(current_file, [])
    else:
        # more files are linked in the current file and program is allowed to go deeper
        child_file_groups = []
        for linked_file in linked_files:
            linked_file = help_funcs.find_file_path(root_directory, linked_file)
            child_group = return_linked_files_V3(
                linked_file, max_link_depth - 1, root_directory, parent_file=None
            )
            child_file_groups.append(child_group)
        file_group = File_Group(current_file, child_file_groups)
    return file_group


start_file_path = r"D:\Obsidian\Recursive file 1.md"

final_file_group = return_linked_files_V3(
    start_file_path, 3, os.path.dirname(start_file_path)
)
print(final_file_group)
