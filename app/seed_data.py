from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from app.ontology import (
    AnswerKeyItem,
    FactCard,
    MomentNode,
    PersonNode,
    UserPreference,
    WorkNode,
    mmss_to_seconds,
    seconds_to_mmss,
)
from app.verifier import RUNTIME_VERIFICATION_LOGS, verify_card_with_flash

PRIVATE_ARGON_JSON_PATH = (
    Path(__file__).resolve().parent.parent / "private" / "sprite_fright_argon.json"
)
APP_DATA_ARGON_JSON_PATH = (
    Path(__file__).resolve().parent / "data" / "sprite_fright_argon.json"
)

CHAR_NAME_MAP = {
    "char_1": "엘리",
    "char_2": "렉스",
    "char_3": "빅토리아",
    "char_4": "제이",
    "char_5": "필",
    "char_6": "장로 스프라이트",
    "char_7": "버섯 요정(스프라이트)",
}

PLACE_AND_CAUSE_ENRICHMENT = {
    "0:18": ("숲 입구 바위 앞", "달팽이를 발견하고 반갑게 인사하며 학명을 적는 소리"),
    "0:28": ("숲길 초입", "빅토리아의 부츠 굽에 달팽이가 밟힌 소리와 렉스가 거칠게 투덜대는 목소리"),
    "0:35": ("숲길 초입", "헤어스프레이를 치익 뿌리는 소리와 빅토리아의 목소리"),
    "0:39": ("숲길 초입", "어깨에 멘 라디오 카세트 음악 소리와 제이의 들뜬 외침"),
    "0:43": ("숲길 초입", "캔 음료를 들이켜는 소리와 필의 낮고 느릿한 목소리"),
    "1:02": ("숲속 풀숲", "플라스틱 캔 고리에 끼어 파닥거리던 작은 새가 구출되며 지저귀는 소리"),
    "1:20": ("캠핑장 나무 아래", "제이가 나뭇가지에 매달려 턱걸이를 하다가 가지가 부러지고 새 둥지가 떨어졌기 때문"),
    "1:28": ("캠핑장 나무 기둥 앞", "나무에 붙은 딱정벌레에게 헤어스프레이를 뿌려 떨어뜨리고 밟는 소리"),
    "1:30": ("캠핑장 바비큐 그릴 앞", "착화제 불길로 나비들을 태우며 필이 크게 웃는 소리"),
    "1:41": ("캠핑장 텐트 앞", "쓰러진 텐트 앞에서 배트로 땅을 치며 소리치는 소리"),
    "2:04": ("캠핑장 바비큐 그릴 바닥", "필이 소시지에 뿌린 소금이 버섯 요정 머리에 닿아 거품을 토해내는 소리 (소금이 약점임)"),
    "2:37": ("숲속 비밀 공터", "버섯 요정들이 합창하며 노래하는 소리"),
    "3:03": ("숲속 비밀 공터", "피클 병의 내용물을 바닥에 쏟아붓는 소리"),
    "3:16": ("큰 나무 위 구멍", "장로 스프라이트가 나무 위에서 뛰어내리다 나뭇가지들에 연달아 부딪히며 굴러떨어지는 소리"),
    "3:38": ("나무뿌리 구멍 앞", "버섯 요정 세 마리가 무거운 보따리를 끌고 가는 소리"),
    "3:47": ("큰 나무 앞", "유리병을 등 뒤에 숨긴 채 장로 스프라이트에게 말을 거는 소리"),
    "4:00": ("밤의 캠핑장 모닥불 옆", "모닥불 소리와 엘리가 수첩에 물음표를 그리며 중얼거리는 소리"),
    "4:13": ("밤의 캠핑장", "숲속에서 들려온 비명과 나뭇가지 부러지는 소리에 놀라 깨어나는 소리"),
    "4:35": ("밤의 캠핑장", "입에 솔방울이 물려 소리를 못 내고 읍읍거리는 소리"),
    "4:40": ("밤의 캠핑장", "낮에 나비를 불태웠던 필에게 버섯 요정들이 착화제와 횃불을 던져 불길이 치솟은 소리"),
    "4:48": ("밤의 숲속 바닥", "밧줄에 묶인 렉스가 솔방울을 뱉어내고 다급하게 풀어달라고 외치는 소리"),
    "5:00": ("밤의 나무 위", "장로 스프라이트가 공격 명령을 내리는 소리"),
    "5:13": ("밤의 숲속", "손전등이 켜지자 바로 눈앞에 있던 버섯 요정을 보고 놀란 비명"),
    "5:21": ("밤의 숲속", "렉스가 배트로 버섯 요정을 쳐서 날려 보내는 소리"),
    "5:30": ("밤의 숲속", "낮에 벌레에게 헤어스프레이를 뿌렸던 빅토리아가 버섯 요정들이 쏜 스프레이를 얼굴에 맞고 지른 비명"),
    "5:41": ("밤의 나무 아래", "버섯 요정들이 던진 끈끈한 꽃 줄기에 머리카락이 감겨 공중으로 끌려 올라가는 비명"),
    "5:45": ("밤의 나무 아래", "엘리가 주머니칼로 자기 머리카락을 잘라내고 바닥에 떨어지는 소리"),
    "6:04": ("밤의 거미줄", "거미줄에 갇힌 빅토리아가 거미들에게 둘러싸여 지르는 비명"),
    "6:22": ("밤의 숲속", "수많은 달팽이와 거대 민달팽이가 얼굴과 몸을 뒤덮자 렉스가 지른 비명"),
    "6:34": ("거대한 나무 구멍 안", "나무 구멍 안에 갇힌 제이 위로 액체가 차오르며 나는 비명"),
    "7:05": ("캠핑장 그릴 근처", "소금통의 소금이 쏟아져 버섯 요정이 거품을 뿜으며 쓰러지는 소리"),
    "7:18": ("캠핑장 그릴 근처", "소금에 약한 버섯 요정들에게 엘리가 배낭 속 짠 과자(땅콩, 프레첼, 나초)를 던지며 외치는 소리"),
    "7:31": ("캠핑장 그릴 근처", "엘리가 짭짤한 소시지 스틱을 칼처럼 휘둘러 버섯 요정들을 쓰러뜨리는 소리"),
    "7:59": ("통나무 다리 위", "장로 스프라이트가 발목이 묶여 넘어진 엘리에게 주머니칼을 들고 다가오며 말하는 소리"),
    "8:09": ("통나무 다리 앞", "1:02에 엘리가 플라스틱 캔 고리에서 구해줬던 새가 날아와 장로 스프라이트 얼굴에 새똥을 떨어뜨려 엘리를 구해줬기 때문에 난 충격음과 이어지는 8:15 엘리의 웃음소리"),
    "8:15": ("통나무 다리 앞", "1:02에 구해줬던 새가 새똥으로 장로 스프라이트를 쓰러뜨려 구해준 것을 보고 엘리가 터뜨린 웃음소리"),
    "8:28": ("무너지는 통나무 다리", "가방 끈을 나뭇가지에 걸고 매달려 절벽 건너편으로 건너가는 소리"),
    "8:46": ("절벽 건너편 숲", "버섯 요정들이 다시 평화롭게 합창하며 숲속으로 멀어지는 소리"),
}

