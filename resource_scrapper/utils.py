def extract_sections(page):
    elements = page.query_selector_all("main h2, main h3, main h4, main p, main img, main iframe")
    sections = []
    current = None

    for el in elements:
        tag = el.evaluate("e => e.tagName.toLowerCase()")
        text = el.inner_text().strip() if tag != "img" else ""
        src = el.get_attribute("src") if tag in ["img", "iframe"] else None

        if tag.startswith("h"):
            if current:
                sections.append(current)
            current = {
                "heading": text,
                "text_blocks": [],
                "images": [],
                "videos": []
            }
        elif current:
            if tag == "p":
                current["text_blocks"].append(text)
            elif tag == "img":
                current["images"].append(src)
            elif tag == "iframe":
                current["videos"].append(src)

    if current:
        sections.append(current)

    return sections
