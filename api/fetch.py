from http.server import BaseHTTPRequestHandler
import json
import re
import requests
from bs4 import BeautifulSoup

FETCH_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://lnmtl.com/",
}

CJK_RE = re.compile(
    r'[一-鿿㐀-䶿豈-﫿'
    r'　-〿！-｠'
    r'「」『』【】《》〈〉'
    r'，。！？；：、…—～]+'
)

CHAPTER_NUM_RE = re.compile(r'^(.*?-chapter-)(\d+)$')


def extract_title(soup):
    for sel in ["h1.chapter-title", ".chapter-title", "h1", "h2"]:
        tag = soup.select_one(sel)
        if tag and tag.get_text(strip=True):
            return tag.get_text(strip=True)
    if soup.title:
        return soup.title.get_text(strip=True)
    return "Chapter"


def extract_body(soup):
    body_selectors = [
        ".chapter-body", ".body", "#chapter-body",
        ".chapter-content", ".entry-content", "article", ".content",
    ]
    for sel in body_selectors:
        candidate = soup.select_one(sel)
        if candidate and len(candidate.get_text(strip=True)) > 200:
            return candidate
    all_divs = soup.find_all("div")
    if all_divs:
        return max(all_divs, key=lambda d: len(d.get_text()))
    return soup.body


def extract_text(body):
    raw = body.get_text(separator="\n")
    lines = [ln.strip() for ln in raw.split("\n") if ln.strip()]

    zh_sentences = []
    en_sentences = []

    for line in lines:
        zh_matches = CJK_RE.findall(line)
        if zh_matches:
            zh_text = " ".join(zh_matches).strip("「」『』")
            if zh_text and len(zh_text) > 2:
                zh_sentences.append(zh_text)
        else:
            en_text = re.sub(r'\s+', ' ', line).strip()
            if en_text and len(en_text) > 5:
                en_sentences.append(en_text)

    if zh_sentences:
        return zh_sentences, "zh"
    return en_sentences, "en"


def find_nav_links(soup, current_url):
    prev_url = next_url = None

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href.startswith("http"):
            href = "https://lnmtl.com" + href
        rel = a.get("rel", [])
        text = a.get_text(strip=True).lower()

        if "prev" in rel or text in ("previous", "prev", "← previous", "previous chapter", "< previous"):
            prev_url = href
        elif "next" in rel or text in ("next", "next →", "next chapter", "next >"):
            next_url = href

    m = CHAPTER_NUM_RE.match(current_url.rstrip("/"))
    if m:
        base, num = m.group(1), int(m.group(2))
        if not next_url:
            next_url = base + str(num + 1)
        if not prev_url and num > 1:
            prev_url = base + str(num - 1)

    return prev_url, next_url


def fetch_chapter(url):
    try:
        resp = requests.get(url, headers=FETCH_HEADERS, timeout=15)
        resp.raise_for_status()
    except requests.exceptions.Timeout:
        return {"error": "หมดเวลา — เว็บไซต์ไม่ตอบสนอง"}, 504
    except requests.exceptions.HTTPError as e:
        return {"error": f"HTTP {e.response.status_code} — อาจถูก Cloudflare บล็อก"}, 502
    except Exception as e:
        return {"error": str(e)}, 502

    soup = BeautifulSoup(resp.text, "html.parser")
    title = extract_title(soup)
    body = extract_body(soup)

    if not body:
        return {"error": "ไม่พบเนื้อหา"}, 422

    sentences, source_lang = extract_text(body)
    if not sentences:
        return {"error": "ไม่พบข้อความในหน้านี้"}, 422

    prev_url, next_url = find_nav_links(soup, url)

    return {
        "title": title,
        "content": "\n".join(sentences),
        "next_url": next_url,
        "prev_url": prev_url,
        "source_lang": source_lang,
        "sentence_count": len(sentences),
    }, 200


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            length = int(self.headers.get('Content-Length', 0))
            try:
                data = json.loads(self.rfile.read(length))
            except Exception:
                data = {}

            url = (data or {}).get("url", "").strip()
            if not url or not url.startswith("http"):
                result, status = {"error": "URL ไม่ถูกต้อง"}, 400
            else:
                result, status = fetch_chapter(url)
        except Exception as e:
            import traceback
            result = {"error": f"Server error: {str(e)}", "trace": traceback.format_exc()[:500]}
            status = 500

        body = json.dumps(result, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
