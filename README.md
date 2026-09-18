# Software Seeds

> Five unrelated small-business tool ideas, each sketched out as a single standalone script — early seeds, not finished products.

Software Seeds is a grab-bag of early prototypes exploring different small-business (SMB) tooling ideas: an acoustic anomaly monitor, an eBay arbitrage scanner, an offline PII auditor, a video-to-PDF documentation generator, and a social-content generator. Each one is a single file with no shared framework — they're proofs of concept, not a product line.

## Features
- **Echo Audit** (`echo_audit.py`) — listens for acoustic anomalies on industrial equipment via the microphone
- **Local Growth** (`local_growth.py`) — drafts social-media content for a small business
- **Part Sniper** (`part_sniper.py`) — scans eBay listings for resale-arbitrage opportunities
- **Privacy Sentry** (`privacy_sentry.py`) — scans local files for PII, fully offline, nothing leaves the machine
- **SOP Vision** (`sop_vision.py`) — turns a walkthrough video into a step-by-step PDF SOP document
- Each script is fully standalone — run any one independently, no shared setup beyond its own imports

## Stack
Python, standalone scripts (numpy, sounddevice, requests, and other per-script libraries — no shared structure).

## Getting started
**Requirements**
- Python 3.x; dependencies vary per script (numpy/sounddevice for audio, requests for scraping) — install as needed per file

**Run**
```bash
bash setup_software_seeds.sh
python echo_audit.py
python local_growth.py
python part_sniper.py
python privacy_sentry.py
python sop_vision.py
```
`setup_software_seeds.sh` is written for Raspberry Pi 5 / Linux (it uses `apt` and assumes a Pi setup) — on other OSes, skip it and `pip install` the per-script dependencies manually.

## Status
**Unmaintained / archived.** Personal project, published as-is — fork it, adapt it, take it over. No support or guarantees.

## License
[MIT](LICENSE) — free to use, fork, and build on.
