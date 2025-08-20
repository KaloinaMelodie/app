from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

def extract_links_after_clicking(page):
    page.goto("https://portal.mwater.co/#/resource_center/getting_started", wait_until="domcontentloaded")
    page.wait_for_timeout(3000)

    # Clique sur tous les éléments du menu une fois pour forcer React à générer le DOM
    items = page.query_selector_all("a.resource-guide-toc-nav-item")
    for item in items:
        try:
            item.click()
            page.wait_for_timeout(200)
        except:
            continue

    # Maintenant, le DOM est prêt. Récupère le HTML complet du menu
    html = page.inner_html(".resource-guide-toc-container")
    soup = BeautifulSoup(html, "html.parser")

    links = []
    for div in soup.select("a.resource-guide-toc-nav-item"):
        label = div.get_text(strip=True)
        href = div.get("href")
        if href and "resource_center" in href:
            full_url = "https://portal.mwater.co" + href
            links.append({"label": label, "url": full_url})

    return links

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=100)
        page = browser.new_page()
        links = extract_links_after_clicking(page)
        for link in links:
            print(link)
        browser.close()

if __name__ == "__main__":
    main()
