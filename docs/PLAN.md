# Second Ear — 기획서 (PLAN)

> [근거]는 확인한 것, [가정]은 아직 확인하지 못한 것, (예시)는 당일 실제 자료에 맞춰 바꿀 문장이다. 사람 이름은 모두 예시다. 이 문서는 대회 전에 준비한 아이디어·설계 문서이고, 코드는 모두 대회 중에 작성한다.



## 0. 한눈에

| 항목 | 내용 |
|---|---|
| 이름 (영어) | Second Ear. 「세컨드 브레인」과 「귀」를 합친 이름. 들은 것과 보지 못한 것을 함께 기억해 주는 두 번째 귀 |
| 트랙 | 3 공익 (접근성). 엔터(영상 감상)에서 출발해 비서로 커지는 세컨드 브레인 |
| 발표 한 문장 (한국어) | 사람을 목소리로만 구분하고 장면은 남에게 물어야 아는 시각장애인을 위해, 보는 영상과 겪는 순간에서 보지 못한 것을 그 사람이 아는 말로 풀어 주고, 출처 달린 위키로 기억하는 「듣는 세컨드 브레인」 |
| Pitch (짧게) | Second brains are built for eyes. Second Ear is one you can hear. |
| Pitch sentence (English) | For blind people who recognize others only by voice and must ask someone to learn what just happened, Second Ear turns the videos they watch and the moments they live into a second brain they can hear: it describes what they couldn't see in words tied to their own memories, saves personal memories only after they confirm, and keeps every fact traceable to the original sound. |
| 한 숫자 | 국내 등록 시각장애인 248,360명, 전체 등록장애인의 9.4% (2023년 말) [근거](https://www.koddi.or.kr/webzine/didimdol/vol299/subPage_003.html). 시각장애 원인은 대부분 후천적이라 기억하는 시각 경험이 사람마다 다르다 [근거](https://www.newnonmun.com/article=10748936) |

## 1. 문제 정의

- **누가:** 영상을 보고, 친구들과 놀고, 모임에 가는 등 사람들과 함께 일상과 문화생활을 즐기는 시각장애인
- **원래 하려던 일:** 영상 속 이야기와 함께 있던 사람들의 순간을 다른 사람들처럼 즐기고, 나중에 다시 떠올리기
- **알고 보니:** 정보가 아예 없어서가 아니다. ① 「누가 말했는지」, 「왜 웃었는지」 같은 빈칸을 매번 사람에게 물어 채워야 하는데 묻는 것 자체가 부담이고, ② 들은 설명이 자기 기억과 이어지지 않는다. 「빨간 모자 쓴 남자」라는 설명은 목소리와 대화로 사람을 기억하는 사람에게 쓸모가 없다
- **문제 문장:** 시각장애인은 영상과 함께한 순간을 즐기고 기억하려 했는데, 알고 보니 정보가 부족해서가 아니라 빈칸을 매번 남에게 물어야 하는 부담과, 들은 설명이 자기 기억(목소리·대화)과 이어지지 않는 문제 때문에 멈췄다
- **근거:**
  - 시각장애인 191명 조사: 질문할 때 드는 사회적 비용이 크다 [근거](https://www.microsoft.com/en-us/research/?p=164168) (Brady 외, CSCW 2013)
  - 사진 설명을 가족·친구에게 부탁하지 않는 이유는 「부담 주기 싫어서」 [근거](https://arxiv.org/pdf/2407.19351) (AccessShare, 2024)
  - 설명을 원하는 방식은 사람마다 다르고 집단(선천·후천·저시력) 차이는 예상보다 작다. 사람마다 물어 맞추라는 권고 [근거](https://uczelniabadawcza.amu.edu.pl/en/wiadomosci/biblioteka/audio-describing-films-for-the-congenitally-and-non-congenitally-blind) [근거](https://www.helenkeller.org/wp-content/uploads/2023/11/HKNC_Considerations-for-Providing-AD-to-DeafBlind-Tip-Sheet.pdf)
  - 태어날 때부터 못 본 사람도 색을 말로 배워 이유까지 이해한다. 시각 표현을 일괄로 바꾸면 안 된다 [근거](https://pmc.ncbi.nlm.nih.gov/articles/PMC8379969) (Bedny 연구팀, PNAS 2021)
  - 당시 사람의 자세·표정 같은 상세 정보가 시각장애인의 추억 회상을 풍부하게 한다 [근거](https://arxiv.org/html/2501.15408v1) (Memory Reviver, UIST 2024)
  - 직접 본 장면: 동규의 시각장애인 친구가 야구장에서 함성마다 「뭐야?」라고 물었다. 목소리가 비슷하면 이름을 묻거나 맞는지 확인해야 하는데, 생활 속에서는 그러기 어려울 때가 많다 (동규 관찰)
- **가정:** 친구가 이런 기록과 위키를 실제로 쓰고 싶어 하는지 [가정]. 영상에서 사람을 목소리와 한 말로 정확히 잇는 정확도 [가정]. 한국어 화자 구분 정확도 [가정]
- **HMW:** 시각장애인이 누구에게도 묻지 않고, 영상과 함께한 순간을 자기 기억 방식대로 즐기고 다시 찾을 수 있게 하려면?
- **실제 한 사람:** 동규의 시각장애인 친구
- **엔터에서 비서로:** 영상을 볼 때 재미있어서 매일 쓰면 기록이 쌓이고, 쌓인 기록이 맥락이 되고, 맥락이 있으니 설명이 나에게 맞아져서 더 자주 쓴다. 같은 위키가 영상 속 인물에서 내 주변 사람으로, 그다음 장소·문서·일정으로 넓어져 비서가 된다
- **이미 있는 것과 다른 점:**

| 이미 있는 것 | 하는 일 | Second Ear의 차이 |
|---|---|---|
| 유튜브 화면해설·질문 도구 (ViDscribe, YouDescribe 등) [근거](https://a11y-paradise.onrender.com/reviews/69ebd7861a03678cbb26dfea) | 영상에 해설을 붙이고 질문에 답함 | 인물을 생김새가 아니라 목소리와 앞에서 한 말로 소개, 본 영상이 위키로 쌓여 다음 회차·다른 영상·내 삶의 기억과 이어짐 |
| Envision Ally [근거](https://letsenvision.com/blog/ally-beta-launch) | 선호와 「나에 대해」를 기억해 답을 맞춤 | 사람·순간·작품 위키, 문장마다 귀로 확인하는 출처 |
| VisionBuddy (Gemini 대회작) [근거](https://ai.google.dev/competition/projects/visionbuddy) | 실시간 영상 분석을 저장해 나중에 질문 | 사람 중심 기억, 개인 설명 방식, 개인 기억은 확인한 것만 저장 |
| 기억 기능이 있는 AI 안경 (Brilliant Labs Halo, Ray-Ban Meta 등) [근거](https://fast.io/resources/best-ai-glasses-2026/) | 지난 대화·장소·시각 맥락을 찾아 줌 (일반 사용자용) | 시각장애인용: 보이는 것을 그 사람의 기억(이름·한 말)으로 바꿔 말함, 저장 전 확인, 귀로 확인하는 출처 |
| Seeing AI·Envision 얼굴 인식 [근거](https://aiindigo.com/blog/envision-ai-review-2026-a-practical-look-at-ai-powered-vision) | 저장한 얼굴로 사람 이름 알려 줌 | 얼굴·목소리 특징을 뽑아 저장하지 않고, 그 사람이 한 말·자기소개·때·곳으로 잇기 |

## 2. 30초 시연 장면

- **처음 5초:** 「눈을 감아 보세요.」 공개 단편 영화의 한 장면 소리만 8초 튼다. 비명과 웃음이 들리는데 무슨 일인지 알 수 없다
- **중간:** 발표자가 「보통 AI라면 '빨간 옷 입은 아이가 넘어졌어요'라고 했을 거예요」라고 말한 뒤 휴대폰에 묻는다. 「방금 무슨 일이야?」 → Second Ear: (예시) 「처음에 버스에서 '숲은 지루해'라고 투덜대던 그 목소리의 아이가 버섯을 밟고 넘어졌어요 (3:12).」 → 「방금 그 목소리 누구야?」 → (예시) 「같은 아이예요. 0:45에 처음 나온 목소리예요.」 → 「원래 소리」를 누르면 그 순간이 다시 나온다
- **끝:** 노트북 화면에 작품 위키(등장인물마다 목소리 특징과 한 말, 장면 목록)와 계기판 숫자

실제 입력: 저작권 문제가 없는 공개 영상(CC BY), 동규의 목소리 질문

## 3. 사용자 흐름

길이 두 개이고, 같은 위키에 쌓인다.

### A. 영상 보기 (엔터, 출발점)
1. **설명 방식 고르기:** 색(그대로/빼고), 표정(행동으로/뜻으로), 길이(한 줄/자세히). 진단은 묻지 않는다
2. **영상 넣기:** 공개 영상 링크(유튜브)를 붙여 넣는다
3. **AI가 영상을 끝까지 본다:** 등장인물(목소리 특징, 처음 한 말), 장면, 대사, 보이는 행동을 시점과 함께 뽑아 작품 카드로 만든다. 기계 검증을 통과한 카드는 작품 위키에 「AI 정리」 표시로 들어간다 (공개 콘텐츠라 사용자 확인은 고를 수 있다)
4. **보면서 또는 본 뒤에 묻는다:** 「방금 무슨 일이야?」, 「방금 그 목소리 누구야?」, 「왜 웃었어?」. 답은 한 문장, 소리로 읽어 주고, 인물은 목소리와 앞에서 한 말로 소개한다
5. **원래 소리:** 답에 붙은 시점부터 영상을 다시 들려준다

### B. 내 삶의 기억 (세컨드 브레인으로 확장, 스마트 안경 가정)
시연에서는 휴대폰을 목에 걸어 안경 대신 쓴다.
1. **기록:** 「기억 켜기」를 누르면 카메라가 30~60초를 기록한다
2. **AI가 정리해 둔다:** 들린 말과 보였던 행동을 뽑아 기억 카드를 만든다. 기계 검증을 통과한 카드만 **검토 대기함**에 쌓인다. 아직 위키에 들어가지 않는다
3. **원할 때 확인한다:** 「정리해 줘」라고 하면 카드를 하나씩 소리로 읽어 준다. 「맞아」면 저장, 「아니야」면 버림, 「고쳐」면 고친 뒤 저장. 처음 보는 사람은 그 사람의 동의도 확인한다. 저장이 끝나면 바뀐 페이지를 알려 준다
4. **묻는다:** 「아까 배터리 얘기한 사람 누구였지?」. 영상 속 인물과 실제 인물은 위키에서 구분한다

### C. (있으면) 오늘의 한 마당
「오늘 들려줘」라고 하면 오늘 본 영상과 확인한 기억으로 하루를 돌아보는 음성을 판소리 아니리처럼 들려준다. 시연에서는 20초, 제품에서는 2~3분짜리 하루 회고다

## 4. 기능 범위

| 꼭 (4시간 안) | 있으면 좋음 (시간 남으면) | 하지 않음 (발표에서 「다음 단계」로만) |
|---|---|---|
| 공개 영상 링크 → 작품 카드 → 작품 위키 | 오늘의 한 마당 (하루 회고 20초) | 스마트 안경 실시간 처리 |
| 물어보기 → 인물을 목소리·한 말로 소개하는 한 문장 답 + 원래 소리 | 심사위원이 준 공개 링크를 즉석에서 처리 | 기기 안 검색 (EmbeddingGemma 2) |
| 검증 루프 + 계기판 | 32MB 넘는 파일 조각 올리기 | 얼굴·목소리 특징 저장 |
| 내 기록 파일 → 기억 카드 → 검토 대기함 → 확인 → 위키 | 긴 영상을 조각으로 나눠 처리하고 합치기 | 친구가 찍은 영상 모으기 |
| 휴대폰 카메라로 현장 기록 | 온톨로지 보기 화면 | 장소·문서·일정 비서 |
| 카드와 답을 소리로 읽기 | 말로 고치기 | 여러 사용자 계정, 앱 설치형 |
| 새 사람 동의 확인, 설명 방식 두 가지 | | |
| 접근성 기본 (읽히는 이름, 자동 읽기, 제목 구조, 키보드) | | |

자세한 개발 순서는 17절.

## 5. 화면 정보 위계 (무엇을 먼저, 크게)

### 기기 나누기
- **휴대폰 = 사용자의 화면.** 영상을 듣고, 묻고, 기록하고, 확인한다. 시연에서는 목에 걸어 안경 대신 쓴다
- **노트북 = 심사위원에게 보여 줄 화면.** 같은 주소에서 영상, 위키, 검토 대기함, 계기판을 크게 보여 준다

### 휴대폰 첫 화면
- 가장 크게: 「영상 넣기」(링크 붙여 넣기)와 「기억 켜기」 두 버튼, 그 아래 「물어보기」 입력칸
- 그다음: 「정리해 줘」(검토 대기 카드 수), 최근 본 영상과 최근 순간 (제목 단위로 넘길 수 있게)
- 빼는 것: 그래프, 썸네일 위주 화면, 작은 아이콘 버튼

### 휴대폰 영상 화면
- 가장 크게: 재생/멈춤, 「방금 뭐야?」 버튼 (누르면 지금 시점에 대해 묻는다)
- 그다음: 물어보기 입력칸, 등장인물 목록 (목소리 특징과 처음 한 말)

### 휴대폰 검토 화면
- 가장 크게: 지금 읽는 카드 한 장 (나오자마자 소리로 읽음)
- 그다음: 「맞아」, 「아니야」, 「고쳐」 큰 버튼 세 개, 「원래 소리」
- 처음 보는 사람이 있으면 「이분을 기억해도 될까요?」 동의 확인

### 휴대폰 답 화면
- 가장 크게: 한 문장 답 (나오자마자 소리로 읽고, 화면 읽기도 자동으로 읽음)
- 그다음: 「원래 소리」, 「틀렸어요」, 「더 자세히」

### 노트북 위키·계기판 화면
- 가장 크게: 작품 / 사람 / 순간 페이지 (제목 구조), 이번에 바뀐 페이지 표시
- 그다음: 검토 대기함 (대기·확인·버림 상태)
- 계기판: 출처 확인 통과율, 인용 일치율, 사람 확인율, 출처 없는 문장 수, 동의 없이 저장된 사람 수, 설명 방식 위반 수, 정답표 정확도

### 접근성 요구
- 화면 읽기(VoiceOver·TalkBack)만으로 핵심 흐름(영상 넣기 → 방금 뭐야 → 원래 소리, 기억 켜기 → 정리해 줘 → 맞아)을 쓸 수 있다. 모든 버튼에 읽히는 이름이 있다
- 새 카드, 새 답, 상태 변화는 자동으로 읽힌다
- 저시력 사용자를 위해 큰 글자와 고대비. 색으로만 상태를 나타내지 않는다
- 화면 읽기 사용자가 이미 아는 동작(쓸기, 두 번 탭)만 쓰고 새 손동작을 만들지 않는다
- 말로 묻기는 먼저 휴대폰 기본 받아쓰기로 해결한다 (화면 읽기 사용자가 이미 쓰는 방식)

## 6. 입력과 출력

| | 무엇 | 형식·크기 | 어디서 구하나 |
|---|---|---|---|
| 입력 | 공개 단편 영화 한 편 | Blender Studio의 「Sprite Fright」(2021, 10분 29초). 영국 십대 다섯 명이 숲에서 버섯 정령들을 만나는 공포 코미디 [근거](https://studio.blender.org/films/sprite-fright/pages/about). 유튜브 https://www.youtube.com/watch?v=_cMxraX_5RE (archive.org 기록 기준, 당일 Blender Studio 공식 채널인지 확인) [근거](https://archive.org/details/sprite-fright-2021). 라이선스는 CC BY (Blender Studio 페이지는 1.0, archive.org는 4.0. 둘 다 출처 표시 조건) → README와 데모 영상에 「Sprite Fright © Blender Studio, CC BY」 | 유튜브 |
| 입력 | 심사위원이 고른 공개 영상 링크 (있으면) | 짧은 공개 영상 | 시연 중 |
| 입력 | 행사장 기록 2~3개 (점심 때 다른 참가자, 시연 때 심사위원) | 30~60초, 휴대폰 카메라 720p | 당일 동의받고 녹화 |
| 입력 (선택) | 친구들과 찍었던 예전 영상 | 대회 시작 뒤 노트북에서 macOS 기본 도구(avconvert, 1280x720)로 줄인다 | 동규 사진첩. 나온 사람의 동의를 받은 것만 |
| 입력 | 말로 하는 질문, 확인 답(맞아/아니야) | 받아쓰기한 글, 버튼 | 시연 중 |
| 입력 | 정답표 | 공개 영화 질문 8~10개와 정답 | 동규가 영화를 보고 작성. 개인 기억 질문이 들어가면 비공개 저장소에만 |
| 출력 | 작품 카드, 기억 카드 (검토 대기함) | 카드마다 출처 시점 | — |
| 출력 | 작품·사람·순간 위키 페이지 | 문장마다 출처 시점 | — |
| 출력 | 한 문장 답 (글 + 소리), 원래 소리 구간 | 몇 초 | — |
| 출력 | 계기판 숫자 | 화면 | — |
| 출력 (있으면) | 오늘의 한 마당 | 20초 음성 | — |

**공개 영상은 올릴 필요가 없다:** Gemini API 문서의 「유튜브 링크 넣기」 예시는 모두 Interactions API로 되어 있다. 미리보기 기능이라 무료이고, 무료 등급은 하루 8시간까지, 공개 영상만 되며(일부 공개·비공개 불가), Gemini 2.5 이후 모델은 요청 하나에 영상 10개까지다 [근거](https://ai.google.dev/gemini-api/docs/video-understanding). 같은 문서에 영상을 에이전트처럼 살펴보는 「agentic」 처리 방식도 있다(시간이 되면 시험). 링크가 실패하면 archive.org의 CC BY 영화 파일(MP4 57.8MB)을 서버가 받아 Files API(무료 등급 파일당 2GB)로 넘긴다. 「원래 소리」는 유튜브 공식 플레이어를 그 시점부터 틀어 준다

**내 기록의 크기 한도:** Cloud Run은 요청 하나에 32MB까지 받는다 [근거](https://docs.cloud.google.com/run/quotas). 휴대폰 카메라를 720p로 두고 30~60초로 찍으면 한도 안에 들어온다. 큰 파일은 브라우저가 30MB보다 작은 조각으로 나눠 보내고 서버가 이어 붙인다 (있으면 좋음)

**긴 영상은 나눠서 처리하고 합친다 (있으면 좋음):** 서버가 영상을 1~2분 조각으로 자르고, 조각마다 flash가 동시에 첫 정리를 한 뒤, 시점을 원래 영상 기준으로 보정해 Argon이 하나로 합친다. Gemini의 「영상 구간 지정」 기능은 Interactions API 문서에 없고 오류 보고가 있어서 기대지 않는다 [근거](https://discuss.ai.google.dev/t/videometadata-clipping-on-youtube-urls-no-longer-clips-audio-frames-still-clipped-20x-token-inflation-on-long-videos/178970)

### 6-1. 온톨로지 (기억의 뼈대)

| 대상 | 뜻 | 예 |
|---|---|---|
| 작품 | 본 영상 | 「Sprite Fright」 |
| 사람 | 영상 속 인물 또는 실제로 만난 사람 (둘을 구분) | (예시) 버스에서 투덜대던 아이 / 민수 |
| 순간 | 영상의 장면 또는 함께한 일 | (예시) 숲에 도착한 장면 / 9월 공원 소풍 |
| 장소 | 순간이 일어난 곳 | 숲 / 한강 공원 |
| 말 | 누가 한 말 | (예시) 「숲은 지루해」 |
| 행동 | 누가 한, 눈에 보이는 행동 | (예시) 버섯을 밟고 넘어짐 |
| 출처 | 어느 영상의 몇 초 | (예시) 3:12 |
| 나 | 사용자의 설명 방식 | 색 빼고, 한 줄로 |

**관계:** 작품은 장면과 인물을 가진다 · 사람이 말을 했다 · 사람이 행동을 했다 · 말과 행동은 어느 순간에 있었다 · 순간은 어느 장소에서 · 사람은 순간에 함께 있었다 · 말과 행동은 출처를 가진다

**모든 사실(말·행동)이 가지는 것:** 누가, 무엇을, 언제(출처 시점), 어디서, 찾기용 낱말, 상태(AI 정리 / 대기 / 확인 / 버림), 확인한 사람, 확인한 시각. 실제 인물은 동의 여부를 가진다

### 6-2. 위키 (온톨로지를 사람이 읽는 글로)
- **작품 페이지:** 등장인물마다 목소리 특징과 처음 한 말, 장면 목록, 웃음·비명 같은 소리가 난 순간과 그 이유
- **사람 페이지:** 이름, 처음 만난 때와 곳, 그 사람이 한 말 중 기억할 것, 함께한 순간 목록, 동의 여부
- **순간 페이지:** 언제·어디·누구, 들린 것, 보였던 것(몸짓·장면)
- **나 페이지:** 설명 방식 (진단 정보는 받지 않음)
- 개인 기억은 **확인된 사실만**, 작품은 기계 검증을 통과한 사실만 들어간다. 문장마다 출처가 붙고, 누가(AI/사용자) 무엇을 언제 바꿨는지 남는다
- 저장 위치는 비공개 Cloud Storage. 공개 저장소에는 개인 영상·위키·정답표가 들어가지 않는다

### 6-3. AI가 찾기 쉽게
- **지금 (시연 크기):** 위키 전체를 Argon이 한 번에 읽는다. 질문은 온톨로지 관계로 풀린다. 예: 「방금 그 목소리 누구야?」는 지금 시점 근처 대사의 화자를 찾고, 그 인물이 처음 한 말을 답한다. 「배터리 얘기한 사람 누구야?」는 「배터리」가 들어간 말을 찾고, 그 말을 한 사람을 답한다
- **커지면:** 온톨로지 색인(사람·작품·장소·날짜·낱말)으로 후보를 좁히고, 임베딩 검색으로 뜻이 비슷한 사실을 더한 뒤 Argon에게 넘긴다
- **다음 단계:** EmbeddingGemma 2로 휴대폰 안에서 검색한다. 2026-10-06 공개된 Gemma 4 기반 모델로, 글·이미지·소리·영상을 한 공간에 담아 기기 안에서 영상 속 순간을 찾는다 [근거](https://developers.googleblog.com/embeddinggemma-2-the-developer-guide/). 개인 기억이 기기 밖으로 나가지 않게 되고, 트랙 3의 「기기 안 모델」과도 맞는다

## 7. 모델 역할 나누기

| 할 일 | 모델 | 왜 이 모델인가 |
|---|---|---|
| 영상을 끝까지 보고 작품 카드 만들기(인물·목소리·대사·행동·시점), 기억 카드를 기존 위키와 잇기(같은 사람인지, 어긋나는 기록은 없는지), 어려운 질문(시간을 거슬러 웃음의 원인 찾기, 멀리 떨어진 장면 잇기), 검증 지휘 | `gemini-4-argon` (thinking low~medium) | 영상 전체와 위키를 한 맥락에 놓고 판단해야 인물 잇기가 깨지지 않는다 |
| 기록의 첫 정리(들린 말, 보인 행동, 시점), 근거 재확인(카드·답이 가리킨 구간을 다시 보고 예/아니오), 빠른 답 | `gemini-3.8-flash` | 빠르고 여러 개를 동시에 돌릴 수 있다 |
| 카드와 답, 한 마당 목소리 | `gemini-3.8-flash-tts` | 영상 속 사람들과 확실히 다른 안내 목소리 |
| (있으면) 화자 구분과 단어 시점 | `gemini-3.5-transcribe` | 화자 구분과 단어 시점을 지원한다. 화자 구분을 켜면 30분 한도, 3명 이상은 실험 단계 [근거](https://ai.google.dev/gemini-api/docs/models/gemini-3.5-transcribe). 한국어 정확도는 당일 먼저 시험 [가정] |
| (선택) 정리를 뒤에서 돌리기 | Managed Agents | 한 번의 API 호출로 도구를 쓰는 에이전트를 띄운다(2026-05 공개) [근거](https://gigazine.net/gsc_news/en/20260520-google-gemini-api-managed-agents). 7월부터 뒤에서 실행 가능 [근거](https://www.dawan.africa/news/google-upgrades-gemini-api-with-background-execution-and-remote-mcp-integration). 11시 허용 확인 뒤 |
| (다음 단계) 안경에서 실시간 정리 | `gemini-3.8-live` | 실시간 음성·카메라 (영상은 초당 1장) |
| (다음 단계) 기기 안 검색 | EmbeddingGemma 2 | 6-3절 |

내 기록 영상은 Files API로 올리고, 처리 상태가 끝난 뒤(ACTIVE)에 모델에 넘긴다. 준비 전에 부르면 오류가 난다 [근거](https://discuss.ai.google.dev/t/gemini-2-5-flash-api-cannot-process-video-input/80093).

**Argon이어야만 하는 이유 (심사 기준 3번):**
- **1M 통합 맥락:** 10분짜리 영화 전체(영상 1초에 약 300토큰)를 한 번에 놓고 「3분의 이 목소리가 처음 0:45에 나온 그 아이인가」를 판단한다. 드라마 여러 회차, 안경이 하루 종일 모은 기록, 몇 달 치 위키로 커질수록 더 필요하다. 조각으로 나누면 인물 잇기가 깨진다
- **깊은 추론:** 웃음과 비명은 원인 뒤에 터진다. 시간을 거슬러 원인을 찾고, 기록끼리 어긋나는 곳을 찾아낸다
- **멀티모달 지휘:** 첫 정리, 근거 재확인, 목소리 모델을 지휘해 검증된 카드 묶음으로 합친다
- **긴 출력:** 영상 하나가 인물·장면 카드 수십 장과 위키 페이지 여러 개를 한 번에 만든다

## 8. 검증 루프 (심사 기준 1번)

카드는 **기계 검증을 통과해야 위키나 검토 대기함으로 간다.** 개인 기억은 그다음에 사용자가 확인한다.

| 무엇을 검사 | 어떻게 기계가 판정 | 통과 기준 | 실패하면 | 화면에 보이는 숫자 |
|---|---|---|---|---|
| 근거: 카드·답이 가리킨 시점에 그 말·행동이 정말 있나 | flash가 그 시점을 다시 보고 예/아니오 | 100% | 그 문장만 다시 쓴다. 3번 실패하면 「확실하지 않음」으로 표시 | 출처 확인 통과율 |
| 인용: 「그 사람이 한 말」이 첫 정리의 대사 목록에 있나 | 글자 대조 | 100% | 다시 쓴다 | 인용 일치율 |
| 출처: 모든 카드와 위키 문장에 출처 시점이 붙었나 | 형식 검사 | 출처 없는 문장 0개 | 다시 쓴다 | 출처 없는 문장 수 |
| 동의: 위키의 실제 인물마다 동의 표시가 있나 | 목록 대조 | 동의 없이 저장된 사람 0명 | 저장 보류, 사용자에게 확인 요청 | 동의 없이 저장된 사람 수 |
| 설명 방식: 「색 빼고」면 색 낱말 0개, 「한 줄」이면 길이 제한, 감정 짐작 낱말 0개 | 낱말 목록, 글자 수 | 위반 0 | 다시 쓴다 | 설명 방식 위반 수 |
| 정답표: 공개 영화에 대해 손으로 적은 질문 8~10개 | 정답과 대조 | 80% 이상 | 원인 기록 | 정확도 |
| 사람 확인: 사용자가 「맞아」라고 한 기억 카드의 비율 | 확인 기록 집계 | 참고 지표 | 「아니야」가 나온 카드의 원인 기록 | 사람 확인율 |

- 최대 반복 횟수: 3회 (전역 규칙 상한 5회 안)
- 재확인은 카드·답을 만든 호출과 다른 호출(flash)이 한다
- 정답지: 동규가 공개 영화를 보고 적은 질문·정답 표 (누가, 무엇을, 몇 초에)

## 9. 사람이 확인하는 지점 (심사 테스트 3번)

- **검토 대기함이 핵심 확인 지점이다.** AI가 정리한 개인 기억은 사용자가 「맞아」라고 하기 전에는 위키에 들어가지 않는다
- **시각장애인은 보이는 사실을 직접 확인할 수 없다.** 그래서 확인을 둘로 나눈다. 사용자는 자기가 아는 것(누구인지, 들은 말, 기억할지 말지)을 확인하고, 눈으로만 확인되는 것(몸짓·장면)은 기계 검증과 「확실하지 않음」 표시로 지킨다. 다음 단계에서는 그 자리에 있던 사람에게 그 순간만 보내 확인받을 수 있게 한다
- 새 사람은 그 사람의 동의를 받은 뒤에만 저장한다 (「이분을 기억해도 될까요?」)
- AI가 이름이나 같은 사람을 추측한 카드는 「추측」이라고 밝히고 읽는다 (「이 목소리를 민수로 기억할까요?」)
- 공유하거나 내보내기 전에 확인한다
- 동의·보관: 사용자가 참여한 대화만 기록한다(타인 간 대화 녹음은 통신비밀보호법 위반). 얼굴이나 목소리에서 특징을 뽑아 저장하지 않는다. 원본 영상은 출처 확인용으로 비공개 저장소에만 두고, 버린 카드의 내용은 지운다. 사용자는 언제든 사람·순간을 지울 수 있다

## 10. 합격 기준 (시연 전에 기계·사람이 확인할 것)

- [ ] 공개 영화 링크를 넣으면 작품 위키가 만들어지고, 「방금 무슨 일이야?」와 「방금 그 목소리 누구야?」에 인물을 목소리·한 말로 소개하는 답이 나온다
- [ ] 모든 답에 출처 시점이 있고, 「원래 소리」를 누르면 그 시점부터 나온다
- [ ] 현장 기록 1개를 넣으면 검토 대기함에 카드가 생기고, 「맞아」로 위키에 저장되고, 바뀐 페이지가 보인다. 여기까지 3분 안에 끝난다
- [ ] 계기판 숫자가 실제 실행 값으로 보인다
- [ ] 휴대폰 VoiceOver를 켜고 핵심 흐름을 한 번 끝까지 해 본다
- [ ] Cloud Run 주소가 휴대폰과 노트북에서 열린다
- [ ] 공개 저장소에 개인 영상·위키·키가 없고, 공개 영화의 출처가 README에 있다
- [ ] 정답표 정확도 80% 이상

## 11. 기술 선택

- 언어·프레임워크: Python 3.12 + uv + FastAPI, 휴대폰 브라우저용 웹 화면
- 라이브러리: google-genai 2.3.0 이상(Interactions API), FastAPI, uvicorn, 파일 업로드 처리용 python-multipart, google-cloud-storage. 긴 영상 나누기를 하면 ffmpeg (Dockerfile에 설치). 공식 공개 템플릿을 쓰면 README Credits에 적는다
- 원래 소리: 유튜브 공식 플레이어를 그 시점부터 재생. 퍼가기가 막힌 영상이면 유튜브 링크를 그 시점으로 연다. 내 기록은 비공개 버킷의 원본을 그 시점부터 재생
- 저장: 비공개 Cloud Storage 버킷 (내 기록 영상, 온톨로지·위키, 정답표). 막히면 시연용으로 인스턴스 메모리에 두고 최종 배포 뒤 다시 넣는다
- 배포: Google Cloud Run (서울), 인스턴스 최대 1개 (상태를 한곳에 두기 위해), 기본 HTTPS (카메라·마이크 권한에 필요)
- 휴대폰 카메라: 웹의 파일 선택에서 카메라로 바로 찍는 기본 기능을 쓴다 (따로 녹화 기능을 만들지 않음). 시연 휴대폰의 카메라 녹화 설정은 720p
- 화면 언어: 11시 규칙 설명에서 답을 듣기 전까지 화면 글은 영어와 한국어를 함께 보여 준다. 답과 카드 음성은 한국어 기본, 영어로 바꿀 수 있게
- 쓰지 않음: Streamlit, PHP, 외부에 열린 DB, 구글 밖 AI API, 유튜브 영상 내려받기

## 12. 위험과 대응

| 위험 | 대응 |
|---|---|
| 유튜브 링크 읽기가 실패함 (문서상 되지만 미리보기 기능) | 11:40 첫 시험에서 확인. 안 되면 archive.org의 CC BY 영화 파일(MP4 57.8MB)을 서버가 받아 Files API로 넘긴다 |
| 영화 처리가 느림 | 시연용 영화는 대회 중에 미리 처리해 둔다. 심사위원 링크는 짧은 영상만, 기다리는 동안 계기판을 설명한다 |
| 유튜브 퍼가기가 막힘 | 그 시점의 유튜브 링크를 연다 |
| 저작권 | CC BY 영상만 쓰고 README와 데모 영상에 출처를 적는다. 유튜브 영상은 내려받지 않는다 |
| 내 기록 업로드가 32MB를 넘음 | 720p·60초 이하. 그래도 크면 조각 올리기 또는 노트북에서 비공개 버킷에 직접 |
| 재배포 때 위키가 사라짐 | 비공개 버킷에 저장. 버킷 권한이 막히면 최종 배포 뒤 다시 넣는다 (10분 잡기) |
| 인물 잇기가 틀림 | 확실하지 않으면 그렇다고 말한다. 개인 기억의 추측 카드는 「추측」이라고 밝히고 사용자가 확인한다 |
| 한국어 화자 구분이 약함 | 행사장 기록은 자기소개와 말 내용으로만 잇는다 |
| 카드·답 음성(TTS)이 안 나옴 | 화면 글로 보여 주고, 노트북 화면 읽기로 읽는다 |
| 무대에서 VoiceOver 조작이 꼬임 | 라이브는 앱 목소리로 진행하고, VoiceOver 사용 장면은 데모 영상에 담는다 |
| 「단순 챗봇」 또는 「유튜브 해설 도구」로 보임 | 인물을 목소리·한 말로 잇는 답, 작품 위키, 검토 대기함, 검증 숫자, 내 삶의 기억으로 이어지는 장면을 함께 보여 준다 |

## 13. 4시간 시간표

| 시각 | 할 일 | 끝났다는 기준 |
|---|---|---|
| 11:20~11:40 | `/hackathon-setup` → 14절 목표 설명을 Argon에게 주고 질문·설계안 받기 | 저장소, Argon 첫 호출 |
| 11:40~12:00 | 먼저 시험: Sprite Fright 링크로 인물·목소리 특징·대사·행동·시점이 나오는지, 걸리는 시간(flash와 Argon 각각). 30초 한국어 클립도 하나 | 결과와 시간 기록 |
| 12:00~12:15 | 빈 화면이라도 Cloud Run에 첫 배포, 비공개 버킷 연결 | HTTPS 주소가 휴대폰에서 열림 |
| ~13:00 | P0: 공개 영상 → 작품 위키, 물어보기 → 인물을 목소리·한 말로 소개하는 답과 원래 소리 | 공개 영화로 질문·답·원래 소리 |
| ~13:30 | P0: 검증 루프와 계기판 | 숫자가 실제 값으로 나옴 |
| ~14:00 | P0: 내 기록 → 기억 카드 → 검토 대기함 → 맞아 → 위키 | 행사장 기록 1개로 처음부터 끝까지 |
| ~14:15 | P1: 휴대폰 카메라 기록, 소리 읽기, 동의 확인, 설명 방식, 접근성 기본 | 17절 장면 1~5가 돈다 |
| 14:15~14:20 | 최종 배포 | 휴대폰·노트북에서 열림 |
| 14:20 | 기능 동결, 3분 리허설 2번 | 3분 안에 끝남 |
| ~15:05 | 데모 영상 녹화 → 개인 YouTube 일부 공개, GitHub push | 링크 |
| 15:00 | Antigravity에 「제출 점검」 | 표 전부 통과 |
| ~15:20 | 영어 소개글 제출 | 제출 완료 |

## 14. Argon에게 처음 줄 목표 설명 (자연어만)

**한국어:** 시각장애인을 위한 「듣는 세컨드 브레인」 웹앱 Second Ear를 휴대폰 브라우저용으로 만들고 싶다. 길은 두 개이고 같은 위키에 쌓인다. 첫째, 사용자가 공개 유튜브 영상 링크를 넣으면 영상을 끝까지 보고 등장인물(목소리 특징, 처음 한 말), 장면, 대사, 보이는 행동을 시점과 함께 작품 카드로 만들어 작품 위키에 넣는다. 사용자가 「방금 무슨 일이야?」, 「방금 그 목소리 누구야?」라고 물으면 한 문장으로 답해 소리로 읽어 주고, 그 시점부터 원래 영상을 다시 들려준다. 둘째, 스마트 안경을 가정하고(시연에서는 목에 건 휴대폰) 사용자가 30~60초를 기록하면 들린 말과 보인 행동으로 기억 카드를 만들어 검토 대기함에 쌓고, 사용자가 「정리해 줘」라고 하면 하나씩 읽어 준 뒤 「맞아」라고 한 것만 위키에 저장한다. 위키는 작품·사람·순간·장소·말·행동·출처로 이루어진 온톨로지 위에 만든다. 인물은 생김새가 아니라 이름이나 목소리와 앞에서 한 말로 소개하고, 감정은 짐작하지 않는다. 카드는 다른 호출이 근거를 다시 확인하는 검증을 통과해야 한다. 새 사람은 동의를 받은 뒤에만 저장한다. 핵심 흐름은 화면 읽기 프로그램만으로 쓸 수 있어야 한다. 내 기록 업로드는 Cloud Run 한도(32MB) 안에서 받고, 개인 자료는 비공개 버킷에만 둔다. 시연 흐름과 개발 순서는 17절, 온톨로지는 6-1절, 검증 루프와 합격 기준은 8절과 10절이다. 코드를 쓰기 전에 질문과 설계안(화면 흐름, 모델 역할, 검증 루프, 17절 순서대로 자를 범위)을 먼저 달라.

**English:** I want to build Second Ear, a mobile web app that works as a "second brain you can hear" for blind people. It has two paths that feed one wiki. First, when the user pastes a public YouTube link, the app watches the whole video and turns its characters (voice traits and first lines), scenes, dialogue, and visible actions into timestamped cards stored in a work wiki. When the user asks "What just happened?" or "Whose voice was that?", the app answers in one sentence, reads it aloud, and replays the original video from that moment. Second, assuming smart glasses (a phone hung around the neck in the demo), when the user records 30 to 60 seconds, the app turns what was heard and what was visible into memory cards in a review inbox; when the user says "catch me up," it reads them aloud one by one and saves only what the user confirms. The wiki sits on an ontology of works, people, moments, places, utterances, actions, and sources. People are introduced by name, or by their voice and what they said earlier, never by appearance, and the app never guesses emotions. Cards must pass a verification step in which a separate call re-checks the evidence. A new person is saved only after their consent. The core flow must be usable with a screen reader alone. Personal recordings stay under the Cloud Run request limit (32 MB), and personal data stays in a private bucket only. The demo flow and build order are in section 17, the ontology in section 6-1, and the verification loop and acceptance criteria in sections 8 and 10. Before writing code, please give me your questions and a design proposal: screen flow, model roles, verification loop, and what to cut, following the order in section 17.

## 15. 영어 소개글 틀

- **Problem:** Blind people recognize others by voice and conversation. When voices sound alike, or when everyone laughs at something visual, they have to ask someone, and research shows that asking every time carries a real social cost. Existing AI descriptions say "a kid in a red jacket", which means nothing to someone who has never seen that jacket.
- **Who it's for:** Blind people who enjoy videos, everyday life, and culture with friends. Our first user is the builder's blind friend, who asked "What happened?" at every cheer during a baseball game.
- **Why Gemini 4 Argon:** Telling whose voice that was requires the whole film, or weeks of memories, in one context; finding why people laughed requires reasoning backward in time; and turning a video into one verified set of cards requires orchestrating analysis, re-checking, and voice models.
- **How it works:** (초안, 당일 실제로 만든 것에 맞춰 고친다) Paste a public video link and Gemini 4 Argon watches the whole video, turning every character (voice traits and first lines), scene, line of dialogue, and visible action into timestamped cards that build a work wiki. Ask "What just happened?" or "Whose voice was that?" and Second Ear answers in one sentence, read aloud, introducing people by their voice and what they said earlier, then replays the original moment. The same wiki extends to real life: with a phone hung around the neck standing in for smart glasses, a short recording becomes memory cards in a review inbox, and only the cards the user confirms are saved into an ontology of people, moments, places, utterances, actions, and sources.
- **Verification loop:** (초안, 숫자는 당일 실제 값) Every card and answer must cite a timestamp, and a separate Gemini call re-watches that moment to confirm it (up to 3 retries, then the claim is marked "uncertain"). Quotes are matched against the extracted dialogue, sentences without a source are rejected, style rules (no color words if the user opts out, no guessed emotions) are checked by word lists, and accuracy is measured against a hand-written answer key. Live numbers on the dashboard: evidence pass rate __%, quote match __%, unsourced sentences 0, people saved without consent 0, answer-key accuracy __%.
- **Human in the loop:** Personal memories never enter the wiki until the user says "that's right." Because a blind user cannot check visual details, those are guarded by machine re-checks and clearly labeled uncertainty. A new person is saved only with that person's consent, and no face or voice prints are ever extracted. Every answer can be checked by ear against the original sound.
- **Demo:** (초안) The demo video shows a phone with VoiceOver on: pasting the Sprite Fright link, asking "What just happened?" and "Whose voice was that?", hearing the original moment, then recording a short conversation, confirming the memory cards, and seeing the wiki and dashboard update. Sprite Fright © Blender Studio, CC BY.

## 16. 3분 발표 대본

| 시간 | 말할 것 | 화면 |
|---|---|---|
| 0:00~0:20 | 「눈을 감아 보세요.」 공개 영화 소리 8초. 친구 이야기: 야구장에서 함성마다 「뭐야?」, 목소리가 비슷하면 「누구세요?」라고 묻기 미안해한다 | 제목, 한 숫자 |
| 0:20~0:55 | 「보통 AI라면 '빨간 옷 입은 아이'라고 했을 거예요.」 「방금 무슨 일이야?」 → 인물을 목소리·한 말로 소개하는 답 → 「방금 그 목소리 누구야?」 → 원래 소리 | 휴대폰 답, 노트북 작품 위키 |
| 0:55~1:30 | 「같은 위키가 내 삶으로 이어져요. 안경 대신 휴대폰을 목에 걸었어요.」 심사위원 한 분 동의 → 30초 대화 기록 → 기다리는 동안 계기판 설명 | 기록 → 정리 |
| 1:30~2:00 | 「정리해 줘」 → 카드를 소리로 읽음 → 「이분을 기억해도 될까요?」 → 「맞아」 → 위키 저장, 바뀐 페이지 | 검토 대기함 → 위키 |
| 2:00~2:20 | 「아까 점심때 배터리 얘기한 분이랑 같은 사람이야?」 → 「아니요, 점심때 만난 지훈 님이에요」 + 원래 소리 | 사람 페이지 두 개 |
| 2:20~2:45 | 왜 Argon인가, 이미 있는 것과 다른 점 (목소리·한 말로 인물 잇기, 확인한 것만 기억, 귀로 확인하는 출처), 계기판 숫자 | 계기판 |
| 2:45~3:00 | (있으면) 「오늘 들려줘」 → 20초 하루 회고. 다음 단계: 안경 실시간, 기기 안 검색, 오픈소스 | 한 마당 또는 로드맵 |

## 17. 데모 흐름과 개발 순서 (Argon과 대화할 때 기준)

### 17-1. 시연 전에 갖춰 둘 상태 (대회 중에 만든다)
- 공개 영화 한 편이 처리돼 작품 위키에 들어가 있다
- 점심 때 동의받은 행사장 기록 2개가 확인을 거쳐 위키에 들어가 있다 (사람 2명)
- 정답표가 들어가 있고 계기판 정확도가 계산돼 있다
- 설명 방식이 하나 골라져 있다 (예: 색 빼고, 행동으로, 한 줄)
- 휴대폰과 노트북에서 같은 배포 주소가 열려 있다

### 17-2. 장면별 흐름

| 장면 | 사용자가 하는 일 | 앱이 하는 일 | 필요한 기능 | 실패하면 |
|---|---|---|---|---|
| 1. 영상 속 순간 묻기 | 「방금 무슨 일이야?」 | 작품 위키와 영상으로 원인을 찾아 한 문장 답, 출처 시점, 소리로 읽기 | P0 작품 위키·물어보기, P1 음성 | 글 답만 보여 주고 발표자가 읽는다 |
| 2. 목소리로 인물 잇기 | 「방금 그 목소리 누구야?」 | 그 인물이 처음 나온 시점과 처음 한 말로 답하고 원래 소리 | P0 물어보기·원래 소리 | 미리 확인해 둔 질문만 쓴다 |
| 3. 안경 모드 기록 | 목에 건 휴대폰으로 심사위원과 30초 대화 | 업로드 → 정리 → 카드 → 기계 검증 → 검토 대기함 | P0 내 기록 → 카드, P1 카메라 기록 | 대회 중 찍어 둔 행사장 기록을 넣는다 |
| 4. 확인하고 저장 | 「정리해 줘」 → 「맞아」 | 카드를 소리로 읽고, 동의 확인 뒤 위키 저장, 바뀐 페이지 표시 | P0 검토·저장, P1 동의 확인·음성 | 노트북 화면에서 카드를 눌러 확인 |
| 5. 기억끼리 잇기와 숫자 | 「아까 배터리 얘기한 분이랑 같은 사람이야?」, 노트북 화면 | 온톨로지로 사람·말을 찾아 비교해 답, 위키·출처·계기판 | P0 물어보기(Argon)·검증 루프 | 질문을 「배터리 얘기한 사람 누구였지?」로 단순하게 |
| 6. 오늘의 한 마당 | 「오늘 들려줘」 | 오늘 본 영상과 확인한 기억으로 20초 하루 회고 | P2 | 로드맵으로 마무리 |

### 17-3. 개발 순서
1. **P0-1 공개 영상 → 작품 위키:** 유튜브 링크를 넣으면 영상을 끝까지 보고 인물(목소리 특징, 처음 한 말)·장면·대사·행동을 시점과 함께 카드로 만들어 작품 위키에 넣는다
2. **P0-2 물어보기와 원래 소리:** 글로 물으면(지금 재생 시점 포함) 위키와 영상을 근거로 한 문장 답과 출처 시점을 준다. 「원래 소리」는 그 시점부터 유튜브 플레이어로 틀어 준다
3. **P0-3 검증 루프와 계기판:** 8절 표대로 판정하고 다시 쓰고, 숫자를 노트북 화면에 보여 준다
4. **첫 배포 확인 (12:15까지 한 번, 이후 기능마다)**
5. **P0-4 내 기록 → 검토 대기함 → 위키:** 영상 파일을 올리면 기억 카드를 만들어 대기함에 넣고, 「맞아」인 카드만 6-1절 온톨로지와 6-2절 위키에 저장하고 바뀐 페이지를 표시한다
6. **P1-1 휴대폰 카메라 기록:** 「기억 켜기」로 카메라를 열어 찍고 바로 올린다
7. **P1-2 소리와 동의:** 카드·답을 소리로 읽기, 새 사람 동의 확인, 추측 카드 표시
8. **P1-3 설명 방식 두 가지**
9. **P1-4 접근성 기본:** 읽히는 이름, 자동 읽기, 제목 구조, 키보드만으로 조작, VoiceOver로 한 번 끝까지
10. **P2:** 오늘의 한 마당 → 심사위원 링크 즉석 처리 → 조각 올리기 → 긴 영상 나눠 처리·합치기 → 온톨로지 보기 화면 → 말로 고치기 (이 순서)

### 17-4. 제출용 데모 영상 (2분 안팎)
1. 0:00 문제 한 문장과 친구 이야기 (자막)
2. 0:15 휴대폰에서 VoiceOver를 켜고 공개 영화 링크 넣기 → 「방금 무슨 일이야?」 → 「방금 그 목소리 누구야?」 → 원래 소리
3. 0:50 「기억 켜기」 → 기록 → 「정리해 줘」 → 카드 읽기 → 「맞아」 → 위키 저장
4. 1:25 계기판 숫자, 왜 Argon인가
5. 1:45 다음 단계: 안경 실시간, 기기 안 검색. 공개 영화 출처 자막

## 18. 다음 단계 (대회 뒤 제품으로 클 길)

- **스마트 안경:** `gemini-3.8-live`로 실시간 정리, 검토 대기함은 그대로
- **기기 안 기억:** EmbeddingGemma 2와 Gemma 4로 휴대폰 안에서 검색과 정리. 개인 기억이 기기 밖으로 나가지 않는다
- **엔터 넓히기:** 드라마 회차를 잇는 작품 위키, 함께 본 영화로 친구와 이야기하기, 친구들이 찍은 영상 모으기
- **비서로:** 자주 가는 장소, 받은 문서, 일정
- **오픈소스:** 온톨로지와 검토 흐름을 공개해 다른 접근성 앱이 쓸 수 있게

