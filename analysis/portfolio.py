"""Portfolio-aware investment suggestions."""


def analyze_portfolio(holdings, stock_scores, sectors):
    """Generate suggestions based on current portfolio vs market signals."""
    suggestions = []

    if not holdings:
        return suggestions

    total_equity = sum(h["equity"] for h in holdings)
    if total_equity == 0:
        return suggestions

    # Calculate sector exposure
    sector_exposure = {}
    for h in holdings:
        sector = h.get("sector", "Unknown")
        sector_exposure[sector] = sector_exposure.get(sector, 0) + h["equity"]

    # Check concentration risk
    for h in holdings:
        pct = h["equity"] / total_equity * 100
        if pct > 25:
            suggestions.append({
                "type": "WARNING",
                "symbol": h["symbol"],
                "message": f"High concentration: {h['symbol']} is {pct:.0f}% of portfolio. Consider trimming.",
            })
        elif pct > 15:
            suggestions.append({
                "type": "CAUTION",
                "symbol": h["symbol"],
                "message": f"{h['symbol']} is {pct:.0f}% of portfolio. Monitor position size.",
            })

    # Check for stocks with strong signals that you already own
    for h in holdings:
        symbol = h["symbol"]
        if symbol in stock_scores:
            score_data = stock_scores[symbol]
            score = score_data["total_score"]
            if score >= 30:
                suggestions.append({
                    "type": "ADD",
                    "symbol": symbol,
                    "message": f"Strong signals for {symbol} (score: {score}). Consider adding to position.",
                })
            elif score <= -30:
                suggestions.append({
                    "type": "REDUCE",
                    "symbol": symbol,
                    "message": f"Weak signals for {symbol} (score: {score}). Consider reducing position.",
                })

    # Check for high-scoring stocks NOT in portfolio
    held_symbols = {h["symbol"] for h in holdings}
    for symbol, data in stock_scores.items():
        if symbol not in held_symbols and data["total_score"] >= 25:
            suggestions.append({
                "type": "NEW",
                "symbol": symbol,
                "message": f"Consider opening position in {symbol} (score: {data['total_score']}). Not currently held.",
            })

    # Check losers to consider tax-loss harvesting
    for h in holdings:
        if h["total_return_pct"] < -15:
            suggestions.append({
                "type": "TAX",
                "symbol": h["symbol"],
                "message": f"{h['symbol']} is down {h['total_return_pct']:.0f}%. Consider tax-loss harvesting if thesis has changed.",
            })

    # Sort by priority
    priority = {"WARNING": 0, "REDUCE": 1, "ADD": 2, "NEW": 3, "TAX": 4, "CAUTION": 5}
    suggestions.sort(key=lambda x: priority.get(x["type"], 99))

    return suggestions
