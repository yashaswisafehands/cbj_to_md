import os
import json
from markdownify import markdownify as md
import re

INPUT_DIR = "cbj_input"
OUTPUT_DIR = "cbj_output"
MODULE_PREVIEWS_DIR = "module_previews" 

INDEX_SECTIONS = ["procedures", "actionCards", "drugs", "keyLearningPoints", "certificates"]

def html_to_markdown(html_content: str) -> str:
    if not html_content:
        return ""
    return md(html_content, heading_style="ATX").strip()

def sanitize_filename(name: str) -> str:
    name = re.sub(r'[^a-zA-Z0-9_-]', '_', name)
    return name.strip('_')

def build_content_index(json_data: dict) -> dict:
    print("  -> Building content index for fast lookups...")
    content_index = {}
    for section in INDEX_SECTIONS:
        if section in json_data and isinstance(json_data[section], list):
            for item in json_data[section]:
                if isinstance(item, dict) and 'id' in item:
                    content_index[item['id']] = item
    print(f"  -> Index built with {len(content_index)} items.")
    return content_index

def format_content_as_markdown(item: dict) -> str:
    markdown_parts = []
    if 'chapters' in item and isinstance(item['chapters'], list):
        for chapter in item['chapters']:
            if 'content' in chapter and chapter['content']:
                markdown_parts.append(html_to_markdown(chapter['content']))
    elif 'content' in item and item['content']:
        markdown_parts.append(html_to_markdown(item['content']))
    if 'questions' in item and isinstance(item['questions'], list):
        for q_index, question in enumerate(item['questions']):
            q_text = question.get('question', f"Question {q_index+1}")
            markdown_parts.append(f"#### {q_text}")
            for a_index, answer in enumerate(question.get('answers', [])):
                marker = "[x]" if answer.get('correct') else "[ ]"
                markdown_parts.append(f"- {marker} {answer.get('value')}")
            markdown_parts.append("\n")
    return "\n\n".join(markdown_parts)

def process_modules(json_data: dict, content_index: dict):
    if 'modules' not in json_data:
        print("  -> [!] No 'modules' section found. Cannot process.")
        return
    print("  -> Processing modules...")
    os.makedirs(MODULE_PREVIEWS_DIR, exist_ok=True)
    for module in json_data['modules']:
        module_name = module.get('description', module['id'])
        print(f"\n    - Assembling module: '{module_name}'")
        module_markdown_content = [f"# Module: {module_name}\n"]
        sections_in_module = {
            "Action Cards": "actionCards",
            "Procedures": "procedures",
            "Key Learning Points": "keyLearningPoints",
            "Drugs": "drugs",
        }
        for title, key in sections_in_module.items():
            if key in module and module[key]:
                module_markdown_content.append(f"## {title}\n")
                for item_id in module[key]:
                    if item_id in content_index:
                        item_data = content_index[item_id]
                        item_title = item_data.get('description', item_id)
                        module_markdown_content.append(f"### {item_title}\n")
                        module_markdown_content.append(format_content_as_markdown(item_data))
                        module_markdown_content.append("\n---\n")
                    else:
                        print(f"      -> [!] Warning: ID '{item_id}' not found in index.")
        output_filename = sanitize_filename(module_name) + ".md"
        output_path = os.path.join(MODULE_PREVIEWS_DIR, output_filename)
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("\n".join(module_markdown_content))
            print(f"    -> [✔] Successfully created module file: {output_path}")
        except Exception as e:
            print(f"    -> [❌] Failed to save module file {output_path}: {e}")

def main():
    if not os.path.exists(INPUT_DIR):
        print(f"Error: Input directory '{INPUT_DIR}' not found.")
        return
    print(f"--- Starting Module-Based Content Migration ---")
    print(f"Source: '{INPUT_DIR}'")
    print(f"Output (Markdown Modules): '{MODULE_PREVIEWS_DIR}'")
    print("-" * 50)
    for filename in os.listdir(INPUT_DIR):
        if filename.endswith(".json"):
            input_file_path = os.path.join(INPUT_DIR, filename)
            print(f"Processing bundle: '{filename}'")
            try:
                with open(input_file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception as e:
                print(f"  -> [❌] Failed to read or parse {filename}: {e}")
                continue
            index = build_content_index(data)
            process_modules(data, index)
    print("\n--- Migration complete. ---")

if __name__ == "__main__":
    main()