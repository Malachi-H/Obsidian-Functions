from pathlib import Path
from pprint import pprint
import general_helper_functions as help_funcs
import obsidian_helper_functions as obs_funcs
import default_values


def handle_flashcard_tag_but_no_flashcard_section(
    all_file_lines: list[str], path: Path, name: str, tag: str
):
    multiline_question_lines = (
        obs_funcs.check_for_multiline_flashcard_style_section_in_note(
            all_file_lines, file_name=name
        )
    )
    singleline_question_lines = (
        obs_funcs.check_for_singleline_flashcard_style_section_in_note(all_file_lines)
    )
    if len(multiline_question_lines) == 0 and len(singleline_question_lines) == 0:
        print(
            f"'{help_funcs.terminal_link(path,name)}' has flashcard tag ({tag}) but no flashcard section"
        )
        choice = ""
        while choice not in ["y", "n"]:
            choice = input("remove flashcard tag? (y/n): ")
            print()
        if choice == "y":
            all_file_lines = obs_funcs.remove_yaml_tag(
                tag, all_file_lines, filename=name
            )
            with open(path, "w", encoding="utf-8") as f:
                f.write("".join(all_file_lines))
                print(f"removed flashcard tag ({tag}) from {name}")
        print("continuing program..\n\n")


def handle_no_flashcard_tag_but_has_flashcard_section(
    all_file_lines: list[str], path: Path, name: str, yaml_tags_list: list[str]
):
    multiline_question_lines = (
        obs_funcs.check_for_multiline_flashcard_style_section_in_note(
            all_file_lines, file_name=name
        )
    )
    singleline_question_lines = (
        obs_funcs.check_for_singleline_flashcard_style_section_in_note(all_file_lines)
    )
    flashcard_tag_found = False
    for tag in yaml_tags_list:
        if obs_funcs.has_yaml_tag(tag, all_file_lines):
            flashcard_tag_found = True

    if len(multiline_question_lines) > 0 or len(singleline_question_lines) > 0:
        if flashcard_tag_found == False:
            print(
                f"'{help_funcs.terminal_link(path,name)}' has flashcard section but no flashcard tag."
            )

            if len(multiline_question_lines) > 0:
                print(f"Note contains {len(multiline_question_lines)}")
                print("multiline flashcard questions at lines:")
                for line in multiline_question_lines:
                    print(line)
            if len(singleline_question_lines) > 0:
                print(
                    f"{len(singleline_question_lines)} singleline flashcard questions at lines:"
                )
                for line in singleline_question_lines:
                    print(line)
            choice = ""
            while choice not in ["y", "n"]:
                choice = input("add flashcard tag? (y/n): ")
                print()
            if choice == "y":
                pass
                # all_file_lines = obs_funcs.add_yaml_tag(
                #     tag, all_file_lines, filename=name
                # )
                # with open(path, "w", encoding="utf-8") as f:
                #     f.write("".join(all_file_lines))
                #     print(f"added flashcard tag to {name}")
            print("continuing program..\n\n")


def check_for_flashcard_tag_discrepancy(input_directory: str):
    all_files = help_funcs.return_all_paths_in_directory_as_dictionary(
        input_directory, file_type=".md"
    )

    yaml_allowed_flashcard_map_notes = [
        "School Subject Flashcard Tags",
    ]

    (
        yaml_allowed_flashcard_map_notes,
        unfindable_files,
    ) = help_funcs.convert_file_base_names_to_full_path_V2(
        yaml_allowed_flashcard_map_notes, all_files, input_directory
    )

    yaml_tags_list = []
    for note in yaml_allowed_flashcard_map_notes:
        with open(note, "r", encoding="utf-8") as f:
            all_file_lines = f.readlines()
        (
            yaml_tags,
            line_number_of_tags,
            yaml_section_exists,
        ) = obs_funcs.return_yaml_property("allowedTags", all_file_lines)
        if yaml_tags == None:
            raise ValueError(f"allowedTags property not found in {note}")
        yaml_tags = obs_funcs.yaml_tags_to_list(yaml_tags)
        yaml_tags_list.extend(yaml_tags)

    for name, path in all_files.items():
        with open(path, "r", encoding="utf-8") as f:
            all_file_lines = f.readlines()
        for tag in yaml_tags_list:
            if obs_funcs.has_yaml_tag(tag, all_file_lines):
                handle_flashcard_tag_but_no_flashcard_section(
                    all_file_lines, path, name, tag
                )

        handle_no_flashcard_tag_but_has_flashcard_section(
            all_file_lines, path, name, yaml_tags_list
        )


if __name__ == "__main__":
    input_directory = help_funcs.get_input_directory(
        DEFAULT_DIRECTORY=default_values.Default_Input_Directory
    )
    print()
    check_for_flashcard_tag_discrepancy(input_directory)
    print("Program Finished!")
