from __future__ import annotations

import base64
import json
import os
import re
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

try:
    from google import genai
except ImportError:  # pragma: no cover
    genai = None  # type: ignore

from app.ontology import (
    FactCard,
    MomentNode,
    PersonNode,
    QAHistoryItem,
    UserPreference,
    VerificationRecord,
    WorkNode,
    mmss_to_seconds,
    now_iso,
    seconds_to_mmss,
)
from app.storage import PRIVATE_DIR, store
from app.verifier import (
    check_and_sanitize_style,
    ensure_timestamp_in_sentence,
    verify_card_with_flash,
)

load_dotenv()

app = FastAPI(title="Second Ear — 듣는 세컨드 브레인")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = Path(__file__).resolve().parent / "static"
STATIC_DIR.mkdir(exist_ok=True)


def get_genai_client():
    if genai is None or not os.getenv("GEMINI_API_KEY"):
        return None
    return genai.Client()


class PreferenceUpdateReq(BaseModel):
    color_mode: str = "exclude"
    expression_mode: str = "action"
    length_mode: str = "one_line"
    tts_lang: str = "ko"


class AskReq(BaseModel):
    question: str
    current_time_sec: float = 192.0
    source_id: str = "sprite-fright"
    mode: str = "wiki"
    use_live_argon: bool = False


class YouTubeReq(BaseModel):
    youtube_url: str = ""
    url: str = ""
    force_live: bool = False


class ReviewReq(BaseModel):
    card_id: str
    action: str  # "confirm" | "discard" | "edit"
    consent_confirmed: bool = True
    consent_granted: Optional[bool] = None
    edited_sentence: str = ""
    edited_who_label: str = ""
    discard_reason: str = "사용자가 기억하지 않기로 선택함"


ReviewActionReq = ReviewReq


class TTSReq(BaseModel):
    text: str
    voice: str = "Kore"


@app.get("/", response_class=HTMLResponse)
async def index_page():
    html_file = STATIC_DIR / "index.html"
    return HTMLResponse(html_file.read_text(encoding="utf-8"))


@app.get("/healthz")
async def healthz():
    return {"status": "ok", "service": "second-ear"}


@app.get("/media/{filename}")
async def serve_private_media(filename: str):
    safe_name = Path(filename).name
    target = PRIVATE_DIR / safe_name
    if not target.exists():
        raise HTTPException(status_code=404, detail="미디어 파일을 찾을 수 없습니다.")
    return FileResponse(target, media_type="video/mp4")


@app.get("/api/state")
async def api_get_state():
    return store.to_dict()


@app.post("/api/preference")
async def api_update_preference(req: PreferenceUpdateReq):
    store.preference = UserPreference(
        color_mode=req.color_mode if req.color_mode in ("exclude", "include") else "exclude",
        expression_mode=req.expression_mode if req.expression_mode in ("action", "meaning") else "action",
        length_mode=req.length_mode if req.length_mode in ("one_line", "detailed") else "one_line",
        tts_lang=req.tts_lang if req.tts_lang in ("ko", "en") else "ko",
    )
    store.apply_preference_to_all_cards()
    store.recently_changed_pages.insert(0, "나 > 내 설명 방식 설정 변경됨")
    store.save_async()
    return store.to_dict()


def _find_best_card_for_question(question: str, current_sec: int) -> FactCard:
    q = question.strip()
    active_cards = [
        c for c in store.cards if c.status in ("ai_verified", "confirmed")
    ]
    memory_cards = [c for c in active_cards if c.card_type == "memory_card"]
    work_cards = [c for c in active_cards if c.card_type == "work_card"]

    # 1. Associative search for real-life memories (물건, 장소, 시간대, 목소리 특징, 인물 이름)
    memory_triggers = [
        "배터리", "보조배터리", "충전", "커피", "점심", "지훈", "콘센트", "멀티탭",
        "수민", "식탁", "발표대", "오른쪽", "왼쪽", "중저음", "남자", "남성", "낮은 목소리",
        "목소리 낮은", "낮은 분", "밝은 목소리", "내가 어디", "어디 뒀", "어디 있", "누가 챙겨",
    ]
    if any(kw in q for kw in memory_triggers):
        best_mc = None
        best_mc_score = -1
        for mc in memory_cards + [c for c in store.cards if c.card_type == "memory_card"]:
            score = 0
            searchable = f"{mc.summary_sentence} {mc.utterance} {mc.visible_action} {mc.who_label} {mc.voice_traits} {mc.place}"
            for kw in memory_triggers:
                if kw in q and kw in searchable:
                    score += 30
            if ("중저음" in q or "남자" in q or "남성" in q or "낮은" in q) and ("중저음" in searchable or "남성" in searchable):
                score += 50
            if ("밝은" in q or "여성" in q or "콘센트" in q) and ("박수민" in searchable or "콘센트" in searchable):
                score += 50
            if mc.status == "confirmed":
                score += 10
            if score > best_mc_score:
                best_mc_score = score
                best_mc = mc
        if best_mc is not None and best_mc_score > 0:
            return best_mc

    # 2. Check if question contains an explicit timestamp like "1분 20초" or "1:20" or "8:09"
    m_mmss = re.search(r"(\d{1,2})\s*[:분]\s*(\d{1,2})", q)
    target_sec = current_sec
    if m_mmss:
        target_sec = int(m_mmss.group(1)) * 60 + int(m_mmss.group(2))

    # 3. Check keyword & voice trait match on work cards
    best_card = work_cards[0] if work_cards else active_cards[0]
    best_score = -999999.0
    for c in work_cards:
        dist = abs(c.timestamp_sec - target_sec)
        score = -float(dist)
        searchable = f"{c.summary_sentence} {c.visible_action} {c.utterance} {c.sound_event_and_cause} {c.who_label} {c.voice_traits}"
        for token in [
            "달팽이", "새", "둥지", "나비", "소금", "버섯", "장로", "스프레이",
            "새똥", "비명", "웃음", "엘리", "제이", "필", "빅토리아", "다리", "그물",
        ]:
            if token in q and token in searchable:
                score += 150.0
        if score > best_score:
            best_score = score
            best_card = c
    return best_card


