from enum import Enum
import glob
import json
import os
from pathlib import Path
from pprint import pprint
from random import randint, random
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
    r"""Returns a list of all the linked attachments in the file as paths.
    Links must follow the [[{attachment_path-name}.{file_extension}]] format.

    all_file_lines: All the lines of the file as a list of strings.
    file_extension: The file extension of the attachments to search for in the format r"\.{file_extension}". eg. file_extension = r"\.pdf" for pdf files.

    """

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


class FileTreeNode:
    def __init__(self, file_path):
        self.file_path: Path = Path(file_path)
        self.children: list["FileTreeNode"] = []
        self.parent: "FileTreeNode" | None = None
        self.unfindable_files: list[str] = []
        self.id = randint(0, 1000000)  # TODO: remove this
        self._has_been_sorted = False
        self.hierarchical_importance = int
        self.duplicate_nodes = list[FileTreeNode]

    @property
    def is_last_born_child(self):
        if self.parent == None:
            return True
        if self.parent.children[-1] == self:
            return True
        return False

    @property
    def has_children(self):
        if self.children:
            return True
        return False

    def find_root_node(self):
        root_node = self
        while root_node.parent:
            root_node = root_node.parent
        return root_node

    def list_all_descendants(self) -> list["FileTreeNode"] | list[None]:
        descendants = []
        for child in self.children:
            descendants.append(child)
            descendants += child.list_all_descendants()
        return descendants

    def find_all_duplicate_nodes(self):
        root_node = self.find_root_node()
        all_nodes = root_node.list_all_descendants()
        grouped_nodes: dict[str, list[FileTreeNode]] = {}
        for note in all_nodes:
            if note != None:
                if str(note.file_path) in grouped_nodes.keys():
                    grouped_nodes[str(note.file_path)].append(note)
                else:
                    grouped_nodes[str(note.file_path)] = [note]
        duplicates = {
            key: value for (key, value) in grouped_nodes.items() if len(value) > 1
        }  # remove all non-duplicates
        return duplicates

    def add_child(self, child):
        self.children.append(child)
        child.parent = self

    def add_unfindable_file(self, file_base_name):
        self.unfindable_files.append(file_base_name)

    def get_depth(self):
        level = 0
        p = self.parent
        while p:
            level += 1
            p = p.parent
        return level

    def list_all_parents(self) -> list["FileTreeNode"]:
        parents = []
        p = self.parent
        while p:
            parents.append(p)
            p = p.parent
        return parents

    def count_all_descendants(self, node: "FileTreeNode", depth_limit=10000) -> int:
        count = 0
        for child in node.children:
            count += 1
            if depth_limit > 0:
                count += self.count_all_descendants(child, depth_limit=depth_limit - 1)
        return count

    def sort_tree_by_number_of_children(self):
        # current node is not root
        self.children.sort(
            key=lambda node: self.count_all_descendants(node), reverse=False
        )
        for child in self.children:
            child.sort_tree_by_number_of_children()

    def sort_tree_by_alphabetical_order_and_number_of_children_to_set_depth(self):
        if self._has_been_sorted == False:
            self._has_been_sorted = True
            self.children.sort(
                key=lambda node: (node.has_children, node.file_path.name.lower())
            )
            for child in self.children:
                child.sort_tree_by_alphabetical_order_and_number_of_children_to_set_depth()

    def should_draw_tree_branch_line(self):
        should_draw = True
        if self.parent:
            if self.parent.is_last_born_child:
                should_draw = False

    def print_improved_tree(
        self, depth=0, siblings: None | list["FileTreeNode"] = None
    ):
        if siblings == None:
            siblings = []
        if self.parent == None:
            # If the current node is the root node
            print(self.file_path)
            for child in self.children:
                child_siblings = self.children
                child.print_improved_tree(depth + 1, child_siblings)
        else:
            file_name = f"{str(self.file_path.name)}"
            print_children = True
            if self.children:
                # current node has children
                duplicate_nodes = self.find_all_duplicate_nodes()
                if str(self.file_path) in duplicate_nodes.keys():
                    # current node has a duplicate
                    for duplicate_node in duplicate_nodes[str(self.file_path)]:
                        # print(duplicate_node.get_depth(), self.get_depth())
                        if duplicate_node.get_depth() < self.get_depth():
                            print_children = False
                            file_name = f"<< {file_name} >>"

                if self.is_last_born_child:
                    print_string = self.get_depth() * "    " + "└── " + file_name
                else:
                    print_string = self.get_depth() * "    " + "├───" + file_name

            else:
                # current node does not have children
                print_string = self.get_depth() * "    " + file_name

            print(print_string)
            if print_children:
                for child in self.children:
                    child_siblings = self.children
                    child.print_improved_tree(depth + 1, child_siblings)

    def __repr__(self) -> str:
        return f"FileTreeNode({self.file_path}) - {self.id}"


def return_linked_files_V4(
    root_directory: str,
    max_link_depth: int,
    current_file: str,
    _parent_node: FileTreeNode | None = None,
):
    current_node = FileTreeNode(current_file)
    if _parent_node == None:
        root_node = current_node
    else:
        # find root node
        root_node = _parent_node
        while root_node.parent:
            root_node = root_node.parent

    if _parent_node:
        _parent_node.add_child(current_node)

    if max_link_depth != 0:
        with open(current_file, "r", encoding="utf8") as f:
            all_file_lines = f.readlines()
        linked_file_base_names = return_linked_base_names(
            all_file_lines, must_have_no_extension=True
        )
        (
            linked_files,
            un_finable_files,
        ) = help_funcs.convert_file_base_names_to_full_path(
            linked_file_base_names, root_directory
        )

        for file in un_finable_files:
            current_node.add_unfindable_file(file)

        for linked_file in linked_files:
            if True:
                return_linked_files_V4(
                    root_directory,
                    max_link_depth - 1,
                    current_file=linked_file,
                    _parent_node=current_node,
                )
    return current_node


start_file_path = r"D:\Obsidian\School\School Index.md"
start_file_path = r"D:\Obsidian\School\Maths\Maths.md"
vault_folder = r"D:\Obsidian"
result = return_linked_files_V4(
    vault_folder,
    max_link_depth=7,
    current_file=start_file_path,
)
result.sort_tree_by_alphabetical_order_and_number_of_children_to_set_depth()
result.print_improved_tree()
pass
