# Contract iQ — AI-Powered Contract Risk Review

**Contract iQ** is an AI-assisted contract review system that helps identify important risks, unclear terms, and potentially unfavorable clauses in legal agreements.

Instead of asking one AI model to review an entire contract in a single pass, Contract iQ breaks the review into focused areas, allowing different reviewers to examine different aspects of a contract and bring their findings together.

The goal is not to replace lawyers or make legal decisions. It is to make contract review easier to understand, faster to navigate, and more structured.

🔗 **Try application:** https://ask-contract-iq.streamlit.app/  
📂 **GitHub :** https://github.com/tameszn/contract-review-system

---

<img width="1818" height="733" alt="Screenshot 2026-11-23 010146" src="https://github.com/user-attachments/assets/2bd0fd2c-5835-4df0-84f0-df9efa5dda40" />



![](screenshots/home.png)

---

## The Problem

Contracts can be lengthy, difficult to read, and filled with terms that are easy to overlook. Reviewing an agreement manually requires time, attention, and an understanding of how different clauses can affect one another.

Some of the most important risks aren't necessarily hidden in complicated language. They may come from:

- Unbalanced liability and indemnity obligations
- Unclear payment terms or financial commitments
- Restrictive termination conditions
- Ownership of intellectual property
- Missing protections or obligations
- Terms that appear reasonable individually but become problematic when considered together

A simple AI summary may explain what a contract says, but that doesn't necessarily help someone understand what deserves attention, why it matters, or where the concern originates.

That is the gap Contract iQ aims to address.

---

## 💡 What Contract iQ Does

Contract iQ takes an uploaded contract and processes it through a structured review workflow.

The application extracts the document's text, identifies relevant contract information, and evaluates different risk areas using specialized AI reviewers. Their findings are then checked and organized into a consolidated assessment.

### Core capabilities

- **PDF Contract Processing** — Upload a contract and extract its text for analysis.
- **Contract Information Extraction** — Identify important details, parties, dates, and clauses.
- **Multi-Agent Risk Review** — Analyze different contractual risk areas independently.
- **Evidence-Based Findings** — Connect identified risks with supporting contract language and page references.
- **Risk Consolidation** — Bring findings from different reviewers into a more organized assessment.
- **Reliability Controls** — Handle failed reviews, retry unsuccessful steps, and track assessment completion rather than blindly accepting every response.

---

## 🖥️ Application Walkthrough

### 1. Upload a Contract

Users begin by uploading a PDF agreement. The application extracts the document content and prepares it for further processing.

<!-- SCREENSHOT 1: Upload / Home Page -->
![](screenshots/upload.png)<img width="809" height="479" alt="Screenshot 2026-11-23 010718" src="https://github.com/user-attachments/assets/174ef231-5670-4dc4-abd4-da06a3e1cebb" />



### 2. Extract and Prepare Contract Information

The extracted text is processed into manageable sections, while important contract information and clause-level details are collected for the subsequent review.

This step helps reduce unnecessary repetition and gives the review process a more structured foundation.

<!-- SCREENSHOT 2: Contract Extraction / Processed Contract -->
<img width="1762" height="390" alt="Screenshot 2026-11-23 010856" src="https://github.com/user-attachments/assets/67f60f3e-16e0-432b-a0ba-dd9657cf6bcb" />

![](screenshots/extraction.png)

### 3. Specialized Risk Review

Rather than treating contract review as one broad task, Contract iQ uses four specialized reviewers, each working on a defined area of the agreement.

<!-- SCREENSHOT 3: Risk Assessment in Progress / Agent Workflow -->
![](screenshots/assessment.png)

| Reviewer | What it examines |
|---|---|
| Liability Reviewer | Liability limits, indemnification, exposure, and responsibility |
| Financial Reviewer | Payments, penalties, fees, financial obligations, and unfavorable terms |
| Termination & IP Reviewer | Termination rights, exit conditions, and intellectual property ownership |
| Compliance Reviewer | Compliance-related obligations, regulatory concerns, and contractual requirements |

Each reviewer produces its own findings based on the contract evidence it receives.

### 4. Consolidated Risk Assessment

The findings are brought together to provide a more organized view of the agreement, helping users identify which clauses deserve closer attention.

<!-- SCREENSHOT 4: Final Risk Results -->
![](screenshots/results.png)

The intended focus is not simply to generate a long list of warnings, but to make each finding useful by connecting it to the relevant contractual language.

---

## ⚙️ How the System Works

The application follows a staged workflow, where each step has a specific responsibility.

![Contract iQ Pipeline](screenshots/pipeline.png)

### Workflow

1. **Document Upload** — The user submits a PDF contract.
2. **Text Extraction** — The content is extracted page by page.
3. **Contract Processing** — The document is prepared, divided into manageable sections, and relevant contract details are extracted.
4. **Specialized Review** — Four AI reviewers evaluate their respective risk areas.
5. **Evidence Validation** — Findings are checked against available contract evidence to reduce unsupported claims.
6. **Quality Control** — Failed or invalid reviews are handled through retry and validation logic.
7. **Consolidation** — Validated findings are organized into a final assessment.
8. **Persistence** — Contract data, findings, and assessment information are stored for application use.

The separation of these stages makes the system easier to debug, test, and improve without redesigning the entire application whenever a single component changes.

---

## 🧠 Design Decisions That Matter