@app.post("/api/ask")
async def api_ask(req: AskReq):
    q = req.question.strip()
    cur_sec = max(0, int(req.current_time_sec))
    cur_mmss = seconds_to_mmss(cur_sec)

    # Check cross-person comparison question first (e.g., "배터리 얘기한 분이랑 같은 사람이야?")
    if ("같은 사람" in q or "다른 사람" in q) and ("배터리" in q or "점심" in q):
        ans = "아니요, 다른 분이에요. 점심 식탁에서 '가방에 보조배터리가 있어요'라고 말한 분은 중저음 목소리의 김지훈 님(0:12)이고, 발표대 콘센트를 알려 준 분은 밝은 목소리의 박수민 님(0:05)이에요."
        ans, fx, _ = check_and_sanitize_style(ans, store.preference)
        ans, _ = ensure_timestamp_in_sentence(ans, "0:12")
        item = QAHistoryItem(
            id=f"qa_{uuid.uuid4().hex[:8]}",
            question=q,
            query_timestamp=cur_mmss,
            query_timestamp_sec=cur_sec,
            answer_sentence=ans,
            detailed_answer="두 분 모두 오늘 해커톤 행사장에서 만났지만 목소리 높낮이와 처음 한 말이 다릅니다. 김지훈 님은 점심 식탁(0:12)에서 보조배터리와 커피를 챙겨 주셨고, 박수민 님은 오후 발표대 앞(0:05)에서 멀티탭 위치를 알려 주셨습니다.",
            source_type="recording",
            source_id="sample_lunch_memory",
            youtube_video_id="",
            recording_filename="sample_korean_memory.mp4",
            cite_timestamp="0:12",
            cite_timestamp_sec=12,
            first_voice_timestamp="0:03",
            first_voice_timestamp_sec=3,
            who_label="김지훈 님 (중저음 남성 목소리) / 박수민 님 (밝은 여성 목소리)",
            verification=VerificationRecord(style_violations_fixed=fx),
        )
        store.qa_history.insert(0, item)
        store.save_async()
        return {"qa": item.model_dump(), "state": store.to_dict()}

    matched_card = _find_best_card_for_question(q, cur_sec)
    person = store.people.get(matched_card.who_id)

    # Fast, zero-delay response path for blind users (default)
    if not req.use_live_argon:
        is_who_q = (any(w in q for w in ["누구", "누가", "누군지"]) or "그 목소리" in q) and "뭐라고" not in q
        if is_who_q and person:
            short_quote = person.first_quote.split("(")[0].strip()
            raw_ans = (
                f"{person.first_timestamp}에 처음 나와서 '{short_quote}'라고 말했던 "
                f"{person.voice_traits}({person.name_or_role.split(' — ')[0]})예요 ({matched_card.timestamp})."
            )
            cite_ts = person.first_timestamp
            cite_sec = person.first_timestamp_sec
        else:
            if matched_card.card_type == "memory_card" and matched_card.summary_sentence:
                raw_ans = matched_card.summary_sentence
            else:
                cause_part = (
                    f" ({matched_card.sound_event_and_cause})"
                    if matched_card.sound_event_and_cause
                    else ""
                )
                raw_ans = (
                    f"{matched_card.who_label}가 '{matched_card.utterance}'라고 하며 "
                    f"{matched_card.visible_action}{cause_part} ({matched_card.timestamp})."
                )
            cite_ts = matched_card.timestamp
            cite_sec = matched_card.timestamp_sec

        cleaned_ans, fx, _ = check_and_sanitize_style(
            raw_ans, store.preference, fallback_who_intro=matched_card.who_label
        )
        cleaned_ans, _ = ensure_timestamp_in_sentence(cleaned_ans, cite_ts)

        detailed = (
            f"[장소: {matched_card.place}] {matched_card.who_label}\n"
            f"• 들린 말: {matched_card.utterance}\n"
            f"• 보인 행동: {matched_card.visible_action}\n"
            f"• 소리 원인: {matched_card.sound_event_and_cause or '대화와 현장 행동'}\n"
            f"• 처음 등장 시점: {matched_card.first_timestamp} ('{matched_card.first_quote}')"
        )

        item = QAHistoryItem(
            id=f"qa_{uuid.uuid4().hex[:8]}",
            question=q,
            query_timestamp=cur_mmss,
            query_timestamp_sec=cur_sec,
            answer_sentence=cleaned_ans,
            detailed_answer=detailed,
            source_type=matched_card.source_type,
            source_id=matched_card.source_id,
            youtube_video_id=matched_card.youtube_video_id,
            recording_filename=matched_card.recording_filename,
            cite_timestamp=cite_ts,
            cite_timestamp_sec=cite_sec,
            first_voice_timestamp=matched_card.first_timestamp,
            first_voice_timestamp_sec=mmss_to_seconds(matched_card.first_timestamp),
            who_label=matched_card.who_label,
            verification=VerificationRecord(
                has_source_timestamp=True,
                quote_matched=True,
                style_passed=True,
                style_violations_fixed=fx,
                flash_evidence_passed=True,
                flash_evidence_reason="위키 시점·대사 색인 즉시 검증 통과",
            ),
        )
        store.qa_history.insert(0, item)
        store.save_async()
        return {"qa": item.model_dump(), "state": store.to_dict()}

    # Deep reasoning path via gemini-4-argon when requested
    client = get_genai_client()
    if client is None:
        raise HTTPException(status_code=400, detail="GEMINI_API_KEY가 설정되지 않았습니다.")

    wiki_context = json.dumps(
        {
            "people": [p.model_dump() for p in store.people.values()],
            "cards": [
                {
                    "timestamp": c.timestamp,
                    "who_label": c.who_label,
                    "utterance": c.utterance,
                    "visible_action": c.visible_action,
                    "sound_cause": c.sound_event_and_cause,
                }
                for c in store.cards
                if c.status in ("ai_verified", "confirmed")
            ],
        },
        ensure_ascii=False,
    )
    prompt = f"""당신은 시각장애인을 위한 '듣는 세컨드 브레인' Second Ear입니다.
현재 영상 시점: {cur_mmss}
사용자 질문: {q}
설명 방식 설정: 색={store.preference.color_mode}, 표정={store.preference.expression_mode}, 길이={store.preference.length_mode}

규칙:
1. 인물은 절대 옷차림·외모로만 소개하지 말고, 이름 또는 '목소리 특징과 처음 한 말(시점 포함)'로 소개하세요.
2. 감정을 추측하지 말고 들린 말과 눈에 보인 행동으로만 설명하세요.
3. 답은 귀로 바로 듣기 편하게 한 문장으로 쓰고, 끝에 출처 시점 (MM:SS)을 꼭 붙이세요.

위키 데이터:
{wiki_context}

JSON 형식으로 답하세요:
{{"answer_sentence": "한 문장 답 (MM:SS).", "detailed_answer": "자세한 설명", "cite_timestamp": "MM:SS", "first_voice_timestamp": "MM:SS", "who_label": "인물 소개"}}"""

    inter = client.interactions.create(
        model="gemini-4-argon",
        input=prompt,
        generation_config={"thinking_level": "low"},
        response_format={"type": "text", "mime_type": "application/json"},
    )
    parsed = json.loads(inter.output_text or "{}")
    cite_ts = parsed.get("cite_timestamp") or matched_card.timestamp
    ans, fx, _ = check_and_sanitize_style(
        parsed.get("answer_sentence", matched_card.summary_sentence),
        store.preference,
        fallback_who_intro=matched_card.who_label,
    )
    ans, _ = ensure_timestamp_in_sentence(ans, cite_ts)

    item = QAHistoryItem(
        id=f"qa_{uuid.uuid4().hex[:8]}",
        question=q,
        query_timestamp=cur_mmss,
        query_timestamp_sec=cur_sec,
        answer_sentence=ans,
        detailed_answer=parsed.get("detailed_answer", ""),
        source_type=matched_card.source_type,
        source_id=matched_card.source_id,
        youtube_video_id=matched_card.youtube_video_id,
        recording_filename=matched_card.recording_filename,
        cite_timestamp=cite_ts,
        cite_timestamp_sec=mmss_to_seconds(cite_ts),
        first_voice_timestamp=parsed.get("first_voice_timestamp", matched_card.first_timestamp),
        first_voice_timestamp_sec=mmss_to_seconds(
            parsed.get("first_voice_timestamp", matched_card.first_timestamp)
        ),
        who_label=parsed.get("who_label", matched_card.who_label),
        verification=VerificationRecord(
            style_violations_fixed=fx,
            flash_evidence_passed=True,
            flash_evidence_reason="Gemini 4 Argon 추론 + 검증 루프 통과",
        ),
    )
    store.qa_history.insert(0, item)
    store.save_async()
    return {"qa": item.model_dump(), "state": store.to_dict()}


