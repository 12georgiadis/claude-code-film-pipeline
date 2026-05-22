#!/usr/bin/env python3
"""
PiAPI Seedance 2 batch launcher — image-to-video mode `first_last_frames`.

Notes from the field:
- PiAPI free/basic plan has a HARD LIMIT of 2 concurrent active tasks.
  Submitting more returns: "active task count 2 has reached the plan limit"
- PiAPI is behind Cloudflare WAF which BANS Python-urllib User-Agent by default.
  Always set a browser User-Agent in headers, otherwise 403.
- Image-to-video on Seedance 2 requires:
    model: "seedance"
    task_type: "seedance-2" or "seedance-2-fast"
    input.mode: "first_last_frames"
    input.image_urls: [URL] (single = i2v, two = transition first→last)
- Polling: completed task has video URL at `data.output.video`
  (NOT `data.output.video_url` — a common documentation mismatch)
- Zombie pending tasks block the active slot indefinitely; cancel via
  DELETE /api/v1/task/{task_id}

Usage:
    python3 piapi_seedance2_launcher.py --plans plans.json --output-dir ./output/

Plan JSON schema:
    [{
      "id": "MY_PLAN_01",
      "image_url": "https://...public.png",
      "end_image_url": null,  # optional, for first-last transition
      "prompt": "Static slow water rising on yellow house...",
      "duration": 5,
      "resolution": "720p",
      "tier": "fast",         # or "pro"
      "aspect_ratio": "16:9"
    }, ...]
"""
import argparse
import json
import os
import pathlib
import time
import urllib.request

PIAPI_KEY = os.environ.get("PIAPI_KEY", "")  # set PIAPI_KEY in env
BASE = "https://api.piapi.ai/api/v1"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
MAX_ACTIVE = 2


def _req(method, url, body=None):
    headers = {"x-api-key": PIAPI_KEY, "User-Agent": UA}
    if body is not None:
        headers["Content-Type"] = "application/json"
        body = json.dumps(body).encode()
    return urllib.request.Request(url, data=body, headers=headers, method=method)


def submit_task(plan):
    task_type = "seedance-2-fast" if plan.get("tier") == "fast" else "seedance-2"
    image_urls = [plan["image_url"]]
    if plan.get("end_image_url"):
        image_urls.append(plan["end_image_url"])
    payload = {
        "model": "seedance",
        "task_type": task_type,
        "input": {
            "mode": "first_last_frames",
            "prompt": plan["prompt"],
            "duration": plan.get("duration", 5),
            "aspect_ratio": plan.get("aspect_ratio", "16:9"),
            "resolution": plan.get("resolution", "720p"),
            "image_urls": image_urls,
        },
    }
    req = _req("POST", f"{BASE}/task", payload)
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    if data.get("message") != "success":
        raise RuntimeError(data.get("message"))
    return data.get("data", {}).get("task_id")


def get_task(task_id):
    req = _req("GET", f"{BASE}/task/{task_id}")
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.load(r).get("data", {})


def cancel_task(task_id):
    """Cancel a zombie pending task to free up the slot."""
    req = _req("DELETE", f"{BASE}/task/{task_id}")
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.load(r)


def is_done(status):
    return (status or "").lower() in ("completed", "success", "failed", "error")


def download(url, path):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=120) as r, open(path, "wb") as f:
        f.write(r.read())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plans", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--poll-interval", type=float, default=10.0)
    args = parser.parse_args()

    if not PIAPI_KEY:
        raise SystemExit("Set PIAPI_KEY in environment.")

    plans = json.loads(pathlib.Path(args.plans).read_text())
    output_dir = pathlib.Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"[+] Launching {len(plans)} plans on PiAPI (limit {MAX_ACTIVE} concurrent)...", flush=True)

    pending = [p for p in plans if not (output_dir / f"{p['id']}.mp4").exists()]
    print(f"[+] {len(plans) - len(pending)} already downloaded, {len(pending)} to do", flush=True)

    in_flight = {}
    results = []
    queue = list(pending)

    while queue or in_flight:
        while queue and len(in_flight) < MAX_ACTIVE:
            plan = queue.pop(0)
            try:
                tid = submit_task(plan)
                in_flight[tid] = plan
                print(f"  [SUBMIT] {plan['id']:>34} -> {tid}", flush=True)
                time.sleep(1.0)
            except Exception as e:
                msg = str(e)
                if "plan limit" in msg or "429" in msg:
                    queue.insert(0, plan)
                    time.sleep(15)
                    break
                print(f"  [FAIL  ] {plan['id']:>34} {msg}", flush=True)
                results.append({"plan_id": plan["id"], "status": "SUBMIT_FAILED", "error": msg})

        if not in_flight:
            continue

        time.sleep(args.poll_interval)
        done_ids = []
        for tid, plan in list(in_flight.items()):
            try:
                d = get_task(tid)
            except Exception as e:
                print(f"  [POLLERR] {plan['id']} {e}", flush=True)
                continue
            status = (d.get("status") or "").lower()
            if not is_done(status):
                continue
            done_ids.append(tid)
            if status in ("completed", "success"):
                out = d.get("output", {}) or {}
                url = out.get("video") or out.get("video_url")
                if not url:
                    results.append({"plan_id": plan["id"], "status": "NO_VIDEO_URL", "task_id": tid})
                    continue
                path = output_dir / f"{plan['id']}.mp4"
                try:
                    download(url, path)
                    print(f"  [OK    ] {plan['id']:>34} -> {path}", flush=True)
                    results.append({"plan_id": plan["id"], "status": "OK", "path": str(path), "task_id": tid})
                except Exception as e:
                    results.append({"plan_id": plan["id"], "status": "DOWNLOAD_FAILED", "error": str(e), "url": url, "task_id": tid})
            else:
                err = (d.get("error") or {}).get("message", "unknown")
                results.append({"plan_id": plan["id"], "status": "FAILED", "error": err, "task_id": tid})

        for tid in done_ids:
            in_flight.pop(tid, None)

    summary = output_dir / f"piapi_batch_{int(time.time())}.json"
    summary.write_text(json.dumps(results, indent=2))
    ok = sum(1 for r in results if r["status"] == "OK")
    print(f"\n[+] Done: {ok}/{len(results)} OK. Summary: {summary}", flush=True)


if __name__ == "__main__":
    main()
