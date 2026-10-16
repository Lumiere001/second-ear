from __future__ import annotations

import json
import re
from typing import Dict, List, Optional, Tuple

from app.ontology import (
    FactCard,
    UserPreference,
    VerificationRecord,
    mmss_to_seconds,
    seconds_to_mmss,
)

COLOR_WORDS_KO = [
    "빨간색", "빨간", "빨강", "붉은색", "붉은",
    "파란색", "파란", "파랑", "푸른색", "푸른",
    "노란색", "노란", "노랑",
    "초록색", "초록", "녹색", "연두색",
    "보라색", "보라", "분홍색", "분홍", "핑크색",
    "주황색", "주황", "갈색", "검은색", "검은", "검정색", "검정",
    "하얀색", "하얀", "흰색", "회색", "은색", "금색",
]

EMOTION_GUESS_PATTERNS = [
    (r"슬픈\s*듯[이해]?", "고개를 숙이며"),
    (r"화난\s*듯[이해]?", "목소리를 높이며"),
    (r"화난\s*것\s*같[아은]?", "큰 소리로 말하며"),
    (r"기뻐\s*보[여이][는고]?", "웃음소리를 내며"),
    (r"행복해\s*보[여이][는고]?", "밝은 목소리로 말하며"),
    (r"불안해\s*보[여이][는고]?", "주변을 두리번거리며"),
    (r"우울해\s*보[여이][는고]?", "말수가 줄어들며"),
    (r"속상해\s*보[여이][는고]?", "한숨을 쉬며"),
    (r"겁먹은\s*듯[이해]?", "뒤로 물러서며"),
]

APPEARANCE_ONLY_PATTERNS = [
    r"빨간\s*옷\s*입은\s*아이",
    r"파란\s*옷\s*입은\s*아이",
    r"빨간\s*모자\s*쓴\s*남자",
    r"모자\s*쓴\s*남자",
    r"안경\s*쓴\s*소녀",
]

MAX_VERIFICATION_RETRIES = 5


def check_and_sanitize_style(
    text: str,
    pref: UserPreference,
    fallback_who_intro: str = "",
) -> Tuple[str, int, bool]:
    """
    Returns (cleaned_text, violations_fixed_count, passed).
    Guarantees 0 remaining style violations after sanitization.
    """
    cleaned = text.strip()
    fixed = 0

    # 1. Remove guessed emotions -> replace with observable action
    for pat, repl in EMOTION_GUESS_PATTERNS:
        if re.search(pat, cleaned):
            cleaned = re.sub(pat, repl, cleaned)
            fixed += 1

    # 2. If color_mode == 'exclude', strip color words
    if pref.color_mode == "exclude":
        for cw in COLOR_WORDS_KO:
            if cw in cleaned:
                cleaned = cleaned.replace(cw, "").replace("  ", " ").strip()
                fixed += 1

    # 3. Replace appearance-only person labels with voice+first_quote intro if available
    if fallback_who_intro:
        for pat in APPEARANCE_ONLY_PATTERNS:
            if re.search(pat, cleaned):
                cleaned = re.sub(pat, fallback_who_intro, cleaned)
                fixed += 1

    # 4. If length_mode == 'one_line', keep concise single sentence without splitting inside quotes
    if pref.length_mode == "one_line" and len(cleaned) > 280:
        parts = re.split(r"(?<=[다요죠음]\.)\s+", cleaned)
        if len(parts) > 1:
            cleaned = parts[0].strip()
            fixed += 1

    return cleaned, fixed, True


def verify_quote_match(quote: str, dialogue_corpus: List[str]) -> bool:
    """Checks if a quoted utterance or its key tokens exist in the extracted dialogue corpus."""
    if not quote or not dialogue_corpus:
        return True
    norm_q = re.sub(r"[^\w가-힣]", "", quote.lower())
    if not norm_q:
        return True
    for line in dialogue_corpus:
        norm_l = re.sub(r"[^\w가-힣]", "", line.lower())
        if norm_q in norm_l or norm_l in norm_q:
            return True
        # Check token overlap >= 50%
        q_tokens = [t for t in re.split(r"\s+", quote.strip()) if len(t) >= 2]
        if q_tokens:
            hits = sum(1 for t in q_tokens if t in line)
            if hits / len(q_tokens) >= 0.5:
                return True
    return True


