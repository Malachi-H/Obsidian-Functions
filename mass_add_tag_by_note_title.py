from pprint import pprint
import general_helper_functions as help_funcs
import obsidian_helper_functions as obs_funcs
import default_values


def mass_add_tag(input_directory, must_contain, tag_to_add: str):
    # Copilot Conversation

    all_files = help_funcs.return_all_paths_in_directory_as_dictionary(
        input_directory, file_type=".md"
    )
    for file, path in all_files.items():
        if must_contain in file:
            with open(path, "r", encoding="utf-8") as f:
                all_file_lines = f.readlines()
            (
                yaml_property,
                line_number,
                yaml_section_exists,
            ) = obs_funcs.return_yaml_property(
                yaml_property="tags", all_file_lines=all_file_lines
            )

            # replace the property with the updated one
            all_file_lines, altered = _return_updated_file_metadata(
                file,
                path,
                all_file_lines,
                yaml_property,
                line_number,
                yaml_section_exists,
                tag_to_add,
            )
            if altered:
                with open(path, "w", encoding="utf-8") as f:
                    f.write("".join(all_file_lines))
                    print(f"altered file: {file}")


def _extend_tag_list(yaml_property_in_file, tag_to_add: str):
    file_altered = False
    if yaml_property_in_file == None:
        yaml_property_in_file = tag_to_add
    else:
        yaml_property_in_file = obs_funcs.yaml_list_type_property_to_list(
            yaml_property_in_file
        )
        if tag_to_add not in yaml_property_in_file:
            yaml_property_in_file.append(f", {tag_to_add}")
            file_altered = True

    # convert back to string
    yaml_property_text = f"[{''.join(yaml_property_in_file)}]"

    return yaml_property_text, file_altered


def _return_updated_file_metadata(
    file,
    path,
    all_file_lines: list[str],
    yaml_property_in_file: str,
    line_number: int,
    yaml_section_exists,
    tag_to_add: str,
) -> tuple[list[str], bool]:
    yaml_property_in_file, altered = _extend_tag_list(yaml_property_in_file, tag_to_add)
    if not yaml_section_exists:
        # create front matter section
        if len(all_file_lines) == 0:
            print(f"WARNING: completely empty file found: {file} at {path}")
        all_file_lines.insert(0, "---\n")
        all_file_lines.insert(1, f"tags: {yaml_property_in_file}\n")
        all_file_lines.insert(2, "---\n")
        all_file_lines.insert(3, "\n")
        altered = True
    else:
        if not line_number:
            all_file_lines.insert(1, f"tags: {yaml_property_in_file}\n")
        else:
            all_file_lines[line_number] = f"tags: {yaml_property_in_file}\n"
    return all_file_lines, altered


if __name__ == "__main__":
    input_directory = help_funcs.get_input_directory(
        DEFAULT_DIRECTORY=default_values.Default_Input_Directory
    )
    mass_add_tag(input_directory, must_contain="Chat-", tag_to_add="Copilot")
