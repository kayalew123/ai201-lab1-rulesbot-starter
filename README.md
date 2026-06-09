# UMD Dining Unofficial Guide — RAG System

A Retrieval-Augmented Generation (RAG) system that makes unofficial student knowledge about UMD dining halls searchable and answerable. Ask plain-language questions about food quality, vegan/vegetarian options, allergens, crowding, and food safety — get grounded, cited answers drawn from real documents.

---

## Domain and Document Sources

UMD dining halls (251 North, South Campus, and Yahentamitsi) are a daily necessity for thousands of resident students, yet the official Dining Services website only publishes menus, hours, and nutritional labels. It says nothing about whether vegetarian labels can be trusted, which hall is dangerously crowded at noon, or what to do if you have a serious food allergy. That knowledge lives in Reddit threads, student newspaper columns, and word of mouth — scattered and invisible to incoming students who need it most.

**Sources (10 documents):**

| File | Source |
|------|--------|
| `reddit_best_dining_hall.txt` | r/UMD thread on best dining hall overall |
| `reddit_vegan_food.txt` | r/collegeparkmd thread on vegan options |
| `reddit_dining_crowded.txt` | r/UMD thread on crowding at dining halls |
| `reddit_south_unsafe.txt` | r/UMD thread on food safety concerns at South Campus |
| `reddit_dining_questions.txt` | r/UMD general dining questions thread |
| `dbk_vegetarian_yahentamitsi.txt` | Diamondback — vegetarian mislabeling at Yahentamitsi (2022) |
| `dbk_dining_hours_crowding.txt` | Diamondback — inconsistent hours and overcrowding (2024) |
| `dbk_food_safety_violations.txt` | Diamondback — salmonella and health violations (2019) |
| `umd_dining_allergy_page.txt` | UMD Dining Services — allergy/special diets policy |
| `umd_dining_faqs.txt` | UMD Dining Services — FAQ page |

---

## Chunking Strategy

**Chunk size: 400 characters. Overlap: 80 characters.**

The corpus is mixed: Reddit comments are 1–5 sentences of opinion; Diamondback articles are multi-paragraph journalism with quotes; official UMD pages are structured policy text. At 400 characters, a single Reddit comment fits in one chunk with context intact. For longer articles, 400 characters captures roughly 2–3 sentences — enough to hold a complete thought (e.g., a student quote plus the surrounding sentence that names the dining hall).

Smaller chunks (200 chars) would strip context — a quote like "There was chicken in it" is meaningless without the surrounding sentence naming the dining hall and dietary restriction. Larger chunks (600+ chars) merge distinct claims from Diamondback articles, diluting the semantic signal.

80-character overlap preserves context across quote boundaries in journalism, where attribution often comes after the quote.

**Result: 80 chunks across 10 documents.**

---

## Sample Chunks

**Chunk 1** (source: `dbk_vegetarian_yahentamitsi.txt`):
> Morford and Morgan Carnell expressed their overall disappointment with the vegetarian options available in Yahentamitsi, specifically its lack of variety. "It's mainly just carbs. There's not very much fake meat at all being used," Morford said. "It could be a lot better."

**Chunk 2** (source: `umd_dining_faqs.txt`):
> Q: How does UMD accommodate food allergies? A: UMD Dining has a Purple Zone at 251 North and South Campus Dining Hall that is free from the eight most common allergens. Each hall also has a Purple Freezer with pre-packaged allergen-labeled items. Students with allergies should fill out the allergy/intolerance form and meet with the nutrition team.

**Chunk 3** (source: `reddit_dining_questions.txt`):
> South campus gets busy around lunch time but they also have variety. 251 only gets busy after 9 as it's the only one open and while they don't have a large variety there's always at least salads and burgers plus they have actual ice cream and not soft serve. Most are open 7/8am to 9 though 251 is opened until 10.

**Chunk 4** (source: `reddit_best_dining_hall.txt`):
> sin-omelet: People are sleeping on South in these replies. South has specials/rotates more often than the Y in my experience (ex. Ramen night, pasta to order night, etc.) and has good rotations. They also have focaccia sometimes which is really good and I like the dessert selection more too. The south stir fry clears the Y stir fry imo mostly bc you don't have to wait in line.

**Chunk 5** (source: `umd_dining_allergy_page.txt`):
> Purple Zones are open for breakfast, lunch, and dinner, serving many of the same menu items found at other stations — allergen free. Purple Zone menus change every meal and repeat after four weeks. Trained chefs wear purple chef coats and trained servers wear purple aprons.

