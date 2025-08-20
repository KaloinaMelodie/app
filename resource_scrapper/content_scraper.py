from utils import extract_sections

def scrape_page(page, metadata):
    try:
        page.wait_for_selector("h1", timeout=5000)
    except:
        return None

    content_sections = extract_sections(page)

    return {
        # "id": metadata["label"].lower().replace(" ", "_"),
        "id" : metadata["url"].split("#/")[-1].replace("/", "_"),
        "title": metadata["label"],
        "url": metadata["url"],
        "sections": content_sections,
        "metadata": {
            "source": "mWater Resource Center"
        }
    }
