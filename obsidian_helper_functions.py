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
import default_values


def check_for_singleline_flashcard_style_section_in_note(
    all_file_lines: List[str],
) -> list[int]:
    """Returns the line numbers of the flashcard style sections if they exists. None otherwise.
    all_file_lines: All the lines of the file.
    """

    question_lines: list[int] = []
    for current_line_number, line in enumerate(all_file_lines):
        if ";;" in line or ":::" in line:  # reversible or non-reversible
            question_lines.append(current_line_number + 1)
    return question_lines


def check_for_multiline_flashcard_style_section_in_note(
    all_file_lines: List[str], file_name: str
) -> list[int]:
    """Returns the line numbers of the flashcard style sections if they exists. None otherwise.
    all_file_lines: All the lines of the file.
    """

    # group the lines before and after the current one into a list of lists
    # eg. [1,2,3,4] => [[None, 1, 2], [1,2,3], [2,3,4], [3,4,None]]
    l1 = all_file_lines.copy()
    l1.insert(0, None)  # type: ignore
    l1.insert(1, None)  # type: ignore
    l2 = all_file_lines.copy()
    l2.insert(0, None)  # type: ignore
    l2.insert(len(l2), None)  # type: ignore
    l3 = all_file_lines.copy()
    l3.insert(len(l3), None)  # type: ignore
    l3.insert(len(l3), None)  # type: ignore
    list_of_lists = list(zip(l1, l2, l3))

    question_lines: list[int] = []
    for current_line_number, line_group in enumerate(list_of_lists):
        previous_line = line_group[0]
        current_line = line_group[1]
        next_line = line_group[2]

        if previous_line == "\n":
            continue
        elif current_line == None:
            continue
        elif current_line[0] != "?":  # reversible or non-reversible
            continue
        elif next_line == "\n":
            continue
        elif next_line == None:
            continue
        elif current_line_number < 2:
            continue
        else:
            # Fits the format of a multiline flashcard style section
            question_lines.append(current_line_number)

    return question_lines


def extract_tags_from_note_basenames(
    input_directory: Path,
    all_files: dict[str, Path],
    notes_for_tag_extraction: list[str],
) -> dict:
    """
    Extracts yaml tags from notes specified in notes_for_tag_extraction.

    Parameters:
        input_directory (Path): The input directory where the notes are located.
        all_files (dict[str, Path]): A dictionary containing all the file basenames and their paths.
        notes_for_tag_extraction (list[str]): A list of note basenames to extract tags from.

    Returns:
        dict: A dictionary with the following keys:
            - note (str): The full path of the note.
            - yaml_tags (list[str]): The list of yaml tags extracted from the note.
            - line_number_of_tags (int): The line number of the yaml tags section.
            - yaml_section_exists (bool): Indicates whether the yaml section exists in the note.
    """
    (
        notes_for_tag_extraction_full_path,
        unfindable_files,
    ) = help_funcs.convert_file_base_names_to_full_path_V2(
        notes_for_tag_extraction, all_files, input_directory
    )
    if len(unfindable_files) > 0:
        raise ValueError(
            f"Unable to find file ({unfindable_files}) to extract yaml tags from."
        )

    yaml_tags_dict = {}
    for note in notes_for_tag_extraction_full_path:
        with open(note, "r", encoding="utf-8") as f:
            all_file_lines = f.readlines()
        (
            yaml_tags,
            line_number_of_tags,
            yaml_section_exists,
        ) = return_yaml_property("allowedTags", all_file_lines)
        if yaml_tags == None:
            raise ValueError(f"allowedTags property not found in {note}")
        yaml_tags = yaml_list_type_property_to_list(yaml_tags)
        yaml_tags_dict["note"] = note
        yaml_tags_dict["yaml_tags"] = yaml_tags
        yaml_tags_dict["line_number_of_tags"] = line_number_of_tags
        yaml_tags_dict["yaml_section_exists"] = yaml_section_exists
    return yaml_tags_dict


def yaml_list_type_property_to_list(yaml_property: str) -> list[str]:
    """Converts a yaml property to a list of strings.
    yaml_property: The yaml property to convert to a list of strings.
    """
    yaml_property = yaml_property.replace("[", "")
    yaml_property = yaml_property.replace("]", "")
    yaml_property = yaml_property.replace("\n", "")
    yaml_property_list = yaml_property.split(",")
    yaml_property_list = [x.strip() for x in yaml_property_list]
    return yaml_property_list


def has_yaml_tag(tag: str, all_file_lines: List[str]) -> bool:
    """Returns True if the file has the appropriate yaml tag. False otherwise.
    tag: The tag to search for in the yaml section of the file.
    all_file_lines: All the lines of the file.
    """
    yaml_line = "---\n"

    in_yaml_section = False
    in_tags_section = False
    has_tag = False
    for index, line in enumerate(all_file_lines):
        if line == yaml_line:
            in_yaml_section = True
        if in_yaml_section:
            yaml_property = line.split(":")
            if yaml_property[0] == "tags":
                yaml_tags = yaml_property[1]
                yaml_tags = yaml_tags.replace("[", "")
                yaml_tags = yaml_tags.replace("]", "")
                yaml_tags = yaml_tags.replace("\n", "")
                yaml_tags = yaml_tags.split(",")
                yaml_tags = [x.strip() for x in yaml_tags]

                if tag in yaml_tags:
                    has_tag = True
                    return has_tag
    return has_tag


