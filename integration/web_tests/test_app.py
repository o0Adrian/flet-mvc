import os
import socket
import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

import pytest
from playwright.async_api import (
    TimeoutError as PlaywrightTimeoutError,
)
from playwright.async_api import async_playwright, expect

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "integration" / "src" / "main.py"
INTEGRATION = ROOT / "integration"
PYODIDE_EVENT_TIMEOUT = 60_000


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@contextmanager
def run_web_app(app: Path, cwd: Path):
    port = _free_port()
    url = f"http://127.0.0.1:{port}"
    env = {
        **os.environ,
        "FLET_FORCE_WEB_SERVER": "1",
        "FLET_SERVER_IP": "127.0.0.1",
        "FLET_SERVER_PORT": str(port),
        "PYTHONPATH": os.pathsep.join(
            value for value in (str(ROOT), os.environ.get("PYTHONPATH")) if value
        ),
    }
    process = subprocess.Popen(
        [sys.executable, str(app)],
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    try:
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            if process.poll() is not None:
                output = process.stdout.read() if process.stdout else ""
                pytest.fail(f"Flet web app exited early:\n{output}")
            try:
                with urlopen(url, timeout=0.5) as response:
                    if response.status == 200:
                        break
            except (OSError, URLError):
                time.sleep(0.1)
        else:
            pytest.fail("Flet web app did not become ready within 30 seconds")

        yield url
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        else:
            process.wait()
        if process.stdout:
            process.stdout.close()


@contextmanager
def serve_static_site(site: Path):
    port = _free_port()
    url = f"http://127.0.0.1:{port}"
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "http.server",
            str(port),
            "--bind",
            "127.0.0.1",
            "--directory",
            str(site),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            if process.poll() is not None:
                pytest.fail(
                    f"Static web server exited early with code {process.returncode}"
                )
            try:
                with urlopen(url, timeout=0.5) as response:
                    if response.status == 200:
                        break
            except (OSError, URLError):
                time.sleep(0.1)
        else:
            pytest.fail("Static web server did not become ready within 30 seconds")

        yield url
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        else:
            process.wait()


@pytest.fixture
def web_app_url():
    with run_web_app(APP, ROOT) as url:
        yield url


async def enable_flutter_accessibility(page) -> None:
    enable_accessibility = page.get_by_role("button", name="Enable accessibility")
    if await enable_accessibility.count():
        await enable_accessibility.evaluate("(element) => element.click()")


def chrome_launch_options() -> dict[str, object]:
    chrome_path = os.environ.get("FLET_MVC_CHROME_PATH")
    if chrome_path:
        return {"headless": True, "executable_path": chrome_path}
    return {"headless": True, "channel": "chrome"}


@pytest.mark.asyncio
async def test_reactivity_components_table_tabs_and_routing_in_browser(web_app_url):
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(**chrome_launch_options())
        page = await browser.new_page()
        try:
            await page.goto(web_app_url, wait_until="networkidle")
            await enable_flutter_accessibility(page)

            await expect(page.get_by_text("initial:0", exact=True)).to_be_visible()
            await expect(
                page.get_by_text("Declarative ready", exact=True)
            ).to_be_visible()
            await expect(
                page.get_by_text("FletComponent ready", exact=True)
            ).to_be_visible()
            await expect(page.get_by_text("Ada", exact=True)).to_be_visible()
            await expect(page.get_by_text("Grace", exact=True)).to_be_visible()
            await expect(page.get_by_role("tab", name="State")).to_be_visible()

            await page.get_by_role("textbox").fill("typed")
            await expect(page.get_by_text("typed:0", exact=True)).to_be_visible()

            await page.get_by_text("Set from model", exact=True).click()
            await expect(page.get_by_text("server:0", exact=True)).to_be_visible()

            await page.get_by_text("Component +1", exact=True).click()
            await expect(page.get_by_text("server:1", exact=True)).to_be_visible()

            await page.get_by_role("tab", name="About").click()
            await expect(
                page.get_by_role("tabpanel", name="Integration ready")
            ).to_be_visible()

            await page.get_by_text("Open details", exact=True).click()
            await expect(page.get_by_text("Details route", exact=True)).to_be_visible()

            await page.get_by_text("Return home", exact=True).click()
            await expect(page.get_by_text("server:1", exact=True)).to_be_visible()
        finally:
            await browser.close()


@pytest.mark.asyncio
async def test_dynamic_browser_sessions_keep_model_state_isolated(web_app_url):
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(**chrome_launch_options())
        first = await browser.new_page()
        second = await browser.new_page()
        try:
            for page in (first, second):
                await page.goto(web_app_url, wait_until="networkidle")
                await enable_flutter_accessibility(page)
                await expect(page.get_by_text("initial:0", exact=True)).to_be_visible()

            await first.get_by_role("textbox").fill("first-session")
            await first.get_by_text("Component +1", exact=True).click()

            await expect(
                first.get_by_text("first-session:1", exact=True)
            ).to_be_visible()
            await expect(second.get_by_text("initial:0", exact=True)).to_be_visible()
            assert await second.get_by_text("first-session:1", exact=True).count() == 0
        finally:
            await first.close()
            await second.close()
            await browser.close()


@pytest.mark.asyncio
async def test_static_pyodide_build_runs_in_browser(tmp_path):
    output = tmp_path / "web"
    build = subprocess.run(
        [
            sys.executable,
            "-m",
            "flet.cli",
            "build",
            "web",
            "--output",
            str(output),
            "--yes",
            "--no-rich-output",
        ],
        cwd=INTEGRATION,
        capture_output=True,
        text=True,
        timeout=600,
    )
    assert build.returncode == 0, build.stdout + build.stderr
    assert (output / "index.html").is_file()

    browser_errors: list[str] = []
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(**chrome_launch_options())
        page = await browser.new_page()
        page.on(
            "console",
            lambda message: (
                browser_errors.append(f"console {message.type}: {message.text}")
                if message.type == "error"
                else None
            ),
        )
        page.on(
            "pageerror",
            lambda error: browser_errors.append(f"page error: {error}"),
        )
        try:
            with serve_static_site(output) as url:
                await page.goto(url, wait_until="domcontentloaded")

                accessibility = page.get_by_role(
                    "button",
                    name="Enable accessibility",
                )
                try:
                    await accessibility.wait_for(state="attached", timeout=180_000)
                except PlaywrightTimeoutError:
                    # Accessibility can already be enabled by the browser.
                    pass
                await enable_flutter_accessibility(page)

                await expect(page.get_by_text("initial:0", exact=True)).to_be_visible(
                    timeout=180_000
                )
                await expect(
                    page.get_by_text("Declarative ready", exact=True)
                ).to_be_visible(timeout=PYODIDE_EVENT_TIMEOUT)
                await expect(
                    page.get_by_text("FletComponent ready", exact=True)
                ).to_be_visible()
                await expect(page.get_by_text("Ada", exact=True)).to_be_visible()
                await expect(page.get_by_text("Grace", exact=True)).to_be_visible()

                await page.get_by_role("textbox").fill("pyodide")
                await expect(page.get_by_text("pyodide:0", exact=True)).to_be_visible(
                    timeout=PYODIDE_EVENT_TIMEOUT
                )

                await page.get_by_text("Set from model", exact=True).click()
                await expect(page.get_by_text("server:0", exact=True)).to_be_visible(
                    timeout=PYODIDE_EVENT_TIMEOUT
                )

                await page.get_by_text("Component +1", exact=True).click()
                await expect(page.get_by_text("server:1", exact=True)).to_be_visible(
                    timeout=PYODIDE_EVENT_TIMEOUT
                )

                await page.get_by_role("tab", name="About").click()
                await expect(
                    page.get_by_role("tabpanel", name="Integration ready")
                ).to_be_visible(timeout=PYODIDE_EVENT_TIMEOUT)

                await page.get_by_text("Open details", exact=True).click()
                await expect(
                    page.get_by_text("Details route", exact=True)
                ).to_be_visible(timeout=PYODIDE_EVENT_TIMEOUT)

                await page.get_by_text("Return home", exact=True).click()
                await expect(page.get_by_text("server:1", exact=True)).to_be_visible(
                    timeout=PYODIDE_EVENT_TIMEOUT
                )
        finally:
            await browser.close()

    assert browser_errors == []


@pytest.mark.asyncio
async def test_generated_templates_render_and_interact_in_browser(tmp_path):
    expectations = {
        "start": ("Hello, World!", "Toggle title", "Hello from Flet MVC!"),
        "routes": (
            "This is the home view.",
            "Go to secondary view",
            "This is the secondary view.",
        ),
        "tabs": ("This is the home tab.", "Settings", "This is the settings tab."),
        "reactive": (
            "You clicked 0 times.",
            "Add one",
            "You clicked 1 time.",
        ),
    }

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(**chrome_launch_options())
        try:
            for command, (initial, action, expected) in expectations.items():
                destination = tmp_path / command
                generated = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "mvc_commands.cli",
                        command,
                        "--destination",
                        str(destination),
                    ],
                    cwd=ROOT,
                    capture_output=True,
                    text=True,
                )
                assert generated.returncode == 0, generated.stdout + generated.stderr

                with run_web_app(destination / "src" / "main.py", destination) as url:
                    page = await browser.new_page()
                    try:
                        await page.goto(url, wait_until="networkidle")
                        await enable_flutter_accessibility(page)

                        if command == "tabs":
                            await expect(
                                page.get_by_role("tabpanel", name=initial)
                            ).to_be_visible()
                            await page.get_by_role("tab", name=action).click()
                            await expect(
                                page.get_by_role("tabpanel", name=expected)
                            ).to_be_visible()
                        else:
                            await expect(
                                page.get_by_text(initial, exact=True)
                            ).to_be_visible()
                            await page.get_by_text(action, exact=True).click()
                            await expect(
                                page.get_by_text(expected, exact=True)
                            ).to_be_visible()

                            if command == "routes":
                                await page.get_by_text(
                                    "Return home", exact=True
                                ).click()
                                await expect(
                                    page.get_by_text(initial, exact=True)
                                ).to_be_visible()
                    finally:
                        await page.close()
        finally:
            await browser.close()