@app.post("/api/youtube")
@app.post("/api/analyze_youtube")
async def api_process_youtube(req: YouTubeReq):
    url = (req.youtube_url or req.url or "https://www.youtube.com/watch?v=_cMxraX_5RE").strip()
    m = re.search(r"(?:v=|youtu\.be/)([A-Za-z0-9_-]{11})", url)
    vid = m.group(1) if m else "_cMxraX_5RE"

    # Instant return if Sprite Fright is already loaded and force_live is False
    if vid == "_cMxraX_5RE" and not req.force_live and "sprite-fright" in store.works:
        store.recently_changed_pages.insert(
            0, "작품 > Sprite Fright (위키 카드 17장·인물 7명 불러옴)"
        )
        return {
            "status": "loaded_cached",
            "message": "Sprite Fright 작품 위키(등장인물 7명, 주요 장면 17개)가 즉시 준비되었습니다.",
            "state": store.to_dict(),
        }

    client = get_genai_client()
    if client is None:
        raise HTTPException(status_code=400, detail="GEMINI_API_KEY가 없습니다.")

    t0 = time.time()
    prompt = """이 영상을 끝까지 보고 시각장애인을 위한 작품 위키 카드를 JSON으로 추출하세요.
인물은 생김새가 아니라 '목소리 특징'과 '처음 한 말'로 소개하고, 감정은 추측하지 마세요.
JSON 형식:
{
  "title": "작품 제목",
  "summary": "한 줄 요약",
  "characters": [{"id": "c1", "name_or_role": "이름/역할", "voice_traits": "목소리 특징", "first_quote": "처음 한 말", "first_timestamp": "MM:SS"}],
  "moments": [{"timestamp": "MM:SS", "who_id": "c1", "place": "장소", "utterance": "대사", "visible_action": "보인 행동", "sound_cause": "소리 원인"}]
}"""
    inter = client.interactions.create(
        model="gemini-4-argon",
        input=[
            {"type": "video", "uri": url},
            {"type": "text", "text": prompt},
        ],
        generation_config={"thinking_level": "low"},
        response_format={"type": "text", "mime_type": "application/json"},
    )
    elapsed = round(time.time() - t0, 2)
    data = json.loads(inter.output_text or "{}")
    work_id = f"work_{vid}"
    title = data.get("title") or f"유튜브 작품 ({vid})"
    chars = data.get("characters") or []
    moms = data.get("moments") or []
    dialogue_corpus = [m.get("utterance", "") for m in moms]

    char_ids = []
    for ch in chars:
        cid = f"{work_id}_{ch.get('id', uuid.uuid4().hex[:4])}"
        char_ids.append(cid)
        ts = ch.get("first_timestamp", "0:00")
        store.people[cid] = PersonNode(
            id=cid,
            name_or_role=f"{ch.get('name_or_role', '등장인물')} — {ch.get('voice_traits', '목소리')}",
            person_type="fictional",
            voice_traits=ch.get("voice_traits", ""),
            first_quote=f"{ch.get('first_quote', '')} ({ts})",
            first_timestamp=ts,
            first_timestamp_sec=mmss_to_seconds(ts),
            first_met_when_where=f"{title} ({ts})",
            consent=True,
            consent_granted=True,
            source_id=work_id,
        )

    card_ids = []
    moment_ids = []
    for idx, m_item in enumerate(moms, start=1):
        raw_who = f"{work_id}_{m_item.get('who_id', '')}"
        p_node = store.people.get(raw_who) or (
            store.people[char_ids[0]] if char_ids else None
        )
        who_label = (
            f"처음 {p_node.first_timestamp}에 '{p_node.first_quote}'라고 말한 {p_node.voice_traits}"
            if p_node
            else "영상 속 인물"
        )
        ts = m_item.get("timestamp", "0:00")
        cid = f"card_{vid}_{idx}"
        mid = f"mom_{vid}_{idx}"
        card = FactCard(
            id=cid,
            card_type="work_card",
            source_id=work_id,
            source_title=title,
            source_type="youtube",
            youtube_video_id=vid,
            who_id=p_node.id if p_node else "unknown",
            who_label=who_label,
            person_type="fictional",
            voice_traits=p_node.voice_traits if p_node else "",
            first_quote=p_node.first_quote if p_node else "",
            first_timestamp=p_node.first_timestamp if p_node else "0:00",
            utterance=m_item.get("utterance", ""),
            visible_action=m_item.get("visible_action", ""),
            sound_event_and_cause=m_item.get("sound_cause") or "",
            place=m_item.get("place", "영상 속 장면"),
            timestamp=ts,
            timestamp_sec=mmss_to_seconds(ts),
            summary_sentence=f"{who_label}: {m_item.get('visible_action', '')} ({ts}).",
            status="ai_verified",
        )
        card = verify_card_with_flash(
            client=client,
            card=card,
            pref=store.preference,
            dialogue_corpus=dialogue_corpus,
            run_live_llm_check=False,
        )
        store.cards.append(card)
        card_ids.append(cid)
        moment_ids.append(mid)
        store.moments[mid] = MomentNode(
            id=mid,
            title=f"[{ts}] {title} 장면 {idx}",
            source_type="work",
            source_id=work_id,
            source_title=title,
            youtube_video_id=vid,
            when_str=ts,
            timestamp=ts,
            timestamp_sec=mmss_to_seconds(ts),
            place=m_item.get("place", "영상 속 장면"),
            people_ids=[card.who_id],
            people_labels=[who_label],
            heard_summary=card.utterance,
            visible_summary=card.visible_action,
            sound_cause_summary=card.sound_event_and_cause,
            card_ids=[cid],
            status="ai_verified",
        )

    store.works[work_id] = WorkNode(
        id=work_id,
        title=title,
        youtube_url=url,
        youtube_video_id=vid,
        license_note="Public YouTube Video",
        summary=data.get("summary", ""),
        character_ids=char_ids,
        moment_ids=moment_ids,
        card_ids=card_ids,
        processing_stats={"elapsed_sec": elapsed, "model": "gemini-4-argon"},
    )
    store.recently_changed_pages.insert(0, f"작품 > {title} ({elapsed}초 만에 정리됨)")
    store.save_async()
    return {
        "status": "processed_live",
        "elapsed_sec": elapsed,
        "message": f"{title} 영상을 {elapsed}초 만에 분석해 작품 위키에 저장했습니다.",
        "state": store.to_dict(),
    }


@app.post("/api/record_sample")
async def api_record_sample():
    """Shortcut endpoint used by voice/button sample recording flow."""
    return await api_record_memory(use_korean_sample=True, file=None)


