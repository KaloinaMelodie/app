import traceback
from typing import Optional, Dict, Any
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError
from app.exceptions import RenderError

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

def _wait_for_spa(page, wait_ms: int, extra_selector: Optional[str] = None):
    """
    Stabilise les SPA:
    - attend DOMContentLoaded + networkidle
    - attend un sélecteur raisonnable (main/body)
    - attend en plus wait_ms si demandé
    """
    # 1) États de charge
    page.wait_for_load_state("domcontentloaded")
    try:
        page.wait_for_load_state("networkidle", timeout=5000)
    except PWTimeoutError:
        # Certaines apps ne déclenchent jamais "networkidle": on tolère
        pass

    # 2) Un sélecteur "garde-fou" pour le contenu (adapte si tu connais la cible)
    selector = extra_selector or "main, #root, #app, body"
    try:
        page.wait_for_selector(selector, state="attached", timeout=10000)
    except PWTimeoutError as e:
        # On ne stoppe pas forcément, certaines pages rendent dans body sans sous-sélecteurs
        pass

    # 3) Attente additionnelle
    if wait_ms and wait_ms > 0:
        page.wait_for_timeout(wait_ms)

def render_page(url: str, wait_ms: int = 3500, timeout_ms: int = 20000, extra_selector: Optional[str] = None) -> Dict[str, Any]:
    url = str(url)  
    console_logs = []
    req_errors = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
            context = browser.new_context(
                user_agent=DEFAULT_USER_AGENT,
                viewport={"width": 1366, "height": 768}
            )
            page = context.new_page()

            # Collecte console & erreurs réseau pour debug
            page.on("console", lambda msg: console_logs.append({"type": msg.type(), "text": msg.text()}))
            page.on("requestfailed", lambda req: req_errors.append({"url": req.url, "failure": (req.failure() or {}).get("errorText")}))

            # GOTO
            try:
                resp = page.goto(url, timeout=timeout_ms, wait_until="domcontentloaded")
                
            except PWTimeoutError as e:
                raise RenderError(
                    f"Timeout during navigation to {url}",
                    step="goto",
                    code="TIMEOUT_GOTO",
                    stack=traceback.format_exc(),
                )

            # Vérifie statut HTTP s’il existe (les hash routes retournent souvent None)
            if resp is not None:
                status = resp.status
                if status >= 400:
                    raise RenderError(
                        f"HTTP {status} on initial document for {url}",
                        step="goto",
                        code=f"HTTP_{status}",
                        stack=None,
                    )

            # Attendre un conteneur stable (SPA)
            selector = extra_selector or "#main_pane_container, .resource-guide-content-area, main, #root, #app, body"
            try:
                page.wait_for_selector(selector, state="attached", timeout=10000)
            except PWTimeoutError:
                pass

            # Attente additionnelle optionnelle
            if wait_ms and wait_ms > 0:
                page.wait_for_timeout(wait_ms)

            # >>> Remplace l'extraction HTML <<<
            # Évite page.content() pour contourner "'str' object is not callable"
            try:
                # Méthode Playwright standard (si elle marche dans ton env)
                html = page.content()
            except TypeError:
                # Fallback robuste : récupère l’HTML via le DOM
                html = page.evaluate("() => document.documentElement.outerHTML")

            browser.close()

            return {
                "url": url,
                "html": html,
                "debug": {
                    "console": console_logs[-20:],  # dernières lignes utiles
                    "requestErrors": req_errors[:50],
                },
            }

    except RenderError:
        # déjà enrichi
        raise
    except Exception as e:
        raise RenderError(
            f"Unexpected error rendering {url}: {e!r}",
            step="unknown",
            code="UNHANDLED",
            stack=traceback.format_exc(),
        )
