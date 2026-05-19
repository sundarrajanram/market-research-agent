"""Technical analysis scoring."""


def score_stock(data):
    """Score a stock based on technical indicators. Returns -100 to +100."""
    score = 0
    signals = []

    if data.get("rsi") is not None:
        rsi = data["rsi"]
        if rsi < 30:
            score += 20
            signals.append(f"RSI oversold ({rsi})")
        elif rsi < 40:
            score += 10
            signals.append(f"RSI approaching oversold ({rsi})")
        elif rsi > 70:
            score -= 20
            signals.append(f"RSI overbought ({rsi})")
        elif rsi > 60:
            score -= 10
            signals.append(f"RSI approaching overbought ({rsi})")

    price = data.get("price", 0)
    sma_20 = data.get("sma_20")
    sma_50 = data.get("sma_50")

    if sma_20 and price:
        if price > sma_20:
            score += 10
            signals.append("Price above 20-day SMA (bullish)")
        else:
            score -= 10
            signals.append("Price below 20-day SMA (bearish)")

    if sma_20 and sma_50:
        if sma_20 > sma_50:
            score += 15
            signals.append("Golden cross pattern (20 > 50 SMA)")
        else:
            score -= 15
            signals.append("Death cross pattern (20 < 50 SMA)")

    vol_ratio = data.get("volume_ratio", 1)
    if vol_ratio > 2:
        score += 10
        signals.append(f"High volume ({vol_ratio}x average)")
    elif vol_ratio < 0.5:
        score -= 5
        signals.append(f"Low volume ({vol_ratio}x average)")

    change = data.get("change_pct", 0)
    if change > 3:
        score += 10
        signals.append(f"Strong momentum (+{change}%)")
    elif change < -3:
        score -= 10
        signals.append(f"Negative momentum ({change}%)")

    return {"score": max(-100, min(100, score)), "signals": signals}


def classify_signal(score):
    """Classify overall signal strength."""
    if score >= 40:
        return "STRONG BUY"
    elif score >= 20:
        return "BUY"
    elif score >= -20:
        return "HOLD"
    elif score >= -40:
        return "SELL"
    else:
        return "STRONG SELL"
