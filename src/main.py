import os
import shutil

from textnode import *


def recursive_copy(source, dest):
    if os.path.exists(dest):
        shutil.rmtree(dest)
    os.mkdir(dest)
    files = os.listdir(source)
    for file in files:
        file_path = os.path.join(source, file)
        if os.path.isfile(file_path):
            shutil.copy(file_path, dest)
        else:
            dir_path = os.path.join(dest, file)
            os.mkdir(dir_path)
            recursive_copy(file_path, dir_path)


def generate_page(from_path, template_path, dest_path):
    print(
        f"Generating page from {from_path} to {dest_path} using {template_path}")

    with open(from_path, 'r', encoding='utf-8') as markdown_file:
        markdown_content = markdown_file.read()

    with open(template_path, 'r', encoding='utf-8') as template_file:
        template_content = template_file.read()

    html_node = markdown_to_html_node(markdown_content)
    html_content = html_node.to_html()

    title = extract_title(markdown_content)

    final_content = template_content.replace("{{ Title }}", title)
    final_content = final_content.replace("{{ Content }}", html_content)

    os.makedirs(os.path.dirname(dest_path), exist_ok=True)

    with open(dest_path, 'w', encoding='utf-8') as dest_file:
        dest_file.write(final_content)

    print(f"Page generated successfully at {dest_path}")


if __name__ == "__main__":
    source = "./static"
    dest = "./public"
    recursive_copy(source, dest)
    from_path = "content/index.md"
    template_path = "template.html"
    dest_path = "public/index.html"
    generate_page(from_path, template_path, dest_path)
