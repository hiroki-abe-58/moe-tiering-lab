#!/usr/bin/env python3
"""Fixed quality suite for A/B arms of the same engine (greedy, non-thinking chat template, one engine start per run).

  <maya>\\.venv\\Scripts\\python.exe scripts\\maya_quality.py --maya-dir <maya> --config maya-xxx.json \\
      --env STRATA_GLM_RAM_GB=42 --env STRATA_GLM_CPU_LANE=0 --label t42L0 --out results/phase3/exp5-determinism/q-t42L0.json

~40 short tasks in 5 families (math, code, json, ja, en); each is graded by a program (integer answer, unit tests run in an
isolated ``python -I`` subprocess, JSON schema checks, constraint checks). Reports pass rates per family plus every output.
With ~40 tasks the pass rate has a sampling error of several points: it can show a gross regression, not prove equality.
Maya must be stopped (it needs the GPU).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

N_NEW = 320


# ---------------------------------------------------------------- graders
def last_int(text: str):
    m = re.findall(r"Answer:\s*\**\s*(-?[\d,]+)", text)
    if not m:
        m = re.findall(r"-?\d[\d,]*", text)
    return int(m[-1].replace(",", "")) if m else None


def g_int(expect):
    return lambda out: last_int(out) == expect


def g_code(fn, tests):
    def grade(out):
        m = re.search(r"```(?:python)?\n(.*?)```", out, re.S)
        src = m.group(1) if m else out
        prog = src + "\n\nimport sys\nok = True\n" + "\n".join(
            f"try:\n    ok = ok and ({t})\nexcept Exception:\n    ok = False" for t in tests) + "\nsys.exit(0 if ok else 1)\n"
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "t.py"
            p.write_text(prog, encoding="utf-8")
            try:
                r = subprocess.run([sys.executable, "-I", str(p)], capture_output=True, timeout=10, cwd=d)
            except subprocess.TimeoutExpired:
                return False
            return r.returncode == 0
    return grade


def json_of(out):
    m = re.search(r"```(?:json)?\n(.*?)```", out, re.S)
    s = m.group(1) if m else out
    ia, ib = s.find("{"), s.find("[")
    if ib >= 0 and (ia < 0 or ib < ia):   # an array comes first: its closing bracket, not the last object's brace
        a, b = ib, s.rfind("]")
    else:
        a, b = ia, s.rfind("}")
    try:
        return json.loads(s[a:b + 1])
    except Exception:
        return None


def g_json(check):
    def grade(out):
        j = json_of(out)
        try:
            return j is not None and bool(check(j))
        except Exception:
            return False
    return grade


def g_ja(maxlen=None, must=(), must_not=(), ends=None, minlen=None):
    def grade(out):
        t = out.strip()
        t = re.sub(r"<[^>]+>", "", t).strip()
        if maxlen and len(t) > maxlen:
            return False
        if minlen and len(t) < minlen:
            return False
        if any(w not in t for w in must) or any(w in t for w in must_not):
            return False
        if ends and not t.endswith(ends):
            return False
        return len(re.findall(r"[぀-ヿ一-鿿]", t)) >= max(5, len(t) // 3)
    return grade


def g_en(fn):
    return lambda out: bool(fn(out.strip()))


def bullets(t):
    return [l for l in t.splitlines() if re.match(r"^\s*([-*•]|\d+[.)])\s+\S", l)]


TASKS = []


def add(fam, prompt, grader):
    TASKS.append({"id": f"{fam}{sum(1 for t in TASKS if t['fam'] == fam) + 1:02d}", "fam": fam, "prompt": prompt, "grade": grader})


# math: ground truth computed here
for q, v in [
    ("What is 17 * 23 + 49?", 17 * 23 + 49),
    ("A train travels 60 km/h for 2.5 hours and then 80 km/h for 1.5 hours. How many km in total?", 60 * 2.5 + 80 * 1.5),
    ("What is the sum of all integers from 1 to 100 that are divisible by 7?", sum(range(7, 101, 7))),
    ("How many positive divisors does 360 have?", sum(1 for d in range(1, 361) if 360 % d == 0)),
    ("What is 2 to the power 15?", 2 ** 15),
    ("A shop sells pens at 3 for 40 yen. How many yen do 27 pens cost?", 27 // 3 * 40),
    ("What is the remainder when 7^100 is divided by 13?", pow(7, 100, 13)),
    ("What is the greatest common divisor of 462 and 1071?", __import__("math").gcd(462, 1071)),
    ("How many prime numbers are there below 60?", sum(1 for n in range(2, 60) if all(n % d for d in range(2, int(n ** .5) + 1)))),
    ("What is the 12th Fibonacci number if F1 = 1 and F2 = 1?", 144),
]:
    add("math", q + " Think step by step briefly, then end with 'Answer: <integer>'.", g_int(int(v)))

# code
add("code", "Write a Python function is_palindrome(s) that ignores case and non-alphanumeric characters. Only output a python code block.",
    g_code("is_palindrome", ["is_palindrome('A man, a plan, a canal: Panama')", "not is_palindrome('hello')", "is_palindrome('')"]))
add("code", "Write a Python function fizzbuzz(n) returning the list of strings for 1..n (FizzBuzz rules). Only output a python code block.",
    g_code("fizzbuzz", ["fizzbuzz(15)[-1]=='FizzBuzz'", "fizzbuzz(5)==['1','2','Fizz','4','Buzz']"]))
add("code", "Write a Python function merge_intervals(iv) that merges overlapping [start,end] intervals in a list and returns them sorted. Only output a python code block.",
    g_code("merge_intervals", ["merge_intervals([[1,3],[2,6],[8,10]])==[[1,6],[8,10]]", "merge_intervals([])==[]", "merge_intervals([[1,4],[4,5]])==[[1,5]]"]))
add("code", "Write a Python function count_words(text) returning a dict of lowercase word -> count, splitting on whitespace and stripping .,!? from the ends of words. Only output a python code block.",
    g_code("count_words", ["count_words('Hi hi, there!')=={'hi':2,'there':1}"]))
add("code", "Write a Python function two_sum(nums, target) returning a tuple (i, j) with i<j of indices whose values sum to target, or None. Only output a python code block.",
    g_code("two_sum", ["two_sum([2,7,11,15],9)==(0,1)", "two_sum([3,3],6)==(0,1)", "two_sum([1,2],10) is None"]))
add("code", "Write a Python function flatten(x) that flattens arbitrarily nested lists into one flat list. Only output a python code block.",
    g_code("flatten", ["flatten([1,[2,[3,[4]]],5])==[1,2,3,4,5]", "flatten([])==[]"]))
add("code", "Write a Python function roman_to_int(s) for Roman numerals up to 3999. Only output a python code block.",
    g_code("roman_to_int", ["roman_to_int('MCMXCIV')==1994", "roman_to_int('IX')==9", "roman_to_int('LVIII')==58"]))
add("code", "Write a Python function binary_search(a, x) returning the index of x in sorted list a, or -1. Only output a python code block.",
    g_code("binary_search", ["binary_search([1,3,5,7,9],7)==3", "binary_search([1,3,5],4)==-1", "binary_search([],1)==-1"]))

# json
add("json", 'Output only a JSON object with keys "name" (string "Alice"), "age" (integer 30) and "tags" (array of exactly 3 strings).',
    g_json(lambda j: j.get("name") == "Alice" and j.get("age") == 30 and isinstance(j.get("tags"), list) and len(j["tags"]) == 3 and all(isinstance(x, str) for x in j["tags"])))
add("json", 'Output only a JSON array of the first 5 square numbers starting from 1, as integers.',
    g_json(lambda j: j == [1, 4, 9, 16, 25]))
add("json", 'Output only JSON: an object "book" with "title" (string), "year" (integer between 1900 and 2000) and "authors" (array with at least 2 strings).',
    g_json(lambda j: isinstance(j["book"]["title"], str) and 1900 <= j["book"]["year"] <= 2000 and len(j["book"]["authors"]) >= 2))
add("json", 'Convert to JSON, output only the JSON: "red=3, green=5, blue=7" -> an object mapping each color to its integer value.',
    g_json(lambda j: j == {"red": 3, "green": 5, "blue": 7}))
add("json", 'Output only a JSON object with key "matrix" holding a 3x3 identity matrix as nested arrays of integers.',
    g_json(lambda j: j["matrix"] == [[1, 0, 0], [0, 1, 0], [0, 0, 1]]))
add("json", 'Output only a JSON object with key "ok" (boolean true) and key "items" (an empty array) and no other keys.',
    g_json(lambda j: j == {"ok": True, "items": []}))
add("json", 'Output only a JSON array of 4 objects, each with integer "id" (1..4) and boolean "even" that is true for even ids.',
    g_json(lambda j: j == [{"id": i, "even": i % 2 == 0} for i in range(1, 5)]))
add("json", 'Output only a JSON object with key "words" being the array of the words of the sentence "the quick brown fox" in reverse order.',
    g_json(lambda j: j == {"words": ["fox", "brown", "quick", "the"]}))

# ja
add("ja", "富士山について、50字以内の日本語で一文だけ説明してください。", g_ja(maxlen=50, must=("富士山",), ends="。"))
add("ja", "「猫」という単語を必ず含めて、日本語で2文の短い文章を書いてください。", g_ja(must=("猫",), ends="。", maxlen=120))
add("ja", "次の文を丁寧語(です・ます調)に直してください。出力は直した文だけ。「明日は雨が降るだろう。」", g_ja(must=("雨",), ends="。", maxlen=40, must_not=("だろう",)))
add("ja", "1から5までの数字を、漢数字で、読点「、」で区切って書いてください。他の文字は書かないでください。", g_ja(must=("一、二、三、四、五",), maxlen=20, minlen=9))
add("ja", "東京の首都としての特徴を、「、」を3回以上使い、100字以内で説明してください。", g_ja(maxlen=100, must=("東京",)))
add("ja", "「ありがとう」を英語・フランス語・スペイン語でどう言うか、日本語の文章の中で3つとも示してください。", g_ja(must=("Thank", "Merci", "Gracias"), minlen=15))
add("ja", "次の数式の答えを日本語の一文で答えてください。「12×12」", g_ja(must=("144",), ends="。", maxlen=40))
add("ja", "「春」「夏」「秋」「冬」を全て使った、日本語の一文を書いてください。", g_ja(must=("春", "夏", "秋", "冬"), ends="。", maxlen=100))

# en
add("en", "List exactly three benefits of exercise as a bulleted list, one short line each, nothing else.", g_en(lambda t: len(bullets(t)) == 3))
add("en", "Write a one-sentence definition of photosynthesis that contains the word 'light' and does not contain the word 'very'.",
    g_en(lambda t: "light" in t.lower() and "very" not in t.lower() and t.count(".") <= 2))
add("en", "Answer with exactly one word: what is the capital of France?", g_en(lambda t: re.sub(r"[^A-Za-z]", "", t).lower() == "paris" and len(t.split()) <= 2))
add("en", "Translate 'Good morning, how are you?' into Spanish. Output only the translation.", g_en(lambda t: "buen" in t.lower() and "c" in t.lower() and len(t) < 60))
add("en", "Write a haiku-like poem of exactly 3 lines about the sea. Output only the poem.", g_en(lambda t: len([l for l in t.splitlines() if l.strip()]) == 3))
add("en", "Which is larger, 9.11 or 9.9? Answer with the larger number only.", g_en(lambda t: "9.9" in t and "9.11" not in t.replace("9.9", "")))
add("en", "Write the word 'banana' backwards. Output only the result.", g_en(lambda t: re.sub(r"[^a-z]", "", t.lower()) == "ananab"))
add("en", "Give exactly two sentences about the moon. No lists.", g_en(lambda t: len(re.findall(r"[.!?](\s|$)", t)) == 2 and not bullets(t)))


STOP_MARKS = ("<|user|>", "<|endoftext|>", "<|observation|>", "<|assistant|>", "<|system|>")


def clean(text: str) -> str:
    """The engine's token stream ends with the stop token; the answer is what comes before it."""
    cut = min([text.find(m) for m in STOP_MARKS if m in text] or [len(text)])
    return text[:cut].strip()


