from pathlib import Path
from pprint import pprint
import general_helper_functions as help_funcs
import obsidian_helper_functions as obs_funcs
import default_values


def map_Copilot_tag_to_ai_note(input_directory: str, tag_for_search: str):
    all_files = help_funcs.return_all_paths_in_directory_as_dictionary(
        Path(input_directory), file_type=".md"
    )
    filtered_files: dict[str, Path] = {}
    for name, path in all_files.items():
        with open(path, "r", encoding="utf-8") as f:
            all_file_lines = f.readlines()
        if obs_funcs.has_yaml_tag(tag_for_search, all_file_lines):
            filtered_files[name] = path.relative_to(input_directory)

    file_map = [
        "---",
        "tags: [Copilot]",
        "---",
        "",
        "All Past Chat GPT Queries",
        "___",
        "",
    ]
    for name, path in filtered_files.items():
        path = str(path).replace("\\", "/")
        file_map.append(f"[[{path}|{name}]]")

    with open(f"{input_directory}\\Chat GPT Queries.md", "w", encoding="utf-8") as f:
        f.write("\n".join(file_map))


if __name__ == "__main__":
    input_directory = help_funcs.get_input_directory(
        DEFAULT_DIRECTORY=default_values.Default_Input_Directory
    )
    map_Copilot_tag_to_ai_note(input_directory, tag_for_search="Copilot")
