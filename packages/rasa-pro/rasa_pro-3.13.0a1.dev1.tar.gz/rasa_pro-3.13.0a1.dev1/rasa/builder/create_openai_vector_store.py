import json
from dataclasses import dataclass
from pathlib import Path

import openai

DOCS_DIR = "rasa_docs_md"  # Folder with scraped Markdown files
assistant_name = "Rasa Docs Assistant"


@dataclass
class FileWithAttributes:
    file_id: str
    file_name: str
    attributes: dict


def get_files_with_metadata(files) -> list[FileWithAttributes]:
    with open("markdown_to_url.json", "r") as f:
        markdown_to_url = json.load(f)

    files_with_metadata = []
    for file in files:
        files_with_metadata.append(
            FileWithAttributes(
                file_id=file["file_id"],
                file_name=file["file_name"],
                attributes={"url": markdown_to_url[file["file_name"]]},
            )
        )

    return files_with_metadata


# Step 1: Upload files
print("📤 Uploading files to OpenAI...")

files = []

# try to read the file ids from the json file
if Path("file_ids.json").exists():
    with open("file_ids.json", "r") as f:
        files = json.load(f)
else:
    for md_file in Path(DOCS_DIR).glob("*.md"):
        with open(md_file, "rb") as f:
            uploaded = openai.files.create(file=f, purpose="assistants")
            files.append({"file_id": uploaded.id, "file_name": md_file.name})
            print(f"✅ Uploaded {md_file.name} → {uploaded.id}")

    # persist the file ids in a json file
    with open("file_ids.json", "w") as f:
        json.dump(files, f, indent=2)

# Step 2: Create Vector Store
print("\n🤖 Creating vector store...")

vector_store = openai.vector_stores.create(name="Rasa Docs")

for file in get_files_with_metadata(files):
    openai.vector_stores.files.create(
        vector_store_id=vector_store.id,
        file_id=file.file_id,
        attributes=file.attributes,
    )
    print(f"✅ Added {file.file_name} to vector store.")

print("\n🎉 Vector store created successfully!")
print(f"Vector store ID: {vector_store.id}")
