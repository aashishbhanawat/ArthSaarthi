# Functional Requirement: FR8.2.2 - Concall Transcript & Whisper Audio Analysis (Edge ML)

**Status:** In Progress  
**Parent Requirement:** [FR8.2: Market News Feed](requirements.md#fr8-market-insights--research)  
**Issue Reference:** [#618](https://github.com/aashishbhanawat/ArthSaarthi/issues/618)

---

## 1. Overview & Problem Statement

Earnings conference calls (concalls) represent one of the most information-dense disclosures made by listed companies every quarter. However, an investor typically lacks the time to listen to 45–60 minutes of audio podcasts per company.

While generative Large Language Models (LLMs) are deferred to v2.0.0, investors require actionable fundamental insights today:
1. **Management Guidance & Capex:** Explicit revenue, margin, and plant capacity targets.
2. **Tone & Confidence Analysis:** Objective measurement of management optimism versus analyst skepticism.
3. **Core Discussion Sentences:** Top takeaways verbatim from the call without listening to the entire recording.
4. **Multi-Source Availability:** Handling cases where official transcripts exist (e.g., text/PDF) as well as fallback cases where only podcast audio (`.m4a` / `.mp3`) is published.

---

## 2. Functional Requirements

### FR8.2.2.1: Multi-Tiered Transcript Extraction Flow
* **Tier 1 (Direct Transcript):** If a transcript URL or text is provided (or extracted from Trendlyne `<description>` link), ingest and analyze the text directly in milliseconds with zero audio download.
* **Tier 2 (Whisper Audio Fallback):** If no text transcript is available, but an audio URL (`.m4a` / `.mp3`) exists and the **Whisper** edge model is downloaded and enabled, transcribe speech to text locally using an INT8 quantized Whisper model.
* **Tier 3 (User Paste / Upload):** Provide a fallback UI allowing the user to paste transcript excerpts or links for instant analysis.

### FR8.2.2.2: Whisper Edge Audio Model in Model Catalog
* Register `whisper_tiny_int8` (~39 MB) in the Edge ML Catalog (`ModelManager`).
* Administrators can download, monitor progress, and delete the Whisper model under **Admin > System Maintenance > AI Model Management** (reusing FR10.7 infrastructure).
* Support an environment/config toggle: `ENABLE_WHISPER_TRANSCRIPTION` (default `True` if model is active).

### FR8.2.2.3: Pure Non-LLM Extractive Intelligence Pipeline
* **Section Segmentation:** Automatically divide transcripts into *Management Discussion* and *Analyst Q&A*.
* **FinBERT-Tone Sentiment Profiling:** Run the edge `finbert_int8` ONNX engine (fine-tuned on corporate earnings calls - HKUST FinBERT-Tone) to compute:
  - *Management Confidence Score* (% Positive, % Neutral, % Negative).
  - *Analyst Q&A Sentiment* (Assessing analyst skepticism vs. management clarity).
  - *Continuous Polarity Score* ($P(\text{Positive}) - P(\text{Negative})$ in $[-1.0, +1.0]$).
* **4-Aspect Financial Sentiment Scorecard:**
  - Categorizes sentences into 4 core financial buckets using TF-IDF cosine similarity against anchor phrase vectors:
    1. Demand & Revenue
    2. Margins & Input Costs
    3. Guidance & Targets
    4. CapEx & Balance Sheet
  - Computes an independent tone score for each aspect.
* **Tone Divergence Gap Alert:**
  - Automatically measures the gap between Opening Remarks and Analyst Q&A ($\text{Tone Gap} = \text{Prepared} - \text{Q&A}$).
  - Alerts the user when management tone turns defensive under analyst questioning ($\text{Tone Gap} > +0.20$).
* **Loughran-McDonald Hedging & Uncertainty Index:**
  - Calculates `hedge_rate_per_100w` (frequency of uncertainty words like *headwinds, volatility, pressure, slowdown* per 100 words).
* **Extractive Red Flags:**
  - Extracts the top 2-3 most cautious or negative verbatim management statements from the call.
* **Guidance & Capex Pattern Mining:** Deterministic financial regex engine extracting:
  - Capex figures (`₹... Cr / Crore`, expansion projects).
  - Margin outlook (`...% EBITDA`, `bps` expansion/contraction).
  - Revenue & Volume growth guidance (`...% YoY/CAGR`).
  - Debt & Deleveraging targets.
* **Extractive Summarization (TextRank / TF-IDF Centrality):**
  - Graph-based sentence centrality ranking selecting the top 5 most salient verbatim sentences.
  - Zero hallucination risk: all sentences are quoted verbatim from management.
* **Key Theme Extraction:** N-gram TF-IDF keyword extraction filtering corporate pleasantries, executive speaker names, and corporate suffixes to rank dominant operational topics.

### FR8.2.2.4: Storage & Caching
* Persist the structured analysis in `MarketNewsArticle.metadata_json["concall_analysis"]`.
* Once analyzed, subsequent views load instantaneously from the database without re-running inference.

### FR8.2.2.5: User Interface (Research Feed)
* Add an **"Analyze Concall"** / **"View Analysis"** action to each concall card in the Research Feed.
* Open a responsive modal with:
  - **Tone Gauge & Sentiment Breakdown** (Management Tone vs. Q&A Tone).
  - **Tone Divergence Banner** (Highlighting Q&A defensive shifts).
  - **Aspect Sentiment Scorecard** (Demand, Margins, Guidance, CapEx).
  - **Loughran-McDonald Hedging Density Badge**.
  - **Cautionary Red Flags Card**.
  - **Key Guidance & Capex Badges**.
  - **Top Extracted Sentences / Key Takeaways**.
  - **Discussion Topic Tags**.
