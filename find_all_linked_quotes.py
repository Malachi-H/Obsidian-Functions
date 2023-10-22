"""
Finds and returns all quotes that are linked to a particular file with an adjustable level of recursion depth.
Also optionally checks if any quotes are found that do not have a an appropriate yaml tag eg. english-flashcards.
"""
"""

CURRENTLY NOT WORKING IN THE SLIGHTEST
    
"""

import glob
import os
from pprint import pprint
import obsidian_helper_functions as obs
import general_helper_functions as help_funcs

if __name__ == "__main__":
    # default_input_directory = r"d:\Obsidian"
    # all_full_file_paths = help_funcs.return_all_full_file_paths(default_input_directory)
    # default_start_file = all_full_file_paths[0]

    # start_file_path = help_funcs.get_start_file(default_start_file)
    # start_file_directory = os.path.dirname(start_file_path)

    start_file_path = r"D:\Obsidian\File Level 0.md"
    start_file_directory = r"D:\Obsidian"

    pprint(
        obs.return_linked_files_with_recursion_depth__V2(
            start_file_path, start_file_directory, recursion_depth_max=10
        )
    )

    TAG_NAMES = {"software": "softwaredd\n", "flashcards": "flashcards\n"}

    filenames = glob.glob(
        os.path.join(start_file_directory, "**/*.md"), recursive=True
    )  # get all .md files in the input directory

    for file in filenames:
        path = os.path.join(start_file_directory, file)
        basename = os.path.basename(
            file
        )  # used as file output name because directory structure is removed
        with open(file, "r", encoding="utf8") as f:
            all_file_lines = f.readlines()

            if obs.has_yaml_tag(
                TAG_NAMES["software"], all_file_lines
            ) and obs.has_yaml_tag(TAG_NAMES["flashcards"], all_file_lines):
                # print("Has both tags")

                linked_attachments = obs.return_linked_attachments(all_file_lines)

                obs.copy_attachments_to_new_directory(
                    linked_attachments,
                    start_file_directory,
                    os.path.join(output_directory, "attachments\\"),
                )

                changed_file = obs.remove_flashcard_metadata(all_file_lines)
                with open(
                    os.path.join(output_directory, basename), "w", encoding="utf8"
                ) as file:
                    file.writelines(changed_file)
    input("Press anything to close...")
