#hashing
import json
import sys
import argparse
from pathlib import Path

from datetime import datetime, timezone
from .core import detect, scan_dir
from .types import DetectionResult, Candidate, Result


def to_detection_result(path: Path, res: Result) -> DetectionResult:
    cand = res.candidates[0] if res.candidates else Candidate(media_type="", confidence=0.0)
    size = path.stat().st_size if path.exists() else res.bytes_analyzed
    return DetectionResult(
        file_name=str(path),
        detected_type=cand.media_type,
        confidence_score=round(cand.confidence * 100, 2),
        detection_method=res.engine,
        timestamp=datetime.now(timezone.utc).isoformat(),

        errors=[res.error] if res.error else [],
        warnings=[],
        analysis_time=res.elapsed_ms,
        file_size=size,
        mime_type=cand.media_type,
        extension=cand.extension,

    )
def cmd_one(args: argparse.Namespace) -> None:
    res = detect(args.file, only=args.only, extensions=args.ext)

    report = to_detection_result(args.file, res)
    json.dump(report.model_dump(), sys.stdout, indent=None if args.raw else 2)
    sys.stdout.write("\n")
def cmd_all(args: argparse.Namespace) -> None:
    results = []
    for path, res in scan_dir(
        args.root,
        pattern=args.pattern,
        workers=args.workers,
        only=args.only,
        extensions=args.ext,
    ):
        report = to_detection_result(path, res)
        results.append(report.model_dump())
    json.dump(results, sys.stdout, indent=None if args.raw else 2)
    sys.stdout.write("\n")
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="fastback", description="fastback one|all")
    sub = p.add_subparsers(dest="cmd", required=True)
    p_one = sub.add_parser("one", help="Detect a single file")
    p_one.add_argument("file", type=Path, help="Path to file")
    p_one.add_argument(
        "--only",
        nargs="+",
        metavar="ENGINE",
        help="Restrict detection to these engines",
    )

    p_one.add_argument(
        "--ext",
        nargs="+",
        metavar="EXT",
        help="Only analyze files with these extensions",
    )


    p_one.add_argument("--raw", action="store_true", help="compact JSON")
    p_one.set_defaults(func=cmd_one)
    p_all = sub.add_parser("all", help="Scan directory recursively")
    p_all.add_argument("root", type=Path, help="root folder")
    p_all.add_argument("--pattern", default="**/*", help="glob (default **/*)")
    p_all.add_argument("--workers", type=int, default=8, help="thread pool size")
    p_all.add_argument(
        "--only",
        nargs="+",
        metavar="ENGINE",
        help="Restrict detection to these engines",
    )

    p_all.add_argument(
        "--ext",
        nargs="+",
        metavar="EXT",
        help="Only analyze files with these extensions",
    )


    p_all.add_argument("--raw", action="store_true", help="compact JSON")
    p_all.set_defaults(func=cmd_all)
    return p
def main() -> None:
    args = build_parser().parse_args()
    args.func(args)
if __name__ == "__main__":
    main()
