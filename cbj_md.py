import os
import json
from markdownify import markdownify as md
import re

# --- Configuration ---
INPUT_DIR = "cbj_input"
OUTPUT_DIR = "cbj_output"
PREVIEW_DIR = "md_previews" # Directory for easy-to-preview .md files

# List of top-level keys in the JSON that contain HTML content to be converted.
SECTIONS_WITH_HTML = ["about", "certificates", "procedures", "actionCards", "drugs"]


def html_to_markdown(html_content: str) -> str:
    """
    Converts a string of HTML into a string of Markdown.
    If the input is empty or None, it returns an empty string.
    """
    if not html_content:
        return ""
    return md(html_content, heading_style="ATX").strip()

def sanitize_filename(name: str) -> str:
    """Removes characters that are invalid for filenames to prevent errors."""
    # Replace any characters that are not letters, numbers, hyphens, or underscores
    name = re.sub(r'[^a-zA-Z0-9_-]', '_', name)
    return name.strip('_')

def save_markdown_preview(base_filename: str, section: str, identifier: str, content: str):
    """
    Saves a piece of Markdown content to a dedicated .md file for easy previewing.

    Args:
        base_filename: The name of the original JSON file (e.g., "bundle1").
        section: The top-level section the content came from (e.g., "about").
        identifier: A unique name for the content block (e.g., "introduction").
        content: The Markdown content to save.
    """
    # Create a sub-directory for each JSON file's previews
    preview_path = os.path.join(PREVIEW_DIR, base_filename)
    os.makedirs(preview_path, exist_ok=True)
    
    sanitized_id = sanitize_filename(identifier)
    md_filename = f"{section}_{sanitized_id}.md"
    
    try:
        with open(os.path.join(preview_path, md_filename), "w", encoding="utf-8") as f:
            f.write(content)
        print(f"       -> Saved preview: {os.path.join(preview_path, md_filename)}")
    except Exception as e:
        print(f"       -> [❌] Failed to save preview {md_filename}: {e}")

def process_html_in_sections(data: dict, base_filename: str) -> dict:
    """
    Traverses the JSON data, converts HTML to Markdown, and saves .md preview files.

    Args:
        data: The loaded JSON data as a Python dictionary.
        base_filename: The original name of the json file, used for preview paths.

    Returns:
        The modified dictionary with HTML converted to Markdown.
    """
    print("  -> Searching for HTML in sections:", SECTIONS_WITH_HTML)
    for section_name in SECTIONS_WITH_HTML:
        if section_name in data and isinstance(data[section_name], list):
            for item_index, item in enumerate(data[section_name]):
                if not isinstance(item, dict):
                    continue

                # Scenario 1: Direct 'content' key in the item
                if "content" in item and isinstance(item["content"], str) and item["content"]:
                    markdown_content = html_to_markdown(item["content"])
                    item["content"] = markdown_content
                    
                    identifier = item.get('id', f"item_{item_index}")
                    print(f"     - Converting content in '{section_name}' -> id '{identifier}'")
                    save_markdown_preview(base_filename, section_name, identifier, markdown_content)

                # Scenario 2: Nested 'chapters' with 'content'
                if "chapters" in item and isinstance(item["chapters"], list):
                    for chapter_index, chapter in enumerate(item["chapters"]):
                        if isinstance(chapter, dict) and "content" in chapter and isinstance(chapter["content"], str) and chapter["content"]:
                            markdown_content = html_to_markdown(chapter["content"])
                            chapter["content"] = markdown_content

                            item_id = item.get('id', f'item_{item_index}')
                            chapter_desc = chapter.get('description', f"chapter_{chapter_index}")
                            identifier = f"{item_id}_{chapter_desc}"
                            print(f"     - Converting content in '{section_name}' -> '{identifier}'")
                            save_markdown_preview(base_filename, section_name, identifier, markdown_content)
    return data

def process_single_cbj_file(input_path: str, output_dir: str):
    """
    Reads a single CBJ file, processes it, saves the updated JSON,
    and triggers the creation of .md preview files.
    """
    try:
        with open(input_path, "r", encoding="utf-8") as f:
            json_data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"[❌] Error reading or parsing {input_path}: {e}")
        return

    base_name = os.path.splitext(os.path.basename(input_path))[0]
    updated_data = process_html_in_sections(json_data, base_name)

    os.makedirs(output_dir, exist_ok=True)
    output_filename = f"{base_name}_md.json"
    output_path = os.path.join(output_dir, output_filename)

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(updated_data, f, ensure_ascii=False, indent=4)
        print(f"[✔] Successfully processed and saved to '{output_path}'\n")
    except Exception as e:
        print(f"[❌] Error writing to {output_path}: {e}\n")

def main():
    """Main function to run the bulk conversion process."""
    if not os.path.exists(INPUT_DIR):
        print(f"Error: Input directory '{INPUT_DIR}' not found.")
        return

    # Create output directories if they don't exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(PREVIEW_DIR, exist_ok=True)

    print(f"--- Starting Bulk Conversion from '{INPUT_DIR}' ---")
    print(f"Processed JSON will be saved to: '{OUTPUT_DIR}'")
    print(f"Markdown previews will be saved to: '{PREVIEW_DIR}'")
    print("-" * 50)

    for filename in os.listdir(INPUT_DIR):
        if filename.endswith(".json"):
            input_file_path = os.path.join(INPUT_DIR, filename)
            print(f"Processing file: '{filename}'")
            process_single_cbj_file(input_file_path, OUTPUT_DIR)

    print("--- Bulk processing complete. ---")

if __name__ == "__main__":
    main()