def remove_yaml_tag(tag: str, all_file_lines: List[str], filename: str) -> List[str]:
    """Removes the tag from the file.
    tag: The tag to remove from the yaml tag section.
    all_file_lines: All the lines of the file.

    returns all file lines with the tag removed.
    """
    yaml_line = "---\n"

    in_yaml_section = False
    for index, line in enumerate(all_file_lines):
        if not in_yaml_section:
            if line != yaml_line:
                continue
            else:
                in_yaml_section = True
        yaml_property = line.split(":")
        if yaml_property[0] != "tags":
            continue
        yaml_tags = yaml_property[1]
        yaml_tags = yaml_tags.replace("[", "")
        yaml_tags = yaml_tags.replace("]", "")
        yaml_tags = yaml_tags.replace("\n", "")
        yaml_tags = yaml_tags.split(",")
        yaml_tags = [x.strip() for x in yaml_tags]

        if tag not in yaml_tags:
            raise ValueError(f"Tag '{tag}' not found in {filename}.")
        yaml_tags.remove(tag)
        yaml_tags = ", ".join(yaml_tags)
        yaml_tags = f"[{yaml_tags}]"
        yaml_tag_property = f"tags: {yaml_tags}\n"
        all_file_lines[index] = yaml_tag_property
        return all_file_lines
    return all_file_lines


def add_yaml_tag(tag: str, all_file_lines: List[str], filename: str) -> List[str]:
    """Adds a tag to a file's yaml section.
    tag: The tag to add to the yaml tag section.
    all_file_lines: All the lines of the file.

    returns all file lines with the tag added.
    """
    yaml_line = "---\n"

    in_yaml_section = False
    for index, line in enumerate(all_file_lines):
        if not in_yaml_section:
            if line != yaml_line:
                continue
            else:
                in_yaml_section = True
        yaml_property = line.split(":")
        if yaml_property[0] != "tags":
            continue
        yaml_tags = yaml_property[1]
        yaml_tags = yaml_tags.replace("[", "")
        yaml_tags = yaml_tags.replace("]", "")
        yaml_tags = yaml_tags.replace("\n", "")
        yaml_tags = yaml_tags.split(",")
        yaml_tags = [x.strip() for x in yaml_tags]

        if tag in yaml_tags:
            raise ValueError(f"Tag '{tag}' already found in {filename}.")
        yaml_tags.append(tag)
        yaml_tags = ", ".join(yaml_tags)
        yaml_tags = f"[{yaml_tags}]"
        yaml_tag_property = f"tags: {yaml_tags}\n"
        all_file_lines[index] = yaml_tag_property
        return all_file_lines
    return all_file_lines


def return_yaml_property(
    yaml_property: str, all_file_lines: List[str]
) -> tuple[str | None, int | None, bool]:
    """
    Returns:
    (found_property, line_number, yaml_section_exists)

    Returns the yaml property and line number if the file has the appropriate frontmatter. False otherwise.
    property: The property to search for in the yaml section of the file.
    all_file_lines: All the lines of the file.
    """
    yaml_line = "---\n"
    property_line = "tags:\n"

    yaml_section_exists = False
    in_yaml_section = False
    found_property_list: list[str] = []
    line_number_list: list[int] = []
    for index, line in enumerate(all_file_lines):
        if line == yaml_line:
            in_yaml_section = True
            yaml_section_exists = True
        if in_yaml_section:
            current_line_property = line.split(":")[0]
            if current_line_property == yaml_property:
                split_line = line.split(":")
                found_property_list.append("".join(split_line[1:]))
                line_number_list.append(index)

    if len(found_property_list) > 1:
        print("Warning: Multiple properties found. Using first property found.")
    found_property = found_property_list[0] if found_property_list else None
    line_number = line_number_list[0] if line_number_list else None
    return found_property, line_number, yaml_section_exists


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
            file_name = help_funcs.terminal_link(
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
                    print_string = "│   " + file_name
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
    root_directory: Path,
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
            return FileTreeNode(current_file)

    if all_files_in_base_directory is None:
        # search for all files in the base directory and subdirectories
        all_files_in_base_directory = (
            help_funcs.return_all_paths_in_directory_as_dictionary(root_directory)
        )

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


if __name__ == "__main__":
    start_file_path = Path(default_values.Default_File)
    vault_folder = Path(default_values.Default_Input_Directory)
    result = return_linked_files_V4(
        vault_folder,
        max_link_depth=3125,
        current_file=Path(start_file_path),
    )

    result.sort_tree_by_alphabetical_order_and_number_of_children_to_set_depth()
    result.print_improved_tree()