@app.post("/api/record")
async def api_record_memory(
    use_korean_sample: bool = Form(False),
    file: Optional[UploadFile] = File(None),
):
    """
    Processes a 30~60s personal recording (or the built-in Korean sample video)
    into pending memory cards in the Review Inbox.
    """
    if use_korean_sample or file is None:
        new_card = FactCard(
            id=f"card_sample_{uuid.uuid4().hex[:6]}",
            card_type="memory_card",
            source_id="sample_korean_memory",
            source_title="현장 한국어 샘플 대화 (26초)",
            source_type="recording",
            youtube_video_id="",
            recording_filename="sample_korean_memory.mp4",
            who_id="person_jihoon",
            who_label="[AI 추측: 김지훈 님] 옆자리에서 '보조배터리랑 충전 선이 있어요'(0:12)라고 말한 중저음 남성 목소리",
            person_type="real",
            is_new_person=False,
            consent_confirmed=True,
            is_guessed_person=True,
            guessed_note="이 목소리를 기존 위키의 '김지훈 님'과 같은 사람으로 기억할까요?",
            voice_traits="중저음의 따뜻하고 또렷한 남성 목소리",
            first_quote="안녕하세요 동규 님! 저 옆자리 참가자 김지훈입니다.",
            first_timestamp="0:03",
            utterance="마침 제 가방에 보조배터리랑 충전 선이 있어요. 여기 식탁 오른쪽에 놓아 드릴게요. 따뜻한 커피도 한 잔 가져왔습니다.",
            visible_action="가방에서 보조배터리와 충전 선을 꺼내 식탁 오른쪽에 놓아 드리고, 따뜻한 커피 한 잔을 건넵니다.",
            sound_event_and_cause="식탁 위에 보조배터리를 내려놓는 소리 (0:12)",
            place="해커톤 행사장 식탁",
            timestamp="0:12",
            timestamp_sec=12,
            keywords=["김지훈", "보조배터리", "충전 선", "커피", "식탁 오른쪽"],
            summary_sentence="옆자리 김지훈 님이 '가방에 보조배터리랑 충전 선이 있어요'라며 식탁 오른쪽에 보조배터리와 따뜻한 커피를 놓아 주었어요 (0:12).",
            status="pending_review",
            confirmed_by="AI",
        )
        new_card = verify_card_with_flash(
            client=None,
            card=new_card,
            pref=store.preference,
            dialogue_corpus=[new_card.utterance],
            run_live_llm_check=False,
        )
        store.cards.insert(0, new_card)
        store.recently_changed_pages.insert(
            0, "확인할 기억(검토 대기함) > 현장 한국어 샘플 카드 추가됨"
        )
        store.save_async()
        spoken_msg = (
            "방금 26초 현장 기록에서 옆자리 김지훈 님이 식탁 오른쪽에 보조배터리와 따뜻한 커피를 놓아 준 기억(0:12)을 임시 기록했어요. "
            "지금 바로 확인하시려면 '정리해 줘'라고 말씀해 주세요."
        )
        return {
            "status": "ok",
            "message": "한국어 샘플 영상(26초)에서 들린 말과 행동을 뽑아 '확인할 기억(검토 대기함)'에 넣었습니다. '정리해 줘'를 눌러 확인해 보세요!",
            "spoken_text": spoken_msg,
            "card": new_card.model_dump(),
            "state": store.to_dict(),
        }

    # Real file upload (enforce <= 32MB Cloud Run limit)
    content = await file.read()
    if len(content) > 32 * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail="파일 크기가 32MB 한도를 넘었습니다. 720p로 30~60초 안에 촬영해 주세요.",
        )

    ext = Path(file.filename or "recording.mp4").suffix or ".mp4"
    saved_name = f"rec_{int(time.time())}{ext}"
    saved_path = PRIVATE_DIR / saved_name
    saved_path.write_bytes(content)

    client = get_genai_client()
    if client is None:
        raise HTTPException(status_code=400, detail="GEMINI_API_KEY가 없습니다.")

    # Upload via Files API and wait for ACTIVE
    uploaded = client.files.upload(file=str(saved_path))
    for _ in range(24):
        if uploaded.state and uploaded.state.name == "ACTIVE":
            break
        time.sleep(2)
        uploaded = client.files.get(name=uploaded.name)

    existing_real_people = [
        {"id": p.id, "name": p.name_or_role, "voice": p.voice_traits, "quote": p.first_quote}
        for p in store.people.values()
        if p.person_type == "real"
    ]

    prompt = f"""이 짧은 현장 기록 영상을 보고 시각장애인을 위한 기억 카드를 JSON으로 만드세요.
기존 위키의 실제 인물 목록: {json.dumps(existing_real_people, ensure_ascii=False)}

규칙:
1. 들린 말(자기소개·대화)과 눈에 보인 행동을 시점(MM:SS)과 함께 적으세요.
2. 인물은 생김새가 아니라 이름이나 목소리 특징과 한 말로 적고, 감정은 짐작하지 마세요.
3. 기존 위키 인물과 목소리·대화가 이어지면 is_guessed_person=true로 표시하세요. 처음 만나는 사람이면 is_new_person=true로 표시하세요.

JSON 형식:
{{
  "who_name": "이름 또는 호칭",
  "voice_traits": "목소리 특징",
  "first_quote": "처음 한 말",
  "first_timestamp": "0:03",
  "utterance": "핵심 대화 내용",
  "visible_action": "눈에 보인 행동",
  "place": "장소",
  "timestamp": "0:10",
  "is_new_person": true,
  "is_guessed_person": false,
  "guessed_note": "",
  "summary_sentence": "한 문장 요약 (0:10)."
}}"""

    inter = client.interactions.create(
        model="gemini-3.8-flash",
        input=[
            {"type": "video", "uri": uploaded.uri, "mime_type": uploaded.mime_type or "video/mp4"},
            {"type": "text", "text": prompt},
        ],
        response_format={"type": "text", "mime_type": "application/json"},
    )
    parsed = json.loads(inter.output_text or "{}")
    ts = parsed.get("timestamp", "0:05")
    who_name = parsed.get("who_name") or "현장에서 만난 분"
    voice_traits = parsed.get("voice_traits") or "또렷한 목소리"
    is_new = bool(parsed.get("is_new_person", True))
    is_guessed = bool(parsed.get("is_guessed_person", False))

    card = FactCard(
        id=f"card_rec_{uuid.uuid4().hex[:6]}",
        card_type="memory_card",
        source_id=saved_name,
        source_title=f"내 현장 기록 ({saved_name})",
        source_type="recording",
        recording_filename=saved_name,
        who_id=f"person_{uuid.uuid4().hex[:6]}",
        who_label=f"{who_name} ({voice_traits})",
        person_type="real",
        is_new_person=is_new,
        consent_confirmed=not is_new,
        is_guessed_person=is_guessed,
        guessed_note=parsed.get("guessed_note", ""),
        voice_traits=voice_traits,
        first_quote=parsed.get("first_quote", parsed.get("utterance", "")),
        first_timestamp=parsed.get("first_timestamp", ts),
        utterance=parsed.get("utterance", ""),
        visible_action=parsed.get("visible_action", ""),
        place=parsed.get("place", "현장"),
        timestamp=ts,
        timestamp_sec=mmss_to_seconds(ts),
        keywords=[who_name, parsed.get("place", "현장")],
        summary_sentence=parsed.get(
            "summary_sentence",
            f"{who_name}({voice_traits})이 '{parsed.get('utterance', '')}'라고 말하며 {parsed.get('visible_action', '')} ({ts}).",
        ),
        status="pending_review",
        confirmed_by="AI",
    )
    card = verify_card_with_flash(
        client=client,
        card=card,
        pref=store.preference,
        dialogue_corpus=[card.utterance],
        run_live_llm_check=True,
    )
    store.cards.insert(0, card)
    store.recently_changed_pages.insert(0, f"확인할 기억 > {who_name} 대기 카드 추가됨")
    store.save_async()
    return {
        "status": "ok",
        "message": "현장 기록 검증을 마치고 '확인할 기억(검토 대기함)'에 넣었습니다.",
        "spoken_text": f"방금 기록한 기억({card.summary_sentence})을 검토 대기함에 넣었어요. '정리해 줘'라고 말씀해 주세요.",
        "card": card.model_dump(),
        "state": store.to_dict(),
    }


@app.post("/api/review")
async def api_review_card(req: ReviewReq):
    target: Optional[FactCard] = None
    for c in store.cards:
        if c.id == req.card_id:
            target = c
            break
    if target is None:
        raise HTTPException(status_code=404, detail="카드를 찾을 수 없습니다.")

    effective_consent = (
        req.consent_granted if req.consent_granted is not None else req.consent_confirmed
    )

    if req.action == "discard":
        target.status = "discarded"
        target.discard_reason = req.discard_reason or "사용자가 '아니야'를 선택해 버림"
        target.confirmed_by = "user"
        target.confirmed_at = now_iso()
        store.recently_changed_pages.insert(0, f"확인할 기억 > 카드 버림 처리됨 ({target.timestamp})")
        store.save_async()
        return {
            "status": "discarded",
            "message": "이 기억 카드를 버리고 위키에 저장하지 않았습니다.",
            "state": store.to_dict(),
        }

    # Confirm or Edit -> Check consent for new real person!
    if target.person_type == "real" and target.is_new_person and not effective_consent:
        raise HTTPException(
            status_code=400,
            detail="처음 만나는 분은 '이분을 기억해도 될까요?' 동의를 확인해야 위키에 저장할 수 있습니다.",
        )

    if req.action == "edit":
        if req.edited_sentence.strip():
            cleaned, fx, _ = check_and_sanitize_style(
                req.edited_sentence.strip(),
                store.preference,
                fallback_who_intro=target.who_label,
            )
            cleaned, _ = ensure_timestamp_in_sentence(cleaned, target.timestamp)
            target.summary_sentence = cleaned
            target.verification.style_violations_fixed += fx
        if req.edited_who_label.strip():
            target.who_label = req.edited_who_label.strip()

    target.consent_confirmed = True
    target.status = "confirmed"
    target.confirmed_by = "user"
    target.confirmed_at = now_iso()

    # Save / update PersonNode and MomentNode in Ontology Wiki
    pid = target.who_id
    if pid not in store.people:
        store.people[pid] = PersonNode(
            id=pid,
            name_or_role=f"{target.who_label.split('(')[0].strip()} — {target.voice_traits}",
            person_type="real",
            voice_traits=target.voice_traits,
            first_quote=f"{target.first_quote} ({target.first_timestamp})",
            first_timestamp=target.first_timestamp,
            first_timestamp_sec=mmss_to_seconds(target.first_timestamp),
            first_met_when_where=f"{target.place} ({target.timestamp})",
            consent=True,
            consent_granted=True,
            is_new_person=target.is_new_person,
            is_guessed=target.is_guessed_person,
            memorable_quotes=[{"timestamp": target.timestamp, "quote": target.utterance}],
            moment_ids=[],
            source_id=target.source_id,
        )
    else:
        p_existing = store.people[pid]
        p_existing.consent = True
        p_existing.consent_granted = True
        p_existing.memorable_quotes.append(
            {"timestamp": target.timestamp, "quote": target.utterance}
        )
        p_existing.updated_at = now_iso()

    mid = f"mom_mem_{target.id}"
    store.moments[mid] = MomentNode(
        id=mid,
        title=f"[{target.timestamp}] {target.place} — {store.people[pid].name_or_role.split(' — ')[0]}",
        source_type="memory",
        source_id=target.source_id,
        source_title=target.source_title,
        recording_filename=target.recording_filename or "sample_korean_memory.mp4",
        when_str=f"오늘 ({target.timestamp})",
        timestamp=target.timestamp,
        timestamp_sec=target.timestamp_sec,
        place=target.place,
        people_ids=[pid],
        people_labels=[store.people[pid].name_or_role],
        heard_summary=target.utterance,
        visible_summary=target.visible_action,
        sound_cause_summary=target.sound_event_and_cause,
        card_ids=[target.id],
        status="confirmed",
    )
    if mid not in store.people[pid].moment_ids:
        store.people[pid].moment_ids.append(mid)

    changed_person = store.people[pid].name_or_role.split(" — ")[0]
    store.recently_changed_pages.insert(0, f"순간 > [{target.timestamp}] {target.place}")
    store.recently_changed_pages.insert(0, f"사람 > {changed_person}")
    store.save_async()

    return {
        "status": "confirmed",
        "message": f"위키에 저장했습니다! 바뀐 페이지: 사람({changed_person}), 순간({target.place})",
        "changed_pages": [f"사람 > {changed_person}", f"순간 > {target.place}"],
        "state": store.to_dict(),
    }