### Why four specialized reviewers instead of one?

A single model asked to review everything has to switch between multiple responsibilities, often within the same prompt. That can lead to missed details, shallow analysis, or inconsistent results.

Contract iQ divides the work into narrower review areas. Each reviewer has a defined scope, making the process easier to inspect, validate, and improve.

### Why evidence matters more than a confident answer

An AI-generated legal concern is not useful just because it sounds convincing.

A finding should be supported by language from the actual agreement. Contract iQ therefore places importance on validating the relationship between the reported concern and its supporting text.

The guiding idea is simple:

> A risk without evidence is just an opinion generated by a model.

### Why not send the entire contract to every reviewer?

Repeatedly sending an entire document to every reviewer increases processing cost, wastes context, and may introduce irrelevant information into the analysis.

A more structured approach to extraction and clause preparation allows the review process to become more efficient and focused. This is also an area I am continuing to optimize as the project evolves.

### Why reliability is part of the design

AI applications don't always return usable responses. They can fail due to rate limits, invalid structured outputs, incomplete responses, or temporary provider issues.

Rather than treating a successful API call as a successful assessment, Contract iQ considers the quality and validity of the returned result, with retry handling and assessment status tracking.

---

## 🛠️ Challenges & Engineering Lessons

This project became much more interesting once the goal moved beyond simply getting an AI response.

### 1. Making AI findings traceable

One of the biggest challenges was making risk findings meaningful instead of generic legal advice.

The system needs to identify an issue, understand why it matters, and connect that issue to the actual clause. This creates an important distinction between a plausible-sounding AI answer and a finding that can genuinely be reviewed by a user.

**Takeaway:** The quality of an AI system depends heavily on what it can justify, not just what it can generate.

### 2. Managing multiple reviewers without losing consistency

Each reviewer has a different scope and may return findings in different formats, with different levels of detail and even conflicting interpretations.

Bringing these results together requires consistent output structures, validation, and a clear separation between individual analysis and final consolidation.

**Takeaway:** Multi-agent systems are not automatically better because they have more agents. Their value comes from well-defined responsibilities and reliable coordination.

### 3. Handling model failures and rate limits

Running multiple AI reviews introduces a practical problem: a single assessment can involve several model calls, and those calls can fail independently.

This makes retry logic, controlled execution, model selection, and failure tracking important. A partially completed assessment should not silently appear to be a complete one.

**Takeaway:** Reliability must be designed into AI workflows instead of being added after the application starts breaking.

### 4. Balancing cost, speed, and output quality

More model calls do not necessarily produce better results. Large models may be more capable, but using them for every stage can increase latency, consume limited API capacity, and make repeated testing expensive.

The project explores using different models for different workloads rather than treating every task as equally demanding.

**Takeaway:** Model selection is an engineering decision. The best model for extracting structured information may not be the best model for detailed risk reasoning.

### 5. Designing for failure instead of assuming success

A review pipeline has several dependent stages. If extraction fails, downstream agents cannot produce meaningful results. If one reviewer fails, the system must decide whether to retry, continue with partial coverage, or stop.

This requires tracking not only the final output but also the state of the process itself.

**Takeaway:** A good AI application should know what it successfully completed, what it couldn't complete, and what the user should not trust.

---

## 🧰 Tech Stack

| Technology | Use |
|---|---|
| Python | Core application and processing logic |
| Streamlit | User interface |
| LangChain | Model interaction and structured outputs |
| LangGraph | Workflow orchestration |
| Groq | AI model inference |
| Supabase | Persistent storage |
| ChromaDB | Vector storage and retrieval |
| PyMuPDF | PDF text extraction |
| Pydantic | Structured data and validation |

---

## 📈 Key Takeaways

Building Contract iQ helped me understand that developing an AI application involves much more than connecting a model to an interface.

The more meaningful engineering work often happens around the model:

- Designing the workflow before adding more intelligence.
- Making model outputs predictable enough to work with.
- Validating generated findings against real data.
- Handling failures without corrupting the final result.
- Reducing unnecessary model calls.
- Maintaining a clear boundary between extracted facts and AI interpretations.
- Thinking about how users would verify a result instead of blindly trusting it.

The project also changed how I approach multi-agent systems. I now see them less as a way of adding more AI and more as a way of dividing complex work into smaller responsibilities that can be evaluated independently.

---

## 🚀 Future Scope

Contract iQ is an evolving project. The following improvements are planned to make it more practical, reliable, and useful.

### Smarter Contract Context

- Retrieve only relevant clauses for each reviewer instead of repeatedly passing large amounts of contract text.
- Include related clauses when an issue depends on multiple sections of the agreement.
- Improve handling of cross-references, definitions, and clauses whose meaning depends on surrounding context.

### Better Risk Prioritization

- Improve risk ranking based on potential impact, likelihood, and contractual exposure.
- Distinguish critical risks from routine observations.
- Detect overlapping findings across different reviewers.
- Identify conflicts between clauses instead of reviewing every clause in isolation.

### Review Transparency

- Make it easier to trace every finding back to its exact source clause and page.
- Provide clearer explanations of why a finding was flagged.
- Distinguish direct contractual evidence from model interpretation and suggested actions.

### Improved Reliability and Performance

- Reduce repeated model calls and unnecessary context.
- Improve handling of rate limits and model failures.
- Track reviewer success,
