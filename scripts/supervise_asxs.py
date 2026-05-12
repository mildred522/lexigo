import json
import os
import pathlib
import subprocess
import time
from datetime import datetime


WORKDIR = pathlib.Path(__file__).resolve().parents[1]
PYTHON = r"C:\Python313\python.exe"
BASE_URL = "https://api.asxs.top/v1"
LOG_PATH = WORKDIR / "artifacts" / "reports" / "asxs-supervisor.log"
CACHE_PATH = WORKDIR / "artifacts" / "reports" / "translation-cache.json"
WORKER_STDOUT = WORKDIR / "artifacts" / "reports" / "asxs-longrun.stdout.log"
WORKER_STDERR = WORKDIR / "artifacts" / "reports" / "asxs-longrun.stderr.log"


def log(message: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")


def pending_count() -> int:
    cache = set()
    if CACHE_PATH.exists():
        payload = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
        for item in payload:
            if item.get("source_lang") == "en" and item.get("target_lang") == "zh":
                text = item.get("text", "")
                if text:
                    cache.add(text)

    pending = set()
    input_path = WORKDIR / "artifacts" / "translated" / "jmdict_words.jsonl"
    with input_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("language") != "JA":
                continue
            if row.get("meaning_zh", "").strip():
                continue
            gloss = row.get("meaning_source_text", "").strip()
            if gloss and gloss not in cache:
                pending.add(gloss)
    return len(pending)


def worker_pid() -> int | None:
    probe = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-Command",
            "(Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'python.exe' -and $_.CommandLine -like '*scripts/continue_translate_asxs.py*' -and $_.CommandLine -like '*https://api.asxs.top/v1*' } | Select-Object -First 1 -ExpandProperty ProcessId)",
        ],
        cwd=WORKDIR,
        capture_output=True,
        text=True,
    )
    text = (probe.stdout or "").strip()
    return int(text) if text.isdigit() else None


def start_worker() -> None:
    api_key = os.environ.get("ASXS_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("ASXS_API_KEY is required to start the translation worker.")
    with WORKER_STDOUT.open("ab") as out_handle, WORKER_STDERR.open("ab") as err_handle:
        proc = subprocess.Popen(
            [
                PYTHON,
                "scripts/continue_translate_asxs.py",
                "--api-key",
                api_key,
                "--base-url",
                BASE_URL,
                "--model",
                "gpt-5.4-mini",
                "--max-seconds",
                "7200",
                "--batch-size",
                "4",
                "--min-batch-size",
                "1",
                "--pause-seconds",
                "0.2",
                "--retry-sleep-seconds",
                "2.5",
                "--max-retries-per-batch",
                "8",
                "--flush-every",
                "16",
                "--rewrite-output",
                "--report",
                "artifacts/reports/asxs-progress-report.json",
            ],
            cwd=WORKDIR,
            stdout=out_handle,
            stderr=err_handle,
        )
    log(f"started worker pid={proc.pid}")


def stop_worker(pid: int) -> None:
    subprocess.run(
        ["powershell", "-NoProfile", "-Command", f"Stop-Process -Id {pid} -Force"],
        cwd=WORKDIR,
        capture_output=True,
    )
    log(f"stopped worker pid={pid}")


def main() -> None:
    log("supervisor booted")
    last_cache_mtime = CACHE_PATH.stat().st_mtime if CACHE_PATH.exists() else 0.0
    stale_checks = 0

    while True:
        try:
            pending = pending_count()
        except Exception as exc:
            log(f"pending_count_error={exc}")
            time.sleep(60)
            continue

        pid = worker_pid()
        if pending <= 0:
            if pid:
                stop_worker(pid)
            log("pending reached zero; supervisor exiting")
            break

        if pid is None:
            start_worker()
            time.sleep(10)
            pid = worker_pid()

        if CACHE_PATH.exists():
            mtime = CACHE_PATH.stat().st_mtime
            if mtime > last_cache_mtime:
                last_cache_mtime = mtime
                stale_checks = 0
            else:
                stale_checks += 1
        else:
            stale_checks += 1

        log(f"heartbeat pending={pending} worker={pid} stale_checks={stale_checks}")

        if pid and stale_checks >= 20:
            stop_worker(pid)
            stale_checks = 0
            time.sleep(5)

        time.sleep(60)


if __name__ == "__main__":
    main()