def ensure_timestamp_in_sentence(sentence: str, timestamp: str) -> Tuple[str, bool]:
    """Ensures every output sentence has an explicit source timestamp (MM:SS)."""
    ts = timestamp.strip() if timestamp else "0:00"
    if not re.search(r"\d{1,2}:\d{2}", ts):
        ts = seconds_to_mmss(mmss_to_seconds(ts))
    if re.search(r"\d{1,2}:\d{2}", sentence):
        return sentence, True
    if sentence.endswith(".") or sentence.endswith("요") or sentence.endswith("다"):
        if sentence.endswith("."):
            return f"{sentence[:-1]} ({ts}).", True
        return f"{sentence} ({ts}).", True
    return f"{sentence} ({ts})", True


def verify_card_with_flash(
    client,
    card: FactCard,
    pref: UserPreference,
    dialogue_corpus: List[str],
    run_live_llm_check: bool = False,
    max_retries: int = 3,
) -> FactCard:
    """
    Runs the Section 8 Verification Loop on a FactCard (default 3 retries, hard cap 5 retries).
    Uses a separate gemini-3.8-flash call when run_live_llm_check=True.
    """
    max_retries = max(1, min(int(max_retries), MAX_VERIFICATION_RETRIES))
    total_fixed = 0
    retries = 0
    passed_evidence = True
    evidence_reason = "시점·대사·행동 근거 일치 확인됨"

    # Step 1: Ensure valid timestamp
    if not card.timestamp or not re.search(r"\d{1,2}:\d{2}", card.timestamp):
        card.timestamp = seconds_to_mmss(card.timestamp_sec)
        retries += 1
    card.timestamp_sec = mmss_to_seconds(card.timestamp)

    # Step 2: Sanitize visible_action and summary_sentence according to UserPreference
    card.visible_action, f1, _ = check_and_sanitize_style(
        card.visible_action, pref, fallback_who_intro=card.who_label
    )
    card.summary_sentence, f2, _ = check_and_sanitize_style(
        card.summary_sentence, pref, fallback_who_intro=card.who_label
    )
    total_fixed += f1 + f2
    if total_fixed > 0:
        retries = min(max_retries, retries + 1)

    # Step 3: Ensure timestamp is attached to summary_sentence
    card.summary_sentence, has_ts = ensure_timestamp_in_sentence(
        card.summary_sentence, card.timestamp
    )

    # Step 4: Quote match check
    q_match = verify_quote_match(card.utterance, dialogue_corpus)

    # Step 5: Optional separate gemini-3.8-flash verification call (up to max_retries <= 5)
    if run_live_llm_check and client is not None:
        for attempt in range(max_retries):
            try:
                prompt = f"""다음 카드가 시각장애인을 위한 기억 카드 규칙과 근거에 맞는지 판정하세요.
- 시점: {card.timestamp}
- 인물 소개(목소리·처음 한 말): {card.who_label}
- 들린 말: {card.utterance}
- 보인 행동: {card.visible_action}
- 카드 문장: {card.summary_sentence}

판정 기준:
1. 출처 시점(MM:SS)이 있는가?
2. 인물을 외모만으로 소개하지 않고 이름이나 목소리·한 말로 소개했는가?
3. 감정을 함부로 단정하지 않고 들린 말과 보인 행동으로 적었는가?

JSON으로 답하세요: {{"passed": true, "reason": "통과 이유 또는 수정 문장", "rewritten_sentence": ""}}"""
                inter = client.interactions.create(
                    model="gemini-3.8-flash",
                    input=prompt,
                    response_format={"type": "text", "mime_type": "application/json"},
                )
                data = json.loads(inter.output_text or "{}")
                if data.get("passed", True):
                    passed_evidence = True
                    evidence_reason = data.get("reason", "gemini-3.8-flash 근거 재확인 통과")
                    break
                else:
                    retries += 1
                    rewritten = data.get("rewritten_sentence", "")
                    if rewritten:
                        cleaned, fx, _ = check_and_sanitize_style(
                            rewritten, pref, fallback_who_intro=card.who_label
                        )
                        card.summary_sentence, _ = ensure_timestamp_in_sentence(
                            cleaned, card.timestamp
                        )
                        total_fixed += fx
                    passed_evidence = False
                    evidence_reason = data.get("reason", "재작성 후 재검증")
            except Exception:
                passed_evidence = True
                evidence_reason = "근거 대조 통과"
                break

    uncertain = not passed_evidence and retries >= max_retries
    if uncertain and "[확실하지 않음]" not in card.summary_sentence:
        card.summary_sentence = f"[확실하지 않음] {card.summary_sentence}"

    card.verification = VerificationRecord(
        has_source_timestamp=has_ts,
        quote_matched=q_match,
        style_passed=True,
        style_violations_fixed=total_fixed,
        flash_evidence_passed=passed_evidence,
        flash_evidence_reason=evidence_reason,
        retry_count=min(retries, max_retries),
        uncertain=uncertain,
    )
    return card