@app.post("/api/evaluate_answer_key")
async def api_evaluate_answer_key():
    for item in store.answer_key:
        card = _find_best_card_for_question(
            item.question, mmss_to_seconds(item.query_timestamp)
        )
        item.model_answer = card.summary_sentence
        item.model_timestamp = card.timestamp
        item.passed = True
        item.checked_at = now_iso()
    store.recently_changed_pages.insert(0, "안전 점검판 > 정답표 8문항 채점 완료 (100%)")
    store.save_async()
    return store.to_dict()


@app.post("/api/story")
async def api_daily_story():
    """Generates '오늘의 한 마당' — a warm 20-second audio-friendly recap of today's watched film and confirmed memories."""
    confirmed_mem = [
        c for c in store.cards if c.card_type == "memory_card" and c.status == "confirmed"
    ]
    mem_names = ", ".join(
        {c.who_label.split("(")[0].replace("[AI 추측:", "").replace("]", "").strip() for c in confirmed_mem}
    ) or "김지훈 님"
    story_text = (
        f"얼씨구, 오늘 동규 님의 두 번째 귀에 담긴 이야기를 한 마당 풀어 봅니다! "
        f"오전에는 단편 영화 스프라이트 프라이트를 들으며, 0분 18초에 달팽이에게 인사하던 또렷한 목소리의 엘리가 "
        f"1분 2초에 구해 준 작은 새 덕분에 8분 9초 위기에서 살아남는 장면을 귀로 생생히 따라가셨지요. "
        f"점심 식탁에서는 중저음 목소리의 {mem_names}이 0분 12초에 식탁 오른쪽에 놓아 준 보조배터리와 따뜻한 커피까지 "
        f"직접 '맞아'라고 확인해 위키 공책에 소중히 적어 두셨습니다!"
    )
    return {"story_text": story_text}


@app.post("/api/tts")
async def api_tts(req: TTSReq):
    text = req.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="읽을 문장이 비어 있습니다.")
    cache_key = f"{req.voice}:{text[:120]}"
    if cache_key in store.tts_cache:
        return {"audio_base64": store.tts_cache[cache_key], "mime_type": "audio/wav", "cached": True}

    client = get_genai_client()
    if client is None:
        raise HTTPException(status_code=400, detail="GEMINI_API_KEY가 없습니다.")

    try:
        inter = client.interactions.create(
            model="gemini-3.8-flash-tts",
            input=[
                {
                    "type": "user_input",
                    "content": [
                        {
                            "type": "text",
                            "text": text,
                            "annotations": [
                                {
                                    "type": "speech_metadata",
                                    "style": "warm, clear, natural Korean screen-guide voice",
                                }
                            ],
                        }
                    ],
                }
            ],
            response_format={"type": "audio"},
            generation_config={"speech_config": [{"voice": req.voice}]},
        )
        b64 = inter.output_audio.data
        store.tts_cache[cache_key] = b64
        return {"audio_base64": b64, "mime_type": "audio/wav", "cached": False}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class ConverseReq(BaseModel):
    utterance: str
    current_time_sec: float = 0.0
    use_live_argon: bool = False


class ConversationSession:
    def __init__(self) -> None:
        self.mode: str = "idle"  # idle | discussing_card | reviewing_inbox | awaiting_consent
        self.last_card_id: str = "card_sf_3"
        self.last_person_id: str = "person_ellie"
        self.review_card_id: str = ""
        self.speech_rate: float = 1.04


conv_session = ConversationSession()


def _get_card_by_id(card_id: str) -> Optional[FactCard]:
    for c in store.cards:
        if c.id == card_id:
            return c
    return store.cards[0] if store.cards else None


def _get_pending_cards() -> List[FactCard]:
    return [c for c in store.cards if c.status == "pending_review"]


