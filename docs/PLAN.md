# Second Ear — Design Plan (PLAN)

Korean original: [PLAN.ko.md](PLAN.ko.md)

> [source] marks what we verified, [assumption] marks what we have not yet verified, and (example) marks sentences to be replaced with real material on the day. All person names are examples. This is an idea and design document prepared before the competition; all code is written during the competition.



## 0. At a Glance

| Item | Content |
|---|---|
| Name (English) | Second Ear. A name that combines "second brain" and "ear": a second ear that remembers what you heard together with what you could not see |
| Track | 3 Public good (accessibility). A second brain that starts from entertainment (watching videos) and grows into an assistant |
| Pitch sentence (Korean) | For blind people who tell people apart only by voice and must ask others what is on screen, a "second brain you can hear" that explains what they could not see in words they already know, from the videos they watch and the moments they live through, and remembers it in a wiki with sources |
| Pitch (short) | Second brains are built for eyes. Second Ear is one you can hear. |
| Pitch sentence (English) | For blind people who recognize others only by voice and must ask someone to learn what just happened, Second Ear turns the videos they watch and the moments they live into a second brain they can hear: it describes what they couldn't see in words tied to their own memories, saves personal memories only after they confirm, and keeps every fact traceable to the original sound. |
| One number | 248,360 registered visually impaired people in Korea, 9.4% of all registered people with disabilities (end of 2023) [source](https://www.koddi.or.kr/webzine/didimdol/vol299/subPage_003.html). Most vision loss is acquired later in life, so the visual experiences each person remembers differ [source](https://www.newnonmun.com/article=10748936) |

## 1. Problem Definition

- **Who:** Blind people who watch videos, hang out with friends, go to gatherings, and otherwise enjoy daily life and culture together with other people
- **What they were trying to do:** Enjoy the story in a video and the moments shared with the people around them the way others do, and recall them later
- **It turned out:** It is not that there is no information at all. (1) They have to fill in blanks like "who said that" and "why did they laugh" by asking a person every time, and asking itself is a burden; and (2) the explanations they hear do not connect to their own memory. A description like "a man in a red hat" is useless to someone who remembers people by voice and conversation
- **Problem statement:** Blind people wanted to enjoy and remember videos and shared moments, but it turned out they were stopped not by a lack of information but by the burden of asking others to fill the blanks every time, and by explanations that do not connect to their own memory (voices, conversations)
- **Evidence:**
  - A survey of 191 blind people: the social cost of asking questions is large [source](https://www.microsoft.com/en-us/research/?p=164168) (Brady et al., CSCW 2013)
  - The reason people do not ask family or friends to describe photos is "not wanting to burden them" [source](https://arxiv.org/pdf/2407.19351) (AccessShare, 2024)
  - The preferred way of receiving descriptions differs from person to person, and differences between groups (congenital, acquired, low vision) are smaller than expected. The recommendation is to ask each person and adapt [source](https://uczelniabadawcza.amu.edu.pl/en/wiadomosci/biblioteka/audio-describing-films-for-the-congenitally-and-non-congenitally-blind) [source](https://www.helenkeller.org/wp-content/uploads/2023/11/HKNC_Considerations-for-Providing-AD-to-DeafBlind-Tip-Sheet.pdf)
  - People who have been blind since birth learn colors through language and understand the reasons behind them. Visual expressions must not be replaced across the board [source](https://pmc.ncbi.nlm.nih.gov/articles/PMC8379969) (Bedny et al., PNAS 2021)
  - Detailed information about people at the time, such as posture and facial expressions, enriches blind people's memory recall [source](https://arxiv.org/html/2501.15408v1) (Memory Reviver, UIST 2024)
  - A scene the builder saw directly: the builder's blind friend asked "What was that?" at every cheer at a baseball stadium. When voices sound alike, they have to ask for a name or check that it is right, but in everyday life that is often hard to do (builder's observation)
- **Assumptions:** Whether the friend actually wants to use such records and a wiki [assumption]. The accuracy of linking people in a video to their voices and what they said [assumption]. The accuracy of Korean speaker identification [assumption]
- **HMW:** How might we let a blind person enjoy videos and shared moments in the way they remember, and find them again, without asking anyone?
- **One real person:** The builder's blind friend
- **From entertainment to assistant:** Watching videos is fun, so they use it every day and records accumulate; the accumulated records become context; with context, descriptions fit the person better, so they use it even more. The same wiki then widens from people in videos to people around me, then to places, documents and schedules, and becomes an assistant
- **How it differs from what already exists:**

| Existing thing | What it does | How Second Ear differs |
|---|---|---|
| YouTube audio-description and question tools (ViDscribe, YouDescribe, etc.) [source](https://a11y-paradise.onrender.com/reviews/69ebd7861a03678cbb26dfea) | Adds descriptions to videos and answers questions | Introduces people by voice and what they said earlier, not by appearance; watched videos pile up as a wiki that connects to the next episode, other videos, and memories from my own life |
| Envision Ally [source](https://letsenvision.com/blog/ally-beta-launch) | Remembers preferences and "about me" to tailor answers | A wiki of people, moments and works, with sources you can check by ear for every sentence |
| VisionBuddy (Gemini competition entry) [source](https://ai.google.dev/competition/projects/visionbuddy) | Saves real-time video analysis and answers questions later | People-centered memory, personal description style, and personal memories saved only after confirmation |
| AI glasses with memory (Brilliant Labs Halo, Ray-Ban Meta, etc.) [source](https://fast.io/resources/best-ai-glasses-2026/) | Finds past conversations, places and visual context (for general users) | Built for blind users: turns what is seen into the person's own memory (names, what they said), confirms before saving, and offers sources you can check by ear |
| Face recognition in Seeing AI and Envision [source](https://aiindigo.com/blog/envision-ai-review-2026-a-practical-look-at-ai-powered-vision) | Tells you a person's name from a saved face | Does not extract or store face or voice features; links people by what they said, how they introduced themselves, and when and where |

## 2. 30-Second Demo Scene

- **First 5 seconds:** "Close your eyes." Play only the sound of one scene from a public short film for 8 seconds. Screams and laughter are heard, but you cannot tell what is happening
- **Middle:** The presenter says, "An ordinary AI would have said 'a child in red fell down'," then asks the phone: "What just happened?" -> Second Ear: (example) "The child whose voice complained 'the forest is boring' on the bus at the start stepped on a mushroom and fell (3:12)." -> "Whose voice was that?" -> (example) "The same child. It is the voice that first appeared at 0:45." -> Pressing "Original sound" plays that moment again
- **End:** The laptop screen shows the work wiki (each character's voice traits and what they said, a list of scenes) and the dashboard numbers

Actual input: a public video with no copyright issue (CC BY), and the builder's voice questions

## 3. User Flow

There are two paths, and both accumulate into the same wiki.

### A. Watching a video (entertainment, the starting point)
1. **Choose a description style:** color (as is / leave out), facial expressions (as actions / as meaning), length (one line / detailed). We do not ask about diagnosis
2. **Add a video:** Paste a public video link (YouTube)
3. **The AI watches the whole video:** It extracts characters (voice traits, first line), scenes, dialogue and visible actions with their timestamps and makes work cards. Cards that pass machine verification go into the work wiki marked "AI-organized" (it is public content, so user confirmation can be optional)
4. **Ask while watching or afterward:** "What just happened?", "Whose voice was that?", "Why did they laugh?" The answer is one sentence read aloud, and people are introduced by voice and what they said earlier
5. **Original sound:** Replays the video from the timestamp attached to the answer

### B. Memories from my life (expanding into a second brain, assuming smart glasses)
In the demo, a phone hung around the neck stands in for glasses.
1. **Record:** Pressing "Start remembering" makes the camera record 30 to 60 seconds
2. **The AI organizes it:** It extracts what was heard and the actions that were visible and makes memory cards. Only cards that pass machine verification pile up in the **review inbox**. They do not enter the wiki yet
3. **Confirm when you want:** Say "Catch me up" and the cards are read aloud one by one. "That's right" saves it, "No" discards it, and "Fix it" corrects it and then saves. For a person seen for the first time, that person's consent is also confirmed. When saving is done, the changed pages are announced
4. **Ask:** "Who was the person who talked about batteries earlier?" People in videos and real people are kept separate in the wiki

### C. (If time allows) Today's Hanmadang
Say "Play today" and a voice looks back on the day from the videos watched and the memories confirmed today, in the style of a pansori aniri. 20 seconds in the demo, a 2 to 3 minute daily recap in the product

## 4. Feature Scope

| Must (within 4 hours) | Nice to have (if time remains) | Not doing (mentioned only as "next step" in the pitch) |
|---|---|---|
| Public video link -> work cards -> work wiki | Today's Hanmadang (20-second daily recap) | Real-time processing on smart glasses |
| Ask -> one-sentence answer that introduces people by voice and what they said + original sound | Process a public link given by a judge on the spot | On-device search (EmbeddingGemma 2) |
| Verification loop + dashboard | Chunked upload of files over 32 MB | Storing face or voice features |
| My recording file -> memory cards -> review inbox -> confirm -> wiki | Split a long video into pieces, process, and merge | Collecting videos shot by friends |
| Live recording with the phone camera | Ontology view screen | Assistant for places, documents and schedules |
| Read cards and answers aloud | Correct by voice | Multiple user accounts, an installable app |
| New-person consent check, two description styles | | |
| Accessibility basics (readable names, automatic reading, heading structure, keyboard) | | |

See section 17 for the detailed build order.

## 5. Screen Information Hierarchy (what comes first, and biggest)

### Dividing the devices
- **Phone = the user's screen.** Listen to the video, ask, record, and confirm. In the demo it hangs around the neck in place of glasses
- **Laptop = the screen shown to judges.** At the same address, it shows the video, the wiki, the review inbox and the dashboard at large size

### Phone home screen
- Biggest: two buttons, "Add video" (paste a link) and "Start remembering", with the "Ask" input field below
- Next: "Catch me up" (number of cards waiting for review), recently watched videos and recent moments (can be swiped by title)
- Left out: graphs, thumbnail-heavy screens, small icon buttons

### Phone video screen
- Biggest: play/pause, and a "What was that?" button (pressing it asks about the current moment)
- Next: the Ask input field, and the list of characters (voice traits and first line)

### Phone review screen
- Biggest: the one card being read now (read aloud as soon as it appears)
- Next: three large buttons "That's right", "No" and "Fix it", plus "Original sound"
- If there is a person seen for the first time, a consent check: "May I remember this person?"

### Phone answer screen
- Biggest: the one-sentence answer (read aloud as soon as it appears, and the screen reader also reads it automatically)
- Next: "Original sound", "That's wrong", "More detail"

### Laptop wiki and dashboard screen
- Biggest: work / person / moment pages (heading structure), with a mark on pages changed this time
- Next: the review inbox (waiting, confirmed and discarded states)
- Dashboard: source check pass rate, quote match rate, human confirmation rate, number of unsourced sentences, number of people saved without consent, number of description-style violations, answer-key accuracy

### Accessibility requirements
- The core flow (add video -> what was that -> original sound; start remembering -> catch me up -> that's right) can be used with a screen reader (VoiceOver, TalkBack) alone. Every button has a readable name
- New cards, new answers and state changes are read automatically
- Large text and high contrast for low-vision users. State is never shown by color alone
- Use only gestures that screen reader users already know (swipe, double tap) and do not invent new gestures
- Speaking a question is first solved with the phone's built-in dictation (a method screen reader users already use)

## 6. Input and Output

| | What | Format / size | Where to get it |
|---|---|---|---|
| Input | One public short film | Blender Studio's "Sprite Fright" (2021, 10 min 29 s). A horror comedy in which five British teenagers meet mushroom spirits in a forest [source](https://studio.blender.org/films/sprite-fright/pages/about). YouTube https://www.youtube.com/watch?v=_cMxraX_5RE (based on the archive.org record; on the day, confirm it is the official Blender Studio channel) [source](https://archive.org/details/sprite-fright-2021). License is CC BY (version 1.0 on the Blender Studio page, 4.0 on archive.org; both require attribution) -> put "Sprite Fright © Blender Studio, CC BY" in the README and the demo video | YouTube |
| Input | A public video link chosen by a judge (if any) | Short public video | During the demo |
| Input | 2 to 3 recordings at the venue (another participant at lunch, a judge during the demo) | 30 to 60 s, phone camera 720p | Recorded on the day with consent |
| Input (optional) | An old video shot with friends | After the competition starts, shrink it on the laptop with the built-in macOS tool (avconvert, 1280x720) | The builder's photo library. Only those where the people shown have given consent |
| Input | Spoken questions, confirmation answers (that's right / no) | Dictated text, buttons | During the demo |
| Input | Answer key | 8 to 10 questions about the public film, with answers | Written by the builder after watching the film. If personal-memory questions are included, kept only in private storage |
| Output | Work cards, memory cards (review inbox) | Source timestamp on every card | — |
| Output | Work / person / moment wiki pages | Source timestamp on every sentence | — |
| Output | One-sentence answer (text + sound), original sound segment | A few seconds | — |
| Output | Dashboard numbers | Screen | — |
| Output (if time allows) | Today's Hanmadang | 20-second audio | — |

**Public videos do not need to be uploaded:** All the "pass a YouTube link" examples in the Gemini API documentation use the Interactions API. It is a preview feature and free; the free tier allows up to 8 hours per day, only public videos work (unlisted and private do not), and for Gemini 2.5 and later models up to 10 videos per request [source](https://ai.google.dev/gemini-api/docs/video-understanding). The same document also has an "agentic" way of examining a video like an agent (to be tested if time allows). If the link fails, the server downloads the CC BY film file from archive.org (MP4, 57.8 MB) and passes it to the Files API (2 GB per file on the free tier). "Original sound" plays the official YouTube player from that timestamp

**Size limit for my recordings:** Cloud Run accepts up to 32 MB per request [source](https://docs.cloud.google.com/run/quotas). Setting the phone camera to 720p and recording 30 to 60 seconds fits within the limit. Large files are split by the browser into pieces smaller than 30 MB and joined by the server (nice to have)

**Process long videos in pieces and merge (nice to have):** The server cuts the video into 1 to 2 minute pieces, flash does a first pass on each piece in parallel, the timestamps are corrected to the original video, and Argon merges them into one. Gemini's "video clipping" feature is not in the Interactions API documentation and has error reports, so we do not rely on it [source](https://discuss.ai.google.dev/t/videometadata-clipping-on-youtube-urls-no-longer-clips-audio-frames-still-clipped-20x-token-inflation-on-long-videos/178970)

### 6-1. Ontology (the skeleton of memory)

| Object | Meaning | Example |
|---|---|---|
| Work | A video that was watched | "Sprite Fright" |
| Person | A character in a video or a person actually met (the two are kept separate) | (example) the child who complained on the bus / a friend |
| Moment | A scene in a video or something done together | (example) the scene of arriving in the forest / a September picnic in the park |
| Place | Where the moment happened | The forest / a park by the Han River |
| Utterance | What someone said | (example) "The forest is boring" |
| Action | A visible action someone did | (example) stepping on a mushroom and falling |
| Source | Which video, at what second | (example) 3:12 |
| Me | The user's description style | No color, one line |

**Relations:** A work has scenes and characters · a person said an utterance · a person did an action · utterances and actions happened at a moment · a moment happened at a place · a person was present at a moment · utterances and actions have a source

**What every fact (utterance, action) has:** who, what, when (source timestamp), where, search keywords, state (AI-organized / waiting / confirmed / discarded), who confirmed, and when it was confirmed. A real person also has a consent flag

### 6-2. Wiki (the ontology as text people can read)
- **Work page:** For each character, voice traits and first line; a list of scenes; the moments when sounds such as laughter or screams occurred, and why
- **Person page:** Name, when and where first met, memorable things they said, a list of moments spent together, consent status
- **Moment page:** When, where and who; what was heard; what was seen (gestures, scene)
- **Me page:** Description style (diagnosis information is not collected)
- Personal memories include **only confirmed facts**; works include only facts that passed machine verification. Every sentence carries a source, and a record is kept of who (AI / user) changed what and when
- Storage is private Cloud Storage. Personal videos, wikis and the answer key never go into the public repository

### 6-3. Making it easy for the AI to find things
- **Now (demo scale):** Argon reads the whole wiki at once. Questions are solved through ontology relations. For example, "Whose voice was that?" finds the speaker of the dialogue near the current timestamp and answers with the first thing that character said. "Who talked about batteries?" finds the utterances containing "battery" and answers with the person who said them
- **As it grows:** Narrow the candidates with an ontology index (people, works, places, dates, keywords), add semantically similar facts with embedding search, then hand them to Argon
- **Next step:** Search inside the phone with EmbeddingGemma 2. It is a model based on Gemma 4, released on 2026-10-06, that puts text, images, sound and video in one space and finds moments in videos on the device [source](https://developers.googleblog.com/embeddinggemma-2-the-developer-guide/). Personal memories never leave the device, which also fits the Track 3 "on-device model" theme

## 7. Model Roles

| Task | Model | Why this model |
|---|---|---|
| Watch the video to the end and make work cards (characters, voices, dialogue, actions, timestamps); connect memory cards to the existing wiki (is it the same person, are there conflicting records); hard questions (tracing back in time to find the cause of laughter, connecting distant scenes); directing verification | `gemini-4-argon` (thinking low to medium) | The whole video and the wiki must sit in one context, or the linking of people breaks |
| First pass on recordings (heard speech, seen actions, timestamps), re-checking evidence (re-watch the segment a card or answer points to and say yes/no), quick answers | `gemini-3.8-flash` | Fast, and many can run at the same time |
| Voice for cards, answers and Hanmadang | `gemini-3.8-flash-tts` | A guide voice that is clearly different from the people in the video |
| (If time allows) Speaker identification and word timestamps | `gemini-3.5-transcribe` | Supports speaker identification and word timestamps. With speaker identification on, there is a 30-minute limit, and three or more speakers is experimental [source](https://ai.google.dev/gemini-api/docs/models/gemini-3.5-transcribe). Korean accuracy to be tested first on the day [assumption] |
| (Optional) Run the organizing in the background | Managed Agents | One API call launches an agent that uses tools (released 2026-05) [source](https://gigazine.net/gsc_news/en/20260520-google-gemini-api-managed-agents). Background execution possible since July [source](https://www.dawan.africa/news/google-upgrades-gemini-api-with-background-execution-and-remote-mcp-integration). After confirming it is allowed at 11:00 |
| (Next step) Real-time organizing on glasses | `gemini-3.8-live` | Real-time voice and camera (video at 1 frame per second) |
| (Next step) On-device search | EmbeddingGemma 2 | Section 6-3 |

Upload my recording videos through the Files API and pass them to the model only after the processing state is finished (ACTIVE). Calling before it is ready causes an error [source](https://discuss.ai.google.dev/t/gemini-2-5-flash-api-cannot-process-video-input/80093).

**Why it has to be Argon (judging criterion 3):**
- **1M unified context:** Put the entire 10-minute film (about 300 tokens per second of video) in front of the model at once and decide "is this voice at 3:00 the child who first appeared at 0:45?" It is needed even more as this grows to many drama episodes, a full day of recordings from glasses, and months of wiki. Splitting into pieces breaks the linking of people
- **Deep reasoning:** Laughter and screams burst out after the cause. It traces back in time to find the cause and finds places where records conflict with each other
- **Multimodal direction:** It directs the first pass, the evidence re-check and the voice model, and merges them into one verified set of cards
- **Long output:** One video produces dozens of character and scene cards and several wiki pages at once

## 8. Verification Loop (judging criterion 1)

A card **must pass machine verification before it goes into the wiki or the review inbox.** Personal memories are then confirmed by the user.

| What is checked | How the machine decides | Pass criterion | If it fails | Number shown on screen |
|---|---|---|---|---|
| Evidence: is the utterance or action really there at the timestamp the card or answer points to | flash re-watches that timestamp and says yes/no | 100% | Rewrite only that sentence. After 3 failures, mark it "uncertain" | Source check pass rate |
| Quote: is "what that person said" in the dialogue list from the first pass | Character-by-character comparison | 100% | Rewrite | Quote match rate |
| Source: does every card and wiki sentence carry a source timestamp | Format check | 0 sentences without a source | Rewrite | Number of unsourced sentences |
| Consent: does every real person in the wiki have a consent flag | List comparison | 0 people saved without consent | Hold the save and ask the user to confirm | Number of people saved without consent |
| Description style: if "no color", 0 color words; if "one line", length limit and 0 emotion-guessing words | Word list, character count | 0 violations | Rewrite | Number of description-style violations |
| Answer key: 8 to 10 hand-written questions about the public film | Compare with answers | 80% or more | Record the cause | Accuracy |
| Human confirmation: share of memory cards the user answered "That's right" | Tally confirmation records | Reference metric | Record the cause for cards that got "No" | Human confirmation rate |

- Maximum number of iterations: 3 (within the global rule limit of 5)
- Re-checking is done by a call (flash) different from the one that made the card or answer
- Answer key: a table of questions and answers the builder wrote after watching the public film (who, what, at which second)

## 9. Where People Confirm (judging test 3)

- **The review inbox is the core confirmation point.** A personal memory organized by the AI does not enter the wiki until the user says "That's right"
- **Blind users cannot directly check what is visible.** So confirmation is split in two. The user confirms what they know (who it is, what they heard, whether to remember it), and what only eyes can confirm (gestures, scenes) is guarded by machine verification and the "uncertain" mark. In the next step, we can send just that moment to someone who was there and have them confirm it
- A new person is saved only after that person's consent ("May I remember this person?")
- A card where the AI guessed a name or that two are the same person is read out as a "guess" ("Shall I remember this voice as this friend?")
- Confirm before sharing or exporting
- Consent and retention: record only conversations the user took part in (recording conversations between other people violates Korea's Communications Secrets Protection Act). Do not extract or store features from faces or voices. Original videos are kept only in private storage for source checking, and the content of discarded cards is deleted. The user can delete people and moments at any time

## 10. Acceptance Criteria (what machines and people check before the demo)

- [ ] Pasting a public film link creates a work wiki, and "What just happened?" and "Whose voice was that?" get answers that introduce people by voice and what they said
- [ ] Every answer has a source timestamp, and pressing "Original sound" plays from that timestamp
- [ ] Adding one live recording creates cards in the review inbox, "That's right" saves them to the wiki, and the changed pages are visible. All of this finishes within 3 minutes
- [ ] The dashboard numbers show actual run values
- [ ] Turn on VoiceOver on the phone and go through the core flow once from start to finish
- [ ] The Cloud Run address opens on both the phone and the laptop
- [ ] The public repository contains no personal videos, wiki or keys, and the source of the public film is in the README
- [ ] Answer-key accuracy of 80% or more

## 11. Technical Choices

- Language and framework: Python 3.12 + uv + FastAPI, a web screen for the phone browser
- Libraries: google-genai 2.3.0 or later (Interactions API), FastAPI, uvicorn, python-multipart for file upload handling, google-cloud-storage. ffmpeg if we split long videos (installed in the Dockerfile). If we use an official public template, credit it in the README Credits
- Original sound: play the official YouTube player from that timestamp. If embedding is blocked for a video, open the YouTube link at that timestamp. For my recordings, play the original in the private bucket from that timestamp
- Storage: a private Cloud Storage bucket (my recording videos, ontology and wiki, answer key). If blocked, keep them in instance memory for the demo and load them again after the final deployment
- Deployment: Google Cloud Run (Seoul), at most 1 instance (to keep state in one place), HTTPS by default (needed for camera and microphone permissions)
- Phone camera: use the browser's built-in file picker that opens the camera directly (we do not build a separate recording feature). The demo phone's camera recording setting is 720p
- Screen language: until we hear the answer at the 11:00 rules briefing, show screen text in both English and Korean. Answers and card voice default to Korean, switchable to English
- Not using: Streamlit, PHP, externally exposed databases, non-Google AI APIs, downloading YouTube videos

## 12. Risks and Responses

| Risk | Response |
|---|---|
| Reading the YouTube link fails (works per the documentation, but it is a preview feature) | Confirm in the first test at 11:40. If it does not work, the server downloads the CC BY film file from archive.org (MP4, 57.8 MB) and passes it to the Files API |
| Film processing is slow | Process the demo film in advance during the competition. For judges' links, use only short videos and explain the dashboard while waiting |
| YouTube embedding is blocked | Open the YouTube link at that timestamp |
| Copyright | Use only CC BY videos and state the source in the README and the demo video. Do not download YouTube videos |
| My recording upload exceeds 32 MB | 720p and 60 seconds or less. If still too large, upload in chunks or send directly from the laptop to the private bucket |
| The wiki disappears on redeployment | Save in the private bucket. If bucket permissions are blocked, load it again after the final deployment (budget 10 minutes) |
| Linking of people is wrong | If not sure, say so. Guess cards for personal memories are labeled "guess" and the user confirms them |
| Korean speaker identification is weak | Link venue recordings only by self-introductions and what was said |
| Card and answer voice (TTS) does not play | Show them as screen text and read them with the laptop's screen reader |
| VoiceOver control gets tangled on stage | Run the live demo with the app's own voice, and include the VoiceOver scene in the demo video |
| Looks like a "plain chatbot" or a "YouTube description tool" | Show together: answers that link people by voice and what they said, the work wiki, the review inbox, the verification numbers, and the scene that leads into memories from my life |

## 13. 4-Hour Schedule

| Time | Task | Done when |
|---|---|---|
| 11:20-11:40 | `/hackathon-setup` -> give Argon the goal description from section 14 and receive its questions and design proposal | Repository, first Argon call |
| 11:40-12:00 | Test first: with the Sprite Fright link, check that people, voice traits, dialogue, actions and timestamps come out, and how long it takes (flash and Argon separately). Also one 30-second Korean clip | Results and times recorded |
| 12:00-12:15 | First deployment to Cloud Run even with a blank screen, connect the private bucket | HTTPS address opens on the phone |
| ~13:00 | P0: public video -> work wiki, Ask -> an answer introducing people by voice and what they said, and original sound | Question, answer and original sound with the public film |
| ~13:30 | P0: verification loop and dashboard | Numbers appear as real values |
| ~14:00 | P0: my recording -> memory cards -> review inbox -> that's right -> wiki | End to end with one venue recording |
| ~14:15 | P1: phone camera recording, reading aloud, consent check, description style, accessibility basics | Scenes 1 to 5 of section 17 run |
| 14:15-14:20 | Final deployment | Opens on phone and laptop |
| 14:20 | Feature freeze, two 3-minute rehearsals | Finishes within 3 minutes |
| ~15:05 | Record the demo video -> personal YouTube (unlisted), GitHub push | Links |
| 15:00 | "Submission check" with Antigravity | All table items pass |
| ~15:20 | Submit the English description | Submission complete |

## 14. Goal Description to Give Argon First (natural language only)

**Korean (translated):** I want to build Second Ear, a "second brain you can hear" web app for blind people, for the phone browser. There are two paths, and both accumulate into the same wiki. First, when the user pastes a public YouTube video link, the app watches the video to the end, makes work cards from the characters (voice traits, first line), scenes, dialogue and visible actions with their timestamps, and puts them into the work wiki. When the user asks "What just happened?" or "Whose voice was that?", it answers in one sentence, reads it aloud, and replays the original video from that moment. Second, assuming smart glasses (in the demo, a phone hung around the neck), when the user records 30 to 60 seconds, it makes memory cards from what was heard and the actions that were visible and piles them in the review inbox; when the user says "Catch me up," it reads them one by one and saves to the wiki only those the user answers "That's right." The wiki is built on an ontology made of works, people, moments, places, utterances, actions and sources. People are introduced by name, or by their voice and what they said earlier, not by appearance, and emotions are not guessed. Cards must pass verification in which a different call re-checks the evidence. A new person is saved only after consent. The core flow must be usable with a screen reader alone. Uploads of my recordings are accepted within the Cloud Run limit (32 MB), and personal material is kept only in a private bucket. The demo flow and build order are in section 17, the ontology in section 6-1, and the verification loop and acceptance criteria in sections 8 and 10. Before writing code, first give me your questions and a design proposal (screen flow, model roles, verification loop, and the scope to cut following the order of section 17).

**English:** I want to build Second Ear, a mobile web app that works as a "second brain you can hear" for blind people. It has two paths that feed one wiki. First, when the user pastes a public YouTube link, the app watches the whole video and turns its characters (voice traits and first lines), scenes, dialogue, and visible actions into timestamped cards stored in a work wiki. When the user asks "What just happened?" or "Whose voice was that?", the app answers in one sentence, reads it aloud, and replays the original video from that moment. Second, assuming smart glasses (a phone hung around the neck in the demo), when the user records 30 to 60 seconds, the app turns what was heard and what was visible into memory cards in a review inbox; when the user says "catch me up," it reads them aloud one by one and saves only what the user confirms. The wiki sits on an ontology of works, people, moments, places, utterances, actions, and sources. People are introduced by name, or by their voice and what they said earlier, never by appearance, and the app never guesses emotions. Cards must pass a verification step in which a separate call re-checks the evidence. A new person is saved only after their consent. The core flow must be usable with a screen reader alone. Personal recordings stay under the Cloud Run request limit (32 MB), and personal data stays in a private bucket only. The demo flow and build order are in section 17, the ontology in section 6-1, and the verification loop and acceptance criteria in sections 8 and 10. Before writing code, please give me your questions and a design proposal: screen flow, model roles, verification loop, and what to cut, following the order in section 17.

## 15. English Description Template

- **Problem:** Blind people recognize others by voice and conversation. When voices sound alike, or when everyone laughs at something visual, they have to ask someone, and research shows that asking every time carries a real social cost. Existing AI descriptions say "a kid in a red jacket", which means nothing to someone who has never seen that jacket.
- **Who it's for:** Blind people who enjoy videos, everyday life, and culture with friends. Our first user is the builder's blind friend, who asked "What happened?" at every cheer during a baseball game.
- **Why Gemini 4 Argon:** Telling whose voice that was requires the whole film, or weeks of memories, in one context; finding why people laughed requires reasoning backward in time; and turning a video into one verified set of cards requires orchestrating analysis, re-checking, and voice models.
- **How it works:** (draft; adjust to what is actually built on the day) Paste a public video link and Gemini 4 Argon watches the whole video, turning every character (voice traits and first lines), scene, line of dialogue, and visible action into timestamped cards that build a work wiki. Ask "What just happened?" or "Whose voice was that?" and Second Ear answers in one sentence, read aloud, introducing people by their voice and what they said earlier, then replays the original moment. The same wiki extends to real life: with a phone hung around the neck standing in for smart glasses, a short recording becomes memory cards in a review inbox, and only the cards the user confirms are saved into an ontology of people, moments, places, utterances, actions, and sources.
- **Verification loop:** (draft; numbers are the actual values on the day) Every card and answer must cite a timestamp, and a separate Gemini call re-watches that moment to confirm it (up to 3 retries, then the claim is marked "uncertain"). Quotes are matched against the extracted dialogue, sentences without a source are rejected, style rules (no color words if the user opts out, no guessed emotions) are checked by word lists, and accuracy is measured against a hand-written answer key. Live numbers on the dashboard: evidence pass rate __%, quote match __%, unsourced sentences 0, people saved without consent 0, answer-key accuracy __%.
- **Human in the loop:** Personal memories never enter the wiki until the user says "that's right." Because a blind user cannot check visual details, those are guarded by machine re-checks and clearly labeled uncertainty. A new person is saved only with that person's consent, and no face or voice prints are ever extracted. Every answer can be checked by ear against the original sound.
- **Demo:** (draft) The demo video shows a phone with VoiceOver on: pasting the Sprite Fright link, asking "What just happened?" and "Whose voice was that?", hearing the original moment, then recording a short conversation, confirming the memory cards, and seeing the wiki and dashboard update. Sprite Fright © Blender Studio, CC BY.

## 16. 3-Minute Pitch Script

| Time | What to say | Screen |
|---|---|---|
| 0:00-0:20 | "Close your eyes." 8 seconds of sound from the public film. The friend's story: at the ballpark, "What was that?" at every cheer, and when voices sound alike, being reluctant to ask "Who is this?" | Title, the one number |
| 0:20-0:55 | "An ordinary AI would have said 'a child in red clothes'." "What just happened?" -> an answer introducing people by voice and what they said -> "Whose voice was that?" -> original sound | Phone answer, laptop work wiki |
| 0:55-1:30 | "The same wiki continues into my life. I hung a phone around my neck instead of glasses." One judge consents -> record a 30-second conversation -> explain the dashboard while waiting | Record -> organize |
| 1:30-2:00 | "Catch me up" -> cards read aloud -> "May I remember this person?" -> "That's right" -> saved to the wiki, changed pages shown | Review inbox -> wiki |
| 2:00-2:20 | "Is this the same person who talked about batteries at lunch?" -> "No, that's the person you met at lunch" + original sound | Two person pages |
| 2:20-2:45 | Why Argon, how it differs from what exists (linking people by voice and what they said, remembering only what is confirmed, sources you can check by ear), dashboard numbers | Dashboard |
| 2:45-3:00 | (If time allows) "Play today" -> 20-second daily recap. Next steps: real-time glasses, on-device search, open source | Hanmadang or roadmap |

## 17. Demo Flow and Build Order (the basis when talking with Argon)

### 17-1. State to have ready before the demo (built during the competition)
- One public film has been processed and is in the work wiki
- Two venue recordings with consent obtained at lunch have been confirmed and are in the wiki (2 people)
- The answer key is in, and the dashboard accuracy has been calculated
- One description style has been chosen (e.g., no color, as actions, one line)
- The same deployed address is open on the phone and the laptop

### 17-2. Flow by scene

| Scene | What the user does | What the app does | Required features | If it fails |
|---|---|---|---|---|
| 1. Ask about a moment in the video | "What just happened?" | Finds the cause from the work wiki and the video, gives a one-sentence answer, the source timestamp, and reads it aloud | P0 work wiki and Ask, P1 voice | Show only the text answer and the presenter reads it |
| 2. Link a person by voice | "Whose voice was that?" | Answers with the timestamp where that character first appeared and what they first said, plus original sound | P0 Ask and original sound | Use only questions checked in advance |
| 3. Glasses-mode recording | A 30-second conversation with a judge using the phone around the neck | Upload -> organize -> cards -> machine verification -> review inbox | P0 my recording -> cards, P1 camera recording | Use the venue recordings shot during the competition |
| 4. Confirm and save | "Catch me up" -> "That's right" | Reads cards aloud, saves to the wiki after the consent check, shows changed pages | P0 review and save, P1 consent check and voice | Tap the cards to confirm on the laptop screen |
| 5. Connecting memories and numbers | "Is this the same person who talked about batteries earlier?", the laptop screen | Finds people and utterances via the ontology, compares them, answers; wiki, sources, dashboard | P0 Ask (Argon) and verification loop | Simplify the question to "Who was the person who talked about batteries?" |
| 6. Today's Hanmadang | "Play today" | A 20-second daily recap from the videos watched and memories confirmed today | P2 | Close with the roadmap |

### 17-3. Build order
1. **P0-1 Public video -> work wiki:** When a YouTube link is added, watch the video to the end, make cards of people (voice traits, first line), scenes, dialogue and actions with timestamps, and put them in the work wiki
2. **P0-2 Ask and original sound:** When asked in text (including the current playback time), give a one-sentence answer and the source timestamp based on the wiki and the video. "Original sound" plays from that timestamp in the YouTube player
3. **P0-3 Verification loop and dashboard:** Judge and rewrite per the table in section 8, and show the numbers on the laptop screen
4. **First deployment check (once by 12:15, then after each feature)**
5. **P0-4 My recording -> review inbox -> wiki:** When a video file is uploaded, make memory cards and put them in the inbox, save only cards answered "That's right" to the ontology in section 6-1 and the wiki in section 6-2, and show the changed pages
6. **P1-1 Phone camera recording:** "Start remembering" opens the camera, records, and uploads right away
7. **P1-2 Voice and consent:** Read cards and answers aloud, new-person consent check, show guess cards
8. **P1-3 Two description styles**
9. **P1-4 Accessibility basics:** readable names, automatic reading, heading structure, keyboard-only operation, go through once with VoiceOver
10. **P2:** Today's Hanmadang -> on-the-spot processing of a judge's link -> chunked upload -> process and merge long videos -> ontology view screen -> correct by voice (in this order)

### 17-4. Demo video for submission (about 2 minutes)
1. 0:00 The problem in one sentence and the friend's story (subtitles)
2. 0:15 Turn on VoiceOver on the phone and add the public film link -> "What just happened?" -> "Whose voice was that?" -> original sound
3. 0:50 "Start remembering" -> record -> "Catch me up" -> read the cards -> "That's right" -> saved to the wiki
4. 1:25 Dashboard numbers, why Argon
5. 1:45 Next steps: real-time glasses, on-device search. Subtitle crediting the public film

## 18. Next Steps (the road to growing into a product after the competition)

- **Smart glasses:** Real-time organizing with `gemini-3.8-live`, the review inbox stays the same
- **On-device memory:** Search and organizing inside the phone with EmbeddingGemma 2 and Gemma 4. Personal memories never leave the device
- **Widening entertainment:** A work wiki that links drama episodes, talking with friends about films watched together, collecting videos shot by friends
- **As an assistant:** Frequently visited places, received documents, schedules
- **Open source:** Publish the ontology and review flow so other accessibility apps can use them
