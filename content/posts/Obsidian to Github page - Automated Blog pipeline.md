---
title: Obsidian to Github page - Blog pipeline
tags:
  - Github
  - Obsidian
date: 2024-12-07
draft: "false"
---
As developers, we thrive on automation. Yet, it's often said that one of the best ways to advance our careers is through blog contributions. Despite this, starting a blog can feel daunting—it's not just about writing. There's ideation, creating templates, validation, and the publishing process itself. And let’s face it, it all takes time. 

![Image Description](/images/Pasted%20image%2020241207210246.png)

I have used the following automation blog pipeline inspired from various developers and curated this workflow.

----
## Why Obsidian?

Every developer has their own preferred tool for taking notes. But if you haven’t tried **Obsidian**, you're missing out.

> **Obsidian** is, hands down, the best note-taking application for developers. If you haven't tried it yet, do yourself a favor—[download Obsidian now](https://obsidian.md/)!

With Obsidian, all aspects of the blogging process come together seamlessly. You can ideate, organize notes, draft posts, and even template your blog—all within a single, powerful tool. And with its support for **Markdown**, writing and formatting your posts becomes a breeze.

For blog contents add some front matter/properties like title, data, and tags (based on Hugo themes they support variety of options).
```md
---
title: blogtitle
date: 2024-11-06
draft: false
tags:
  - tag1
  - tag2
---
```

----
## Go - Hugo

But with Obsidian, how to make the markdown written content to html? [Hugo](https://gohugo.io/), makes it hassle-free and with Hugo’s user-friendly setup and an extensive community of [themes](https://themes.gohugo.io/), you can create a professional-looking site with minimal effort.

* Install Hugo - https://gohugo.io/installation, with all the mentioned prerequisites.
* Create a Hugo project (I'm using yaml for my configurations) and configure the Hugo theme of you choice.
```sh
hugo new site MyPersonalBlogSite -f yaml
```

### Hugo Theme
For my blog, I'm using [Papermod](https://themes.gohugo.io/themes/hugo-papermod/) theme. You can choose any, and go over the installation steps and ready to go. For Papermode refer - [Papermod installation wiki](https://github.com/adityatelange/hugo-PaperMod/wiki/Installation).

----

### Sync Obsidian content to Hugo

For mac/linux use [rsync](https://www.geeksforgeeks.org/rsync-command-in-linux-with-examples/) to sync the content from Obsidian folder to Hugo content.
```sh
rsync -av --delete "sourcepath" "destinationpath"
```

Under obsidian, create a new folder to manager your blog content `<obsidian vault>/BlogPosts` and for the hugo project the content should be copied to `<hugo project root>/content/posts`.

**But there's a issue**, with the above command the text content of the files get synced, but Obsidian handles the attachment in a different way like in the root folder (default) or as per the folder configuration configured by the individuals.

To handle that, use the below python script (written for linux, modify accordingly for windows/other OS, or ask straight to a chat LLMs) which looks for the image files with the markdown content and finds the respective file within the obsidian source attachment folder and modifies the content within the hugo's content folder.
```python
import os
import re
import shutil

# Paths for source (Obsidian Vault) and destination (Hugo Project)
POSTS_DIR = "<Hugo project root path>/content/posts/"
ATTACHMENTS_DIR = "<Obsidian vault root path>/learnings_v2/"
STATIC_FILES_DIR = "<Hugo project root path>/static/images/"

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
```

----

## Github Page - repo setup

Now we need to create a repository which will host the static files hosted in the Github pages.

1. Create a repository with the required URL, l used `inbakrish.github.io`. ![Image Description](/images/Pasted%20image%2020241207201814.png)
2. Now configure this repository as s submodule under the hugo blog project for the `/public` folder.
```sh
git submodule add git@github.com-personal:<user name>/<repo name>.git public
```
3. Now verify the remote for the submodule added above,
```sh
cd /public
git remote -v #-> origin git@github.com-personal:<user name>/<repo name>.git
```

---

## Generate static files

Now all the setup in place, modify the `baseURL` config,
```yaml
# config.yaml
baseURL: "https://inbakrish.github.io/"
```

Next, trigger the `hugo` command to generate the static HTML files content,
```sh
hugo

# Output sample
Start building sites … 
hugo v0.139.3-2f6864387cd31b975914e8373d4bf38bddbd47bc+extended linux/amd64 BuildDate=2024-11-29T15:36:56Z VendorInfo=snap:0.139.3


                   | EN  
-------------------+-----
  Pages            | 21  
  Paginator pages  |  0  
  Non-page files   |  0  
  Static files     |  2  
  Processed images |  0  
  Aliases          |  5  
  Cleaned          |  0  

Total in 84 ms
```

---

## Deployment

Stage all the changes under the `public` folder and push the changes to `git@github.com-personal:<user name>/<repo name>.git` repository.

Configure the Github repo pages settings,
![Image Description](/images/Pasted%20image%2020241207205612.png)
use **Deploy from a branch**, with the **main** branch. After the configuration setup, the static content (your awesome blog), will be hosted on the configured repo name (URL).

> NOTE - If you want custom domain configuration, refer to the [official docs](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site) and it can be configured such.


![Image Description](/images/Pasted%20image%2020241207210218.png)