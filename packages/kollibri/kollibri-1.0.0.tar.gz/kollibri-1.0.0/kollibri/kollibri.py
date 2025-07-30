import re

from collections import Counter, defaultdict

import os

from tqdm import tqdm

import math

from functools import reduce

import sys

import csv as _csv

_log2 = lambda x: math.log2(x)

_product = lambda s: reduce(lambda x, y: x * y, s)

_SMALL = 1e-20


def _is_match(query, target, case_sensitive, stopwords):
    """
    Does query match target? can be regex, stopwords might exist, etc
    """
    if not query:
        return True
    if stopwords and target in stopwords:
        return False
    if isinstance(query, str):
        if case_sensitive:
            return query in target
        else:
            return query.lower() in target.lower()
    return re.search(query, target)


def from_words(
    words, left, right, query, target, output, case_sensitive, stopwords, preserve
):
    """
    Turn located matches into a frequency dictionary
    """
    ngram_freq = defaultdict(int)

    pbar = tqdm(ncols=120, unit="match", desc="Formatting collocates", total=len(words))

    for match in words:
        pbar.update()
        for line_ix, match_ix, pieces in match:
            if match_ix is not None and line_ix != match_ix:
                continue
            targ = pieces[target].strip()
            outp = "/".join(pieces[x] for x in output)
            if not case_sensitive:
                outp = outp.lower()
            for line, m, pieces_again in match:
                distance = abs(m - line) if m is not None else abs(line_ix - line)
                real_dist = line_ix - line
                if m is None and not distance:
                    continue
                tok = pieces_again[target].strip()
                if stopwords and (
                    tok.lower() in stopwords or targ.lower() in stopwords
                ):
                    continue
                outp_again = "/".join(pieces_again[x] for x in output)
                # if not query and (outp_again, outp) in ngram_freq:
                #    continue
                if not case_sensitive:
                    outp_again = outp_again.lower()
                if not query and real_dist > 0:
                    if right != -1 and right and real_dist > right:
                        continue
                elif not query and real_dist < 0:
                    if left != -1 and left != 0 and real_dist < left:
                        continue
                if tok is None or tok == targ or not distance:
                    continue
                # these lines make sure every bigram is ordered as it is in the text...
                ordered = (outp, outp_again)
                if real_dist > 0 and not preserve:
                    ordered = (outp_again, outp)
                if stopwords and (
                    outp.lower() in stopwords or outp_again.lower() in stopwords
                ):
                    continue
                ngram_freq[ordered] += 1.0 / max(distance, 1.0)

    pbar.close()

    return ngram_freq


def filter_years(content, span_of_years, year_tag="year"):
    print(f"Filtering content for years {span_of_years}")
    print(f"looking for '{year_tag}' in metadata line to extract years")
    temp_file = f"{content}.tmp"

    # Extract start and end years
    if "," in span_of_years:
        years = span_of_years.split(",")
        start_year, end_year = int(years[0]), int(years[1])
        valid_years = {str(year) for year in range(start_year, end_year + 1)}
    else:
        years = [span_of_years]
        valid_years = {span_of_years}

    writing = False  # Controls whether we are writing lines to output

    with open(content, "r", encoding="utf8") as fi, open(
        temp_file, "w", encoding="utf8"
    ) as fo:
        fo.write("<corpus>\n")
        for line in fi:
            if line.startswith("<text"):
                # Try extracting the pubtime year
                match = re.search(rf'{year_tag}="(\d{{4}})', line)
                if match:
                    year = match.group(1)
                    if year in valid_years:
                        writing = True
                        fo.write(line)
                    else:
                        writing = False
                else:
                    print(
                        f"Warning: No {year_tag} in right format found in line: {line.strip()}"
                    )
                    writing = False
            elif line.startswith("</text>"):
                if writing:
                    fo.write(line)
                writing = False
            else:
                if writing:
                    fo.write(line)
        fo.write("</corpus>")
    return temp_file


def _get_start(match, left, span, boundaries):
    """
    Find the left edge for a given matching query
    """
    if left == 0:
        return match

    if left is None or left == -1:
        left = 99  # backstop

    backward = 1
    while left:
        to_get = match - backward
        if to_get <= 0:
            return 0
        current = boundaries[to_get]
        if span and current == span:
            return to_get + 1
        backward += 1
        if not current:
            left -= 1

    return to_get


def _get_end(match, right, span, boundaries, total_lines):
    """
    Get line number to finish on
    """
    if right == 0:
        return match

    if right is None or right == -1:
        right = 99  # backstop

    real_right = None

    done = 0
    forward = 1
    while done < right:
        real_right = match + forward
        if real_right >= (total_lines - 1):
            return total_lines - 1
        current = boundaries[real_right]
        if span and current == span:
            return real_right
        if not current:
            done += 1
        forward += 1
    return real_right


