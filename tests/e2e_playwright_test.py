import pytest

try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None


def test_home_page_loads():
    if sync_playwright is None:
        pytest.skip('playwright not installed in this environment')
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=True)
        except Exception:
            pytest.skip('playwright browser binaries not installed (run: playwright install)')
        page = browser.new_page()
        try:
            page.goto('http://localhost:5500/', timeout=5000)
        except Exception:
            pytest.skip('server not running on localhost:5500')
        assert page.query_selector('body') is not None
        browser.close()