def summarize(label, env, results, load_s=0.0):
    fams = {}
    for r in results:
        f = fams.setdefault(r["fam"], [0, 0])
        f[0] += r["ok"]
        f[1] += 1
    return {"label": label, "env": env, "total": [sum(f[0] for f in fams.values()), len(results)],
            "by_family": fams, "load_s": load_s}


def regrade(path: Path) -> int:
    """Grade a saved run again with the current graders (the outputs are kept in the file)."""
    by_id = {t["id"]: t for t in TASKS}
    d = json.loads(path.read_text(encoding="utf-8"))
    for r in d["results"]:
        r["ok"] = bool(by_id[r["id"]]["grade"](clean(r["text"])))
    d["summary"] = summarize(d["summary"]["label"], d["summary"]["env"], d["results"], d["summary"].get("load_s", 0.0))
    path.write_text(json.dumps(d, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(d["summary"], ensure_ascii=False))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--regrade", type=Path, help="grade a saved run again and exit")
    ap.add_argument("--maya-dir", type=Path)
    ap.add_argument("--config", type=Path)
    ap.add_argument("--env", action="append", default=[], metavar="KEY=VALUE")
    ap.add_argument("--label", default="q")
    ap.add_argument("--out", type=Path)
    ap.add_argument("--n-new", type=int, default=N_NEW)
    a = ap.parse_args(argv)
    if a.regrade:
        return regrade(a.regrade)
    if not (a.maya_dir and a.config and a.out):
        ap.error("--maya-dir, --config and --out are required")

    root = a.maya_dir.resolve()
    sys.path.insert(0, str(root))
    sys.path.insert(0, str(root / "tools"))
    import serve.server as SV
    import strata_tokenizer as ST

    cfg = json.loads((a.config if a.config.is_absolute() else root / a.config).read_text(encoding="utf-8"))
    cfg.setdefault("env", {})
    for kv in a.env:
        k, v = kv.split("=", 1)
        cfg["env"][k] = v
    args = cfg.get("args") or []
    pack = Path(args[args.index("--glm-pack") + 1])
    tok = ST.Tokenizer.from_dir(Path(cfg.get("tokenizer") or pack / "tokenizer"))
    chat = lambda q: tok.encode("[gMASK]<sop><|user|>\n" + q + "<|assistant|>\n</think>", parse_special=True)

    log_path = a.out.with_suffix(".engine.log")
    results, t_start = [], time.time()
    with open(log_path, "w", encoding="utf-8") as log:
        p = subprocess.Popen([cfg["exe"], "--serve"] + SV.engine_args(cfg), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                             stderr=log, text=True, env=SV.child_env(cfg), cwd=cfg.get("cwd") or str(root), bufsize=1)
        while True:
            line = p.stdout.readline()
            if not line:
                raise SystemExit(f"engine stopped while loading; see {log_path}")
            if line.startswith("READY"):
                break
        for t in TASKS:
            ids = chat(t["prompt"])
            p.stdin.write(f"GEN {a.n_new} temperature=0 " + ",".join(map(str, ids)) + "\n")
            p.stdin.flush()
            toks, t0 = [], time.time()
            while True:
                line = p.stdout.readline()
                if not line:
                    raise SystemExit(f"engine stopped during {t['id']}; see {log_path}")
                if line.startswith("T "):
                    toks.append(int(line.split()[1]))
                elif line.startswith("DONE") or line.startswith("ERR"):
                    break
            text = tok.decode(toks)
            ok = bool(t["grade"](clean(text)))
            results.append({"id": t["id"], "fam": t["fam"], "ok": ok, "n_tokens": len(toks), "done": line.strip(),
                            "wall_s": round(time.time() - t0, 2), "text": text, "tokens": toks})
            print(f"{t['id']} {'PASS' if ok else 'FAIL'} ({len(toks)} tok)", flush=True)
        p.stdin.write("QUIT\n")
        p.stdin.flush()
        try:
            p.wait(timeout=180)
        except subprocess.TimeoutExpired:
            p.kill()
    summary = summarize(a.label, cfg["env"], results, time.time() - t_start)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps({"summary": summary, "results": results}, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
