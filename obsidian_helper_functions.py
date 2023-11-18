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
import time
import cProfile, pstats, io


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
        self._depth = None

    @property
    def depth(self):
        if self._depth == None:
            self._depth = self.get_depth()
        return self._depth

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
        grouped_nodes = {}
        # Use try/except to append to list or create new list if key doesn't exist
        for node in all_nodes:
            if node is not None:
                try:
                    grouped_nodes[str(node.file_path)].append(node)
                except KeyError:
                    grouped_nodes[str(node.file_path)] = [node]
        # Filter original dictionary in-place to keep only duplicates
        for key in list(
            grouped_nodes.keys()
        ):  # Create a copy of keys to avoid RuntimeError
            if len(grouped_nodes[key]) <= 1:
                del grouped_nodes[key]
        return grouped_nodes

    def add_child(self, child):
        if child not in self.children:
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
        "returns a list of all the parent nodes in order from the current node to the root node"
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

    def sort_tree_by_alphabetical_order_and_number_of_children_to_set_depth(self):
        if self._has_been_sorted == False:
            self._has_been_sorted = True
            self.children.sort(
                key=lambda node: (node.has_children, node.file_path.name.lower())
            )
            for child in self.children:
                child.sort_tree_by_alphabetical_order_and_number_of_children_to_set_depth()

    def determine_indents(self) -> str:
        parents = self.list_all_parents()[::-1]
        indent = ""
        for parent in parents:
            if parent.parent == None:
                indent += ""
            elif parent.is_last_born_child:
                indent += "    "
            else:
                indent += "│   "
        return f"{indent}"

    def print_improved_tree(
        self,
        depth=0,
        siblings: None | list["FileTreeNode"] = None,
        duplicate_nodes=None,
    ):
        if duplicate_nodes == None:
            duplicate_nodes = self.find_all_duplicate_nodes()

        if siblings == None:
            siblings = []
        if self.parent == None:
            # If the current node is the root node
            print(self.file_path)
            for child in self.children:
                child_siblings = self.children
                child.print_improved_tree(
                    depth + 1, siblings=child_siblings, duplicate_nodes=duplicate_nodes
                )
        else:
            file_name = help_funcs.link(
                f"{self.file_path}", f"{str(self.file_path.name[:-3])}"
            )
            print_children = True
            indents = self.determine_indents()
            if self.children:
                # current node has children
                if str(self.file_path) in duplicate_nodes.keys():
                    # current node has a duplicate
                    for duplicate_node in duplicate_nodes[str(self.file_path)]:
                        # print(duplicate_node.get_depth(), self.get_depth())
                        if duplicate_node.depth < self.depth:
                            print_children = False
                            file_name = f"<< {file_name} >>"

                if self.is_last_born_child:
                    fork = "└── "
                else:
                    fork = "├───"
                blank_space = f"{indents}│"
                print_string = indents + fork + file_name
                print_string = f"{blank_space}\n{print_string}"

            else:
                # current node does not have children
                if self.parent.parent == None:
                    # special formatting for zeroth level children without descendants
                    print_string = "|   " + file_name
                else:
                    print_string = indents + file_name

            print(print_string)
            if print_children:
                for child in self.children:
                    child_siblings = self.children
                    child.print_improved_tree(
                        depth + 1, child_siblings, duplicate_nodes=duplicate_nodes
                    )

    def __repr__(self) -> str:
        return f"FileTreeNode({self.file_path}) - {self.id}"


def return_linked_files_V4(
    root_directory: str,
    max_link_depth: int,
    current_file: Path,
    _parent_node: FileTreeNode | None = None,
    all_files_in_base_directory: dict[str, Path] | None = None,
    previously_visited_files: dict[Path, int] | None = None,
    previously_created_nodes: list[FileTreeNode] | None = None,
):
    if previously_created_nodes == None:
        previously_created_nodes = []

    if previously_visited_files == None:
        previously_visited_files = {}
    elif current_file not in previously_visited_files.keys():
        previously_visited_files[current_file] = 1
    else:
        previously_visited_files[current_file] += 1
        if previously_visited_files[current_file] > 2:
            previously_visited_files[current_file] = 1
            return

    if all_files_in_base_directory is None:
        # search for all files in the base directory and subdirectories
        all_files_in_base_directory = {
            Path(file).name: Path(root) / file
            for root, dirs, files in os.walk(root_directory)
            for file in files
        }

    duplicate_node = False
    """for node in previously_created_nodes:
        if current_file == node.file_path:
            duplicate_node = node"""
    if duplicate_node == False:
        current_node = FileTreeNode(current_file)
        previously_created_nodes.append(current_node)
    else:
        current_node = duplicate_node
    root_node = current_node if _parent_node is None else _parent_node
    if _parent_node:
        _parent_node.add_child(current_node)
    if max_link_depth != 0:
        with open(current_file, "r", encoding="utf8") as f:
            all_file_lines = f.readlines()
        linked_file_base_names = return_linked_base_names(
            all_file_lines, must_have_no_extension=True
        )
        linked_file_base_names = list(set(linked_file_base_names))  # remove duplicates
        (
            linked_files,
            un_finable_files,
        ) = help_funcs.convert_file_base_names_to_full_path_V2(
            linked_file_base_names, all_files_in_base_directory, root_directory
        )
        for file in un_finable_files:
            current_node.add_unfindable_file(file)
        for linked_file in linked_files:
            return_linked_files_V4(
                root_directory,
                max_link_depth - 1,
                current_file=linked_file,
                _parent_node=current_node,
                all_files_in_base_directory=all_files_in_base_directory,
                previously_visited_files=previously_visited_files,
                previously_created_nodes=previously_created_nodes,
            )
    return current_node


start_file_path = Path(r"D:\Obsidian\School\School Index.md")
vault_folder = r"D:\Obsidian"
result = return_linked_files_V4(
    vault_folder,
    max_link_depth=100,
    current_file=Path(start_file_path),
)

result.sort_tree_by_alphabetical_order_and_number_of_children_to_set_depth()
result.print_improved_tree()
