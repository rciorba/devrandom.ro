import os
import os.path

from collections import defaultdict

from jinja2 import Environment, FileSystemLoader, ChoiceLoader, select_autoescape
from markdown2 import markdown_path


def process_folder(path, tags, template_env):
    items = [i for i in os.scandir(path)]
    names = set(i.name for i in items)
    processed = {}
    for item in items:
        name = item.name
        if item.is_file():
            html_fname = None
            if not (name.startswith(".")):
                if name.endswith(".md"):
                    content, meta = process_markdown(item, tags, template_env)
                    html_fname = item.path[:-3] + ".html"
                elif name.endswith(".jinja"):
                    content, meta = process_jinja(item, template_env)
                    html_fname = item.path[:-6] + ".html"
                if html_fname:
                    meta['path'] = html_fname
                    processed[item.name] = (item, meta)
                    print("<", item.path)
                    print(">", html_fname)
                    with open(html_fname, "w") as fd:
                        fd.write(content)
        elif item.is_dir():
            if not name.startswith(".") and ".norecurse" not in names:
                process_folder(item.path, tags, template_env)
    if "index.jinja" not in names:
        process_listing(path, processed, template_env)


def process_listing(path, processed, template_env):
    print(processed)
    pages = []
    page = []
    for key in sorted(processed.keys(), reverse=True):
        if key.lower().startswith("wip"):
            continue  # don't list WIP articles
        page.append(processed[key])
        if len(page) == 10:
            pages.append(page)
            page = []
    pages.append(page)
    for (page_number, page) in enumerate(pages):
        process_page(
            path,
            page,
            page_number+1,
            template_env=template_env,
            meta={"page_number": len(pages)},
        )


def process_page(path, page, page_number, template_env, meta):
    prefix = path
    if page_number != 1:
        prefix = os.path.join(prefix, str(page_number))
    html_fname = os.path.join(prefix, "index.html")
    template = template_env.get_template("page.html")
    content = template.render(page=page, **meta)
    with open(html_fname, "w") as fd:
        fd.write(content)


def process_markdown(item, tags, template_env):
    post = markdown_path(item.path, extras=["fenced-code-blocks", "metadata", "toc"])
    meta = post.metadata.copy()
    print("md", meta)
    post_tags = [t.strip() for t in meta.pop("tags", "").split(",")]
    template = template_env.get_template("post.html")
    # print(post)
    content = template.render(post=str(post), tags=post_tags, toc=post.toc_html, **meta)
    return content, meta


def process_jinja(item, template_env):
    template = template_env.get_template(item.path)
    # print(post)
    return template.render(), {}


def generate():
    tags = defaultdict(int)
    loader = ChoiceLoader(
        [FileSystemLoader("generator/templates"), FileSystemLoader(".")]
    )
    env = Environment(loader=loader, autoescape=select_autoescape(["html", "xml"]))
    return process_folder(".", tags=tags, template_env=env)


if __name__ == "__main__":
    import sys

    generate()
