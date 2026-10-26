"""Decode a video and report measured dimensions, frame timing, and optional freeze equality.

Uses only Python's standard library and an existing FFmpeg binary. Expected
settings are optional; fractional FPS can be specified as 30000/1001.
"""
import argparse
import hashlib
import json
import re
import subprocess
from fractions import Fraction
from pathlib import Path


def run(command):
    return subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))


def rgb_frame(ffmpeg, source, index=None):
    command = [ffmpeg, "-hide_banner", "-loglevel", "error", "-xerror", "-i", str(source), "-map", "0:v:0"]
    if index is not None:
        command.extend(["-vf", f"select=eq(n\\,{index})"])
    command.extend(["-frames:v", "1", "-fps_mode", "passthrough", "-pix_fmt", "rgb24", "-f", "rawvideo", "pipe:1"])
    result = run(command)
    if result.returncode:
        raise RuntimeError(result.stderr.decode("utf-8", errors="replace")[-2000:])
    return result.stdout


def verify(args):
    result = run([args.ffmpeg, "-hide_banner", "-loglevel", "info", "-xerror", "-err_detect", "explode",
                  "-i", str(args.video), "-map", "0:v:0", "-an", "-vf", "showinfo",
                  "-fps_mode", "passthrough", "-f", "null", "-"])
    log = result.stderr.decode("utf-8", errors="replace")
    rows = [(int(n), int(pts), int(width), int(height)) for n, pts, width, height in
            re.findall(r"\bn:\s*(\d+)\s+pts:\s*(-?\d+).*?\bs:(\d+)x(\d+)", log)]
    config = re.search(r"config in time_base:\s*(\d+)/(\d+), frame_rate:\s*(\d+)/(\d+)", log)
    issues = []
    report = {"video": str(args.video.resolve()), "pass_check": False,
              "all_frames_decoded": result.returncode == 0 and bool(rows),
              "decoded_frames": len(rows), "issues": issues}
    if result.returncode:
        issues.append("FFmpeg decoding failed: " + log[-1500:])
    if not rows or not config:
        issues.append("No complete frame/timing information could be measured.")
        return report
    tb = Fraction(int(config[1]), int(config[2]))
    fps = Fraction(int(config[3]), int(config[4])) if int(config[4]) and int(config[3]) else None
    pts = [row[1] for row in rows]
    sizes = sorted({(row[2], row[3]) for row in rows})
    ordered = all(row[0] == index for index, row in enumerate(rows))
    monotonic = all(b > a for a, b in zip(pts, pts[1:]))
    uniform = (all(abs(float((stamp - pts[0]) * tb - Fraction(index, 1) / fps))
                   <= float(tb) / 2 + 1e-6 for index, stamp in enumerate(pts))
               if fps and len(rows) > 1 else None)
    report.update({"dimensions": [list(size) for size in sizes], "fps_rational": str(fps) if fps else None,
                   "fps": float(fps) if fps else None, "time_base": str(tb),
                   "first_timestamp_s": float(pts[0] * tb), "last_timestamp_s": float(pts[-1] * tb),
                   "duration_by_frames_s": len(rows) / float(fps) if fps else None,
                   "sequential_frame_numbers": ordered, "timestamps_strictly_increasing": monotonic,
                   "constant_frame_timing": uniform})
    if not ordered or not monotonic:
        issues.append("Decoded frame indices or timestamps are discontinuous.")
    if args.expected_frames is not None and len(rows) != args.expected_frames:
        issues.append(f"Expected {args.expected_frames} frames; decoded {len(rows)}.")
    if args.expected_width is not None and any(width != args.expected_width for width, _ in sizes):
        issues.append("Video width differs from the requested width.")
    if args.expected_height is not None and any(height != args.expected_height for _, height in sizes):
        issues.append("Video height differs from the requested height.")
    if args.expected_fps is not None:
        expected = Fraction(args.expected_fps)
        if not fps or abs(float(fps - expected)) > max(1e-6, float(expected) * 1e-6) + 1e-9:
            issues.append("Frame rate differs from the requested rate.")
        if uniform is False:
            issues.append("Frame timestamps do not form the requested constant-rate timeline.")
    if args.freeze:
        if len(sizes) != 1:
            issues.append("Cannot compare freeze for a video with changing dimensions.")
        else:
            last = rgb_frame(args.ffmpeg, args.video, len(rows) - 1)
            freeze = rgb_frame(args.ffmpeg, args.freeze)
            width, height = sizes[0]
            match = len(last) == width * height * 3 and last == freeze
            report["freeze"] = {"path": str(args.freeze.resolve()), "matches_decoded_last_frame": match,
                                "last_frame_rgb_sha256": hashlib.sha256(last).hexdigest(),
                                "freeze_rgb_sha256": hashlib.sha256(freeze).hexdigest()}
            if not match:
                issues.append("Freeze pixels differ from the decoded last video frame.")
    report["pass_check"] = not issues
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ffmpeg", default="ffmpeg")
    parser.add_argument("--video", required=True, type=Path)
    parser.add_argument("--expected-width", type=int)
    parser.add_argument("--expected-height", type=int)
    parser.add_argument("--expected-fps", help="For example 24 or 30000/1001.")
    parser.add_argument("--expected-frames", type=int)
    parser.add_argument("--freeze", type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()
    for key in ("expected_width", "expected_height", "expected_frames"):
        if getattr(args, key) is not None and getattr(args, key) <= 0:
            parser.error(key.replace("_", "-") + " must be positive")
    if args.expected_fps is not None:
        try:
            if Fraction(args.expected_fps) <= 0:
                raise ValueError()
        except (ValueError, ZeroDivisionError):
            parser.error("--expected-fps must be a positive number or fraction")
    try:
        report = verify(args)
    except (OSError, RuntimeError, ValueError) as error:
        report = {"video": str(args.video), "pass_check": False, "issues": [str(error)]}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"pass_check": report["pass_check"], "report": str(args.report),
                      "issues": report["issues"]}, ensure_ascii=False), flush=True)
    return 0 if report["pass_check"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
