import re
import os
import argparse
import requests
from bs4 import BeautifulSoup

CACHE_DIR = os.path.expanduser("~/.cache/onionvalidator/")
CACHE_FILE = os.path.join(CACHE_DIR, "onionlist.txt")

SOURCES = [
    "https://daunt.link",
    "https://tor.watch",
    "https://dark.contact",
    "https://onion.rip",
]

ONION_REGEX = re.compile(r"([a-z2-7]{16,56})\.onion", re.IGNORECASE)

def fetch_onions():
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(CACHE_FILE, "w") as f:
        seen = set()
        for url in SOURCES:
            try:
                r = requests.get(url, timeout=10)
                soup = BeautifulSoup(r.text, "html.parser")
                found = ONION_REGEX.findall(soup.text)
                for onion in found:
                    onion += ".onion"
                    onion = onion.lower()
                    if onion not in seen:
                        f.write(onion + "\n")
                        seen.add(onion)
            except Exception as e:
                print(f"[!] Failed to fetch from {url}: {e}")
    print(f"[+] Saved {len(seen)} .onion addresses to cache.")

def load_cache():
    if not os.path.exists(CACHE_FILE):
        print("[!] No cache found. Run with --update first.")
        return set()
    with open(CACHE_FILE, "r") as f:
        return set(line.strip().lower() for line in f if line.strip())

def validate(onion, cache):
    if not ONION_REGEX.fullmatch(onion.lower()):
        return "INVALID FORMAT ❌"
    return "VALID ✅" if onion.lower() in cache else "NOT FOUND ❌"

def main():
    parser = argparse.ArgumentParser(description=".onion address validator")
    parser.add_argument("onion", nargs="?", help="Single .onion address to validate")
    parser.add_argument("-f", "--file", help="Validate a list of .onion addresses from a file")
    parser.add_argument("--update", action="store_true", help="Update onion database from known sources")
    args = parser.parse_args()

    if args.update:
        fetch_onions()
        return

    cache = load_cache()
    if not cache:
        return

    if args.onion:
        print(f"{args.onion}: {validate(args.onion, cache)}")
    elif args.file:
        try:
            with open(args.file, "r") as f:
                for line in f:
                    onion = line.strip()
                    if onion:
                        print(f"{onion}: {validate(onion, cache)}")
        except FileNotFoundError:
            print(f"[!] File not found: {args.file}")
    else:
        print("[*] Enter .onion addresses (Ctrl+D to finish):")
        try:
            while True:
                onion = input("> ").strip()
                if onion:
                    print(f"{onion}: {validate(onion, cache)}")
        except EOFError:
            pass