---

## Embedding Model

**Model:** `all-MiniLM-L6-v2` via sentence-transformers. Runs locally — no API key, no rate limits, no cost.

**Production tradeoffs:** For a real deployment I'd evaluate OpenAI's `text-embedding-3-small` (higher accuracy, low cost per token) vs. a locally-hosted model (zero cost, privacy-preserving for student data). I'd also consider context length: `all-MiniLM-L6-v2` has a 256-token limit, fine for 400-character chunks but would need upgrading if chunk sizes grew. For multilingual support (relevant at UMD given its international student population), `paraphrase-multilingual-MiniLM-L12-v2` would be worth testing.

---

## Retrieval Test Results

**Query 1: "vegetarian food mislabeled at Yahentamitsi"**

Top chunks returned:
- `dbk_vegetarian_yahentamitsi.txt` (distance: 0.2384) — student quotes about mislabeled pasta dishes containing chicken
- `umd_dining_faqs.txt` (distance: 0.3697) — FAQ on vegetarian/vegan availability
- `dbk_vegetarian_yahentamitsi.txt` (distance: 0.3728) — article intro paragraph

Why relevant: The top result directly contains student accounts of mislabeling incidents at Yahentamitsi, which is exactly what the query asks about. Distance of 0.23 indicates a strong semantic match.

**Query 2: "which dining hall is most crowded during lunch"**

Top chunks returned:
- `dbk_dining_hours_crowding.txt` (distance: 0.3619) — student observation about peak hour seating
- `dbk_dining_hours_crowding.txt` (distance: 0.3693) — extended hours argument
- `reddit_dining_crowded.txt` (distance: 0.3825) — Reddit thread on crowding

Why relevant: Both the Diamondback article and the Reddit thread directly address crowding at peak hours. Multiple sources converge on the same topic.

**Query 3: "food allergy options Purple Zone"**

Top chunks returned:
- `umd_dining_allergy_page.txt` (distance: 0.2065) — special diets support info
- `umd_dining_allergy_page.txt` (distance: 0.2799) — Purple Zone hours and allergen-free description
- `umd_dining_faqs.txt` (distance: 0.3054) — FAQ on allergy accommodations

Why relevant: The official allergy page is the authoritative source on the Purple Zone. Distance scores under 0.30 indicate very strong matches for this query.

---

## Grounded Generation

The system prompt explicitly instructs the LLM to answer **only** from retrieved context:

> "Answer the user's question using ONLY the information provided in the documents below. Do NOT use any outside knowledge or general information not present in the provided documents. Always cite which source(s) your answer comes from."

If documents don't contain enough information, the system is instructed to say: "I don't have enough information in my documents to answer that question." This was observed in practice when asking about peak-hour crowding — the system declined rather than hallucinating.

Source attribution is programmatically guaranteed: retrieved source filenames are extracted from ChromaDB metadata and displayed in the "Retrieved From" panel regardless of what the LLM generates.

---

## Example Responses

**Query:** Have students reported vegetarian food being mislabeled at UMD dining halls?

**Answer:** According to [Source 1: dbk_vegetarian_yahentamitsi.txt] and [Source 4: dbk_vegetarian_yahentamitsi.txt], yes, students have reported vegetarian food being mislabeled at UMD dining halls, specifically at Yahentamitsi dining hall. A student, Carnell, is quoted as saying, "I am a little skeptical about the labels of whether or not the foods have meat in them or not," indicating concerns about the accuracy of food labeling. Additionally, [Source 1: dbk_vegetarian_yahentamitsi.txt] states that Yahentamitsi dining hall has presented challenges to vegetarian students with "mislabeled food and scarce options."

**Retrieved from:** dbk_vegetarian_yahentamitsi.txt, umd_dining_faqs.txt, dbk_food_safety_violations.txt

---

**Query:** What allergen-free options does UMD dining offer for students with food allergies?

**Answer:** According to [Source 1: umd_dining_faqs.txt], UMD Dining offers a Purple Zone at 251 North and South Campus Dining Hall that is free from the eight most common allergens. Additionally, each hall has a Purple Freezer with pre-packaged allergen-labeled items. This information is also supported by [Source 3: umd_dining_allergy_page.txt] and [Source 4: umd_dining_allergy_page.txt], which mention the support for allergies and food intolerance, and the importance of asking the manager or chef on duty for specific allergen questions.

