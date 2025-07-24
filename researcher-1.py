import asyncio
import uuid
import time
from datetime import datetime
from playwright.async_api import async_playwright
from docx import Document
from bs4 import BeautifulSoup

LOADING_SPINNER_SELECTOR = None  # optional: e.g. "div.loading-spinner"

async def run_bohrium_search():
    async with async_playwright() as p:
        print("[*] Launching browser...")
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        async def auto_close_modal():
            while True:
                try:
                    modal = await page.query_selector("div._modal_7bdw1_1")
                    if modal:
                        print("[!] Login popup detected.")
                        close_btn = await modal.query_selector("div._close_7bdw1_31")
                        if close_btn:
                            await close_btn.click()
                            print("[!] Login popup closed.")
                            await page.wait_for_selector("div._modal_7bdw1_1", state="detached", timeout=7000)
                    await asyncio.sleep(0.5)
                except:
                    pass

        try:
            print("[*] Navigating to Bohrium AI...")
            await page.goto("https://www.bohrium.com/en-US", timeout=60000, wait_until="domcontentloaded")
            await page.wait_for_timeout(6000)
            asyncio.create_task(auto_close_modal())
            print("[*] Page loaded.")

            await page.wait_for_selector("textarea", timeout=15000)
            prompt_text = "The impact of AI in education"
            await page.fill("textarea", prompt_text)
            print(f"[*] Prompt entered: '{prompt_text}'")

            await page.wait_for_selector("button._buttons-send-wrapper_bf84e_11", timeout=15000)
            submit_btn = await page.query_selector("button._buttons-send-wrapper_bf84e_11")
            await submit_btn.scroll_into_view_if_needed()
            print("[*] Clicking submit button...")
            await submit_btn.click()
            print("[*] Query submitted.")

            print("[*] Waiting 20s before content processing...")
            await asyncio.sleep(20)

            stable_count = 0
            last_len = 0
            stable_threshold = 10
            max_wait = 600
            pre_refresh_wait = 10
            post_refresh_wait = 10
            refreshed = False
            start_time = time.time()

            combined_html_after_refresh = ""

            while True:
                elapsed = time.time() - start_time
                if elapsed > max_wait:
                    print("[!] Max wait reached.")
                    break

                if int(elapsed) % 10 == 0:
                    await page.evaluate("window.scrollBy(0, window.innerHeight);")
                    await asyncio.sleep(1)

                elements = await page.query_selector_all("div.mt-20")
                print(f"[ ] {int(elapsed)}s: Found {len(elements)} content blocks.")

                combined_html = ""
                for el in elements:
                    inner_html = await el.inner_html()
                    combined_html += f"<div class='mt-20'>{inner_html}</div>"

                if len(combined_html) == last_len:
                    stable_count += 1
                    print(f"[✓] Stable for {stable_count}s.")
                else:
                    stable_count = 0
                    print("[*] Content changed, resetting stability counter.")

                last_len = len(combined_html)

                if stable_count >= stable_threshold and not refreshed:
                    print(f"[✓] Stability detected. Waiting {pre_refresh_wait}s before refreshing...")
                    await asyncio.sleep(pre_refresh_wait)
                    print("[✓] Performing one-time refresh now...")
                    await page.reload()
                    if LOADING_SPINNER_SELECTOR:
                        try:
                            await page.wait_for_selector(LOADING_SPINNER_SELECTOR, state="detached", timeout=10000)
                        except:
                            pass
                    print(f"[*] Waiting {post_refresh_wait}s after refresh...")
                    await asyncio.sleep(post_refresh_wait)
                    refreshed = True
                    break

                await asyncio.sleep(1)

            print("[*] Collecting final refreshed content...")
            refreshed_elements = await page.query_selector_all("div.mt-20")
            for el in refreshed_elements:
                inner_html = await el.inner_html()
                combined_html_after_refresh += f"<div class='mt-20'>{inner_html}</div>"

            print("[*] Parsing final content...")
            soup = BeautifulSoup(combined_html_after_refresh, 'html.parser')
            doc = Document()
            doc.add_heading(prompt_text, level=1)
            captions_already_inserted = set()

            for block in soup.select("div.mt-20"):
                paragraphs = block.find_all("p", recursive=True)
                if not paragraphs:
                    text = block.get_text(strip=True)
                    if text and text not in captions_already_inserted:
                        doc.add_paragraph(text)
                        print(f"[+] Inserted block text: {text[:60]}...")
                    continue

                for p in paragraphs:
                    img_div = p.find("div", class_="_img_1k32x_74")
                    if img_div:
                        # Extract image URL
                        img_tag = img_div.find("img")
                        img_url = img_tag["src"] if img_tag and img_tag.has_attr("src") else ""

                        # Extract caption
                        caption_div = img_div.find("div", class_="_img-title_1k32x_79")
                        caption_text = caption_div.get_text(strip=True) if caption_div else ""

                        # Extract source text (inside <em>)
                        source_text = ""
                        em_tag = p.find("em")
                        if em_tag:
                            source_text = em_tag.get_text(strip=True)

                        full_sentence = f"{img_url}. {caption_text}. Source: {source_text}."
                        if full_sentence not in captions_already_inserted:
                            doc.add_paragraph(full_sentence)
                            captions_already_inserted.add(full_sentence)
                            print(f"[+] Inserted image+caption+source: {full_sentence[:60]}...")
                        continue

                    # Regular paragraph text
                    p_text = p.get_text(strip=True)
                    if not p_text:
                        continue
                    if p_text in captions_already_inserted:
                        print(f"[–] Skipped duplicate: {p_text[:60]}...")
                        continue
                    doc.add_paragraph(p_text)
                    captions_already_inserted.add(p_text)
                    print(f"[+] Inserted paragraph: {p_text[:60]}...")

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = uuid.uuid4().hex[:6]
            filename = f"bohrium_ai_response_{timestamp}_{unique_id}.docx"
            doc.save(filename)
            print(f"[✓] Document saved as '{filename}'")

            await page.wait_for_timeout(3000)

        except Exception as e:
            print(f"[ERROR] Exception occurred: {e}")
        finally:
            print("[*] Closing browser...")
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run_bohrium_search())
