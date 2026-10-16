#!/usr/bin/env python3
"""Write a job spec and submit it to the durable runner (scripts/durable/job_runner.ps1, as a Windows scheduled task).

  python scripts/durable/submit.py --name audit1 --timeout-min 40 --stop-strata --restore-strata \\
      --env STRATA_GLM_LANE_AUDIT=200 -- E:\\oss\\project-maya\\.venv\\Scripts\\python.exe scripts\\maya_probe.py ...

Everything after ``--`` is the command (exe first). Output goes to results/phase4/logs/<name>/ (git-ignored): status.json,
stdout.log, stderr.log, runner.log, heartbeat.txt. ``--wait`` blocks until status.json shows an end time.
Stop a job early with an empty file named STOP in its output directory.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--name", required=True)
    ap.add_argument("--timeout-min", type=float, required=True)
    ap.add_argument("--cwd", default=str(ROOT))
    ap.add_argument("--out-dir", default=None)
    ap.add_argument("--env", action="append", default=[], metavar="KEY=VALUE")
    ap.add_argument("--stop-strata", action="store_true")
    ap.add_argument("--restore-strata", action="store_true")
    ap.add_argument("--wait", action="store_true")
    ap.add_argument("cmd", nargs=argparse.REMAINDER)
    a = ap.parse_args(argv)
    cmd = a.cmd[1:] if a.cmd[:1] == ["--"] else a.cmd
    if not cmd:
        ap.error("no command after --")
    out_dir = Path(a.out_dir) if a.out_dir else ROOT / "results" / "phase4" / "logs" / a.name
    out_dir.mkdir(parents=True, exist_ok=True)
    for stale in ("status.json", "STOP"):
        (out_dir / stale).unlink(missing_ok=True)
    spec = {"name": a.name, "exe": cmd[0], "args": cmd[1:], "cwd": a.cwd, "out_dir": str(out_dir),
            "timeout_min": a.timeout_min, "env": dict(kv.split("=", 1) for kv in a.env),
            "stop_strata": a.stop_strata, "restore_strata": a.restore_strata}
    spec_path = out_dir.parent / f"{a.name}.spec.json"
    spec_path.write_text(json.dumps(spec, indent=1), encoding="utf-8")
    r = subprocess.run(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                        str(ROOT / "scripts" / "durable" / "job_submit.ps1"), "-SpecFile", str(spec_path)],
                       capture_output=True, text=True, timeout=300)
    print(r.stdout.strip())
    if r.returncode != 0:
        print(r.stderr, file=sys.stderr)
        return r.returncode
    if a.wait:
        while True:
            try:
                st = json.loads((out_dir / "status.json").read_text(encoding="utf-8-sig"))
                if st.get("ended"):
                    print(json.dumps(st))
                    return 0 if st.get("state") == "finished" and st.get("exit_code") == 0 else 1
            except (OSError, ValueError):
                pass
            time.sleep(5)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
