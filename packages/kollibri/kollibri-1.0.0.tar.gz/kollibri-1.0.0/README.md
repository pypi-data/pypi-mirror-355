# kollibri: extract collocations from VERT formatted corpora

> Author: Danny McDonald, Sonja Huber, UZH

## Installation

```bash
pip install kollibri
# or
git clone https://gitlab.uzh.ch/corpus-linguistic-uzh/kollibri
cd kollibri
python setup.py install
```

## CLI Usage

You can start the tool from your shell with:

```bash
python -m kollibri input/file.vrt
# or
kollibri input/file.vrt
```

Arguments are like this:

```
usage: kollibri [-h] [-l LEFT] [-r RIGHT] [-s SPAN] [-m {ll,sll,lmi,mi,mi3,ld,t,z}] [-sw STOPWORDS] [-t TARGET] [-n NUMBER] [-o OUTPUT] [-c] [-p] [-csv [CSV]] input [query]

Extract collocations from VERT formatted corpora

positional arguments:
  input                 Input file path
  query                 Optional regex to search for (i.e. to appear in all collocation results)

optional arguments:
  -h, --help            show this help message and exit
  -l LEFT, --left LEFT  Window to the left in tokens
  -r RIGHT, --right RIGHT
                        Window to the right in tokens
  -s SPAN, --span SPAN  XML span to use as window (e.g. s or p)
  -m {lr,sll,lmi,mi,mi3,ld,t,z}, --metric {lr,sll,lmi,mi,mi3,ld,t,z}
                        Collocation metric
  -sw STOPWORDS, --stopwords STOPWORDS
                        Path to file containing stopwords (one per line)
  -t TARGET, --target TARGET
                        Index of VERT column to be searched as node
  -n NUMBER, --number NUMBER
                        Number of top results to return (-1 will return all)
  -o OUTPUT, --output OUTPUT
                        Comma-sep index/indices of VERT column to be calculated as collocations
  -c, --case-sensitive  Do case sensitive search
  -p, --preserve        Preserve original sequential order of tokens in bigram
  -csv [CSV], --csv [CSV]
                        Output comma-separated values
```

### Python usage

```python
from kollibri import kollibri

kollibri(
    "path/to/file.vrt",
    query="^Reg(ex|ular expression)$",  # optional
    left=5,
    right=5,
    span=None,
    number=20,
    metric='lr',
    target=0,
    output=[0],
    stopwords=None,
    case_sensitive=False,
    preserve=False,
    csv=False
)
```

### Metrics supported (and their short name):

* Likelihood ratio (`lr`)
* Simple Log likelihood (`sll`)
* Mutual information (`mi`)
* Local mutual information (`lmi`)
* MI3 (`mi3`)
* Log Dice (`ld`)
* T-score (`t`)
* Z-score (`z`)

### Spans

If you enter a span (e.g. `s`) instead of a left/right window, collocation windows will expand from the matching node to the nearest `s` tags in both directions. Of course, this can lead to very large windows and potential memory/performance issues, especially for spans broader than one sentence.

If you specify a left and/or right as well as a span, matches will be cut off at matching XML elements if they are encountered. So you can specify (e.g.) `left=2, right=2, span="s"` to get a window of `2`, while not allowing the window to cross sentence boundaries. If you do not enter a span, left/right windows can cross sentence boundaries.

Note that you cannot give regular expressions for spans, or provide multiple spans (yet).

### Target and output

`target` denotes the index of the column of the VRT you want to match with your query, with the leftmost column, typically the original token, being number 0. So, if your VRT corpus is in the format of `token<tab>POS<tab>lemma`, you would set `target` to 2 in order to query on the lemma column.

For `output`, you are still providing column indices, but you can provide more than one. So, if you're using the CLI, you can do `--output=1,2` to format results from a corpus in `token<tab>POS<tab>lemma` format as `NNS/friend`. If you're in Python, provide a list of integers, matching the column indices you want to use.

### Example

```python
from kollibri import kollibri
kollibri("./sample.vrt",
    query="en$",
    target=0,
    output=[1,2],
    number=3,
    left=0,
    right=1,
    metric="lr",
    stopwords="stopwords.txt",
    case_sensitive=True,
    preserve=False,
    csv=False
)
```

Results in:

```
VAFIN/sein    ART/d           1202.0321
VAINF/werden  VMFIN/können    853.0279
VAFIN/haben   PPER/wir        758.4650
```

The exact equivalents on the command line would be:

```bash
kollibri ./sample.vrt "en$" -t 0 -o 1,2 -n 3 -l 0 -r 1 -m lr -sw stopwords.txt -c
````

or

```bash
python -m kollibri ./sample.vrt "en$" --target=0 --output=1,2 --number=3 --left=0 --right=1 --metric=lr --stopwords=stopwords.txt --case-sensitive
````

### CSV creation

If you want to generate a CSV file containing your results, use the `-csv` argument with a filepath:

```bash
kollibri example.vrt "test" -csv output.csv
```

Without a filename, the CSV results will print to stdout (so you can pipe them elsewhere if need be):

```bash
kollibri example.vrt "test" -csv | grep ...
```

From the Python interface you can do `kollibri(csv="output.csv")` to write results to a specific file. `csv=True` will output CSV-formatted results to stdout.


## Using kollibri with Timespans

If only a subcorpus, determined by the year in the metadata, is to be examined, the following additional arguments can be entered:

```
optional arguments:
  -y --span_of_years SPAN OF YEARS
                        comma-seperated list in a string of the span of years that shall be queried
  -yt --year_tag YEAR TAG
                        string of the name of the metadata tag that contains the year in the first four digits.
```

The list in span_of_years can also only contain one year. 

:warning: Be aware that the year has to be within the first four digits of the year_tag content, of the script will not work as intended.
Eg. 2024-01-01 will work, 01-01-2024 will not. :warning:

```python
from kollibri import kollibri
kollibri("./sample.vrt",
    query="en$",
    target=0,
    output=[1,2],
    number=3,
    left=0,
    right=1,
    metric="lr",
    stopwords="stopwords.txt",
    case_sensitive=True,
    preserve=False,
    csv="sample_2010_2020"
    span_of_years="2010, 2020",
    year_tag="date"
)
```

Due to growing number of arguments using a python script is recommended. 