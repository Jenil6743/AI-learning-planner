#  AI Personal Learning Planner

An intelligent, personalized learning path generator that creates structured 30-day roadmaps tailored to your current skills and career goals.

##  Overview

This AI-powered application analyzes your current skill set, identifies gaps relative to your target role, and generates a comprehensive 30-day learning plan with:

-  **Skill Gap Analysis** - Detailed breakdown of matched, partial, and missing skills
-  **Daily Learning Tasks** - Structured, actionable tasks for each day
-  **Curated Resources** - Specific tutorials, documentation, and learning materials
-  **Weekly Milestones** - Clear progress checkpoints
-  **Export Options** - Download plans in Markdown or Text format

---

##  Features

### Core Functionality
- **Personalized Skill Gap Analysis** - AI-powered comparison of your skills vs. target role requirements
- **30-Day Structured Plan** - Day-by-day learning schedule with realistic pacing
- **Smart Resource Recommendations** - Context-aware suggestions for tutorials and documentation
- **Progress Tracking** - Weekly milestones to keep you motivated
- **Multiple Export Formats** - Download as Markdown (.md) or Plain Text (.txt)

### User Experience
- **Quick Start Examples** - Pre-filled profiles for common roles (Backend Engineer, Data Analyst, ML Engineer)
- **Adjustable Time Commitment** - Customize daily learning hours (0.5 to 3 hours)
- **Difficulty Level Selection** - Beginner, Intermediate, or Advanced — shapes both the gap analysis and plan depth
- **Clean, Intuitive UI** - Tab-based navigation with collapsible weekly sections
- **Robust Error Handling** - Validation, retry logic, and user-friendly error messages

---

##  Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit |
| Backend | Python |
| LLM | Groq — llama-3.3-70b-versatile |
| LLM Orchestration | LangChain |
| JSON Repair | json-repair |

---

##  Installation & Setup

### Prerequisites
- Python 3.8 or higher
- Groq API key 

### Step 1: Clone the Repository
```bash
git clone https://github.com/shahjenil76/AI-Learning-Planner.git
cd AI-Learning-Planner
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Configure API Key

Create a `.streamlit/secrets.toml` file in the project root:

```toml
GROQ_API_KEY = "your-groq-api-key-here"
```

**Or** set as an environment variable:
```bash
export GROQ_API_KEY="your-groq-api-key-here"
```

### Step 4: Run the Application
```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

---

##  How to Use

### Quick Start
1. Open the app in your browser
2. Click one of the **Quick Start Examples** in the sidebar (e.g., "Backend Developer")
3. Click **"Generate My Learning Plan"**
4. View your personalized plan across three tabs:
   - **Skill Gap Analysis** - See what you know vs. what you need
   - **30-Day Plan** - Daily learning schedule
   - **Export** - Download your plan

### Custom Plan
1. Enter your **Current Skills** (comma-separated) in the sidebar
2. Specify your **Target Role**
3. Set your **Daily Time Commitment** (0.5 to 3 hours)
4. Choose your **Difficulty Level** (Beginner / Intermediate / Advanced)
5. Click **"Generate My Learning Plan"**

---

## 🧠 How It Works

### Architecture Overview

```
User Input (Skills + Target Role + Hours + Difficulty)
        ↓
    Validation & Normalization
        ↓
    Skill Gap Analysis (LLM Call #1)
        ↓
    Plan Summary — focus areas + milestones (LLM Call #2)
        ↓
    Daily Plan Days 1–15 (LLM Call #3)
        ↓
    Daily Plan Days 16–30 (LLM Call #4)
        ↓
    Display in Streamlit UI
        ↓
    Export to Markdown / Text
```

### Why 4 LLM Calls?

The plan generation was originally a single LLM call. This caused a JSON parse error in production:

```
Expecting ',' delimiter: line 419 column 10 (char 20122)
```

The root cause was response truncation — 30 days of detailed JSON is a large output and Groq's free tier would cut it off mid-sentence, breaking the JSON structure. The fix was to split into three smaller calls: a summary call, Days 1–15, and Days 16–30. Each call is half the size and well within token limits. This eliminated the error completely.

### Skill Gap Analysis Logic

**LLM Call #1 — Gap Analysis**
- Compares user's current skills against target role requirements
- Difficulty level shapes the analysis — Beginner gets foundational gaps flagged, Advanced only sees specialist gaps
- Categorizes skills into: Matched, Partial Gaps, Missing
- Determines learning priority order (foundational → advanced)
- Returns reasoning explaining why each skill matters for the target role

**LLM Calls #2, #3, #4 — Plan Generation**
- Call #2 generates the plan summary: focus areas and weekly milestones
- Calls #3 and #4 generate daily plans in two 15-day chunks
- Takes gap analysis output as direct input — plan is built on actual gaps, not generic role requirements
- Organizes topics in logical progression:
  - Days 1–10: Foundations (calibrated to difficulty level)
  - Days 11–20: Intermediate + Hands-On Practice
  - Days 21–30: Advanced + Mini Projects
- Balances task load based on daily hours selected

### How Difficulty Level Affects the Output

| Level | Gap Analysis | Plan Generation |
|---|---|---|
| Beginner | Flags foundational skills as gaps | Starts from setup and terminology, explains concepts |
| Intermediate | Skips basics the user likely knows | Focuses on tool-specific patterns and projects |
| Advanced | Highlights only specialist gaps | Targets architecture, performance, production-grade skills |

### Prompt Engineering Strategy

**Gap Analysis Prompt:**
- Strict JSON output for consistent parsing
- Difficulty level passed as context to shape categorization
- Explicit reasoning field required for transparency

