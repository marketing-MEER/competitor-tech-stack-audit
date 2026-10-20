import functools
import http.server
import tempfile
import threading
import unittest
from pathlib import Path

from click.testing import CliRunner

from competitor_tech_stack_audit import cli, core

FULL_HOME = """<!doctype html><html><head><title>Full site home page title</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="canonical" href="/"><meta property="og:title" content="Full">
<link rel="alternate" hreflang="de" href="/de/"><link rel="alternate" hreflang="x-default" href="/">
<script type="application/ld+json">{"@context":"https://schema.org","@graph":[{"@type":"Organization"},{"@type":"WebSite"}]}</script>
<link rel="stylesheet" href="/wp-content/themes/x/style.css"></head>
<body><img src="/a.webp"><img src="/b.jpg"><script src="/app.js"></script></body></html>"""
ROBOTS = "User-agent: GPTBot\nDisallow: /\n\nUser-agent: *\nAllow: /\nSitemap: {base}/sitemap.xml\n"
SITEMAP = '<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>{base}/</loc></url></urlset>'


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def serve(files: dict):
    tmp = tempfile.TemporaryDirectory()
    root = Path(tmp.name)
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(QuietHandler, directory=str(root)))
    base = f"http://127.0.0.1:{server.server_port}"
    for name, text in files.items():
        (root / name).write_text(text.replace("{base}", base), encoding="utf-8")
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return tmp, server, base


class AuditTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.full = serve({"index.html": FULL_HOME, "robots.txt": ROBOTS, "sitemap.xml": SITEMAP,
                          "llms.txt": "# Full site\n> About us"})
        cls.bare = serve({"index.html": "<html><head><title>Bare</title></head><body>hi</body></html>"})
        cls.full_row = core.audit_domain(cls.full[2])
        cls.bare_row = core.audit_domain(cls.bare[2])

    @classmethod
    def tearDownClass(cls):
        for tmp, server, _ in (cls.full, cls.bare):
            server.shutdown()
            tmp.cleanup()

    def test_full_site(self):
        r = self.full_row
        self.assertEqual(r["status"], 200)
        self.assertEqual(r["cms_framework"], "WordPress")
        self.assertEqual(r["schema_types"], "Organization, WebSite")
        self.assertTrue(r["has_organization_schema"] and r["mobile_viewport"] and r["open_graph"])
        self.assertEqual(r["hreflang_tags"], 2)
        self.assertTrue(r["xml_sitemap"] and r["robots_txt"] and r["llms_txt"])
        self.assertEqual((r["images"], r["modern_images"]), (2, 1))
        self.assertEqual(r["ai_GPTBot"], "blocked")
        self.assertEqual(r["ai_ClaudeBot"], "allowed")
        self.assertEqual(r["ai_crawlers_blocked"], 1)

    def test_bare_site(self):
        r = self.bare_row
        self.assertEqual(r["cms_framework"], "unknown / custom")
        self.assertFalse(r["xml_sitemap"] or r["robots_txt"] or r["llms_txt"] or r["mobile_viewport"])
        self.assertEqual(r["ai_crawlers_blocked"], 0)   # no robots.txt = everything allowed

    def test_scorecard_and_tables(self):
        card = core.scorecard([self.full_row, self.bare_row])
        domains = card.columns[1:]
        self.assertEqual(card.iloc[-1]["check"], "Score")
        full_score = int(card.iloc[-1][domains[0]].split("/")[0])
        bare_score = int(card.iloc[-1][domains[1]].split("/")[0])
        self.assertGreater(full_score, bare_score)
        self.assertEqual(len(core.ai_table([self.full_row])), len(core.AI_CRAWLERS))
        self.assertIn("yes", core.matrix([self.full_row]).iloc[:, 1].tolist())

    def test_unreachable(self):
        self.assertEqual(core.audit_domain("http://127.0.0.1:9")["status"], "unreachable")

    def test_cli(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "tech"
            res = CliRunner().invoke(cli.main, [self.full[2], self.bare[2], "--delay", "0", "-o", str(out)])
            self.assertEqual(res.exit_code, 0, res.output)
            self.assertIn("Technical SEO comparison", out.with_suffix(".html").read_text(encoding="utf-8"))


class HelperTest(unittest.TestCase):
    def test_detectors(self):
        self.assertEqual(core.detect_cms('<script id="__NEXT_DATA__">'), "Next.js")
        self.assertEqual(core.detect_cdn({"Server": "cloudflare", "CF-RAY": "x"}), "Cloudflare")
        self.assertEqual(core.base_url("example.com/"), "https://example.com")


if __name__ == "__main__":
    unittest.main()
