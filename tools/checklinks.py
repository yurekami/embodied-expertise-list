"""Deterministic verifier: every source URL in data/orgs.json must answer. Prints the ones that do not."""
import io, json, os, sys, concurrent.futures as cf
import urllib.request, urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/128 Safari/537.36",
      "Accept": "text/html,*/*;q=0.8"}


def probe(url):
    for method in ("HEAD", "GET"):
        try:
            req = urllib.request.Request(url, headers=UA, method=method)
            with urllib.request.urlopen(req, timeout=20) as r:
                return r.status
        except urllib.error.HTTPError as e:
            if method == "GET" or e.code in (404, 410):
                return e.code
        except Exception as e:
            if method == "GET":
                return type(e).__name__
    return "?"


def main():
    orgs = json.load(io.open(os.path.join(ROOT, "data", "orgs.json"), encoding="utf-8"))
    items = [(o["name"], s[0], s[1]) for o in orgs for s in o["sources"]] + [(o["name"], "main link", o["url"]) for o in orgs]
    with cf.ThreadPoolExecutor(16) as ex:
        codes = list(ex.map(lambda t: probe(t[2]), items))
    bad = [(t, c) for t, c in zip(items, codes) if not (isinstance(c, int) and c < 400)]
    print(f"{len(items)} urls, {len(bad)} not OK")
    for (name, label, url), c in bad:
        print(f"  {c}\t{name}\t{label}\t{url}")


if __name__ == "__main__":
    main()