**Plan Generation Prompts:**
- Gap analysis output passed directly as input context
- Day range specified per call (1–15 or 16–30) to prevent truncation
- Difficulty guidance text included to adjust depth
- Daily hours parameter controls task count per day
- Resource specificity enforced — generic suggestions not permitted

### JSON Parsing — Fault Tolerance

All LLM responses go through a three-layer extraction function:

1. **Strip markdown fences** — Groq sometimes wraps JSON in ` ```json ``` `
2. **Standard `json.loads`** — fast path for clean responses
3. **`json-repair` library** — fixes minor issues like missing commas or truncated items
4. **Brute-force trim** — finds the last complete `}` and parses from there

This means a single bad character or minor truncation never crashes the app.

---


### Skill Gap Analysis
```
 Skills You Already Have
  - Python
  - SQL
  - Git

 Skills That Need Improvement
  - API Design
  - Testing

 Skills You Need to Learn
  - FastAPI
  - Docker
  - PostgreSQL
  - Redis
  - CI/CD Pipelines
```

### Daily Plan Example (Day 1)
```
Day 1: Introduction to FastAPI Basics

Topics: FastAPI fundamentals, HTTP methods, routing

Tasks:
- [ ] Read FastAPI official documentation introduction
- [ ] Install FastAPI and Uvicorn
- [ ] Build a simple "Hello World" API
- [ ] Test endpoints using Swagger UI

Resources:
- FastAPI Official Docs: https://fastapi.tiangolo.com/
- Tutorial: Building Your First FastAPI App
- Video: FastAPI in 10 Minutes

Time Breakdown: 30 min reading, 30 min hands-on practice
```

---

## ⚙️ Error Handling

- **Input Validation** — Both fields checked before any API call is made
- **LLM Call Protection** — Try-except blocks around every API call
- **JSON Fault Tolerance** — Three-layer extraction handles truncation, code fences, and malformed output
- **Staged Failure** — If gap analysis fails, plan generation does not run
- **User-Friendly Messages** — Clear error descriptions so users know what went wrong and can retry
- **Session State Persistence** — Results survive page interactions without re-generating

---


### File Structure
```
AI-Learning-Planner/
├── app.py                  # Main Streamlit application
├── requirements.txt        # Python dependencies
├── README.md               # This file
├── .streamlit/
│   └── secrets.toml        # API keys 
```

### Key Functions

**`get_api_key(key_name)`**
- Reads API key from Streamlit secrets or environment variables
- Handles both local and cloud deployment

**`initialize_llm()`**
- Initializes Groq LLM client
- Returns configured ChatGroq instance

**`normalize_skills(skills_input)`**
- Splits comma-separated input, strips whitespace, removes empty strings
- Ensures consistent skill formatting before passing to LLM

**`extract_json(response_text)`**
- Strips markdown code fences
- Tries standard parsing, then json-repair, then brute-force trim
- Returns parsed dict or None

**`analyze_skill_gap(llm, current_skills, target_role, difficulty_level)`**
- LLM Call #1 — gap analysis
- Returns JSON with matched / partial / missing skills, priority order, and reasoning
- Difficulty level shapes what gets flagged

**`_plan_chunk(llm, ..., day_start, day_end, phase_label)`**
- Internal helper — generates a subset of days (1–15 or 16–30)
- Kept small to avoid response truncation

**`generate_learning_plan(llm, gap_analysis, target_role, daily_hours, difficulty_level)`**
- Orchestrates LLM Calls #2, #3, #4
- Returns combined plan with summary and all 30 daily entries

**`export_to_markdown()` / `export_to_text()`**
- Formats full plan for download
- Includes profile, gap analysis, milestones, and all 30 days

---

##  API Key Setup

### Getting a Groq API Key (Free)

1. Go to https://console.groq.com
2. Sign up for a free account
3. Navigate to API Keys section
4. Click "Create API Key"
5. Copy the key (format: `gsk_...`)

### Adding to Streamlit

**Local Development** — create `.streamlit/secrets.toml`:
```toml
GROQ_API_KEY = "gsk_your_key_here"
```

**Streamlit Cloud Deployment:**
1. Go to your app settings
2. Click "Secrets"
3. Add:
```toml
GROQ_API_KEY = "gsk_your_key_here"
```

---

##  Testing the App

**Test 1: Backend Engineer Path**
- Current Skills: `Python, SQL, Git`
- Target Role: `Backend Engineer`
- Expected: FastAPI, Docker, API design, testing, deployment

**Test 2: Data Analyst Path**
- Current Skills: `Excel, Basic SQL, Statistics`
- Target Role: `Data Analyst`
- Expected: Advanced SQL, Python (Pandas), Data Visualization, Statistical Analysis

**Test 3: ML Engineer Path**
- Current Skills: `Python, NumPy, Pandas`
- Target Role: `Machine Learning Engineer`
- Expected: Scikit-learn, TensorFlow/PyTorch, ML algorithms, model deployment, MLOps

---
##  Future Enhancements

- [ ] **Progress Tracking** - Mark completed days and track completion percentage
- [ ] **Persistent Storage** - Save plans to a database so they survive page refresh
- [ ] **Calendar Export** - Download as .ics format for Google Calendar
- [ ] **Multi-Role Comparison** - Compare learning paths for different roles side-by-side
- [ ] **Skill Assessment Quiz** - Interactive quiz to validate current skill level
- [ ] **Adaptive Difficulty** - Adjust plan difficulty based on user feedback on completed days
- [ ] **Resource Ratings** - Community ratings for recommended learning materials

---

##  Author

**Jenil Shah**
- LinkedIn: [linkedin.com/in/jenil-shah](https://linkedin.com/in/jenil-shah)
- GitHub: [github.com/shahjenil76](https://github.com/shahjenil76)

---


- Built as a technical assessment for E2M Solutions Private Limited