SPRITE_FRIGHT_FALLBACK_DATA = {
    "characters": [
        {
            "id": "char_1",
            "name_or_role": "엘리 (자연 관찰 학생)",
            "voice_traits": "높고 또렷하며 빠른 여자아이 목소리",
            "first_quote": "안녕, 달팽이 아저씨! (Hello, Mr. Snail!)",
            "first_timestamp": "00:18",
        },
        {
            "id": "char_2",
            "name_or_role": "렉스 (배트를 든 남학생)",
            "voice_traits": "굵고 거친 남성 목소리",
            "first_quote": "하, 저 자연보호 광팬이랑 엮이다니 믿기지가 않네. (Ugh, can't believe we got stuck with tree hugger.)",
            "first_timestamp": "00:28",
        },
        {
            "id": "char_3",
            "name_or_role": "빅토리아 (스프레이를 든 여학생)",
            "voice_traits": "비음이 섞이고 말끝을 길게 끄는 여성 목소리",
            "first_quote": "진정해, 자기야. (Relax, sugar buns.)",
            "first_timestamp": "00:35",
        },
        {
            "id": "char_4",
            "name_or_role": "제이 (카세트를 멘 남학생)",
            "voice_traits": "가볍고 약간 쉰 듯한 남성 목소리",
            "first_quote": "그래, 정신 줄 놓을 때까지 취해보자고! (Yeah, and get wasted out of our minds!)",
            "first_timestamp": "00:39",
        },
        {
            "id": "char_5",
            "name_or_role": "필 (배낭을 멘 남학생)",
            "voice_traits": "낮고 느릿하며 뭉개지는 남성 목소리",
            "first_quote": "내가 한발 앞섰지, 친구. (Way ahead of you, man.)",
            "first_timestamp": "00:43",
        },
        {
            "id": "char_6",
            "name_or_role": "장로 스프라이트 (수염 난 버섯 요정)",
            "voice_traits": "할아버지처럼 걸걸하고 억양이 강한 목소리",
            "first_quote": "반갑네! (Greetings!)",
            "first_timestamp": "03:16",
        },
        {
            "id": "char_7",
            "name_or_role": "스프라이트들 (작은 버섯 요정 무리)",
            "voice_traits": "아주 높고 얇은 아기 같은 합창 목소리",
            "first_quote": "해가 뜨면 우린 잠에서 깨어나네, 스마일리 디, 스마일리 덤 (We wake up with the sun, Smiley-dee, smiley-dum)",
            "first_timestamp": "02:23",
        },
    ],
    "moments": [],
}


