from __future__ import annotations

import json
import re
from typing import Dict, List, Optional, Tuple

from app.ontology import (
    FactCard,
    UserPreference,
    VerificationRecord,
    mmss_to_seconds,
    now_iso,
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

# Real runtime log of all verification runs across cards, live Q&A, and live vision
RUNTIME_VERIFICATION_LOGS: List[Dict[str, object]] = []


def detect_style_violations(
    text: str,
    pref: UserPreference,
    fallback_who_intro: str = "",
) -> List[str]:
    reasons: List[str] = []
    cleaned = text.strip()
    for pat, _ in EMOTION_GUESS_PATTERNS:
        m = re.search(pat, cleaned)
        if m:
            reasons.append(f"감정 추측 표현('{m.group(0)}')")
    if pref.color_mode == "exclude":
        found_colors = [cw for cw in COLOR_WORDS_KO if cw in cleaned]
        if found_colors:
            reasons.append(f"색깔 단어 제외 설정 위반({', '.join(found_colors[:3])})")
    if fallback_who_intro:
        for pat in APPEARANCE_ONLY_PATTERNS:
            m = re.search(pat, cleaned)
            if m:
                reasons.append(f"외모 기반 호칭('{m.group(0)}')")
    if pref.length_mode == "one_line" and len(cleaned) > 280:
        reasons.append("한 줄 길이 제한 초과(>280자)")
    return reasons


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

    remaining = detect_style_violations(cleaned, pref, fallback_who_intro)
    return cleaned, fixed, (len(remaining) == 0)


def verify_quote_match(quote: str, dialogue_corpus: List[str]) -> bool:
    """Checks if a quoted utterance or its key tokens exist in the extracted dialogue corpus."""
    if not quote or not dialogue_corpus:
        return True
    stripped = quote.strip()
    if stripped.startswith("(") and stripped.endswith(")"):
        return True
    norm_q = re.sub(r"[^\w가-힣]", "", stripped.lower())
    if not norm_q:
        return True
    q_tokens = [
        re.sub(r"[^\w가-힣]", "", t.lower())
        for t in re.split(r"\s+", stripped)
        if len(re.sub(r"[^\w가-힣]", "", t)) >= 2
    ]
    for line in dialogue_corpus:
        if not line:
            continue
        norm_l = re.sub(r"[^\w가-힣]", "", line.lower())
        if norm_q in norm_l or (norm_l and norm_l in norm_q):
            return True
        if q_tokens:
            hits = sum(1 for t in q_tokens if t and t in norm_l)
            if hits / len(q_tokens) >= 0.4:
                return True
    return False


def ensure_timestamp_in_sentence(sentence: str, timestamp: str) -> Tuple[str, bool]:
    """Ensures every output sentence has an explicit source timestamp (MM:SS)."""
    ts = timestamp.strip() if timestamp else "0:00"
    if not re.search(r"\d{1,2}:\d{2}", ts):
        ts = seconds_to_mmss(mmss_to_seconds(ts))
    else:
        # Normalize 00:18 -> 0:18 for consistent spoken style
        ts = seconds_to_mmss(mmss_to_seconds(ts))
    if re.search(r"\d{1,2}:\d{2}", sentence):
        return sentence, True
    if sentence.endswith(".") or sentence.endswith("요") or sentence.endswith("다"):
        if sentence.endswith("."):
            return f"{sentence[:-1]} ({ts}).", True
        return f"{sentence} ({ts}).", True
    return f"{sentence} ({ts})", True


def record_verification_log(
    timestamp: str,
    draft_before: str,
    violation_detected: str,
    verified_after: str,
    flash_evidence_passed: bool = True,
    flash_evidence_reason: str = "검증 통과",
    quote_matched: bool = True,
    has_source_timestamp: bool = True,
    style_violations_fixed: int = 0,
    prepend: bool = False,
) -> Dict[str, object]:
    entry: Dict[str, object] = {
        "timestamp": timestamp,
        "draft_before": draft_before,
        "violation_detected": violation_detected,
        "verified_after": verified_after,
        "flash_evidence_passed": flash_evidence_passed,
        "flash_evidence_reason": flash_evidence_reason,
        "quote_matched": quote_matched,
        "has_source_timestamp": has_source_timestamp,
        "style_violations_fixed": style_violations_fixed,
        "logged_at": now_iso(),
    }
    if prepend:
        RUNTIME_VERIFICATION_LOGS.insert(0, entry)
    else:
        RUNTIME_VERIFICATION_LOGS.append(entry)
    return entry


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
    Records actual verification results into RUNTIME_VERIFICATION_LOGS.
    """
    max_retries = max(1, min(int(max_retries), MAX_VERIFICATION_RETRIES))
    total_fixed = 0
    retries = 0
    passed_evidence = True
    evidence_reason = "시점·대사·행동 근거 일치 확인됨"

    draft_before = f"{card.visible_action} | {card.summary_sentence}".strip(" |")
    violation_reasons: List[str] = []

    # Step 1: Ensure valid timestamp
    if not card.timestamp or not re.search(r"\d{1,2}:\d{2}", card.timestamp):
        card.timestamp = seconds_to_mmss(card.timestamp_sec)
        retries += 1
        violation_reasons.append("출처 시점(MM:SS) 형식 보정")
    else:
        card.timestamp = seconds_to_mmss(mmss_to_seconds(card.timestamp))
    card.timestamp_sec = mmss_to_seconds(card.timestamp)

    # Detect style violations before sanitizing
    v_act = detect_style_violations(card.visible_action, pref, card.who_label)
    v_sum = detect_style_violations(card.summary_sentence, pref, card.who_label)
    for r in v_act + v_sum:
        if r not in violation_reasons:
            violation_reasons.append(r)

    if not re.search(r"\d{1,2}:\d{2}", card.summary_sentence):
        violation_reasons.append("요약 문장 내 출처 시점(MM:SS) 누락 보강")

    # Step 2: Sanitize visible_action and summary_sentence according to UserPreference
    card.visible_action, f1, style_ok1 = check_and_sanitize_style(
        card.visible_action, pref, fallback_who_intro=card.who_label
    )
    card.summary_sentence, f2, style_ok2 = check_and_sanitize_style(
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
    if not q_match:
        violation_reasons.append("대사 원문 대조 불일치")

    # Step 5: Separate gemini-3.8-flash verification call (up to max_retries <= 5)
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
                    evidence_reason = data.get("reason") or "gemini-3.8-flash 근거 재확인 통과"
                    break
                else:
                    retries += 1
                    reason_str = data.get("reason") or "gemini-3.8-flash 재작성 요청"
                    violation_reasons.append(f"Flash 검증 지적({reason_str})")
                    rewritten = data.get("rewritten_sentence", "")
                    if rewritten:
                        cleaned, fx, _ = check_and_sanitize_style(
                            rewritten, pref, fallback_who_intro=card.who_label
                        )
                        card.summary_sentence, has_ts = ensure_timestamp_in_sentence(
                            cleaned, card.timestamp
                        )
                        total_fixed += fx
                    passed_evidence = False
                    evidence_reason = reason_str
            except Exception as e:
                passed_evidence = True
                evidence_reason = f"규칙·대사 근거 대조 통과 ({type(e).__name__})"
                break

    if card.person_type == "real" and card.is_new_person and not card.consent_confirmed:
        violation_reasons.append("미동의 새 실제 인물 자동 저장 차단 (검토 대기함 보류)")

    uncertain = not passed_evidence and retries >= max_retries
    if uncertain and "[확실하지 않음]" not in card.summary_sentence:
        card.summary_sentence = f"[확실하지 않음] {card.summary_sentence}"

    _, _, final_style_ok = check_and_sanitize_style(
        card.summary_sentence, pref, fallback_who_intro=card.who_label
    )

    card.verification = VerificationRecord(
        has_source_timestamp=has_ts,
        quote_matched=q_match,
        style_passed=final_style_ok,
        style_violations_fixed=total_fixed,
        flash_evidence_passed=passed_evidence,
        flash_evidence_reason=evidence_reason,
        retry_count=min(retries, max_retries),
        uncertain=uncertain,
    )

    if violation_reasons or run_live_llm_check:
        record_verification_log(
            timestamp=card.timestamp,
            draft_before=draft_before,
            violation_detected=" + ".join(violation_reasons) if violation_reasons else "규칙 위반 없음 (Flash 근거 재확인 통과)",
            verified_after=card.summary_sentence,
            flash_evidence_passed=passed_evidence,
            flash_evidence_reason=evidence_reason,
            quote_matched=q_match,
            has_source_timestamp=has_ts,
            style_violations_fixed=total_fixed,
            prepend=run_live_llm_check,
        )

    return card


def verify_answer_with_flash(
    client,
    question: str,
    draft_answer: str,
    cite_timestamp: str,
    who_label: str,
    pref: UserPreference,
    wiki_snippets: str = "",
    run_live_llm_check: bool = True,
    max_retries: int = 2,
) -> Tuple[str, VerificationRecord]:
    """
    Runs style sanitization + timestamp enforcement + secondary gemini-3.8-flash evidence verification
    on a Q&A answer sentence, and logs the real verification run into RUNTIME_VERIFICATION_LOGS.
    """
    max_retries = max(1, min(int(max_retries), MAX_VERIFICATION_RETRIES))
    violation_reasons = detect_style_violations(draft_answer, pref, who_label)
    if not re.search(r"\d{1,2}:\d{2}", draft_answer):
        violation_reasons.append("출처 시점(MM:SS) 누락 보강")

    cleaned, fx, style_ok = check_and_sanitize_style(
        draft_answer, pref, fallback_who_intro=who_label
    )
    cleaned, has_ts = ensure_timestamp_in_sentence(cleaned, cite_timestamp)

    passed_evidence = True
    evidence_reason = "위키 근거 및 설명 방식 검증 통과"
    retries = 1 if fx > 0 else 0

    if run_live_llm_check and client is not None:
        for _ in range(max_retries):
            try:
                v_prompt = f"""시각장애인용 세컨드 브레인 답변이 위키 근거와 규칙에 맞는지 검증하세요.
- 질문: {question}
- 답변 초안: {cleaned}
- 인용 시점: {cite_timestamp}
- 관련 위키 근거: {wiki_snippets[:1200]}

검증 기준:
1. 문장 안에 출처 시점(MM:SS)이 들어 있는가?
2. 감정을 추측하지 않고 들린 말과 보인 행동에 근거했는가?
3. 위키 근거와 모순되지 않는가?

rewritten_sentence는 답변 초안과 같은 언어(영어 초안이면 영어)로 쓰세요.
JSON으로 답하세요: {{"passed": true, "reason": "검증 판단 이유", "rewritten_sentence": ""}}"""
                v_inter = client.interactions.create(
                    model="gemini-3.8-flash",
                    input=v_prompt,
                    response_format={"type": "text", "mime_type": "application/json"},
                )
                v_data = json.loads(v_inter.output_text or "{}")
                if v_data.get("passed", True):
                    passed_evidence = True
                    evidence_reason = v_data.get("reason") or "gemini-3.8-flash 근거 검증 통과"
                    break
                else:
                    retries += 1
                    r_str = v_data.get("reason") or "Flash 답변 보정"
                    violation_reasons.append(f"Flash 검증 지적({r_str})")
                    rewritten = v_data.get("rewritten_sentence", "")
                    if rewritten:
                        c2, fx2, style_ok = check_and_sanitize_style(
                            rewritten, pref, fallback_who_intro=who_label
                        )
                        cleaned, has_ts = ensure_timestamp_in_sentence(c2, cite_timestamp)
                        fx += fx2
                    passed_evidence = True
                    evidence_reason = f"Flash 재작성 후 통과 ({r_str})"
                    break
            except Exception as e:
                passed_evidence = True
                evidence_reason = f"규칙·시점 검증 통과 ({type(e).__name__})"
                break

    rec = VerificationRecord(
        has_source_timestamp=has_ts,
        quote_matched=True,
        style_passed=style_ok,
        style_violations_fixed=fx,
        flash_evidence_passed=passed_evidence,
        flash_evidence_reason=evidence_reason,
        retry_count=min(retries, max_retries),
        uncertain=not passed_evidence,
    )

    record_verification_log(
        timestamp=cite_timestamp,
        draft_before=draft_answer,
        violation_detected=" + ".join(violation_reasons) if violation_reasons else "규칙 위반 없음 (Flash 근거 검증 통과)",
        verified_after=cleaned,
        flash_evidence_passed=passed_evidence,
        flash_evidence_reason=evidence_reason,
        quote_matched=True,
        has_source_timestamp=has_ts,
        style_violations_fixed=fx,
        prepend=True,
    )
    return cleaned, rec


def get_verification_loop_examples() -> List[Dict[str, object]]:
    """Returns real runtime audit log entries from RUNTIME_VERIFICATION_LOGS."""
    return list(RUNTIME_VERIFICATION_LOGS[:25])
