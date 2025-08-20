from sidebar_extractor import extract_links
from content_scraper import scrape_page
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

def main():
    output_path = Path("output.ndjson")
    output_path.unlink(missing_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=200)  # pour voir ce qu’il fait
        page = browser.new_page()

        base_url = "https://portal.mwater.co/#/resource_center/getting_started"
        print("🔗 Accès à la page de départ...")
        page.goto(base_url, wait_until="domcontentloaded", timeout=60000)

        # Ajoute une pause manuelle pour laisser le JS charger le sidebar
        page.wait_for_timeout(2000)

        # Maintenant on peut commencer l'exploration
        links = extract_links(page)

        print(f"✅ {len(links)} lien(s) réel(s) trouvé(s) à scraper.")

        # with open("output.ndjson", "a", encoding="utf-8") as f:
        #     for link in links:
        #         print(f"📄 Scraping: {link['label']}")
        #         page.goto(link["url"], wait_until="domcontentloaded", timeout=60000)
        #         page.wait_for_timeout(1000)
        #         try:
        #             content = scrape_page(page, link)
        #             if content:
        #                 f.write(json.dumps(content, ensure_ascii=False) + "\n")
        #         except Exception as e:
        #             print(f"❌ Erreur scraping page {link['url']} : {e}")

        browser.close()

if __name__ == "__main__":
    main()
