import os
import re
import shutil

# Paths for source (Obsidian Vault) and destination (Hugo Project)
POSTS_DIR = "/home/rently/self/inbaKrish_Blog/content/posts/"
ATTACHMENTS_DIR = "/home/rently/obsidian_vaults/Learnings_zettlekasten"
STATIC_FILES_DIR = "/home/rently/self/inbaKrish_Blog/static/images/"

# Regex to match any attachment (image, pdf, etc.)
ATTACHMENT_REGEX = r'\[\[([^]]+\.\S+)\]\]'

# Process each markdown file in the posts directory
for filename in os.listdir(POSTS_DIR):
    if filename.endswith(".md"):
        filepath = os.path.join(POSTS_DIR, filename)
        print(f"Processing file: {filepath}")
        
        # Read the content of the markdown file
        with open(filepath, "r") as file:
            content = file.read()
        
        # Find all attachment links (images, PDFs, etc.)
        attachments = re.findall(ATTACHMENT_REGEX, content)

        for attachment in attachments:
            print(f"  Found attachment: {attachment}")

            # Format the attachment link for markdown
            formatted_link = f"[Image Description](/images/{attachment.replace(' ', '%20')})"
            content = content.replace(f"[[{attachment}]]", formatted_link)

            # Copy the attachment to the Hugo static files directory
            attachment_source = os.path.join(ATTACHMENTS_DIR, attachment)
            if os.path.exists(attachment_source):
                target_path = os.path.join(STATIC_FILES_DIR, attachment)
                target_dir = os.path.dirname(target_path)
                
                # Create the target directory if it doesn't exist
                if not os.path.exists(target_dir):
                    os.makedirs(target_dir)
                    print(f"  Created directory: {target_dir}")

                # Copy the attachment to the static folder
                shutil.copy(attachment_source, target_path)
                print(f"  Copied {attachment} to {target_path}")
            else:
                print(f"  Warning: Attachment not found: {attachment_source}")

        # Write the updated content back to the markdown file
        with open(filepath, "w") as file:
            file.write(content)

print("Markdown files processed and attachments copied successfully.")
