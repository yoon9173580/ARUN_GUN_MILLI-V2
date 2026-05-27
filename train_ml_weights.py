#!/usr/bin/env python3
"""
Train ML weights from backtest trade history.
Feeds each trade through ml_weights.feedback_trade_result() to adjust per-layer multipliers.
"""
import os
import sys
import json
import argparse
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "api"))

from engines.ml_weights import _ml_engine, feedback_trade_result, get_ml_multipliers


def reset_weights():
    """Reset weights to 1.0 baseline before training."""
    for k in ("technical", "regime", "flow", "correlation"):
        _ml_engine.weights[k] = 1.0
    _ml_engine.save_weights()


def train(trades_path: str, reset: bool = True, verbose: bool = False):
    if not os.path.exists(trades_path):
        print(f"ERROR: trades file not found: {trades_path}")
        sys.exit(1)

    with open(trades_path) as f:
        data = json.load(f)
    trades = data.get("trades", [])
    if not trades:
        print("ERROR: no trades in file")
        sys.exit(1)

    print(f"[*] Loaded {len(trades)} trades from {trades_path}")

    if reset:
        reset_weights()
        print(f"[*] Reset weights to baseline 1.0")

    print(f"[*] Before training: {get_ml_multipliers()}")

    dominant_dist = Counter()
    pnl_by_dom = {}

    for t in trades:
        dom = t.get("dominant_layer")
        if not dom:
            continue
        dominant_dist[dom] += 1
        pnl_by_dom.setdefault(dom, []).append(t.get("pnl", 0))
        # Map "time" → no ml weight key; skip. ml_weights tracks: technical/regime/flow/correlation
        if dom == "time":
            continue
        feedback_trade_result({"pnl": t.get("pnl", 0), "dominant_layer": dom})
        if verbose:
            print(f"  {t['date']}: dom={dom}, pnl={t['pnl']:+.2f} -> weights={get_ml_multipliers()}")

    print()
    print("[*] Dominant-layer distribution:")
    for layer, n in dominant_dist.most_common():
        pnls = pnl_by_dom[layer]
        wins = sum(1 for p in pnls if p > 0)
        total = sum(pnls)
        print(f"    {layer:12s}: {n:3d} trades, {wins}W/{n-wins}L, PnL ${total:+.2f}")

    print()
    print(f"[*] After training: {get_ml_multipliers()}")
    print(f"[*] Weights saved to: {os.path.abspath(os.path.join('data_cache', 'ml_weights.json'))}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--trades", default="backtest_v4.json")
    p.add_argument("--no-reset", action="store_true")
    p.add_argument("--verbose", "-v", action="store_true")
    args = p.parse_args()
    train(args.trades, reset=not args.no_reset, verbose=args.verbose)
