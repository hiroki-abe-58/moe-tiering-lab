"""Sanity of scripts/maya_quality.py graders: known-good and known-bad outputs, so a grader bug cannot masquerade as a quality gap."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import maya_quality as q  # noqa: E402

T = {t["id"]: t for t in q.TASKS}

CASES = [
    ("math01", "17*23=391, +49 = 440. Answer: 440", True),
    ("math01", "Answer: 441", False),
    ("code01", "```python\nimport re\ndef is_palindrome(s):\n    s=re.sub(r'[^a-z0-9]','',s.lower())\n    return s==s[::-1]\n```", True),
    ("code01", "```python\ndef is_palindrome(s):\n    return s==s[::-1]\n```", False),
    ("json01", '```json\n{"name":"Alice","age":30,"tags":["a","b","c"]}\n```', True),
    ("json01", '{"name":"Alice","age":"30","tags":[]}', False),
    ("json07", '[\n {"id": 1, "even": false},\n {"id": 2, "even": true},\n {"id": 3, "even": false},\n {"id": 4, "even": true}\n]', True),
    ("json02", "[1, 4, 9, 16, 25]", True),
    ("math01", "Answer: 440", True),
    ("ja01", "富士山は日本で最も高い標高三千七百七十六メートルの山です。", True),
    ("ja01", "Mount Fuji is tall.", False),
    ("ja04", "一、二、三、四、五", True),
    ("ja06", "ありがとうは英語でThank you、フランス語でMerci、スペイン語でGraciasです。", True),
    ("en01", "- run\n- sleep\n- eat", True),
    ("en01", "- run\n- sleep", False),
    ("en03", "Paris", True),
    ("en03", "The capital is Paris.", False),
    ("en07", "ananab", True),
    ("en08", "The moon orbits Earth. It is bright.", True),
]


class Graders(unittest.TestCase):
    def test_cases(self):
        for tid, out, want in CASES:
            self.assertEqual(bool(T[tid]["grade"](out)), want, f"{tid}: {out[:40]!r}")

    def test_suite_shape(self):
        fams = {}
        for t in q.TASKS:
            fams[t["fam"]] = fams.get(t["fam"], 0) + 1
        self.assertEqual(fams, {"math": 10, "code": 8, "json": 8, "ja": 8, "en": 8})


if __name__ == "__main__":
    unittest.main()
