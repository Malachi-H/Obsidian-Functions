import glob
import os
import obsidian_helper_functions as obs
import general_helper_functions as help_funcs

if __name__ == "__main__":
    DEFAULT_INPUT_DIRECTORY = r"d:\Obsidian"  # default
    INPUT_DIRECTORY = help_funcs.get_input_directory(
        DEFAULT_DIRECTORY=DEFAULT_INPUT_DIRECTORY
    )

    DEFAULT_OUTPUT_DIRECTORY = f"{INPUT_DIRECTORY}_comments_removed"  # default
    OUTPUT_DIRECTORY = help_funcs.get_output_directory(
        default_directory=DEFAULT_OUTPUT_DIRECTORY
    )

    print("Running...")

    TAG_NAMES = {"software": "softwaredd\n", "flashcards": "flashcards\n"}

    all_full_file_paths = help_funcs.return_all_full_file_paths(INPUT_DIRECTORY)

    for file_path in all_full_file_paths:
        basename = os.path.basename(
            file_path
        )  # used as file output name because directory structure is removed
        with open(file_path, "r", encoding="utf8") as f:
            all_file_lines = f.readlines()

            if obs.has_yaml_tag(
                TAG_NAMES["software"], all_file_lines
            ) and obs.has_yaml_tag(TAG_NAMES["flashcards"], all_file_lines):
                # print("Has both tags")

                linked_files = obs.return_linked_base_names(all_file_lines)

                obs.copy_attachments_to_new_directory(
                    linked_files,
                    INPUT_DIRECTORY,
                    os.path.join(OUTPUT_DIRECTORY, "attachments\\"),
                )

                changed_file = obs.remove_flashcard_metadata(all_file_lines)
                with open(
                    os.path.join(OUTPUT_DIRECTORY, basename), "w", encoding="utf8"
                ) as file_path:
                    file_path.writelines(changed_file)
    input("Press anything to close...")
