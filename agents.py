import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from markdownify import markdownify as md
import pdfkit

BASE_URL = "https://developer.ukg.com/"

visited = set()
pages_content = []

async def scrape_page(page, url):
    if url in visited:
        return
    visited.add(url)

    print(f"Scraping: {url}")

    try:
        await page.goto(url, timeout=60000)
        await page.wait_for_load_state("networkidle")

        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")

        main = soup.find("main") or soup.body
        text = md(str(main))

        pages_content.append(f"# {url}\n\n{text}\n\n")

        links = soup.find_all("a", href=True)
        for link in links:
            href = link["href"]

            if href.startswith("/"):
                full_url = BASE_URL.rstrip("/") + href
            elif href.startswith("http") and "ukg.com" in href:
                full_url = href
            else:
                continue

            if full_url not in visited:
                await scrape_page(page, full_url)

    except Exception as e:
        print(f"Error scraping {url}: {e}")


async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        await scrape_page(page, BASE_URL)

        await browser.close()

    full_content = "\n\n".join(pages_content)

    with open("ukg_docs.md", "w", encoding="utf-8") as f:
        f.write(full_content)

    pdfkit.from_file("ukg_docs.md", "ukg_docs.pdf")

    print("✅ PDF generated: ukg_docs.pdf")


asyncio.run(run())
