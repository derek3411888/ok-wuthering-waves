import os
import sys
from pathlib import Path

import cv2


def main(video_path: str, out_dir: str):
    p = Path(video_path)
    if not p.exists():
        print(f"ERROR: Video not found: {p}")
        sys.exit(1)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(str(p))
    if not cap.isOpened():
        print(f"ERROR: cannot open video: {p}")
        sys.exit(2)

    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    duration = count / fps if fps > 0 else 0
    print(f"VIDEO: {p}")
    print(f"FPS: {fps} Frames: {count} Duration: {duration:.2f}s")

    targets = []
    for t in (1, 3, 5):  # sample 1s, 3s, 5s
        f = int(t * fps)
        if f < count:
            targets.append(f)
    last = int(max(0, count - 1 - fps))
    if last > 0:
        targets.append(last)
    if len(targets) == 0:  # fallback evenly
        step = max(1, count // 10) if count else 1
        targets = list(range(0, count, step))[:5]
    print(f"Targets: {targets}")

    wrote = []
    for i, f in enumerate(targets):
        cap.set(cv2.CAP_PROP_POS_FRAMES, f)
        ok, frame = cap.read()
        if not ok or frame is None:
            print(f"WARN: failed to read frame {f}")
            continue
        out_file = out / f"frame_{i}_{f}.png"
        cv2.imwrite(str(out_file), frame)
        wrote.append(str(out_file))
        print(f"WROTE: {out_file}")

    cap.release()
    if not wrote:
        print("No frames extracted")
        sys.exit(3)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python extract_frames.py <video_path> <out_dir>")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])