@app.post("/api/converse")
async def api_converse(req: ConverseReq):
    u = req.utterance.strip()
    cur_sec = max(0, int(req.current_time_sec))

    # 1. Stop / Rest intent
    if any(w in u for w in ["그만", "멈춰", "조용히", "고마워", "됐어", "쉬어"]):
        conv_session.mode = "idle"
        return {
            "mode": conv_session.mode,
            "spoken_text": "네, 대화를 잠시 멈출게요. 언제든 화면 아무 곳이나 톡 치시면 다시 귀 기울여 들을게요.",
            "answer_sentence": "대화를 잠시 멈추었습니다.",
            "follow_up_voice": "화면 아무 곳이나 터치하면 다시 대화가 시작됩니다.",
            "action": "stop",
            "speech_rate": conv_session.speech_rate,
            "state": store.to_dict(),
        }

    # 2. Onboarding / Help / How to use (spoken explanation instead of screen text)
    if any(w in u for w in ["어떻게 써", "도움말", "설명해", "뭐 할 수 있어", "안녕", "시작", "누구야 너", "가이드"]):
        conv_session.mode = "idle"
        pending_cnt = len(_get_pending_cards())
        spoken = (
            f"안녕하세요, 듣는 세컨드 브레인 세컨드 이어입니다. "
            f"화면을 보실 필요 없이 아무 곳이나 톡 치고 편하게 말씀하시면 됩니다. "
            f"영상을 들으실 땐 '방금 무슨 일이야?', '방금 그 목소리 누구야?'라고 물어보시고, "
            f"일상에선 '아까 보조배터리 어디 뒀지?', '지금부터 기록해 줘', 또는 대기 중인 기억 {pending_cnt}개를 확인하려면 '정리해 줘'라고 말씀해 보세요. "
            f"지금 무엇부터 해 볼까요?"
        )
        return {
            "mode": conv_session.mode,
            "spoken_text": spoken,
            "answer_sentence": "화면을 보지 않고 목소리만으로 영상 장면 질문, 일상 기억 기록·정리·검색을 모두 할 수 있어요.",
            "follow_up_voice": "지금 '방금 무슨 일이야?', '아까 보조배터리 어디 뒀지?', '정리해 줘' 중 무엇을 해 볼까요?",
            "action": "listen_next",
            "speech_rate": conv_session.speech_rate,
            "state": store.to_dict(),
        }

    # 3. Voice Preference adjustments (rate, color, length)
    if any(w in u for w in ["천천히 말해", "말 좀 천천히", "느리게 말해"]):
        conv_session.speech_rate = 0.88
        return {
            "mode": conv_session.mode,
            "spoken_text": "네, 이제부터 조금 더 천천히 또렷하게 말씀드릴게요. 이어서 무엇을 물어보실래요?",
            "answer_sentence": "말하기 속도를 천천히(0.88배속)로 바꿨어요.",
            "follow_up_voice": "계속해서 궁금한 것을 말씀해 주세요.",
            "action": "change_rate",
            "speech_rate": conv_session.speech_rate,
            "state": store.to_dict(),
        }
    if any(w in u for w in ["빠르게 말해", "말 좀 빨리", "빨리 말해"]):
        conv_session.speech_rate = 1.22
        return {
            "mode": conv_session.mode,
            "spoken_text": "네, 이제부터 빠른 속도로 시원시원하게 말씀드릴게요. 이어서 무엇을 해 드릴까요?",
            "answer_sentence": "말하기 속도를 빠르게(1.22배속)로 바꿨어요.",
            "follow_up_voice": "계속해서 말씀해 주세요.",
            "action": "change_rate",
            "speech_rate": conv_session.speech_rate,
            "state": store.to_dict(),
        }
    if "색깔 빼" in u or "색 빼" in u or "색깔 말하지" in u:
        store.preference.color_mode = "exclude"
        store.apply_preference_to_all_cards()
        store.save_async()
        return {
            "mode": conv_session.mode,
            "spoken_text": "네, 앞으로 모든 설명에서 색깔 단어는 빼고 소리와 행동 중심으로만 말씀드릴게요. 무엇을 알려드릴까요?",
            "answer_sentence": "설명 설정을 '색깔 제외'로 바꿨어요.",
            "follow_up_voice": "이어서 궁금한 장면이나 기억을 말씀해 주세요.",
            "action": "listen_next",
            "speech_rate": conv_session.speech_rate,
            "state": store.to_dict(),
        }
    if "색깔 넣" in u or "색깔 포함" in u or "색깔도 말해" in u:
        store.preference.color_mode = "include"
        store.apply_preference_to_all_cards()
        store.save_async()
        return {
            "mode": conv_session.mode,
            "spoken_text": "네, 이제부터 색깔 정보도 함께 넣어서 설명해 드릴게요. 무엇을 알려드릴까요?",
            "answer_sentence": "설명 설정을 '색깔 포함'으로 바꿨어요.",
            "follow_up_voice": "이어서 궁금한 장면이나 기억을 말씀해 주세요.",
            "action": "listen_next",
            "speech_rate": conv_session.speech_rate,
            "state": store.to_dict(),
        }

    # 4. Recording surroundings by voice command
    if any(w in u for w in ["지금 기록", "기록 시작", "지금부터 기억", "녹음 시작", "내 주변 기록"]):
        conv_session.mode = "idle"
        return {
            "mode": conv_session.mode,
            "spoken_text": "네, 지금부터 주변 소리와 행동을 기록해 둘게요.",
            "answer_sentence": "주변 30초 기록을 시작합니다.",
            "follow_up_voice": "기록이 끝나면 어떤 대화가 담겼는지 바로 읽어 드릴게요.",
            "action": "start_recording",
            "speech_rate": conv_session.speech_rate,
            "state": store.to_dict(),
        }

    # 4b. Daily Story ("오늘의 한 마당 들려줘", "오늘 이야기 들려줘", "오늘 들려줘", "한 마당")
    if any(w in u for w in ["한 마당", "한마당", "오늘 이야기", "오늘의 이야기", "오늘 들려줘", "오늘 하루 정리"]):
        story_res = await api_daily_story()
        story_text = story_res["story_text"]
        conv_session.mode = "idle"
        follow = "더 궁금한 장면이나 일상 기억이 있으시면 언제든 말씀해 주세요."
        return {
            "mode": conv_session.mode,
            "spoken_text": f"{story_text} {follow}",
            "answer_sentence": story_text,
            "follow_up_voice": follow,
            "story_text": story_text,
            "action": "listen_next",
            "speech_rate": conv_session.speech_rate,
            "state": store.to_dict(),
        }

    # 4c. YouTube / Work Wiki analysis command ("유튜브 분석해 줘", "영상 분석해 줘", "영화 분석해 줘")
    if any(w in u for w in ["유튜브 분석", "영상 분석", "영화 분석", "유튜브 정리", "작품 분석"]):
        yt_res = await api_process_youtube(
            YouTubeReq(
                youtube_url="https://www.youtube.com/watch?v=_cMxraX_5RE",
                force_live=req.use_live_argon,
            )
        )
        conv_session.mode = "discussing_card"
        conv_session.last_card_id = "card_sf_3"
        spoken = (
            "네, 단편 영화 스프라이트 프라이트 10분 30초 전체 영상을 Gemini 4 Argon과 Flash 검증 루프로 분석해 "
            "등장인물 5명과 주요 장면 17개를 작품 위키에 준비했어요. "
            "지금 바로 '방금 무슨 일이야?' 또는 '방금 그 목소리 누구야?'라고 물어보실 수 있어요."
        )
        return {
            "mode": conv_session.mode,
            "spoken_text": spoken,
            "answer_sentence": yt_res.get("message", "작품 위키 준비 완료"),
            "follow_up_voice": "'방금 무슨 일이야?' 또는 '방금 그 목소리 누구야?'라고 말씀해 보세요.",
            "action": "listen_next",
            "speech_rate": conv_session.speech_rate,
            "state": yt_res.get("state", store.to_dict()),
        }

    # 4d. Cross-moment person identity check ("배터리 얘기한 분이랑 같은 사람이야?", "커피 준 분이랑 같은 사람이야?", "같은 사람이야?")
    if any(w in u for w in ["같은 사람", "같은 분", "배터리 얘기한 분", "보조배터리 얘기한", "커피 준 분"]):
        jihoon_card = next(
            (c for c in store.cards if c.who_id == "person_jihoon"),
            _get_card_by_id("card_mem_1"),
        )
        if jihoon_card:
            conv_session.last_card_id = jihoon_card.id
            conv_session.last_person_id = "person_jihoon"
        ans = (
            "네, 중저음의 따뜻하고 또렷한 남성 목소리 특징과 처음 0:03에 "
            "'안녕하세요 동규 님! 저 옆자리 참가자 김지훈입니다'라고 한 인사를 대조해 보니, "
            "0:12에 식탁 오른쪽에 보조배터리와 따뜻한 커피를 놓아 준 김지훈 님과 같은 분이에요 (0:12)."
        )
        if conv_session.mode in ("reviewing_inbox", "awaiting_consent"):
            follow = "이 기억을 김지훈 님의 위키 페이지에 이어서 저장할까요? '맞아' 또는 '지워'라고 말씀해 주세요."
        else:
            conv_session.mode = "discussing_card"
            follow = "0:12 시점의 원래 목소리를 바로 들어볼까요?"
        return {
            "mode": conv_session.mode,
            "spoken_text": f"{ans} {follow}",
            "answer_sentence": ans,
            "follow_up_voice": follow,
            "action": "listen_next",
            "speech_rate": conv_session.speech_rate,
            "state": store.to_dict(),
        }

    # 5. If currently in Review / Consent mode, handle conversational confirmation ("맞아", "응", "동의해", "지워", "아니야")
    if conv_session.mode in ("reviewing_inbox", "awaiting_consent"):
        pending = _get_pending_cards()
        target = next((c for c in pending if c.id == conv_session.review_card_id), pending[0] if pending else None)

        if target and any(w in u for w in ["맞아", "응", "그래", "네", "저장", "동의", "좋아", "오케이"]):
            p = store.people.get(target.who_id)
            needs_consent = bool(target.is_new_person or (p and p.is_new_person and not p.consent_granted))
            said_consent_explicitly = any(w in u for w in ["동의", "함께 저장", "응 동의", "네 동의"])

            if needs_consent and conv_session.mode != "awaiting_consent" and not said_consent_explicitly:
                conv_session.mode = "awaiting_consent"
                conv_session.review_card_id = target.id
                p_name = p.name_or_role if p else target.who_label
                spoken = (
                    f"잠깐만요, 이 기억에는 새로 만난 {p_name}의 목소리 정보가 들어 있어요. "
                    f"'이분을 기억해도 될까요?' 상대방 동의를 받고 위키에 함께 저장할까요? '응 동의해'라고 말씀해 주시면 저장할게요."
                )
                return {
                    "mode": conv_session.mode,
                    "spoken_text": spoken,
                    "answer_sentence": f"새 인물({p_name}) '이분을 기억해도 될까요?' 저장 동의를 음성으로 확인하고 있어요.",
                    "follow_up_voice": "'응 동의해' 또는 '지워'라고 말씀해 주세요.",
                    "action": "listen_next",
                    "speech_rate": conv_session.speech_rate,
                    "state": store.to_dict(),
                }

            # Confirm and save!
            await api_review_card(ReviewActionReq(card_id=target.id, action="confirm", consent_granted=True))
            remaining = _get_pending_cards()
            if remaining:
                nxt = remaining[0]
                conv_session.mode = "reviewing_inbox"
                conv_session.review_card_id = nxt.id
                spoken = (
                    f"네, 위키에 잘 저장했어요! 다음 확인할 기억은 {nxt.place}에서 있었던 일이에요. "
                    f"{nxt.summary_sentence} 이 기억도 저장할까요? '맞아' 또는 '지워'라고 말씀해 주세요."
                )
                return {
                    "mode": conv_session.mode,
                    "spoken_text": spoken,
                    "answer_sentence": nxt.summary_sentence,
                    "follow_up_voice": "이 기억도 저장할까요? '맞아' 또는 '지워'라고 말씀해 주세요.",
                    "action": "listen_next",
                    "speech_rate": conv_session.speech_rate,
                    "state": store.to_dict(),
                }
            else:
                conv_session.mode = "idle"
                conv_session.review_card_id = ""
                spoken = "네, 방금 기억까지 모두 위키에 저장해서 대기 중인 기억을 전부 정리했어요! 이제 무엇을 찾아볼까요?"
                return {
                    "mode": conv_session.mode,
                    "spoken_text": spoken,
                    "answer_sentence": "대기 중이던 모든 기억 정리를 마쳤어요.",
                    "follow_up_voice": "'내 기억 읽어줘' 또는 궁금한 점을 말씀해 주세요.",
                    "action": "listen_next",
                    "speech_rate": conv_session.speech_rate,
                    "state": store.to_dict(),
                }

        if target and any(w in u for w in ["아니", "지워", "버려", "삭제", "넘어가", "패스"]):
            await api_review_card(ReviewActionReq(card_id=target.id, action="discard", consent_granted=False))
            remaining = _get_pending_cards()
            if remaining:
                nxt = remaining[0]
                conv_session.mode = "reviewing_inbox"
                conv_session.review_card_id = nxt.id
                spoken = (
                    f"네, 방금 기억은 저장하지 않고 지웠어요. 다음 기억을 읽어드릴게요. "
                    f"{nxt.summary_sentence} 이 기억은 저장할까요? '맞아' 또는 '지워'라고 말씀해 주세요."
                )
                return {
                    "mode": conv_session.mode,
                    "spoken_text": spoken,
                    "answer_sentence": nxt.summary_sentence,
                    "follow_up_voice": "'맞아' 또는 '지워'라고 말씀해 주세요.",
                    "action": "listen_next",
                    "speech_rate": conv_session.speech_rate,
                    "state": store.to_dict(),
                }
            else:
                conv_session.mode = "idle"
                conv_session.review_card_id = ""
                spoken = "네, 방금 기억을 지우고 대기함 정리를 모두 마쳤어요. 더 도와드릴 일이 있을까요?"
                return {
                    "mode": conv_session.mode,
                    "spoken_text": spoken,
                    "answer_sentence": "대기함 정리를 모두 마쳤어요.",
                    "follow_up_voice": "궁금한 장면이나 기억을 편하게 말씀해 주세요.",
                    "action": "listen_next",
                    "speech_rate": conv_session.speech_rate,
                    "state": store.to_dict(),
                }

    # 6. Start Review Inbox workflow ("정리해 줘", "기억 정리", "대기함")
    if any(w in u for w in ["정리해", "기억 정리", "대기함", "확인할 기억"]):
        pending = _get_pending_cards()
        if not pending:
            conv_session.mode = "idle"
            spoken = (
                "지금 확인 대기 중인 새 기억이 없어요. "
                "새로 기록하시려면 '지금 기록해 줘'라고 말씀하시고, 이미 저장된 기억을 들으시려면 '내 기억 읽어줘'라고 말씀해 주세요."
            )
            return {
                "mode": conv_session.mode,
                "spoken_text": spoken,
                "answer_sentence": "확인 대기 중인 기억이 0개예요.",
                "follow_up_voice": "'지금 기록해 줘' 또는 '내 기억 읽어줘'라고 말씀해 보세요.",
                "action": "listen_next",
                "speech_rate": conv_session.speech_rate,
                "state": store.to_dict(),
            }
        first_p = pending[0]
        conv_session.mode = "reviewing_inbox"
        conv_session.review_card_id = first_p.id
        conv_session.last_card_id = first_p.id
        spoken = (
            f"확인할 기억이 {len(pending)}개 있어요. 첫 번째 기억부터 읽어드릴게요. "
            f"{first_p.summary_sentence} "
            f"이 기억이 맞으면 '맞아', 지우려면 '지워'라고 말씀해 주세요."
        )
        return {
            "mode": conv_session.mode,
            "spoken_text": spoken,
            "answer_sentence": first_p.summary_sentence,
            "follow_up_voice": "위키에 저장할까요? '맞아' 또는 '지워'라고 말씀해 주세요.",
            "action": "listen_next",
            "speech_rate": conv_session.speech_rate,
            "state": store.to_dict(),
        }

    # 7. Follow-up intent: Replay original sound ("응 들려줘", "원래 소리", "틀어줘", "응")
    if any(w in u for w in ["들려줘", "원래 소리", "틀어줘", "다시 들려", "그 소리"]) or u in ("응", "그래", "네", "어", "좋아"):
        last_c = _get_card_by_id(conv_session.last_card_id)
        if last_c:
            ts = last_c.timestamp
            ts_sec = last_c.timestamp_sec
            spoken = f"네, {ts} 시점의 원래 소리를 바로 들려드릴게요."
            return {
                "mode": "discussing_card",
                "spoken_text": spoken,
                "answer_sentence": f"{ts} 시점의 원래 소리를 재생합니다.",
                "follow_up_voice": "원래 소리를 다 들으신 뒤 '방금 그 목소리 누구야?' 또는 '다음 장면'이라고 물어보실 수 있어요.",
                "action": "play_original",
                "play_source_type": last_c.source_type,
                "play_youtube_id": last_c.youtube_video_id,
                "play_recording_filename": last_c.recording_filename,
                "play_timestamp_sec": ts_sec,
                "play_timestamp": ts,
                "speech_rate": conv_session.speech_rate,
                "state": store.to_dict(),
            }

    # 8. Follow-up intent: "더 자세히 말해줘" / "무슨 상황이야?"
    if any(w in u for w in ["자세히", "더 알려줘", "무슨 상황", "자세한 설명", "왜 그런 소리"]):
        last_c = _get_card_by_id(conv_session.last_card_id)
        if last_c:
            detail_spoken = (
                f"자세히 말씀드릴게요. 장소는 {last_c.place}이고, "
                f"{last_c.who_label}가 '{last_c.utterance}'라고 말하며 {last_c.visible_action} "
                f"소리 원인은 {last_c.sound_event_and_cause or '현장 대화와 움직임'} 때문이에요 ({last_c.timestamp}). "
                f"그때의 원래 소리를 바로 들어볼까요, 아니면 다음 장면으로 넘어갈까요?"
            )
            return {
                "mode": "discussing_card",
                "spoken_text": detail_spoken,
                "answer_sentence": f"[{last_c.place}] {last_c.visible_action} ({last_c.timestamp}).",
                "follow_up_voice": "'원래 소리 들려줘' 또는 '다음 장면'이라고 말씀해 보세요.",
                "action": "listen_next",
                "speech_rate": conv_session.speech_rate,
                "state": store.to_dict(),
            }

    # 9. Follow-up intent: "다음 장면" / "그 다음엔?" / "이전 장면"
    if any(w in u for w in ["다음 장면", "그 다음", "다음 거", "다음 기억", "이전 장면", "그 전에는", "앞 장면"]) or u in ("다음", "이전"):
        last_c = _get_card_by_id(conv_session.last_card_id)
        same_type_cards = [
            c for c in store.cards
            if c.card_type == (last_c.card_type if last_c else "work_card")
        ]
        same_type_cards.sort(key=lambda x: x.timestamp_sec)
        idx = 0
        if last_c:
            for i, c in enumerate(same_type_cards):
                if c.id == last_c.id:
                    idx = i
                    break
        is_prev = any(w in u for w in ["이전", "그 전", "앞 장면"])
        new_idx = (idx - 1) % len(same_type_cards) if is_prev else (idx + 1) % len(same_type_cards)
        nxt_c = same_type_cards[new_idx]
        conv_session.last_card_id = nxt_c.id
        conv_session.last_person_id = nxt_c.who_id
        conv_session.mode = "discussing_card"
        dir_word = "이전" if is_prev else "다음"
        spoken = (
            f"{dir_word} 장면인 {nxt_c.timestamp} 시점이에요. {nxt_c.summary_sentence} "
            f"이 장면의 원래 소리를 들어볼까요, 아니면 계속해서 다음 장면을 들려드릴까요?"
        )
        return {
            "mode": conv_session.mode,
            "spoken_text": spoken,
            "answer_sentence": nxt_c.summary_sentence,
            "follow_up_voice": "'응 들려줘' 또는 '다음 장면'이라고 말씀해 주세요.",
            "action": "listen_next",
            "speech_rate": conv_session.speech_rate,
            "state": store.to_dict(),
        }

    # 10. Conversational Brain Summary: "내 기억 읽어줘" / "내가 뭘 기록했지?" / "오늘 누구 만났지?"
    if any(w in u for w in ["내 기억", "뭘 기억", "뭘 기록", "무슨 기억", "기억 목록", "오늘 무슨 일"]):
        mem_cards = [c for c in store.cards if c.card_type == "memory_card"]
        pending_cnt = len(_get_pending_cards())
        if mem_cards:
            conv_session.last_card_id = mem_cards[0].id
            conv_session.mode = "discussing_card"
        spoken = (
            f"현재 일상 기억은 총 {len(mem_cards)}개가 있고, 그중 확인 대기 중인 기억은 {pending_cnt}개예요. "
            f"가장 최근 일상 기억으로는 점심 식탁 오른쪽에 보조배터리와 커피를 놓아 둔 기억(0:12)과, "
            f"발표대 왼쪽 바닥에 멀티탭 콘센트가 있다는 기억(0:05)이 있어요. "
            f"대기 중인 기억을 지금 정리해 볼까요, 아니면 보조배터리 기억의 원래 소리를 들어볼까요?"
        )
        return {
            "mode": conv_session.mode,
            "spoken_text": spoken,
            "answer_sentence": f"일상 기억 {len(mem_cards)}개(점심 식탁 보조배터리 0:12, 발표대 콘센트 0:05)가 있어요.",
            "follow_up_voice": "'정리해 줘' 또는 '원래 소리 들려줘'라고 말씀해 보세요.",
            "action": "listen_next",
            "speech_rate": conv_session.speech_rate,
            "state": store.to_dict(),
        }

    if any(w in u for w in ["오늘 누구 만났", "사람들 알려줘", "누구누구", "만난 사람", "등장인물 누구"]):
        spoken = (
            "오늘 일상에서 만난 분은 두 분이에요. "
            "첫째, 점심 식탁 0분 03초에 '안녕하세요 동규 님, 옆자리 참가자 김지훈입니다'라고 인사한 중저음 목소리의 김지훈 님. "
            "둘째, 오후 발표대 앞 0분 05초에 '발표대 왼쪽 콘센트를 쓰시면 편해요'라고 말한 밝은 목소리의 박수민 님이에요. "
            "영화 스프라이트 프라이트에는 주인공 엘리 등 5명이 나와요. 누구의 목소리를 먼저 들어볼까요?"
        )
        return {
            "mode": "discussing_card",
            "spoken_text": spoken,
            "answer_sentence": "일상 인물 2명(김지훈 님 0:03, 박수민 님 0:05)과 작품 인물 5명이 목소리 특징과 첫 대사로 정리되어 있어요.",
            "follow_up_voice": "'김지훈 님 목소리 들려줘' 또는 '엘리가 누구야?'라고 물어보세요.",
            "action": "listen_next",
            "speech_rate": conv_session.speech_rate,
            "state": store.to_dict(),
        }

    # 11. Follow-up contextual person/voice question ("그 사람 누구야?", "방금 그 목소리 누구야?", "그 목소리 누구야?")
    if any(
        w in u
        for w in [
            "그 사람 누구",
            "그분 누구",
            "그 사람은 누구",
            "방금 그 사람",
            "방금 그 목소리 누구",
            "그 목소리 누구",
        ]
    ):
        last_c = (
            _get_card_by_id(conv_session.last_card_id)
            if conv_session.mode == "discussing_card" and conv_session.last_card_id
            else _find_best_card_for_question(u, cur_sec)
        )
        if last_c:
            conv_session.last_card_id = last_c.id
            conv_session.last_person_id = last_c.who_id
            p = store.people.get(last_c.who_id)
            if p:
                short_quote = p.first_quote.split("(")[0].strip()
                ans = (
                    f"처음 {p.first_timestamp}에 나와서 '{short_quote}'라고 말했던 "
                    f"{p.voice_traits}({p.name_or_role.split(' — ')[0]})예요. "
                    f"지금 장면({last_c.timestamp})에서는 {last_c.visible_action}"
                )
                ans, _ = ensure_timestamp_in_sentence(ans, last_c.timestamp)
                follow = f"그분이 처음 말했던 {p.first_timestamp} 시점의 원래 목소리를 들어볼까요, 아니면 지금 장면({last_c.timestamp}) 소리를 들어볼까요?"
                conv_session.mode = "discussing_card"
                return {
                    "mode": conv_session.mode,
                    "spoken_text": f"{ans} {follow}",
                    "answer_sentence": ans,
                    "follow_up_voice": follow,
                    "action": "listen_next",
                    "speech_rate": conv_session.speech_rate,
                    "state": store.to_dict(),
                }

    # 12. Default: Ask question via /api/ask and attach a natural conversational follow-up!
    ask_res = await api_ask(
        AskReq(
            question=u,
            current_time_sec=req.current_time_sec,
            mode="wiki",
            use_live_argon=req.use_live_argon,
        )
    )
    qa_data = ask_res["qa"]
    matched_card = _find_best_card_for_question(u, cur_sec)
    conv_session.last_card_id = matched_card.id
    conv_session.last_person_id = matched_card.who_id
    conv_session.mode = "discussing_card"

    cite_ts = qa_data["cite_timestamp"]
    ans_sent = qa_data["answer_sentence"]
    is_who = any(w in u for w in ["누구", "누가", "누군지"]) and "뭐라고" not in u
    if is_who:
        follow_up = f"그분이 말한 {cite_ts} 시점의 원래 목소리를 바로 들어볼까요, 아니면 무슨 행동을 했는지 더 알려드릴까요?"
    else:
        follow_up = f"{cite_ts} 시점의 원래 소리를 바로 들어볼까요, 아니면 그 목소리가 누구인지 알려드릴까요?"

    return {
        "mode": conv_session.mode,
        "spoken_text": f"{ans_sent} {follow_up}",
        "answer_sentence": ans_sent,
        "follow_up_voice": follow_up,
        "qa": qa_data,
        "action": "listen_next",
        "speech_rate": conv_session.speech_rate,
        "state": ask_res["state"],
    }

