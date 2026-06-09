# planning.md — The Unofficial Guide: UMD Dining

## Domain

UMD dining halls (251 North, South Campus Dining, and Yahentamitsi) are a daily necessity
for thousands of resident students, yet the official Dining Services website only publishes
menus, hours, and nutritional labels. It says nothing about which halls are dangerously
crowded at noon, whether vegetarian labels can be trusted, or what to do if you have a
serious food allergy. That knowledge lives in Reddit threads, student newspaper columns,
and word of mouth — scattered, hard to search, and invisible to incoming students who need
it most. This system makes that unofficial knowledge queryable in plain language.

## Documents

Ten source documents across four types:

**Reddit threads (copied manually to .txt):**
- `reddit_best_dining_hall.txt` — r/UMD thread on which dining hall is best overall
- `reddit_vegan_food.txt` — r/collegeparkmd thread on vegan options at UMD
- `reddit_dining_crowded.txt` — r/UMD thread on crowding at dining halls and gym
- `reddit_south_unsafe.txt` — r/UMD thread raising food safety concerns at South Campus
- `reddit_dining_questions.txt` — r/UMD general dining questions thread

**The Diamondback (UMD student newspaper):**
- `dbk_vegetarian_yahentamitsi.txt` — reporting on vegetarian mislabeling incidents (2022)
- `dbk_dining_hours_crowding.txt` — opinion column on inconsistent hours and overcrowding (2024)
- `dbk_food_safety_violations.txt` — opinion column on salmonella and health violations (2019)

**UMD Dining Services official pages:**
- `umd_dining_allergy_page.txt` — official allergy/special diets policy and Purple Zone info
- `umd_dining_faqs.txt` — official FAQ page covering dining plans, hours, and policies

Together these sources cover: food quality opinions, vegetarian/vegan options, allergy
accommodations, food safety incidents, peak-hour crowding, and hours consistency — the
five core topics a student actually needs answered.

## Chunking Strategy

My corpus is mixed: Reddit comments are 1–5 sentences of opinion; Diamondback articles
are multi-paragraph journalism with quotes; official UMD pages are structured policy text.

**Strategy: uniform chunk size of 400 characters with 80-character overlap.**

Why 400 characters: Reddit comments are the shortest documents. At 400 characters, a
single comment fits in one chunk with context intact. For longer articles, 400 characters
captures roughly 2–3 sentences — enough to hold a complete thought (e.g., a student quote
plus the surrounding sentence that names the dining hall).

Why not smaller (e.g., 200 chars): A single sentence like "It said vegetarian, so then I
got it. There was chicken in it." carries meaning only with the surrounding context that
names the dining hall and the speaker's dietary restriction. At 200 characters that context
gets cut off, making the chunk unretriveable for specific queries.

Why not larger (e.g., 600+ chars): The Diamondback articles mix multiple topics per
paragraph (e.g., one paragraph discusses mislabeling AND variety AND Dining Services'
response). Larger chunks merge distinct claims, diluting the semantic signal so the
embedding can't distinguish "mislabeling concern" from "lack of variety."

Why 80-character overlap: Quotes in journalism often start mid-sentence with attribution
at the end ("It was a pasta dish...Morford said."). Overlap ensures neither half of a
split quote becomes a stranded fragment.

## Architecture
Raw .txt files (documents/)
│
▼
[Ingestion + Cleaning]
Python / re
strip blank lines, boilerplate, short fragments
│
▼
[Chunking]
LangChain RecursiveCharacterTextSplitter
chunk_size=400, chunk_overlap=80
│
▼
[Embedding]
sentence-transformers
all-MiniLM-L6-v2 (local, no API key)
│
▼
[Vector Store]
ChromaDB (local)
metadata: source filename, chunk index
│
▼
[Retrieval]
Semantic similarity search, top-k=5
│
▼
[Generation]
Groq API — llama-3.3-70b-versatile
grounded prompt: answer from context only + cite source
│
▼
[Interface]
Gradio web UI
Input: query textbox
Output: answer + retrieved sources

## Retrieval Approach

**Embedding model:** `all-MiniLM-L6-v2` via sentence-transformers. Runs locally — no API
key, no rate limits, no cost. Well-suited for short opinion-style text.

**Top-k:** 5 chunks per query. For dining questions, multiple students' opinions are more
useful than one — k=5 gives the LLM enough variety to synthesize a real answer without
flooding it with loosely related content.

