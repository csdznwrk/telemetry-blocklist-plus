# Mobile Telemetry Blocklist

Blocks crash reporters, analytics SDKs, session replay tools, device fingerprinters, and background beacons — the stuff that silently phones home about your device state.

## What's covered

| Category | Examples |
|---|---|
| Crash / error reporting | Sentry, Bugsnag, Rollbar, Instabug, Crashlytics |
| Analytics SDKs | Amplitude, Mixpanel, Segment, Heap, PostHog, Pendo |
| Session replay | FullStory, LogRocket, Hotjar, Glassbox |
| APM / RUM | Datadog, New Relic, Dynatrace, Elastic APM |
| Mobile attribution | AppsFlyer, Adjust, Branch, Kochava |
| Feature flags (with telemetry) | Statsig, LaunchDarkly, Optimizely, Split |
| Google analytics stack | Google Analytics, GTM, Firebase, app-measurement.com |
| Device fingerprinting | ThreatMetrix, Arkose Labs |
| Data pipelines | Rudderstack, Tealium, Snowplow, Sumo Logic |
| Apple device telemetry | metrics.apple.com, xp.apple.com, diagnostics.apple.com |

## Import to NextDNS

```bash
pip install nextdnsctl
nextdnsctl auth YOUR_API_KEY
nextdnsctl denylist import YOUR_PROFILE_ID https://csdznwrk.github.io/telemetry-blocklist/domains.txt
```

## Files

- [`docs/domains.txt`](https://csdznwrk.github.io/telemetry-blocklist/domains.txt) — plain domain list, one per line
- `seeds.txt` — hand-curated base list
- `scripts/update.py` — fetches additional community telemetry sources

## Schedule

GitHub Actions rebuilds the list every 6 hours.
