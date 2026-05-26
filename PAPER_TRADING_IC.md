# SPY 0DTE Iron Condor — Paper Trading Guide

## Why paper trading first

Backtest shows PF 6.86 / WR 90% / Max DD 13% on $1K capital. **Real PF likely 3.0-4.5** after gamma risk, IV expansion, pin risk, real fills. Forward test is non-negotiable.

**Goal**: 4 weeks of paper trading. Decide to go live (or kill) based on observed PF.

---

## Daily Checklist (per trading day)

### Pre-market (8:30 AM ET)
- [ ] Check FOMC / NFP / CPI calendar — **skip entire day** if scheduled
- [ ] Check overnight gap — if SPY gap > 0.5%, mark "elevated risk"
- [ ] Note prior close, current pre-market level
- [ ] VIX level — if VIX > 30, **skip day** (regime not modeled)

### 10:30 AM ET — Score check
- [ ] Open Pine MILLI v3-0 IC (or backtest signal table)
- [ ] Read STRONG / score from chart panel
- [ ] If score < 90 or grade not STRONG → **no trade**
- [ ] If LOCKED → **no trade**

### 10:30 AM — Entry (if signal)
- [ ] Get SPY current price → round to ATM strike (e.g., $710)
- [ ] Construct IC:
  - SELL call at ATM + 3 (e.g., $713)
  - BUY call at ATM + 8 (e.g., $718)
  - SELL put at ATM - 3 (e.g., $707)
  - BUY put at ATM - 8 (e.g., $702)
- [ ] Check net credit on order ticket: should be ~$1.5-2.5
- [ ] Position size: 1 contract per $300 of paper capital
- [ ] Submit as combo order (all 4 legs, limit at mid)

### During day — Manage
- [ ] **TP target**: close IC when net cost ≤ 25% of received credit (e.g., credit $2 → close at $0.50)
- [ ] **SL target**: close IC when net cost ≥ 200% of received credit OR cost ≥ wing width ($5)
- [ ] Watch for: SPY approaching short strike → consider early close at smaller loss

### 15:30 PM ET — EOD exit
- [ ] If not yet TP'd or SL'd, close IC at market
- [ ] Do NOT hold to expiration (pin risk on 0DTE)

### Post-close — Log
- [ ] Record in journal (template below)

---

## Position Sizing (paper trading $5K-10K account)

| Account | Risk/trade | Contracts (typical $300 max loss IC) |
|---|---|---|
| $5,000 | 5% = $250 | 1 contract (round down) |
| $10,000 | 5% = $500 | 1-2 contracts |
| $25,000 | 5% = $1,250 | 4 contracts |

**Cap: 5 contracts** regardless of account size. 0DTE liquidity ≠ infinite.

---

## Pine Script setup

1. Open TradingView, load 5-min SPY chart
2. Pine Editor → paste `YOON_SPY_MILLI_signal_v2-8.pine` (or v3-0 when IC variant ready)
3. Save as "MILLI IC v3"
4. Add to chart
5. Create alert:
   - Condition: `MILLI 0DTE CALL` or `MILLI 0DTE PUT` (either signals STRONG day → IC entry)
   - Trigger: Once per bar close
   - Action: Push notification + email (do NOT auto-execute)

---

## Trade Journal Template (per trade)

```
Date: 2026-MM-DD
SPY entry (10:30): $___
ATM strike: $___
Strikes: K_sp=$___ / K_lc=$___ / K_sc=$___ / K_lp=$___
Credit received: $___
Theoretical max loss: $___
Number of contracts: ___

VIX: ___
Score: ___ / Grade: ___
SPY range so far (9:30-10:30): $___ low to $___ high

Exit type: TP / SL / EOD
Exit time: HH:MM
Exit cost: $___
Net PnL: $___

Notes:
  - Did SPY breach short strike intraday? Y/N which side
  - Any news / FOMC / earnings affecting move? 
  - Fill quality vs theoretical?
```

Use Google Sheets or simple CSV. Track these fields → calculate weekly PF.

---

## "Ship to live" decision criteria (after 4 weeks)

### Go-live conditions (ALL must be true)
- [ ] At least 12 paper trades executed (need sample)
- [ ] **Observed PF ≥ 2.5**
- [ ] **WR ≥ 75%**
- [ ] Max single-trade loss ≤ theoretical max ($300/contract)
- [ ] **No catastrophic days** (loss > 2× modeled max — would indicate gamma/IV blowout)

### Hard kill conditions (ANY one = stop)
- 3 consecutive losses (early signal of regime change)
- Single day loss > 3× theoretical max (modeling completely wrong)
- 2 weeks with WR < 60%
- Observed PF < 1.5 after 4 weeks

### Go-live capital
- Start: $5,000 cash (small enough to lose without pain)
- Sizing: 5% risk per trade, max 5 contracts
- Scale up only if first 2 weeks live show PF > 2.0

---

## Common failure modes (learn from these)

1. **FOMO entries**: Trading on MODERATE score "because it looked good" — stick to STRONG only
2. **Early close on red**: SPY hits short strike intraday, you panic close at -50%, then SPY reverses by EOD. **Hold to TP/SL/EOD only**
3. **Size creep**: Wins → bigger size → one bad day wipes profits. **5% rule is non-negotiable**
4. **Skip the journal**: Without data, you can't tell signal-vs-noise. **Log every trade**
5. **Trading high-vol days**: VIX > 25 = IC expensive AND probability of breach high. **Skip**

---

## Comparison reference (don't conflate these)

| Strategy | Backtest PF | Live status |
|---|---|---|
| SPY 0DTE Debit Spread | 1.14 | **DEAD** — structurally limited |
| **SPY 0DTE Iron Condor** | **6.86** | **PAPER TRADING** — this doc |
| MES Futures | 4.04 | LIVE (per memory) |

Iron Condor is **not** a replacement for MES futures system. They're different products, different strategies. Run both if both work.

---

## Files

- Strategy backtest: `backtest_iron_condor_1min.py`
- Most recent results: `backtest_iron_condor_1min.json`
- Score / signal engine: Pine `YOON_SPY_MILLI_signal_v2-8.pine` (TRADINGVIEW repo)
- This guide: `PAPER_TRADING_IC.md`