def _fix_output(output):
    """
    Get output as a list of ints
    """
    if not isinstance(output, (tuple, list)):
        if isinstance(output, str):
            return [int(x.strip()) for x in output.split(",")]
        else:
            return [output]
    else:
        return [int(x) for x in output]


def _prepare_query(query, case_sensitive):
    """
    Any preprocessing needed for our query? i.e. compiling
    """
    if query and isinstance(query, str) and not query.isalnum():
        if case_sensitive:
            flags = {}
        else:
            flags = {"flags": re.IGNORECASE}
        return re.compile(query, **flags)
    elif query:
        return str(query)


def _log_dice(ngram_freq, both_tokens, total_words):
    return 14 + _log2((2 * ngram_freq) / sum(both_tokens))


def _mi3(ngram_freq, both_tokens, total_words):
    expected = (both_tokens[0] * both_tokens[1]) / total_words
    return _log2(ngram_freq**3 / expected)


def _mi(ngram_freq, both_tokens, total_words):
    expected = (both_tokens[0] * both_tokens[1]) / total_words
    return _log2(ngram_freq / expected)


def _lmi(ngram_freq, both_tokens, total_words):
    expected = (both_tokens[0] * both_tokens[1]) / total_words
    return ngram_freq * _log2(ngram_freq / expected)


def _tscore(ngram_freq, both_tokens, total_words):
    expected = (both_tokens[0] * both_tokens[1]) / total_words
    t_score = (ngram_freq - expected) / math.sqrt(ngram_freq)
    return t_score


def _zscore(ngram_freq, both_tokens, total_words):
    expected = (both_tokens[0] * both_tokens[1]) / total_words
    z_score = (ngram_freq - expected) / math.sqrt(expected)
    return z_score


def _sll(ngram_freq, both_tokens, total_words):
    expected = (both_tokens[0] * both_tokens[1]) / total_words
    can_be_negative = ngram_freq - expected
    if not can_be_negative:
        return 0
    neg = can_be_negative <= 0
    score = 2 * (ngram_freq * math.log(abs(can_be_negative)) - (ngram_freq - expected))
    return score if not neg else -score


def _likelihood_ratio(ngram_freq, both_tokens, total_words):
    (w1, w2) = both_tokens
    n_oi = w2 - ngram_freq
    n_io = w1 - ngram_freq
    cont = (ngram_freq, n_oi, n_io, total_words - ngram_freq - n_oi - n_io)
    comb = sum(cont)
    pieces = []
    for i in range(4):
        pieces.append((cont[i] + cont[i ^ 1]) * (cont[i] + cont[i ^ 2]) / comb)

    return 2 * sum(
        obs * math.log(obs / (exp + _SMALL) + _SMALL) for obs, exp in zip(cont, pieces)
    )


