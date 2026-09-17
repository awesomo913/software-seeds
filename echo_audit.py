#!/usr/bin/env python3
"""
Echo Audit — Industrial Acoustic Guardian
Listens via USB mic, runs FFT analysis every 5 seconds, detects anomalies,
logs findings, and optionally queries local Ollama for repair plans.
"""

import json
import time
import signal
import sys
from datetime import datetime

import numpy as np
import sounddevice as sd
import requests

LOG_FILE = "acoustic_log.json"
OLLAMA_URL = "http://localhost:11434/api/generate"
SAMPLE_RATE = 44100
DURATION = 5  # seconds per capture window
HIGH_FREQ_THRESHOLD = 0.05
RMS_THRESHOLD = 0.3

running = True


def signal_handler(sig, frame):
    global running
    print("\n[Echo Audit] Shutting down gracefully...")
    running = False


signal.signal(signal.SIGINT, signal_handler)


def load_log():
    try:
        with open(LOG_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_log(entries):
    with open(LOG_FILE, "w") as f:
        json.dump(entries, f, indent=2)


def capture_audio():
    """Record audio for DURATION seconds and return as numpy array."""
    try:
        audio = sd.rec(int(DURATION * SAMPLE_RATE), samplerate=SAMPLE_RATE,
                       channels=1, dtype="float32")
        sd.wait()
        return audio.flatten()
    except Exception as e:
        print(f"[MIC ERROR] {e}")
        return None


def analyze_fft(audio):
    """Run FFT analysis and check for anomalies."""
    fft_vals = np.abs(np.fft.rfft(audio))
    freqs = np.fft.rfftfreq(len(audio), 1.0 / SAMPLE_RATE)

    # High-frequency band (>5kHz) — bearing grind, hydraulic hiss
    high_mask = freqs > 5000
    high_freq_mean = np.mean(fft_vals[high_mask]) if np.any(high_mask) else 0

    # RMS — overall loudness (impact / mechanical failure)
    rms = np.sqrt(np.mean(audio ** 2))

    anomalies = []
    if high_freq_mean > HIGH_FREQ_THRESHOLD:
        anomalies.append(f"High-frequency anomaly: mean={high_freq_mean:.4f} "
                         f"(threshold={HIGH_FREQ_THRESHOLD})")
    if rms > RMS_THRESHOLD:
        anomalies.append(f"RMS anomaly: {rms:.4f} (threshold={RMS_THRESHOLD})")

    return {
        "rms": float(rms),
        "high_freq_mean": float(high_freq_mean),
        "peak_freq": float(freqs[np.argmax(fft_vals)]),
        "anomalies": anomalies,
    }


def query_ollama(anomaly_description):
    """Ask local Ollama for a 3-step repair plan."""
    prompt = (
        f"An industrial acoustic sensor detected this anomaly:\n"
        f"{anomaly_description}\n\n"
        f"Provide a concise 3-step repair/investigation plan for a maintenance technician."
    )
    try:
        resp = requests.post(OLLAMA_URL, json={
            "model": "llama3",
            "prompt": prompt,
            "stream": False,
        }, timeout=60)
        if resp.status_code == 200:
            return resp.json().get("response", "No response from model.")
        return f"Ollama returned status {resp.status_code}"
    except requests.ConnectionError:
        return "[Ollama not available — skipping AI analysis]"
    except Exception as e:
        return f"[Ollama error: {e}]"


def main():
    print("=" * 60)
    print("  Echo Audit — Industrial Acoustic Guardian")
    print("  Listening via USB mic... Press Ctrl+C to stop.")
    print("=" * 60)

    log = load_log()

    while running:
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Capturing {DURATION}s audio...")
        audio = capture_audio()
        if audio is None:
            time.sleep(DURATION)
            continue

        analysis = analyze_fft(audio)
        print(f"  RMS: {analysis['rms']:.4f} | High-Freq Mean: {analysis['high_freq_mean']:.4f} "
              f"| Peak: {analysis['peak_freq']:.0f} Hz")

        if analysis["anomalies"]:
            print(f"  \033[91m*** ANOMALY DETECTED ***\033[0m")
            for a in analysis["anomalies"]:
                print(f"    - {a}")

            entry = {
                "timestamp": datetime.now().isoformat(),
                "rms": analysis["rms"],
                "high_freq_mean": analysis["high_freq_mean"],
                "peak_freq": analysis["peak_freq"],
                "anomalies": analysis["anomalies"],
            }

            # Query Ollama for repair plan
            desc = "; ".join(analysis["anomalies"])
            print("  Querying Ollama for repair plan...")
            plan = query_ollama(desc)
            entry["repair_plan"] = plan
            print(f"  AI Plan: {plan[:200]}...")

            log.append(entry)
            save_log(log)
            print(f"  Logged to {LOG_FILE} ({len(log)} total entries)")
        else:
            print("  \033[92mNormal\033[0m")

    print(f"\n[Echo Audit] Stopped. {len(log)} anomalies logged to {LOG_FILE}")


if __name__ == "__main__":
    main()
