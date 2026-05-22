#!/usr/bin/env python3
"""
Upload a local file to fal storage to get a public URL.

Why this is useful:
- fal storage works EVEN when your fal generation account is locked
  ("exhausted balance" lock affects /queue/run not /storage/upload).
- The resulting URL can be consumed by any image-to-video provider
  (PiAPI, Replicate, Krea via Playwright) without paying for storage.
- Free, no upload limits in practice, persistent for at least weeks.

Usage:
    export FAL_KEY="..."
    python3 fal_storage_upload.py path/to/image.png
"""
import json
import mimetypes
import os
import sys
import urllib.request


def fal_upload(local_path):
    fal_key = os.environ.get("FAL_KEY")
    if not fal_key:
        raise SystemExit("Set FAL_KEY in environment.")

    fname = os.path.basename(local_path)
    mime = mimetypes.guess_type(fname)[0] or "application/octet-stream"

    init_body = json.dumps({"file_name": fname, "content_type": mime}).encode()
    req = urllib.request.Request(
        "https://rest.alpha.fal.ai/storage/upload/initiate",
        data=init_body,
        headers={
            "Authorization": f"Key {fal_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        d = json.load(r)
    upload_url = d["upload_url"]
    file_url = d["file_url"]

    with open(local_path, "rb") as f:
        data = f.read()
    put = urllib.request.Request(
        upload_url, data=data, headers={"Content-Type": mime}, method="PUT"
    )
    with urllib.request.urlopen(put, timeout=120) as r:
        if r.status not in (200, 201, 204):
            raise RuntimeError(f"PUT failed status={r.status}")
    return file_url


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: python3 fal_storage_upload.py path/to/file", file=sys.stderr)
        sys.exit(1)
    print(fal_upload(sys.argv[1]))
