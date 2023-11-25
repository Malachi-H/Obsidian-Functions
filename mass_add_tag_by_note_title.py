from pprint import pprint
import general_helper_functions as help_funcs
import obsidian_helper_functions as obs_funcs
import default_values


def mass_add_tag(input_directory, must_contain):
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
            all_file_lines = _return_updated_file_metadata(
                file,
                path,
                all_file_lines,
                yaml_property,
                line_number,
                yaml_section_exists,
            )
            with open(path, "w", encoding="utf-8") as f:
                f.write("".join(all_file_lines))
                print(f"altered file: {file}")


def _extend_tag_list(yaml_property):
    if yaml_property == None:
        yaml_property = ["Copilot"]
    else:
        yaml_property = yaml_property.replace("[", "")
        yaml_property = yaml_property.replace("]", "")
        yaml_property = yaml_property.replace("\n", "")
        yaml_property = yaml_property.split(",")
        yaml_property = [x.strip() for x in yaml_property]

        if "Copilot" not in yaml_property:
            yaml_property.append(", Copilot")

    # convert back to string
    yaml_property_text = f"[{''.join(yaml_property)}]"

    return yaml_property_text


def _return_updated_file_metadata(
    file, path, all_file_lines, yaml_property, line_number, yaml_section_exists
) -> list[str]:
    yaml_property = _extend_tag_list(yaml_property)
    if not yaml_section_exists:
        # create front matter section
        if len(all_file_lines):
            print(f"WARNING: completely empty file found: {file} at {path}")
        all_file_lines.append("---\n")
        all_file_lines.insert(1, f"tags: {yaml_property}\n")
        all_file_lines.append("---\n")
    else:
        if not line_number:
            all_file_lines.insert(1, f"tags: {yaml_property}\n")
        else:
            all_file_lines[line_number] = f"tags: {yaml_property}\n"
    return all_file_lines


if __name__ == "__main__":
    input_directory = help_funcs.get_input_directory(
        DEFAULT_DIRECTORY=default_values.Default_Input_Directory
    )
    mass_add_tag(input_directory, must_contain="Chat-")