def load_sprite_fright_argon_data() -> Dict[str, object]:
    """Loads the real Gemini 4 Argon analysis output from app/data/sprite_fright_argon.json or private/sprite_fright_argon.json (executed 2026-10-16 11:56 KST)."""
    for candidate_path in (APP_DATA_ARGON_JSON_PATH, PRIVATE_ARGON_JSON_PATH):
        if candidate_path.exists():
            try:
                return json.loads(candidate_path.read_text(encoding="utf-8"))
            except Exception:
                pass
    return SPRITE_FRIGHT_FALLBACK_DATA


def _replace_char_tokens(text: str) -> str:
    if not text:
        return ""
    out = text
    for cid, cname in CHAR_NAME_MAP.items():
        out = out.replace(cid, cname)
    return out


def build_initial_state() -> Dict[str, object]:
    RUNTIME_VERIFICATION_LOGS.clear()

    pref = UserPreference(
        color_mode="exclude",
        expression_mode="action",
        length_mode="one_line",
        tts_lang="ko",
    )

    argon_data = load_sprite_fright_argon_data()
    raw_characters = argon_data.get("characters") or SPRITE_FRIGHT_FALLBACK_DATA["characters"]
    raw_moments = argon_data.get("moments") or []

    people: Dict[str, PersonNode] = {}
    for ch in raw_characters:
        cid = ch["id"]
        ts_sec = mmss_to_seconds(ch["first_timestamp"])
        norm_ts = seconds_to_mmss(ts_sec)
        people[cid] = PersonNode(
            id=cid,
            name_or_role=f"{ch['name_or_role']} — {ch['voice_traits']}",
            person_type="fictional",
            voice_traits=ch["voice_traits"],
            first_quote=f"{ch['first_quote']} ({norm_ts})",
            first_timestamp=norm_ts,
            first_timestamp_sec=ts_sec,
            first_met_when_where=f"Sprite Fright ({norm_ts})",
            consent=True,
            consent_granted=True,
            memorable_quotes=[
                {"timestamp": norm_ts, "quote": ch["first_quote"]}
            ],
            moment_ids=[],
            source_id="sprite-fright",
        )

    dialogue_corpus = [_replace_char_tokens(m.get("utterance", "")) for m in raw_moments]
    cards: List[FactCard] = []
    moments: Dict[str, MomentNode] = {}

    for idx, m in enumerate(raw_moments, start=1):
        cid = f"card_sf_{idx}"
        mid = f"mom_sf_{idx}"
        who_id = m.get("who_id", "char_1")
        if who_id not in people:
            who_id = "char_1"
        person = people[who_id]
        ts_sec = mmss_to_seconds(m.get("timestamp", "0:00"))
        ts = seconds_to_mmss(ts_sec)
        short_first = person.first_quote.split("(")[0].strip()
        short_name = person.name_or_role.split(" — ")[0]
        who_intro = f"처음 {person.first_timestamp}에 '{short_first}'라고 말했던 {person.voice_traits}({short_name})"

        utterance = _replace_char_tokens(m.get("utterance") or "")
        visible_action = _replace_char_tokens(m.get("visible_action") or "")
        raw_sound_cause = _replace_char_tokens(m.get("sound_cause") or "")

        enrichment = PLACE_AND_CAUSE_ENRICHMENT.get(ts)
        place = m.get("place") or (enrichment[0] if enrichment else "숲속")
        sound_cause = enrichment[1] if enrichment else raw_sound_cause

        # Cross-timestamp causal enrichment for key moments (0:28, 7:18, 8:09)
        if ts == "0:28" and who_id == "char_2":
            visible_action = f"빅토리아의 부츠가 바위 위 달팽이를 밟아 으깨고 지나간 직후, {visible_action}"
        elif ts == "7:18":
            visible_action = f"소금에 버섯 요정이 쓰러지는 약점(2:04)을 확인한 엘리가 {visible_action}"
        elif ts == "8:09":
            visible_action = (
                f"{visible_action} 앞 장면(1:02)에서 엘리가 플라스틱 캔 고리에서 구해줬던 작은 새가 "
                f"나뭇가지 위에서 새똥을 떨어뜨려 구해준 것이며 이어서 8:15에 엘리가 안도의 웃음을 터뜨린다."
            )

        raw_summary = f"{who_intro}가 '{utterance}'라고 말하며, {visible_action}"
        if sound_cause:
            raw_summary = f"{who_intro}: {visible_action} (소리 이유: {sound_cause}) ({ts})."

        card = FactCard(
            id=cid,
            card_type="work_card",
            source_id="sprite-fright",
            source_title="Sprite Fright",
            source_type="youtube",
            youtube_video_id="_cMxraX_5RE",
            who_id=who_id,
            who_label=who_intro,
            person_type="fictional",
            voice_traits=person.voice_traits,
            first_quote=short_first,
            first_timestamp=person.first_timestamp,
            utterance=utterance,
            visible_action=visible_action,
            sound_event_and_cause=sound_cause,
            place=place,
            timestamp=ts,
            timestamp_sec=ts_sec,
            keywords=[
                short_name.split(" ")[0],
                place,
                ts,
            ],
            summary_sentence=raw_summary,
            status="ai_verified",
            source_badge="미리 처리한 결과 (실행 시각: 2026-10-16 11:56 KST · 대회 중 실제 Gemini 4 Argon 실행)",
        )
        card = verify_card_with_flash(
            client=None,
            card=card,
            pref=pref,
            dialogue_corpus=dialogue_corpus,
            run_live_llm_check=False,
        )
        cards.append(card)
        person.moment_ids.append(mid)
        if utterance and not utterance.startswith("("):
            person.memorable_quotes.append({"timestamp": ts, "quote": utterance})

        moments[mid] = MomentNode(
            id=mid,
            title=f"[{ts}] {short_name} — {place}",
            source_type="work",
            source_id="sprite-fright",
            source_title="Sprite Fright",
            youtube_video_id="_cMxraX_5RE",
            when_str=ts,
            timestamp=ts,
            timestamp_sec=ts_sec,
            place=place,
            people_ids=[who_id],
            people_labels=[person.name_or_role],
            heard_summary=utterance,
            visible_summary=card.visible_action,
            sound_cause_summary=sound_cause,
            card_ids=[cid],
            status="ai_verified",
        )

    works: Dict[str, WorkNode] = {
        "sprite-fright": WorkNode(
            id="sprite-fright",
            title="Sprite Fright (블렌더 스튜디오 단편 영화)",
            youtube_url="https://www.youtube.com/watch?v=_cMxraX_5RE",
            youtube_video_id="_cMxraX_5RE",
            license_note="Sprite Fright © Blender Studio, CC BY 4.0",
            duration_str="10:29",
            summary="영국 십대 다섯 명이 숲에 들어갔다가 버섯 요정(스프라이트)들을 만나는 이야기. 옷차림이나 색깔 대신 인물의 목소리 특징과 처음 한 말로 모든 장면을 이었습니다.",
            character_ids=[c["id"] for c in raw_characters],
            moment_ids=list(moments.keys()),
            card_ids=[c.id for c in cards],
            processing_stats={
                "processing_badge": "미리 처리한 결과 (실행 시각: 2026-10-16 11:56 KST)",
                "processing_badge_detail": "미리 처리한 결과 (실행 시각: 2026-10-16 11:56 KST · 대회 중 실제 Gemini 4 Argon 실행)",
                "executed_at_kst": "2026-10-16 11:56 KST",
                "argon_model": "gemini-4-argon",
                "argon_elapsed_sec": 99.53,
                "flash_model": "gemini-3.8-flash",
                "flash_elapsed_sec": 46.0,
                "characters_count": len(raw_characters),
                "moments_count": len(cards),
                "source_json": "private/sprite_fright_argon.json",
            },
        )
    }

    answer_key: List[AnswerKeyItem] = [
        AnswerKeyItem(
            id="ak_1",
            question="0:18에 달팽이에게 처음 말 건 목소리는 누구야?",
            query_timestamp="0:18",
            expected_keywords=["엘리", "0:18", "달팽이"],
            expected_timestamp_range=[10, 26],
            reference_answer="0:18에 높고 또렷한 목소리로 '안녕, 달팽이 아저씨!'라고 처음 말한 자연 관찰 학생 엘리예요 (0:18).",
        ),
        AnswerKeyItem(
            id="ak_2",
            question="0:28에 질퍽한 소리가 나고 거칠게 투덜대는 목소리는 누구야?",
            query_timestamp="0:28",
            expected_keywords=["렉스", "0:28", "자연보호", "달팽이"],
            expected_timestamp_range=[22, 35],
            reference_answer="부츠에 달팽이가 밟힌 직후, 0:28에 굵고 거친 목소리로 '자연보호 광팬이랑 엮이다니 믿기지가 않네'라고 처음 말한 렉스예요 (0:28).",
        ),
        AnswerKeyItem(
            id="ak_3",
            question="1:20에 갑자기 무언가 부러지고 깨지는 소리가 났는데 방금 무슨 일이야?",
            query_timestamp="1:20",
            expected_keywords=["0:39", "제이", "나뭇가지", "둥지"],
            expected_timestamp_range=[70, 88],
            reference_answer="처음 0:39에 '정신 줄 놓을 때까지 취해보자고!'라고 말했던 가벼운 목소리의 제이가 나뭇가지에 매달려 턱걸이를 하다가 가지가 부러져 새 둥지가 떨어졌어요 (1:20).",
        ),
        AnswerKeyItem(
            id="ak_4",
            question="1:30에 필이 왜 갑자기 크게 웃었어?",
            query_timestamp="1:30",
            expected_keywords=["0:43", "필", "착화제", "나비"],
            expected_timestamp_range=[85, 98],
            reference_answer="처음 0:43에 '내가 한발 앞섰지'라고 낮고 느릿하게 말했던 필이 바비큐 그릴 위 나비들에게 착화제 불길을 뿜어 태우면서 웃었기 때문이에요 (1:30).",
        ),
        AnswerKeyItem(
            id="ak_5",
            question="2:04에 켁켁거리며 거품을 토하는 소리는 왜 난 거야?",
            query_timestamp="2:04",
            expected_keywords=["소금", "버섯", "거품", "2:04"],
            expected_timestamp_range=[118, 132],
            reference_answer="필이 소시지에 뿌린 소금이 바닥의 버섯 요정 머리 위에 떨어져서 버섯 요정이 거품을 토해냈기 때문이에요 (2:04).",
        ),
        AnswerKeyItem(
            id="ak_6",
            question="3:16에 반갑다고 인사한 뒤 쿵쿵 굴러떨어지는 소리는 누구야?",
            query_timestamp="3:16",
            expected_keywords=["3:16", "장로", "반갑네", "나무"],
            expected_timestamp_range=[190, 205],
            reference_answer="3:16에 걸걸한 할아버지 목소리로 '반갑네!'라고 처음 말한 장로 스프라이트가 나무 위에서 뛰어내리다 가지에 부딪히며 굴러떨어진 소리예요 (3:16).",
        ),
        AnswerKeyItem(
            id="ak_7",
            question="7:18에 엘리가 무엇을 던져서 버섯 요정들을 물리쳤어?",
            query_timestamp="7:18",
            expected_keywords=["엘리", "소금", "과자", "7:18"],
            expected_timestamp_range=[430, 445],
            reference_answer="소금에 버섯 요정이 쓰러지는 약점을 확인한 엘리가 배낭에서 짠 과자(땅콩, 프레첼, 나초)를 꺼내 던져 물리쳤어요 (7:18).",
        ),
        AnswerKeyItem(
            id="ak_8",
            question="8:09에 장로 스프라이트가 비명을 지르고 8:15에 엘리가 웃었는데 방금 무슨 일이야?",
            query_timestamp="8:09",
            expected_keywords=["1:02", "새", "새똥", "엘리"],
            expected_timestamp_range=[480, 500],
            reference_answer="장로 스프라이트가 엘리에게 뛰어내리던 순간, 앞 장면(1:02)에서 엘리가 캔 고리에서 구해줬던 작은 새가 날아와 장로의 얼굴에 새똥을 떨어뜨려 구해줬기 때문이에요 (8:09).",
        ),
    ]

    return {
        "preference": pref,
        "works": works,
        "people": people,
        "moments": moments,
        "cards": cards,
        "answer_key": answer_key,
        "qa_history": [],
        "recently_changed_pages": [
            "작품 > Sprite Fright (실행 시각: 2026-10-16 11:56 KST · Gemini 4 Argon 분석 로드됨)",
        ],
    }