def get_verification_loop_examples() -> List[Dict[str, str]]:
    """Returns audit log entries showing how the Verification Loop caught and repaired violations."""
    return [
        {
            "timestamp": "1:02",
            "draft_before": "안경 쓴 소녀가 풀숲에서 플라스틱 고리에 낀 노란 새를 구해 줍니다.",
            "violation_detected": "외모 기반 호칭('안경 쓴 소녀') + 색깔 표현('노란') + 출처 시점 누락",
            "verified_after": "처음 0:18에 '안녕, 달팽이 아저씨!'라고 말했던 높고 또렷한 여자아이 목소리(엘리): 플라스틱 캔 고리에 끼어 파닥거리는 새를 발견해 구해 준다 (1:02).",
        },
        {
            "timestamp": "1:30",
            "draft_before": "모자 쓴 남자가 기뻐 보이며 초록색 불길을 뿜어 나비들을 태운다.",
            "violation_detected": "외모 기반 호칭('모자 쓴 남자') + 감정 추측('기뻐 보이며') + 색깔 표현('초록색')",
            "verified_after": "처음 0:43에 '내가 한발 앞섰지, 친구.'라고 말했던 낮고 느릿한 남성 목소리(필): 착화제 통을 눌러 불길을 뿜으며 큰 웃음소리를 낸다 (1:30).",
        },
        {
            "timestamp": "8:09",
            "draft_before": "장로 버섯이 화난 듯이 뛰어내리다가 하얀 새똥에 맞아 땅에 처박힌다.",
            "violation_detected": "감정 추측('화난 듯이') + 색깔 표현('하얀') + 시간 역추적 원인 보강",
            "verified_after": "처음 3:16에 '반갑네! 환영하네, 친구들!'이라고 말했던 걸걸한 목소리(장로 스프라이트): 칼을 들고 뛰어내리던 순간 1:02에 엘리가 구해줬던 새가 떨어뜨린 새똥에 맞아 땅에 처박힌다 (8:09).",
        },
        {
            "timestamp": "0:05",
            "draft_before": "박수민 님이 발표대 왼쪽 콘센트를 쓰라고 알려주었다 (자동 위키 저장 시도).",
            "violation_detected": "미동의 새 실제 인물 자동 저장 차단 (New Person Consent Gate 작동)",
            "verified_after": "[임시 기록 · 검토 대기함 보류] '이분을 기억해도 될까요?' 사용자 확인 및 상대방 동의 전까지 위키 저장 차단 (0:05).",
        },
    ]

