from datetime import datetime
import pytz
from .time_window import get_time_window_score
from .regime import calculate_regime_score
from .correlation import calculate_correlation_score
from .technical import calculate_technical_score
from .risk_manager import check_risk_rules

NY = pytz.timezone("America/New_York")

def calculate_full_score(data):
    now = datetime.now(NY)
    
    # ====================== LAYER 1 — Macro Gate ======================
    layer1 = get_macro_gate(now)
    if layer1["score"] == -100:
        return {
            "total_score": 0,
            "grade": "NONE",
            "direction": "NEUTRAL",
            "layers": {"layer1_macro": layer1},
            "gate_fail": True,
            "reason": layer1["reason"],
            "max_score": 140
        }

    # ====================== LAYER 2~6 ======================
    layer2 = calculate_regime_score(
        vix_price=data.get("vix_price"), 
        vix3m_price=data.get("vix3m_price"),
        spy_price=data.get("spy_price"), 
        prev_close=data.get("prev_close")
    )
    layer3 = get_options_flow_score(data)      # ← Placeholder (나중에 API 연결)
    layer4 = calculate_correlation_score(data.get("pcts", {}))
    layer5 = get_time_window_score(now)        # ← 버그 완전 수정됨
    layer6 = calculate_technical_score(
        spy_price=data.get("spy_price"),
        vwap=data.get("vwap"),
        vol_ratio=data.get("vol_ratio"),
        range_value=data.get("range_value")
    )
    layer7 = check_risk_rules(data.get("portfolio", {}))

    # 총점 계산 (140점 만점)
    total = (
        layer2.get("score", 0) +
        layer3.get("score", 0) +
        layer4.get("score", 0) +
        layer5.get("score", 0) +
        layer6.get("score", 0)
    )

    normalized = max(0, min(100, int((total / 140) * 100)))

    grade = "STRONG" if normalized >= 90 else \
            "MODERATE" if normalized >= 75 else \
            "WEAK" if normalized >= 60 else "NONE"

    return {
        "total_score": normalized,
        "grade": grade,
        "direction": layer6.get("direction_bias", "NEUTRAL"),
        "layers": {
            "layer1_macro": layer1,
            "layer2_regime": layer2,
            "layer3_options_flow": layer3,
            "layer4_correlation": layer4,
            "layer5_time_window": layer5,      # ← 이제 정확히 나옴
            "layer6_technical": layer6,
            "layer7_risk": layer7
        },
        "gate_fail": False,
        "max_score": 140,
        "raw_total": total
    }

# Layer 1: Macro & Event Gate
def get_macro_gate(now):
    # TODO: Investing.com API 연결 전까지 간단 체크
    if now.weekday() == 4 and now.hour >= 8:   # 금요일 오후 등
        return {"score": -100, "reason": "High-risk day (Friday session)"}
    return {"score": 0, "reason": "OK"}

# Layer 3: Options Flow (Unusual Whales API 자리 - 지금은 Placeholder)
def get_options_flow_score(data):
    return {
        "score": 15,
        "max": 30,
        "reason": "API pending (Layer 3 will be 0~30 after Unusual Whales connection)",
        "gex": None,
        "gamma_wall": None
    }
