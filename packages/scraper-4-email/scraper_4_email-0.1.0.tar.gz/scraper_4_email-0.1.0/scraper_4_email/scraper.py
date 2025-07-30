import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
import xml.etree.ElementTree as ET
from urllib.parse import urljoin, urlparse

# Regex to detect normal and obfuscated emails
email_patterns = [
    r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    r"[a-zA-Z0-9._%+-]+\s?\[\s*@\s*\]\s?[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    r"[a-zA-Z0-9._%+-]+\s?\[\s*at\s*\]\s?[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    r"[a-zA-Z0-9._%+-]+\s?\(\s*@\s*\)\s?[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    r"[a-zA-Z0-9._%+-]+\s?\(\s*at\s*\)\s?[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    r"[a-zA-Z0-9._%+-]+\s?\{\s*@\s*\}\s?[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    r"[a-zA-Z0-9._%+-]+\s?\{\s*at\s*\}\s?[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    r"[a-zA-Z0-9._%+-]+\s+at\s+[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    r"[a-zA-Z0-9._%+-]+\s?@\s?[a-zA-Z0-9.-]+\s?(?:\[dot\]|\(dot\)|\{dot\}| dot )\s?[a-zA-Z]{2,}"
]

def normalize_email(raw_email: str) -> str:
    email = raw_email.lower()
    email = re.sub(r"\[\s*@\s*\]|\(\s*@\s*\)|\{\s*@\s*\}", "@", email)
    email = re.sub(r"\[\s*at\s*\]|\(\s*at\s*\)|\{\s*at\s*\}| at ", "@", email, flags=re.IGNORECASE)
    email = re.sub(r"\[\s*dot\s*\]|\(\s*dot\s*\)|\{\s*dot\s*\}| dot ", ".", email, flags=re.IGNORECASE)
    email = re.sub(r"\s*@\s*", "@", email)
    email = re.sub(r"\s*\.\s*", ".", email)
    return email.strip()

def is_blog_page(url: str) -> bool:
    return re.search(r"/(blog|wp-content|glossaire|article|news|posts?)/", url, re.IGNORECASE) is not None

def get_urls_from_sitemap(sitemap_url: str) -> list:
    urls = []
    try:
        resp = requests.get(sitemap_url, timeout=10)
        tree = ET.fromstring(resp.content)
        if tree.tag.endswith("sitemapindex"):
            for sitemap in tree.findall(".//{*}loc"):
                sub_url = sitemap.text
                if sub_url:
                    urls += get_urls_from_sitemap(sub_url)
        elif tree.tag.endswith("urlset"):
            for url_tag in tree.findall(".//{*}loc"):
                url = url_tag.text
                if url and not is_blog_page(url):
                    urls.append(url)
    except Exception as e:
        print(f"Sitemap read error : {sitemap_url} – {e}")
    return urls

def extract_emails_from_url(url: str) -> set:
    found_emails = set()
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/114.0.0.0 Safari/537.36"
        )
    }
    try:
        response = requests.get(url, timeout=10, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        text = soup.get_text()
        for pattern in email_patterns:
            matches = re.findall(pattern, text, flags=re.IGNORECASE)
            for m in matches:
                cleaned = normalize_email(m)
                found_emails.add(cleaned)
    except:
        pass
    return found_emails

def process_site(site: str) -> dict:
    if not site.startswith("http"):
        site = "https://" + site
    domain = urlparse(site).scheme + "://" + urlparse(site).netloc
    sitemap_url = urljoin(domain, "/page-sitemap.xml")
    page_urls = get_urls_from_sitemap(sitemap_url)
    if not page_urls:
        page_urls = [site]
    all_emails = set()
    for page_url in page_urls:
        emails = extract_emails_from_url(page_url)
        all_emails.update(emails)
    return {
        "site": site,
        "pages_explorees": len(page_urls),
        "emails": ", ".join(all_emails)
    }

def run_scraper(input_excel: str, output_csv: str):
    df = pd.read_excel(input_excel)
    sites = df["site"].dropna().tolist()
    results = []
    for i, site in enumerate(sites, start=1):
        print(f"Site processing {i}/{len(sites)}")
        results.append(process_site(site))
    pd.DataFrame(results).to_csv(output_csv, index=False, encoding="utf-8")
    print(f"Completed: results saved in '{output_csv}'")
