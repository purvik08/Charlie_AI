"""Run the Charlie AI suite and write tests/results.json (id -> status, detail)."""
import json, re, sys, time, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent)); sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_charlie_suite as S

class R(unittest.TextTestResult):
    def __init__(s, *a, **k): super().__init__(*a, **k); s.rec = {}
    def _id(s, t): m = re.search(r"test_((?:UT|IT|WB|BB)_\d+)", t.id()); return m.group(1).replace("_", "-") if m else t.id()
    def addSuccess(s, t): super().addSuccess(t); s.rec[s._id(t)] = ("Pass", "")
    def addFailure(s, t, e): super().addFailure(t, e); s.rec[s._id(t)] = ("Fail", str(e[1]).strip().splitlines()[-1][:200] if str(e[1]).strip() else "assertion failed")
    def addError(s, t, e): super().addError(t, e); s.rec[s._id(t)] = ("Fail", f"{e[0].__name__}: {str(e[1])[:200]}")
    def addSkip(s, t, r): super().addSkip(t, r); s.rec[s._id(t)] = ("Blocked", r.replace("Blocked: ", ""))

if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromModule(S)
    res = unittest.TextTestRunner(resultclass=R, verbosity=1, stream=sys.stdout).run(suite)
    out = {"results": dict(sorted(res.rec.items())), "metrics": S.METRICS, "python": sys.version.split()[0], "platform": sys.platform,
           "when": time.strftime("%Y-%m-%d %H:%M:%S")}
    Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).with_name("results.json")).write_text(json.dumps(out, indent=1))
    c = {}
    for v in res.rec.values(): c[v[0]] = c.get(v[0], 0) + 1
    print("SUMMARY", c); sys.exit(0 if not res.failures and not res.errors else 1)
