from fastapi import APIRouter, HTTPException, Query
from app.models.job import Job
from app.services.renderer_service import render_page
from app.exceptions import RenderError
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError
from typing import Optional, Literal
import hashlib

router = APIRouter()

DEFAULT_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

DEFAULT_SELECTOR = ".resource-guide-content-area, #main_pane_container"

@router.post("/render/extract")
def render_and_extract(
    job: Job,
    selector: Optional[str] = Query(
        default=None,
        description="CSS selector à extraire (défaut: .resource-guide-content-area, #main_pane_container)"
    ),
    mode: Literal["inner_html", "inner_text"] = Query(
        default="inner_html",
        description="inner_html (défaut) ou inner_text"
    ),
):
    url = str(job.url)
    sel = selector.strip() if selector else DEFAULT_SELECTOR
    wait_ms = int(job.wait_ms or 0)
    timeout_ms = int(job.timeout_ms or 100000)
    # timeout_ms = int(1000)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
            context = browser.new_context(user_agent=DEFAULT_UA, viewport={"width": 1366, "height": 900})
            page = context.new_page()

            try:
                page.goto(url, timeout=timeout_ms, wait_until="domcontentloaded")
            except PWTimeoutError:
                browser.close()
                raise HTTPException(status_code=504, detail={
                    "status": "fail", "message": f"Timeout during navigation to {url}", "step": "goto"
                })

            try:
                page.wait_for_selector(sel, state="attached", timeout=15000)
            except PWTimeoutError:
                browser.close()
                raise HTTPException(status_code=504, detail={
                    "status": "fail", "message": f"Selector not found: {sel}", "step": "wait_for_selector"
                })

            readiness_js = r"""
(p) => {
  const el = document.querySelector(p.sel);
  if (!el) return false;
  const text = el.innerText || "";
  const html = el.innerHTML || "";
  const hasLoadingText = /loading\.\.\./i.test(text);
  const hasSpinner = html.includes("<svg") && html.toLowerCase().includes("animate");
  if (hasLoadingText || hasSpinner) return false;
  const hasBlocks = el.querySelector("h1,h2,h3,p,article,section") !== null;
  const hasLinks = el.querySelectorAll("a").length >= 3;
  const htmlLongEnough = html.replace(/\s+/g, "").length > 2000;
  return hasBlocks || hasLinks || htmlLongEnough;
}
"""
            try:
                page.wait_for_function(readiness_js, arg={"sel": sel}, timeout=timeout_ms)
            except PWTimeoutError:
                page.wait_for_timeout(3000)
                try:
                    page.wait_for_function(readiness_js, {"sel": sel}, timeout=5000)
                except PWTimeoutError:
                    browser.close()
                    raise HTTPException(status_code=504, detail={
                        "status": "fail",
                        "message": f"Content still loading for selector: {sel}",
                        "step": "wait_for_function"
                    })

            if wait_ms > 0:
                page.wait_for_timeout(wait_ms)

            extract_js = """
(p) => {
  const el = document.querySelector(p.sel);
  if (!el) return { ok: false, reason: "not_found" };
  if (p.mode === "inner_text") return { ok: true, content: el.innerText };
  return { ok: true, content: el.innerHTML };
}
"""
            result = page.evaluate(extract_js, {"sel": sel, "mode": mode})

            browser.close()

            if not result or not result.get("ok"):
                raise HTTPException(status_code=422, detail={
                    "status": "fail", "message": f"Extraction failed for selector: {sel}",
                    "step": "evaluate", "reason": result.get("reason") if isinstance(result, dict) else "unknown"
                })

            content_id = hashlib.sha1(url.encode("utf-8")).hexdigest()
            return {
                "status": "success",
                "id": content_id,
                "url": url,
                "selector_used": sel,
                "mode": mode,
                "html": result["content"] if mode == "inner_html" else None,
                "text": result["content"] if mode == "inner_text" else None,
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={
            "status": "fail", "message": f"Unexpected error rendering {url}: {e!r}", "step": "unhandled"
        })