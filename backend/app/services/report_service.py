from ..schemas import Verdict


def empty_verdict_counts() -> dict[Verdict, int]:
    """Return every supported verdict, including verdicts with zero claims."""
    return {verdict: 0 for verdict in Verdict}
