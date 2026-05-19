"""Fundamental analysis scoring."""


def score_fundamentals(data):
    """Score stock fundamentals. Returns -50 to +50."""
    score = 0
    signals = []

    pe = data.get("pe_ratio")
    forward_pe = data.get("forward_pe")

    if pe is not None:
        if pe < 15:
            score += 15
            signals.append(f"Low P/E ({pe:.1f}) - potentially undervalued")
        elif pe < 25:
            score += 5
            signals.append(f"Moderate P/E ({pe:.1f})")
        elif pe > 50:
            score -= 15
            signals.append(f"High P/E ({pe:.1f}) - potentially overvalued")
        elif pe > 35:
            score -= 5
            signals.append(f"Elevated P/E ({pe:.1f})")

    if pe and forward_pe:
        if forward_pe < pe * 0.8:
            score += 10
            signals.append("Earnings growth expected (forward P/E much lower)")
        elif forward_pe > pe * 1.2:
            score -= 10
            signals.append("Earnings decline expected (forward P/E higher)")

    return {"score": max(-50, min(50, score)), "signals": signals}
