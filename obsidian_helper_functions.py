from enum import Enum
import glob
import json
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


def return_linked_base_names(
    all_file_lines: List[str],
    file_extension=r"\..+",
    ignore_extension=False,
    must_have_no_extension=False,
) -> List[str]:
    """Returns a list of all the linked attachments in the file as paths.
    Links must follow the [[{attachment_path-name}.{file_extension}]] format.

    all_file_lines: All the lines of the file as a list of strings.
    file_extension: The file extension of the attachments to search for in the format r"\.{file_extension}". eg. file_extension = r"\.pdf" for pdf files.

    """
    # all_file_lines = [
    #     "file start",
    #     "this is a file with [[normal link]] this is end",
    #     "this is a file with [[link with extension.pdf]] this is end",
    #     "this is a file with [[link.WITH A DOT]] this is end",
    #     "this is a file with [[link with alias|alias]] this is end",
    #     "this is a file with [[link with header#header]] this is end",
    #     "this is a file with [[link with header#header|and alias]] this is end",
    #     "this is a file with [[multiple]] [[links]] of [[different|types]] [[includingfile.pdf]]this is end",
    # ]

    if must_have_no_extension:
        all_linked_wikilink_attachment_paths = []
        for line in all_file_lines:
            matches = re.findall(
                r"\[\[(.*?)\]\]", line
            )  # must be text surrounded by [[ and ]]
            for match in matches:
                # must handel the unusual case of multiple matches in 1 line
                if "|" in match:
                    # check if file has an alias
                    match = match.split("|")[0]
                if "#" in match:
                    # check if file has a header
                    match = match.split("#")[0]
                if "." in match:
                    # check if file has an extension or just contains a period
                    num_chars_after_period = len(match.split(".")[-1])
                    if num_chars_after_period > 4:
                        all_linked_wikilink_attachment_paths.append(match)
                    else:
                        continue
                else:
                    # file has no extension, header, or alias
                    all_linked_wikilink_attachment_paths.append(match)
    else:
        if not ignore_extension:
            regex = rf"\[\[(.*{file_extension})\]\]"
        elif ignore_extension:
            regex = rf"\[\[(.*)\]\]"
        else:
            raise ValueError("Unknown error occurred.")

        all_linked_wikilink_attachment_paths = []
        for line in all_file_lines:
            wikilink_attachment_MatchGroups = re.finditer(
                regex, line
            )  # must follow [[{attachment_path-name}.{file_extension}]] format
            for group in wikilink_attachment_MatchGroups:
                # must handel the unusual case of multiple groups
                match = group.groups()
                all_linked_wikilink_attachment_paths.append(match[0])
    return all_linked_wikilink_attachment_paths


class File_Group:
    def __init__(self, file_path: str, child_file_groups: list, parent_file=None):
        self.file_path = Path(file_path)
        self.parent_file = parent_file
        self._child_file_groups = child_file_groups
        for index, child_group in enumerate(self._child_file_groups):
            setattr(self, f"child_file_group_{index}", child_group)

    @property
    def number_of_child_file_groups(self):
        return len(self._child_file_groups)

    def get_depth(self):
        level = 0
        raise NotImplementedError

    def __repr__(self) -> str:
        return f"File_Group({self.file_path}, {self._child_file_groups})"

    # def __str__(self) -> str:
    #     display_text = f"{self.file_path}"
    #     for index, group in enumerate([x for x in self._child_file_groups]):
    #         display_text += f"\n{'  '*(index+1)}-{index+1}- {group}"
    #     return display_text


def return_linked_files_V3(
    current_file: str,
    max_link_depth: int,
    root_directory: str,
    parent_file: str | None = None,
):
    if parent_file == None:
        parent_file = current_file

    with open(current_file, "r", encoding="utf8") as f:
        all_file_lines = f.readlines()

    linked_files = return_linked_base_names(all_file_lines, file_extension=r"")

    if max_link_depth == 0:
        # Just return current file in group without going deeper
        file_group = File_Group(current_file, [], parent_file)
    else:
        # more files are linked in the current file and program is allowed to go deeper
        child_file_groups = []
        for linked_file in linked_files:
            linked_file = help_funcs.find_file_path(root_directory, linked_file)
            child_group = return_linked_files_V3(
                linked_file, max_link_depth - 1, root_directory, parent_file=None
            )
            child_file_groups.append(child_group)
        file_group = File_Group(current_file, child_file_groups, parent_file)
    return file_group


# ################################################################################


class FileTreeNode:
    def __init__(self, file_path):
        self.file_path = Path(file_path)
        self.children = []
        self.parent = None

    def add_child(self, child):
        self.children.append(child)
        child.parent = self

    def get_depth(self):
        level = 0
        p = self.parent
        while p:
            level += 1
            p = p.parent
        return level

    def print_tree(self):
        spaces = " " * self.get_depth() * 3
        prefix = spaces + "|__" if self.parent else ""
        print(prefix + str(self.file_path))
        if self.children:
            for child in self.children:
                child.print_tree()


def return_linked_files_V4(
    root_directory: str,
    max_link_depth: int,
    current_file: str,
    _parent_node: FileTreeNode | None = None,
):
    current_node = FileTreeNode(current_file)
    if _parent_node != None:
        _parent_node.add_child(current_node)
    if max_link_depth == 0:
        # current_file is a leaf node
        pass
    else:
        with open(current_file, "r", encoding="utf8") as f:
            all_file_lines = f.readlines()
        linked_file_base_names = return_linked_base_names(
            all_file_lines, must_have_no_extension=True
        )
        linked_files, un_finable_files = help_funcs.convert_file_base_names_to_full_path(
            linked_file_base_names, root_directory
        )

        for linked_file in linked_files:
            return_linked_files_V4(
                root_directory,
                max_link_depth - 1,
                current_file=linked_file,
                _parent_node=current_node,
            )
    return current_node


start_file_path = r"D:\Obsidian\School\School Index.md"
vault_folder = r"D:\Obsidian"
result = return_linked_files_V4(
    vault_folder,
    max_link_depth=10,
    current_file=start_file_path,
)
result.print_tree()
pass