**Production tradeoffs I'd consider:** For a real deployment, I'd evaluate OpenAI's
`text-embedding-3-small` (higher accuracy, very low cost per token) vs. a locally-hosted
model (zero cost, privacy-preserving for student data). I'd also consider context length:
`all-MiniLM-L6-v2` has a 256-token limit, which is fine for 400-character chunks but
would need upgrading if chunk sizes grew. For multilingual support (relevant at UMD given
its international student population), a model like `paraphrase-multilingual-MiniLM-L12-v2`
would be worth testing.

## Evaluation Plan

Five test questions with specific, verifiable expected answers:

1. **Q:** Have students reported vegetarian food being mislabeled at UMD dining halls?  
   **Expected:** Yes — specifically at Yahentamitsi, where multiple students reported
   pasta dishes labeled vegetarian that contained chicken. Dining Services acknowledged
   the issue.

2. **Q:** What allergen-free options does UMD dining offer for students with food allergies?  
   **Expected:** The Purple Zone at 251 North and South Campus is certified free from 8
   common allergens. Each hall also has a Purple Freezer with packaged allergen-labeled
   items. Students are advised to ask the manager or chef on duty, not front-line servers.

3. **Q:** Which UMD dining hall gets the most crowded during peak hours?  
   **Expected:** Based on student reports, all three halls get overcrowded at lunch — a
   2024 Diamondback column specifically called out 251 North closing early on weekends,
   pushing students to the other halls and worsening crowding.

4. **Q:** Have there been any food safety or health incidents at UMD dining?  
   **Expected:** Yes — a 2019 Diamondback column documented salmonella linked to an
   on-campus eatery, and students posted photos of moldy bread and worm-infested fruit
   from dining halls on r/UMD.

5. **Q:** What do students say about vegan food options at UMD dining halls?  
   **Expected:** Mixed — official dining offers vegan options and a Good Food station at
   Yahentamitsi, but Reddit threads reflect student frustration with limited variety and
   inconsistent labeling.

## Anticipated Challenges

**Challenge 1 — Reddit content sparsity:** Reddit threads may have 5–15 substantive
comments but also many low-value replies ("same lol", upvote chains). After cleaning,
some Reddit files may yield very few usable chunks, making retrieval for Reddit-specific
queries weak. Mitigation: keep chunks that have at least 50 characters of content; flag
in evaluation if retrieval fails on Reddit-dependent questions.

**Challenge 2 — Temporal mismatch:** The food safety Diamondback article is from 2019
and the vegetarian article from 2022. The system has no way to signal to users that some
retrieved information is outdated. The LLM may present old incidents as current. This is
a known limitation I'll document in the README and flag in the evaluation report.

## AI Tool Plan

I will use Claude as my primary AI coding assistant for the following pipeline components:

**1. Ingestion + Cleaning script (`ingest.py`)**  
Input to Claude: this planning.md (Documents section + Chunking Strategy section), plus
the requirement that I need to load .txt files, strip blank lines and boilerplate, and
return clean strings with source metadata attached.  
Expected output: a `load_documents()` function that returns a list of dicts with `text`
and `source` keys.

**2. Chunking implementation (`ingest.py`)**  
Input to Claude: Chunking Strategy section of this doc, specifying
RecursiveCharacterTextSplitter with chunk_size=400, chunk_overlap=80.  
Expected output: a `chunk_documents()` function. I will verify output by printing 5
chunks and checking they are self-contained.

**3. Embedding + ChromaDB storage (`embed.py`)**  
Input to Claude: Architecture diagram + Retrieval Approach section.  
Expected output: script that embeds all chunks with all-MiniLM-L6-v2 and stores them in
a local ChromaDB collection with source metadata. I will verify by querying the
collection and checking distance scores.

**4. Retrieval + generation pipeline (`query.py`)**  
Input to Claude: Architecture diagram, grounding requirement (answer from context only,
cite source), Groq model name, and the desired output format (answer string + list of
source filenames).  
Expected output: an `ask(question)` function returning `{"answer": str, "sources": list}`.
I will test with 3 evaluation questions before wiring to the UI.

**5. Gradio interface (`app.py`)**  
Input to Claude: the Gradio skeleton from the project spec plus my `ask()` function
signature.  
Expected output: working `app.py` with query textbox, answer output, and sources output.
I will verify end-to-end before recording my demo video.