
import asyncio
import json
import re
from urllib.parse import quote
from pathlib import Path
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

BASE_URL = "https://portal.mwater.co/#/resource_center/"
NDJSON_PATH = Path("links.ndjson")

def manual_slugify(text: str) -> str:
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')

def build_url(breadcrumbs):
    return BASE_URL + "/".join(manual_slugify(part) for part in breadcrumbs)

async def extract_sidebar_links():
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, slow_mo=100)
            context = await browser.new_context()
            page = await context.new_page()

            print("🔄 Navigation vers la page...")
            await page.goto(BASE_URL+"account_creation", wait_until="networkidle", timeout=60000)

            print("⏳ Attente du menu latéral...")
            try:
                await page.wait_for_selector(".resource-guide-toc-container", timeout=60000)
            except PlaywrightTimeoutError:
                print("❌ Timeout : menu latéral non chargé.")
                return

            sidebar = await page.query_selector(".resource-guide-toc-container")
            if not sidebar:
                print("❌ Erreur : menu non trouvé.")
                return

            menu_items = await sidebar.query_selector_all(":scope > div")
            print(f"🔍 {len(menu_items)} éléments trouvés.")

            results = []

            async def process_item(item, parent_titles):
                try:
                    title_el = await item.query_selector("a.resource-guide-toc-nav-item")
                    if not title_el:
                        return
                    title = (await title_el.inner_text()).strip()
                    if not title:
                        return

                    path = parent_titles + [title]
                    has_children = await item.query_selector("div.resource-guide-toc-section-content")

                    if has_children:
                        children = await has_children.query_selector_all(":scope > div")
                        for child in children:
                            await process_item(child, path)
                    else:
                        results.append({
                            "title": title,
                            "breadcrumbs": path,
                            "url": build_url(path)
                        })
                except Exception as e:
                    print(f"⚠️ Erreur dans un item : {e}")

            for item in menu_items:
                await process_item(item, [])

            if results:
                with NDJSON_PATH.open("w", encoding="utf-8") as f:
                    for entry in results:
                        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
                print(f"✅ Extraction réussie : {len(results)} liens sauvegardés dans links.ndjson")
            else:
                print("⚠️ Aucun lien trouvé.")

    except PlaywrightTimeoutError as e:
        print(f"⏱️ Timeout Playwright : {str(e)}")
    except Exception as e:
        print(f"❌ Erreur inattendue : {str(e)}")

if __name__ == "__main__":
    asyncio.run(extract_sidebar_links())
