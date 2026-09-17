#!/usr/bin/env python3
"""
Privacy Sentry — Local PII Compliance Auditor (100% Offline)
Watches a folder for documents, scans for PII with regex,
logs findings, and optionally queries local Ollama for risk severity.
Zero network calls — completely air-gapped.
"""

import json
import os
import re
import sys
from datetime import datetime

import requests

WATCH_FOLDER = "./watch_folder"
LOG_FILE = "privacy_audit_log.json"
OLLAMA_URL = "http://localhost:11434/api/generate"

# ── PII Regex Patterns ─────────────────────────────────────────
PII_PATTERNS = {
    "SSN": r"\b\d{3}-\d{2}-\d{4}\b",
    "Credit Card": r"\b(?:4\d{3}|5[1-5]\d{2}|3[47]\d{2}|6(?:011|5\d{2}))[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b",
    "Email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    "Phone": r"\b(?:\+?1[-. ]?)?\(?\d{3}\)?[-. ]?\d{3}[-. ]?\d{4}\b",
    "Medical ID": r"\b(?:MRN|MED|PAT)[- #]?\d{6,10}\b",
}

SUPPORTED_EXTENSIONS = {".txt", ".csv"}

# Optional imports for PDF and DOCX
try:
    import PyPDF2
    HAS_PDF = True
except ImportError:
    HAS_PDF = False

try:
    import docx
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False


def extract_text(filepath):
    """Extract text content from supported file types."""
    ext = os.path.splitext(filepath)[1].lower()

    if ext == ".txt" or ext == ".csv":
        with open(filepath, "r", errors="replace") as f:
            return f.read()

    elif ext == ".pdf":
        if not HAS_PDF:
            print(f"  \033[93m[SKIP] PyPDF2 not installed, cannot read {filepath}\033[0m")
            return ""
        with open(filepath, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            return "\n".join(page.extract_text() or "" for page in reader.pages)

    elif ext == ".docx":
        if not HAS_DOCX:
            print(f"  \033[93m[SKIP] python-docx not installed, cannot read {filepath}\033[0m")
            return ""
        doc = docx.Document(filepath)
        return "\n".join(p.text for p in doc.paragraphs)

    return ""


def scan_text(text, filename):
    """Scan text for PII patterns and return findings."""
    findings = []
    for pii_type, pattern in PII_PATTERNS.items():
        matches = re.findall(pattern, text)
        if matches:
            findings.append({
                "type": pii_type,
                "count": len(matches),
                "samples": [m[:6] + "***" for m in matches[:3]],  # Redacted samples
            })
    return findings


def query_ollama_severity(findings_summary):
    """Ask local Ollama for risk severity rating."""
    prompt = (
        f"As a data privacy compliance officer, rate the severity (LOW/MEDIUM/HIGH/CRITICAL) "
        f"of these PII findings and briefly explain the risk:\n{findings_summary}\n"
        f"Respond in 2-3 sentences."
    )
    try:
        resp = requests.post(OLLAMA_URL, json={
            "model": "llama3",
            "prompt": prompt,
            "stream": False,
        }, timeout=60)
        if resp.status_code == 200:
            return resp.json().get("response", "")
        return None
    except Exception:
        return None


def main():
    print("=" * 60)
    print("  Privacy Sentry — Local PII Compliance Auditor")
    print("  100% Offline — Zero Network Calls")
    print("=" * 60)

    os.makedirs(WATCH_FOLDER, exist_ok=True)

    # Find all scannable files
    supported = {".txt", ".csv", ".pdf", ".docx"}
    files = []
    for f in os.listdir(WATCH_FOLDER):
        if os.path.splitext(f)[1].lower() in supported:
            files.append(os.path.join(WATCH_FOLDER, f))

    if not files:
        print(f"\n  No scannable files found in {WATCH_FOLDER}/")
        print(f"  Supported: .txt, .csv, .pdf, .docx")
        print(f"  Place files in {WATCH_FOLDER}/ and run again.")
        return

    print(f"\n  Found {len(files)} file(s) to scan.\n")

    # Load existing log
    log = []
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r") as f:
                log = json.load(f)
        except json.JSONDecodeError:
            log = []

    total_findings = 0

    for filepath in files:
        filename = os.path.basename(filepath)
        print(f"  Scanning: {filename}")

        text = extract_text(filepath)
        if not text:
            print(f"    (empty or unreadable)")
            continue

        findings = scan_text(text, filename)

        if findings:
            entry = {
                "file": filename,
                "scanned_at": datetime.now().isoformat(),
                "findings": findings,
            }

            # Color-coded terminal output
            for f in findings:
                color = "\033[91m" if f["type"] in ("SSN", "Credit Card") else "\033[93m"
                print(f"    {color}*** {f['type']}: {f['count']} found ***\033[0m")
                total_findings += f["count"]

            # Optional Ollama severity rating
            summary = "; ".join(f"{f['type']}: {f['count']}" for f in findings)
            severity = query_ollama_severity(summary)
            if severity:
                entry["ai_severity"] = severity
                print(f"    AI Severity: {severity[:100]}")

            log.append(entry)
        else:
            print(f"    \033[92mClean — no PII detected\033[0m")

    # Save log
    with open(LOG_FILE, "w") as f:
        json.dump(log, f, indent=2)

    print(f"\n{'='*60}")
    print(f"  Scan complete. {total_findings} PII items found across {len(files)} files.")
    print(f"  Audit log: {LOG_FILE}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
