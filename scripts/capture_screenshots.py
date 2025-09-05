import argparse
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright


async def capture(base_url: str, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1440, "height": 900})

        await page.goto(base_url, wait_until="networkidle")
        await page.screenshot(path=str(output_dir / "home.png"), full_page=True)

        # Scroll to capture more of the page
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.screenshot(path=str(output_dir / "chat.png"), full_page=True)

        await browser.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Capture project screenshots")
    parser.add_argument(
        "--url", default="http://localhost:8501", help="Base URL of the running app"
    )
    parser.add_argument(
        "--out", default="assets/screenshots", help="Output directory for screenshots"
    )
    args = parser.parse_args()

    asyncio.run(capture(args.url, Path(args.out)))


if __name__ == "__main__":
    main()
