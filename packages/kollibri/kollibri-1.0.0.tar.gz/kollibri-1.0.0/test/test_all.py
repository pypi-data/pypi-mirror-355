import unittest
import tempfile
from kollibri import kollibri
from collections import Counter
import os

SENT = """<s>
Al\tNNP\tAl
-\tHYPH\t-
Zaman\tNNP\tZaman
:\t:\t:
American\tJJ\tAmerican
forces\tNNS\tforce
killed\tVBD\tkill
Shaikh\tNNP\tShaikh
Abdullah\tNNP\tAbdullah
al\tNNP\tal
-\tHYPH\t-
Ani\tNNP\tAni
,\t,\t,
the\tDT\tthe
preacher\tNN\tpreacher
at\tIN\tat
the\tDT\tthe
mosque\tNN\tmosque
in\tIN\tin
the\tDT\tthe
town\tNN\ttown
of\tIN\tof
Qaim\tNNP\tQaim
,\t,\t,
near\tIN\tnear
the\tDT\tthe
Syrian\tJJ\tSyrian
border\tNN\tborder
.\t.\t.
</s>"""

TEST = f"""
<corpus>
<text>
{SENT}
{SENT}
{SENT}
</text>
</corpus>
"""

RESULTS = {
    ("al", "-"): 43.66613595822584,
    ("zaman", ":"): 26.099116708212236,
    (":", "american"): 26.099116708212236,
}


class TestAll(unittest.TestCase):
    def test_overall(self):
        tmp = tempfile.NamedTemporaryFile()
        with open(tmp.name, "w") as fo:
            fo.write(TEST)
            fo.seek(0)
            print(fo)
        results = kollibri(tmp.name, left=5, right=5, span="s", number=3)
        self.assertDictEqual(results, RESULTS)

    def test_various(self):
        tmp = tempfile.NamedTemporaryFile()
        with open(tmp.name, "w") as fo:
            fo.write(TEST)
            fo.seek(0)
        # todo oneday: add some asserts?
        self.assertTrue(bool(kollibri(tmp.name, left=-1, right=-1, span="s")))
        self.assertTrue(bool(kollibri(tmp.name, left=5, right=5, span=None)))
        self.assertTrue(bool(kollibri(tmp.name, left=0, right=1, span="s")))
        self.assertTrue(bool(kollibri(tmp.name, left=1, right=0, span="s")))
        self.assertTrue(bool(kollibri(tmp.name, left=0, right=0, span="s")))
        self.assertTrue(bool(kollibri(tmp.name, span="s")))
        self.assertTrue(bool(kollibri(tmp.name, "^S", left=-1, right=-1, span="s")))
        self.assertTrue(bool(kollibri(tmp.name, "^S", left=5, right=5, span=None)))
        self.assertTrue(bool(kollibri(tmp.name, "S", left=0, right=1, span="s")))
        self.assertTrue(bool(kollibri(tmp.name, "^S", left=1, right=0, span="s")))
        self.assertTrue(
            bool(
                kollibri(
                    tmp.name, "^S", left=1, right=0, span="s", output="1,2", metric="lr"
                )
            )
        )
        self.assertTrue(
            bool(
                kollibri(
                    tmp.name, "^S", left=1, right=0, span="s", output="1,2", metric="z"
                )
            )
        )
        self.assertTrue(
            bool(
                kollibri(
                    tmp.name, "^S", left=1, right=0, span="s", output="1,2", metric="mi"
                )
            )
        )
        self.assertTrue(
            bool(
                kollibri(
                    tmp.name, "^S", left=1, right=0, span="s", output=1, metric="mi3"
                )
            )
        )
        self.assertTrue(
            bool(
                kollibri(
                    tmp.name,
                    "^S",
                    left=1,
                    right=0,
                    span="s",
                    output="1,2",
                    metric="lmi",
                )
            )
        )
        self.assertTrue(
            bool(
                kollibri(
                    tmp.name, "^S", left=1, right=0, span="s", output="1,2", metric="ld"
                )
            )
        )
        self.assertTrue(
            bool(
                kollibri(
                    tmp.name,
                    "^S",
                    left=1,
                    right=0,
                    span="s",
                    output="1,2",
                    metric="sll",
                )
            )
        )
        self.assertTrue(bool(kollibri(tmp.name, "^S", span="s")))
        self.assertTrue(bool(kollibri(tmp.name, "^S", span="s", csv="test.csv")))
        self.assertTrue(
            bool(
                kollibri(
                    tmp.name,
                    "^S",
                    preserve=True,
                    target=2,
                    output=[1, 2],
                    metric="t",
                    number=5,
                    csv=True,
                )
            )
        )
        results = kollibri(tmp.name, "^s", span="s", case_sensitive=True, csv=True)
        self.assertFalse(bool(results))

    def test_stopwords(self):
        with open("tmpstopwords.txt", "w") as fo:
            fo.write(",\n.\nthe\n")
        tmp = tempfile.NamedTemporaryFile()
        with open(tmp.name, "w") as fo:
            fo.write(TEST)
            fo.seek(0)
        # todo oneday: add some asserts?
        results = kollibri(
            tmp.name, left=-1, right=-1, span="s", stopwords="tmpstopwords.txt"
        )
        self.assertTrue(all(a != "the" and b != "the" for a, b in results.keys()))
        os.remove("tmpstopwords.txt")

    def test_error(self):
        tmp = tempfile.NamedTemporaryFile()
        with open(tmp.name, "w") as fo:
            fo.write(TEST)
            fo.seek(0)
        with self.assertRaises(ValueError):
            kollibri(tmp.name, left=0, right=0, span=None)


if __name__ == "__main__":
    unittest.main()
