"""Build the site from fixture guides into a temporary folder and check the output."""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE_URL = "https://example.test/kit"


def build(data_dir, out_dir, **env):
    e = dict(os.environ, BUILD_DIR=str(out_dir), MEALPREP_DATA_DIR=str(data_dir), SITE_URL=SITE_URL)
    for k in ("GOATCOUNTER_URL", "PRO_URL", "PRO_LABEL"):
        e.pop(k, None)
    e.update(env)
    r = subprocess.run([sys.executable, str(ROOT / "pipeline" / "build.py")], env=e, capture_output=True, text=True)
    if r.returncode:
        raise AssertionError(r.stdout + r.stderr)
    return r.stdout


class Build(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        shutil.copytree(ROOT / "tests" / "fixtures" / "states", cls.tmp / "data" / "states")
        cls.dist = cls.tmp / "dist"
        build(cls.tmp / "data", cls.dist)
        cls.states = [json.loads(p.read_text()) for p in sorted((cls.tmp / "data" / "states").glob("*.json"))]

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp)

    def read(self, rel):
        return (self.dist / rel).read_text(encoding="utf-8")

    def test_every_state_page_cites_dated_official_sources(self):
        for s in self.states:
            slug = s["state"].lower().replace(" ", "-")
            page = self.read(f"permits/{slug}/index.html")
            self.assertEqual(page.count("<h1"), 1)
            self.assertIn(f'<link rel="canonical" href="{SITE_URL}/permits/{slug}/">', page)
            self.assertIn("Information, not legal advice.", page)
            self.assertIn("local health department", page)
            for sec in s["sections"]:
                for src in sec["sources"]:
                    self.assertIn(src["url"], page)
            self.assertGreaterEqual(page.count("<time datetime="), sum(len(x["sources"]) for x in s["sections"]) + 2)
            for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', page, re.S):
                json.loads(block)

    def test_empty_sections_are_left_out(self):
        page = self.read("permits/vermont/index.html")
        self.assertNotIn('id="business"', page, "a section with no sourced points must not render")

    def test_sitemap_and_robots(self):
        urls = re.findall(r"<loc>([^<]+)</loc>", self.read("sitemap.xml"))
        self.assertEqual(len(urls), len(set(urls)))
        for s in self.states:
            self.assertIn(f"{SITE_URL}/permits/{s['state'].lower().replace(' ', '-')}/", urls)
        self.assertNotIn(f"{SITE_URL}/order/", urls)
        robots = self.read("robots.txt")
        self.assertIn("Disallow: /kit/order/", robots)
        self.assertIn(f"Sitemap: {SITE_URL}/sitemap.xml", robots)
        for u in urls:
            page = self.read(u[len(SITE_URL) + 1:] + "index.html")
            self.assertIn(f'<link rel="canonical" href="{u}">', page)

    def test_order_page_is_not_indexed(self):
        self.assertIn('name="robots" content="noindex', self.read("order/index.html"))

    def test_hub_counts_match_the_data(self):
        page = self.read("permits/index.html")
        self.assertEqual(page.count('class="pill '), len(self.states) + 3)   # one per state + three in the legend
        meta = json.loads(self.read("data/meta.json"))
        self.assertEqual(meta["states"], len(self.states))

    def test_builder_lists_every_state(self):
        page = self.read("build/index.html")
        for s in self.states:
            self.assertIn(f'<option value="{s["abbr"]}">{s["state"]}</option>', page)

    def test_paid_slot_and_analytics_only_when_set(self):
        self.assertNotIn("data-pro", self.read("index.html"))
        self.assertNotIn("goatcounter", self.read("index.html"))
        with tempfile.TemporaryDirectory() as tmp:
            build(self.tmp / "data", Path(tmp) / "dist", PRO_URL="https://pro.example/", GOATCOUNTER_URL="https://x.goatcounter.com/count")
            home = (Path(tmp) / "dist" / "index.html").read_text()
            self.assertIn('href="https://pro.example/"', home)
            self.assertIn('data-goatcounter="https://x.goatcounter.com/count"', home)

    def test_invalid_guides_stop_the_build(self):
        with tempfile.TemporaryDirectory() as tmp:
            shutil.copytree(ROOT / "tests" / "fixtures" / "states", Path(tmp) / "states")
            f = Path(tmp) / "states" / "VT.json"
            d = json.loads(f.read_text())
            d["sections"][0]["sources"][0]["url"] = "https://www.some-law-firm.com/blog"
            f.write_text(json.dumps(d))
            with self.assertRaises(AssertionError):
                build(Path(tmp), Path(tmp) / "dist")


class RealGuides(unittest.TestCase):
    def test_published_guides_validate(self):
        sys.path.insert(0, str(ROOT / "pipeline"))
        from validate_states import main
        if any((ROOT / "data" / "states").glob("*.json")):
            self.assertEqual(main([str(ROOT / "data" / "states")]), 0)


if __name__ == "__main__":
    unittest.main()
