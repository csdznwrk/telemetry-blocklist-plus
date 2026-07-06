#!/usr/bin/env python3
"""
update.py — rebuilds docs/domains.txt from seeds.txt + community sources.
Runs in GitHub Actions on a schedule.
"""
import json
import os
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
SEEDS = ROOT / "seeds.txt"
DOCS  = ROOT / "docs"

# Community telemetry/tracker blocklists (plain-text, one domain per line)
COMMUNITY_SOURCES = [
    # DuckDuckGo tracker radar — telemetry heavy
    "https://raw.githubusercontent.com/duckduckgo/tracker-blocklists/main/app/androidtds.json",
    # Exodus privacy tracker list
    "https://raw.githubusercontent.com/nicehash/NiceHashExodus/master/blocklist.txt",
    # Peter Lowe's adservers list (catches many analytics endpoints)
    "https://pgl.yoyo.org/adservers/serverlist.php?hostformat=plain&showintro=0&mimetype=plaintext",
    # Steven Black unified hosts — analytics subset
    "https://raw.githubusercontent.com/StevenBlack/hosts/master/alternates/fakenews-gambling-porn-social/hosts",
]

# Focused plain-text sources (one domain per line, # comments ok)
PLAIN_SOURCES = [
    # Peter Lowe adservers
    "https://pgl.yoyo.org/adservers/serverlist.php?hostformat=plain&showintro=0&mimetype=plaintext",
    # AdGuard tracking servers
    "https://raw.githubusercontent.com/AdguardTeam/AdguardFilters/master/SpywareFilter/sections/tracking_servers.txt",
    # AssoEchap stalkerware C2 indicators (172 apps, maintained by security researchers)
    "https://raw.githubusercontent.com/AssoEchap/stalkerware-indicators/master/generated/hosts",
    # Blocklist Project malware domains
    "https://raw.githubusercontent.com/blocklistproject/Lists/master/malware.txt",
    # Shreshta Labs DNS Watchtower stalkerware IOCs
    "https://raw.githubusercontent.com/shreshta-labs/stalkerware-iocs/main/stalkerware",
    # AdGuard CNAME cloaking tracker list
    "https://raw.githubusercontent.com/AdguardTeam/cname-trackers/master/data/combined_disguised_trackers_justdomains.txt",
]

# Telemetry-specific keywords — only keep lines matching these
# For the AssoEchap + malware lists we want ALL domains (no keyword filter)
# Cap these at MAX_UNFILTERED_DOMAINS to prevent bloat (Blocklist Project is 400k+)
UNFILTERED_SOURCES = {
    "https://raw.githubusercontent.com/AssoEchap/stalkerware-indicators/master/generated/hosts",
    "https://raw.githubusercontent.com/blocklistproject/Lists/master/malware.txt",
    "https://raw.githubusercontent.com/shreshta-labs/stalkerware-iocs/main/stalkerware",
    "https://raw.githubusercontent.com/AdguardTeam/cname-trackers/master/data/combined_disguised_trackers_justdomains.txt",
}
MAX_UNFILTERED_DOMAINS = 5000

TELEMETRY_KEYWORDS = [
    "sentry", "crashlytics", "bugsnag", "rollbar", "instabug",
    "amplitude", "mixpanel", "segment", "heap", "fullstory", "logrocket",
    "hotjar", "newrelic", "nr-data", "dynatrace", "datadog", "datadoghq",
    "appsflyer", "adjust", "branch", "kochava", "braze", "intercom",
    "statsig", "launchdarkly", "optimizely", "split.io", "posthog", "pendo",
    "firebase", "app-measurement", "crashreport", "telemetry", "analytics",
    "metric", "tracker", "tracking", "ingest", "beacon", "rum.",
    "threatmetrix", "arkoselabs", "funcaptcha", "online-metrix",
    "glassbox", "appsee", "countly",
]


def load_seeds():
    domains = set()
    for line in SEEDS.read_text().splitlines():
        line = line.split("#")[0].strip().lower()
        if line and "." in line:
            domains.add(line)
    return domains


def fetch_url(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": "telemetry-blocklist/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode(errors="replace")
    except Exception as e:
        print(f"  ! fetch failed {url}: {e}")
        return ""


def parse_plain(text, unfiltered=False, max_domains=None):
    domains = set()
    for line in text.splitlines():
        line = line.split("#")[0].strip().lower()
        # strip hosts-file format (e.g. "0.0.0.0 domain.com")
        parts = line.split()
        domain = parts[-1] if parts else ""
        if domain and "." in domain and not domain.startswith("."):
            if unfiltered or any(kw in domain for kw in TELEMETRY_KEYWORDS):
                domains.add(domain)
                if max_domains and len(domains) >= max_domains:
                    break
    return domains


def main():
    DOCS.mkdir(exist_ok=True)
    print("Loading seeds...")
    domains = load_seeds()
    print(f"  {len(domains)} seed domains")

    for url in PLAIN_SOURCES:
        print(f"Fetching {url[:60]}...")
        text = fetch_url(url)
        unfiltered = url in UNFILTERED_SOURCES
        cap = MAX_UNFILTERED_DOMAINS if unfiltered else None
        found = parse_plain(text, unfiltered=unfiltered, max_domains=cap)
        print(f"  +{len(found)} domains{' (unfiltered, capped at ' + str(cap) + ')' if unfiltered else ''}")

        domains |= found
        time.sleep(1)

    # Deduplicate + sort
    domains = sorted(d for d in domains if d and "." in d)

    # Write domains.txt
    (DOCS / "domains.txt").write_text(
        "# Mobile Telemetry Blocklist\n"
        f"# Updated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n"
        f"# Domains: {len(domains)}\n\n" +
        "\n".join(domains) + "\n"
    )

    # Write metadata
    (DOCS / "metadata.json").write_text(json.dumps({
        "updated": datetime.now(timezone.utc).isoformat(),
        "domain_count": len(domains),
        "sources": len(PLAIN_SOURCES) + 1,
    }, indent=2))

    # Write index.html
    (DOCS / "index.html").write_text(f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Mobile Telemetry Blocklist</title>
<style>body{{font-family:system-ui;max-width:640px;margin:40px auto;padding:0 20px;color:#222}}</style>
</head>
<body>
<h1>Mobile Telemetry Blocklist</h1>
<p>Blocks crash reporters, analytics SDKs, session replay, and device fingerprinting endpoints.</p>
<p><strong>{len(domains)}</strong> domains &mdash; updated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}</p>
<h2>Import to NextDNS</h2>
<pre>pip install nextdnsctl
nextdnsctl auth YOUR_API_KEY
nextdnsctl denylist import YOUR_PROFILE_ID https://csdznwrk.github.io/telemetry-blocklist/domains.txt</pre>
<p><a href="domains.txt">domains.txt</a></p>
</body>
</html>""")

    print(f"\nDone: {len(domains)} total domains written to docs/")


if __name__ == "__main__":
    main()
