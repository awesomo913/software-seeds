#!/bin/bash
#==============================================================
# Software Seeds — Setup Script for Raspberry Pi 5
# Installs dependencies, checks Ollama, creates folders, sets cron
#==============================================================

set -e

echo "============================================================"
echo "  Software Seeds — Setup Script"
echo "  Target: Raspberry Pi 5 (16GB RAM, NVMe SSD)"
echo "============================================================"
echo ""

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# ── Step 1: System dependencies ─────────────────────────────────
echo "[1/5] Installing system dependencies..."
sudo apt update -y
sudo apt install -y python3-pip python3-venv ffmpeg portaudio19-dev

# ── Step 2: Python dependencies ─────────────────────────────────
echo ""
echo "[2/5] Installing Python packages..."
pip3 install --break-system-packages \
    numpy \
    sounddevice \
    requests \
    PyPDF2 \
    python-docx \
    markdown \
    weasyprint \
    2>/dev/null || \
pip3 install \
    numpy \
    sounddevice \
    requests \
    PyPDF2 \
    python-docx \
    markdown \
    weasyprint

echo "  Python packages installed."

# ── Step 3: Check Ollama ────────────────────────────────────────
echo ""
echo "[3/5] Checking Ollama..."
if command -v ollama &> /dev/null; then
    echo "  Ollama found: $(ollama --version)"

    # Check if Ollama service is running
    if pgrep -x "ollama" > /dev/null; then
        echo "  Ollama service is running."
    else
        echo "  Starting Ollama service..."
        ollama serve &
        sleep 3
    fi

    # Pull recommended models
    echo "  Pulling recommended models..."
    echo "  (This may take a while on first run)"
    ollama pull llama3 2>/dev/null && echo "    llama3 ready" || echo "    llama3 pull failed (may need manual pull)"
    ollama pull moondream 2>/dev/null && echo "    moondream ready" || echo "    moondream pull failed (may need manual pull)"
else
    echo "  Ollama not installed. Installing..."
    curl -fsSL https://ollama.com/install.sh | sh
    echo "  Ollama installed. Start with: ollama serve"
    echo "  Then pull models: ollama pull llama3 && ollama pull moondream"
fi

# ── Step 4: Create required folders ─────────────────────────────
echo ""
echo "[4/5] Creating required folders..."
mkdir -p "$SCRIPT_DIR/watch_folder"
mkdir -p "$SCRIPT_DIR/job_photos"
mkdir -p "$SCRIPT_DIR/sop_frames"
echo "  Created: watch_folder/ job_photos/ sop_frames/"

# ── Step 5: Set up crontab for part_sniper ──────────────────────
echo ""
echo "[5/5] Setting up crontab for Part Sniper..."
CRON_CMD="0 */6 * * * cd $SCRIPT_DIR && python3 part_sniper.py >> /tmp/part_sniper.log 2>&1"

# Check if cron entry already exists
if crontab -l 2>/dev/null | grep -q "part_sniper.py"; then
    echo "  Part Sniper cron entry already exists."
else
    (crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -
    echo "  Added cron: runs every 6 hours"
fi

# ── Summary ─────────────────────────────────────────────────────
echo ""
echo "============================================================"
echo "  Setup complete!"
echo ""
echo "  Workers:"
echo "    1. echo_audit.py    — Industrial Acoustic Guardian"
echo "    2. part_sniper.py   — eBay Resale Arbitrage (cron: 6h)"
echo "    3. privacy_sentry.py — PII Compliance Auditor"
echo "    4. sop_vision.py    — Video -> SOP Generator"
echo "    5. local_growth.py  — Social Media Content Fabricator"
echo ""
echo "  Quick start:"
echo "    python3 echo_audit.py          # continuous mic monitoring"
echo "    python3 part_sniper.py         # one-shot scoring"
echo "    python3 privacy_sentry.py      # scan watch_folder/"
echo "    python3 sop_vision.py video.mp4 # generate SOP from video"
echo "    python3 local_growth.py        # generate social posts"
echo "============================================================"