def kollibri(
    content,
    query=None,
    left=5,
    right=5,
    span=None,
    number=20,
    metric="lr",
    target=0,
    output=[0],
    stopwords=None,
    case_sensitive=False,
    preserve=False,
    csv=False,
    span_of_years=None,
    year_tag=None,
):
    output = _fix_output(output)

    compiled = _prepare_query(query, case_sensitive)

    if not left and not right and span:
        left, right = -1, -1

    bads = (0, -1)

    if left in bads and right in bads and not span:
        raise ValueError("Need a span, or left/right to be larger than 0...")

    window = (left is not None and left > 0) or (right is not None and right > 0)

    if stopwords:
        with open(stopwords, "r", encoding="utf8") as fo:
            stopwords = set(i.strip().lower() for i in fo.readlines())

    matches = set()
    boundaries = []
    offsets = {}
    total_bytes = 0
    word_count = 0
    word_freqs = Counter()

    # if years, filter the content here, create temporary file with only the relevant years
    if span_of_years is not None:
        content = filter_years(content, span_of_years, year_tag)

    size = os.path.getsize(content)

    with open(content, "rb") as fo:
        pbar = tqdm(
            ncols=120,
            unit="bytes",
            desc="Finding collocates",
            total=size,
            unit_scale=True,
        )

        total_lines = 0

        for i, bytes_line in enumerate(fo):
            line = bytes_line.decode("utf8")
            total_lines += 1
            num_bytes = len(bytes_line)
            pbar.update(num_bytes)
            offsets[i] = total_bytes
            total_bytes += num_bytes
            line = line.strip()
            # empty line:
            if not line:
                boundaries.append(True)
                continue
            # xml element line
            elif line.startswith("<") and line.endswith(">") and "\t" not in line:
                tag = line.strip(" <>").split(" =")[0].strip().split()[0].lstrip("/")
                boundaries.append(tag)
                continue
            # it's a token:
            boundaries.append(False)
            word_count += 1
            pieces = line.strip().split("\t")
            target_token = pieces[target].strip()
            output_token = "/".join(pieces[x] for x in output).strip()
            if not case_sensitive:
                target_token = target_token.lower()
                output_token = output_token.lower()
            word_freqs[output_token] += 1
            if not query:
                matches.add(i)
                continue
            if _is_match(compiled, target_token, case_sensitive, stopwords):
                matches.add(i)

        pbar.close()

        fo.seek(0)

        out = defaultdict(list)

        if not window and not query:
            current = 0
            pbar = tqdm(
                ncols=120, unit="line", desc="Dividing into spans", total=total_lines
            )
            for i, bytes_line in enumerate(fo):
                pbar.update()
                line = bytes_line.decode("utf8")
                line = line.strip()
                if not line:
                    continue
                if span and boundaries[i] == span:
                    current += 1
                    continue
                elif not span and isinstance(boundaries[i], str):
                    # current += 1
                    continue
                elif "\t" not in line or (line.startswith("<") and line.endswith(">")):
                    # current += 1
                    continue
                pieces = [l.strip() for l in line.strip().split("\t")]
                out[current].append((i, None, tuple(pieces)))
            pbar.close()
        else:  # either there is a window, or there has been a query performed
            desc = "Building match contexts" if query else "Building contexts"
            pbar = tqdm(ncols=120, unit="match", desc=desc, total=len(matches))
            for match in sorted(matches):
                start = _get_start(match, left, span, boundaries)
                end = _get_end(match, right, span, boundaries, total_lines)
                sent_len = end - start
                seeker = offsets[start]
                fo.seek(seeker)
                base = int(start)
                for no, bytes_line in enumerate(fo):
                    try:
                        line = bytes_line.decode("utf8")
                    except UnicodeDecodeError:
                        print(f"\nError decoding line {no} in {content}")

                    # line = bytes_line.decode("utf8")
                    check = line.strip()
                    actual_lineno = no + start
                    if (
                        not check
                        or "\t" not in check
                        or (check.startswith("<") and check.endswith(">"))
                    ):
                        continue
                    if actual_lineno >= end + 1:
                        break
                    pieces = [i.strip() for i in line.strip().split("\t")]
                    needed = (actual_lineno, match, tuple(pieces))
                    out[match].append(needed)

                pbar.update()
            pbar.close()

    metrics = {
        "lr": _likelihood_ratio,
        "sll": _sll,
        "ld": _log_dice,
        "mi3": _mi3,
        "mi": _mi,
        "t": _tscore,
        "z": _zscore,
        "lmi": _lmi,
    }

    sents = list(out.values())

    bigrams = from_words(
        sents,
        left,
        right,
        compiled,
        target,
        output,
        case_sensitive,
        stopwords,
        preserve,
    )

    results = Counter()

    pbar = tqdm(
        ncols=120, unit="collocate", desc="Scoring collocates", total=len(bigrams)
    )

    for (w1, w2), n in bigrams.items():
        if n < 1.0:
            n = 1.0
        w1_freq = max(word_freqs[w1], n)
        w2_freq = max(word_freqs[w2], n)

        score = 0
        if n > 0.000000:
            score = metrics[metric](n, (w1_freq, w2_freq), word_count)
        results[(w1, w2)] = score
        pbar.update()

    pbar.close()

    to_show = number if number != -1 else len(results)

    if not results:
        if csv is False:
            print("No results found, sorry.")
            return
        else:
            return

    csv_out = None

    if csv is None or isinstance(csv, str) or csv is True:
        csv_out = (
            open(csv, "w", encoding="utf8") if isinstance(csv, str) else sys.stdout
        )
        writer = _csv.writer(csv_out)
        header = ["w1", "w2", metric]
        writer.writerow(header)

    for k, v in results.most_common(to_show):
        if not csv_out:
            k = "\t".join(k)
            print(f"{k}\t{v:.4f}".expandtabs(13))
        else:
            line = [k[0], k[1], f"{v:.6f}"]
            writer.writerow(line)

    if isinstance(csv, str):
        csv_out.close()

    # if span_of_years is not None:
    # os.remove(content)

    return dict(results.most_common(to_show))


if __name__ == "__main__":
    from .cli import _parse_cmd_line

    kwargs = _parse_cmd_line()
    kollibri(**kwargs)
