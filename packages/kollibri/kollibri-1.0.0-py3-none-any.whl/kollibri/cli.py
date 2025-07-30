import argparse


try:
    BOOL_KWARGS = {"type": bool, "action": argparse.BooleanOptionalAction}
except (ImportError, AttributeError):
    BOOL_KWARGS = {"action": "store_true"}


def _parse_cmd_line():
    """
    Helper for parsing CLI call and displaying help message
    """
    parser = argparse.ArgumentParser(
        description="Extract collocations from VERT formatted corpora"
    )
    parser.add_argument("input", type=str, help="Input file path")
    parser.add_argument(
        "query",
        type=str,
        nargs="?",
        help="Optional regex to search for (i.e. to appear in all collocation results)",
    )
    parser.add_argument(
        "-l",
        "--left",
        type=int,
        required=False,
        default=5,
        help="Window to the left in tokens",
    )
    parser.add_argument(
        "-r",
        "--right",
        type=int,
        required=False,
        default=5,
        help="Window to the right in tokens",
    )
    parser.add_argument(
        "-s",
        "--span",
        type=str,
        required=False,
        # default="p",
        help="XML span to use as window (e.g. s or p)",
    )
    parser.add_argument(
        "-m",
        "--metric",
        type=str,
        required=False,
        default="lr",
        choices=["lr", "sll", "lmi", "mi", "mi3", "ld", "t", "z"],
        help="Collocation metric",
    )
    parser.add_argument(
        "-sw",
        "--stopwords",
        type=str,
        required=False,
        help="Path to file containing stopwords (one per line)",
    )
    parser.add_argument(
        "-t",
        "--target",
        type=int,
        required=False,
        default=0,
        help="Index of VERT column to be searched as node",
    )
    parser.add_argument(
        "-n",
        "--number",
        type=int,
        required=False,
        default=20,
        help="Number of top results to return (-1 will return all)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        required=False,
        default="0",
        help="Comma-sep index/indices of VERT column to be calculated as collocations",
    )
    parser.add_argument(
        "-c",
        "--case-sensitive",
        required=False,
        default=False,
        help="Do case sensitive search",
        **BOOL_KWARGS
    )
    parser.add_argument(
        "-p",
        "--preserve",
        required=False,
        default=False,
        help="Preserve original sequential order of tokens in bigram",
        **BOOL_KWARGS
    )
    parser.add_argument(
        "-csv",
        "--csv",
        required=False,
        default=False,
        help="Output comma-separated values, optionally to an output file",
        type=str,
        nargs="?",
    )
    parser.add_argument(
        "-y",
        "--span_of_years",
        required=False,
        default=None,
        help="Comma-sep years. Only include collocations that were from texts from that span of years. None=include all",
    )

    parser.add_argument(
        "-yt",
        "--year_tag",
        required=False,
        default=None,
        help="XML tag for year of publication (e.g. date or year).",
    )

    kwargs = vars(parser.parse_args())
    kwargs["content"] = kwargs.pop("input")
    return kwargs