**Retrieved from:** umd_dining_faqs.txt, umd_dining_allergy_page.txt

---

**Out-of-scope query:** What time does the Yahentamitsi Starbucks close?

**Answer:** I don't have enough information in my documents to answer that question.

---

## Query Interface

The interface is a Gradio web app running at `http://localhost:7860`.

**Input:** A text box labeled "Your Question" with example questions pre-loaded at the bottom.

**Output:** Two panels — "Answer" (the grounded LLM response with inline source citations) and "Retrieved From" (a bulleted list of source filenames).

**Sample interaction:**

> **Input:** Have students reported vegetarian food being mislabeled at UMD dining halls?
>
> **Answer:** According to [Source 1: dbk_vegetarian_yahentamitsi.txt], yes, students have reported vegetarian food being mislabeled at UMD dining halls, specifically at Yahentamitsi dining hall...
>
> **Retrieved From:**
> • dbk_vegetarian_yahentamitsi.txt
> • umd_dining_faqs.txt
> • dbk_food_safety_violations.txt

---

## Evaluation Report

|---|----------|----------------|-----------------|----------|
| 1 | Have students reported vegetarian food being mislabeled at UMD dining halls? | Yes — specifically at Yahentamitsi, pasta dishes labeled vegetarian contained chicken. Dining Services acknowledged the issue. | Correctly cited mislabeling incidents at Yahentamitsi with student quotes and source attribution. |  Accurate |
| 2 | What allergen-free options does UMD dining offer for students with food allergies? | Purple Zone at 251 North and South Campus (certified free from 8 allergens). Purple Freezer at each hall. Ask manager not servers. | Correctly described Purple Zone, Purple Freezer, and advised asking manager on duty. | Accurate |
| 3 | Which UMD dining hall gets the most crowded during peak hours? | All three halls get overcrowded at lunch; 251 North closes early on weekends pushing students to other halls. | Returned "I don't have enough information" — retrieval pulled crowding chunks but LLM couldn't synthesize a specific answer. | Inaccurate |
| 4 | Have there been any food safety or health incidents at UMD dining? | Yes — salmonella linked to on-campus eatery (2019), moldy bread and worm-infested fruit posted on r/UMD. | Correctly cited salmonella incident and Reddit food safety posts with source attribution. | ✅ Accurate |
| 5 | What do students say about vegan food options at UMD dining halls? | Mixed — official dining offers vegan options but Reddit threads reflect frustration with limited variety and inconsistent labeling. | Correctly synthesized official vegan options with student Reddit concerns about variety and mislabeling. |  Accurate |

**Failure case analysis — Question 3:**

The system returned "I don't have enough information" despite relevant chunks being retrieved (distance scores 0.36–0.39). The failure occurred at the generation stage, not retrieval. The retrieved chunks discussed crowding in general terms (seating shortage, peak hours) but no single chunk made a direct comparison stating which specific hall is *most* crowded. The LLM correctly declined rather than fabricating a ranking not supported by the documents. This is appropriate behavior but represents a gap in document coverage — adding more Reddit content specifically comparing crowding across halls would fix this.

---

## Spec Reflection

**How the spec helped:** Writing the chunking strategy section before touching any code forced a concrete decision (400 chars, 80 overlap) that I could defend. When `embed.py` had issues, I could trace back to exactly what the spec said retrieval should look like and verify against it.

**How implementation diverged:** The spec suggested a single uniform chunking strategy, but in practice the Reddit documents produced very few chunks (some files only 3–4 chunks) due to their short length. In a future version I would use smaller chunks (200 chars) for Reddit files and larger (500 chars) for Diamondback articles — a per-source-type strategy rather than uniform.

---

## AI Usage

**1. Pipeline code generation: I used Claude to help scaffold parts of the pipeline code based on my planning.md spec. I reviewed the generated code, caught a broken import (langchain.text_splitter → langchain_text_splitters), and made adjustments to fit my specific document structure and grounding requirements.

**2. Document collection and formatting:** I used Claude to fetch and clean the Diamondback articles and UMD Dining Services pages, which saved significant time over manual copy-paste. Claude stripped navigation text and formatted the content into clean `.txt` files. I manually collected and formatted all five Reddit threads by copying comments from the browser, which Claude then helped format consistently with source headers.