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

With Obsidian, all aspects of the blogging process come together seamlessly. You can ideate, organize notes, draft posts, and even template your blog—all within a single, powerful tool and with its support for **Markdown**, writing and formatting your posts becomes a breeze.

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

But how to make the Obsidian's markdown written content to html? [Hugo](https://gohugo.io/), makes it hassle-free and with Hugo’s user-friendly setup and an extensive community of [themes](https://themes.gohugo.io/), you can create a professional-looking site with minimal effort.

* Install Hugo - https://gohugo.io/installation, with all the mentioned prerequisites.
* Create a Hugo project (I'm using yaml for my configurations) and configure the Hugo theme of you choice.
```sh
hugo new site MyPersonalBlogSite -f yaml
```

### Hugo Theme
For my blog, I'm using [Papermod](https://themes.gohugo.io/themes/hugo-papermod/) theme. You can choose any, and go over the installation steps and ready to go. For Papermod refer - [Papermod installation wiki](https://github.com/adityatelange/hugo-PaperMod/wiki/Installation).

----

### Sync Obsidian content to Hugo

For mac/linux use [rsync](https://www.geeksforgeeks.org/rsync-command-in-linux-with-examples/) to sync the content from Obsidian folder to Hugo content. For windows there are similar tools like [robocopy](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/robocopy).
```sh
rsync -av --delete "sourcepath" "destinationpath"
```

Under obsidian, create a new folder to manage your blog content `<obsidian vault>/BlogPosts` and for the hugo project the content should be copied to `<hugo project root>/content/posts`.

**But there's a issue**, with the above command the text content of the files get synced, but Obsidian handles the attachment in a different way like in the root folder (default) or as per the folder configuration configured by the individuals.

To handle that, use the below python script (written for linux, modify accordingly for windows/other OS, or ask straight to a LLM chatbot) which looks for the image files within the markdown content and finds the respective file within the obsidian source attachment folder and modifies the content within the hugo's content folder.
```python
import os
import re
import shutil

# Paths for source (Obsidian Vault) and destination (Hugo Project)
POSTS_DIR = "<Hugo project root path>/content/posts/"
ATTACHMENTS_DIR = "<Obsidian vault attachements path>/"
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
        
        # Find all attachment links (images)
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

### Automate deployment using - Github Action (optional)

Now instead of manually building the static files and pushing it to the gh page repository, trigger a github action for the main repository, which generates the static files and pushes it to the github page repo.

1. Create personal access token, as we need to access another repo create access token with repo and workflow scopes.![Image Description](/images/Pasted%20image%2020241208112436.png)
2. Create `production` environment and add the PAT_TOKEN secret ![Image Description](/images/Pasted%20image%2020241208112652.png)
3. Provide read & write access for the github actions settings in the deploy repo. ![Image Description](/images/Pasted%20image%2020241208113243.png)

After the PAT_TOKEN and action permissions setup, use the following Github-action deployment workflow.
```yml
name: Deploy Hugo site to Pages

on:
  push:
    branches: ["master"]
  workflow_dispatch:

permissions:
  contents: write
  pages: write
  id-token: write

defaults:
  run:
    shell: bash

jobs:
  deploy:
    runs-on: ubuntu-latest 
    environment: production
    steps:
      - name: Checkout Source Repository
        uses: actions/checkout@v3
        with:
          submodules: recursive
          fetch-depth: 0

      - name: Setup Hugo
        uses: peaceiris/actions-hugo@v3
        with:
          hugo-version: 'latest'
          extended: true

      - name: Build Hugo Site
        run: hugo

      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3
        with:
          personal_token: ${{ secrets.PAT_TOKEN }}
          external_repository: InbaKrish/inbakrish.github.io
          publish_branch: main
          publish_dir: ./public
          user_name: 'github-actions[bot]'
          user_email: 'github-actions[bot]@users.noreply.github.com'
```

**Hola!**, Now we have improved the automated setup, now steps just involves the files and image sync from obsidian to Hugo project, commit all the push. From the hugo project the Github action deploys the static site to the github page configures repo using the PAT_TOKEN.


![Image Description](/images/Pasted%20image%2020241207210218.png)