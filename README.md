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
- **Difficulty Level Selection** - Tailor content to Beginner, Intermediate, or Advanced learners
- **Clean, Intuitive UI** - Tab-based navigation with collapsible weekly sections
- **Error Handling** - Robust validation and user-friendly error messages

---

##  Tech Stack

- **Frontend**: Streamlit
- **Backend Logic**: Python
- **LLM**: Groq (llama-3.3-70b-versatile) - Free tier
- **Frameworks**: LangChain for LLM orchestration

---

##  Installation & Setup

### Prerequisites
- Python 3.8 or higher
- Groq API key (free tier available at https://console.groq.com)

### Step 1: Clone the Repository
```bash
git clone https://github.com/yourusername/AI-Learning-Planner.git
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
3. Set your **Daily Time Commitment**
4. Choose your **Difficulty Level**
5. Click **"Generate My Learning Plan"**

---

##  How It Works

### Architecture Overview

```
User Input (Skills + Target Role)
        ↓
    Validation & Normalization
        ↓
    Skill Gap Analysis (LLM Call #1)
        ↓
    Learning Plan Generation (LLM Call #2)
        ↓
    Display in Streamlit UI
        ↓
    Export to Markdown/Text
```

### Skill Gap Analysis Logic

The app uses a two-step LLM process:

**Step 1: Gap Analysis**
- Compares user's current skills against target role requirements
- Categorizes skills into: Matched, Partial Gaps, Missing
- Determines learning priority order (foundational → advanced)
- Provides reasoning for why skills matter

**Step 2: Plan Generation**
- Takes gap analysis output as input
- Generates 30 daily learning objectives
- Organizes topics in logical progression:
  - Days 1-10: Foundations
  - Days 11-20: Intermediate + Practice
  - Days 21-30: Advanced + Projects
- Balances learning load based on daily hours available
- Recommends specific resources (tutorials, documentation, courses)

### Prompt Engineering Strategy

**Gap Analysis Prompt:**
- Structured JSON output for consistent parsing
- Explicit categorization of skill levels
- Context-aware reasoning

**Plan Generation Prompt:**
- Day-by-day structure enforcement
- Resource specificity requirements
- Realistic pacing based on time commitment
- Progressive difficulty scaling

---

##  Sample Output

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

##  Error Handling

The application includes comprehensive error handling:

- **Input Validation**: Ensures skills and target role are non-empty
- **LLM Call Protection**: Try-catch blocks around all API calls
- **JSON Parsing**: Robust extraction and validation of structured outputs
- **User-Friendly Messages**: Clear error descriptions with retry options
- **Graceful Degradation**: App remains functional even if one component fails

---

##  Future Enhancements

- [ ] **Calendar Export** - Download as .ics format for Google Calendar
- [ ] **Progress Tracking** - Mark completed days and track completion percentage
- [ ] **Multi-Role Comparison** - Compare learning paths for different roles side-by-side
- [ ] **Community Plans** - Share and discover learning plans from other users
- [ ] **Skill Assessment Quiz** - Interactive quiz to validate current skill level
- [ ] **Adaptive Difficulty** - Adjust plan difficulty based on user feedback
- [ ] **Resource Ratings** - User ratings for recommended learning materials

---

##  Testing the App

### Test Scenarios

**Test 1: Backend Engineer Path**
- Current Skills: `Python, SQL, Git`
- Target Role: `Backend Engineer`
- Expected: FastAPI, Docker, API design, testing, deployment

**Test 2: Data Analyst Path**
- Current Skills: `Excel, Basic SQL, Statistics`
- Target Role: `Data Analyst`
- Expected: Advanced SQL, Python (Pandas), Data Visualization (Tableau/PowerBI), Statistical Analysis

**Test 3: ML Engineer Path**
- Current Skills: `Python, NumPy, Pandas`
- Target Role: `Machine Learning Engineer`
- Expected: Scikit-learn, TensorFlow/PyTorch, ML algorithms, model deployment, MLOps

---

##  Technical Documentation

### File Structure
```
AI-Learning-Planner/
├── app.py                  # Main Streamlit application
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── .streamlit/
│   └── secrets.toml       # API keys (not committed)
└── .gitignore             # Git ignore rules
```

### Key Functions

**`initialize_llm()`**
- Initializes Groq LLM client with API key from secrets
- Returns configured ChatGroq instance

**`normalize_skills(skills_input)`**
- Cleans and splits comma-separated skill input
- Returns list of normalized skill strings

**`analyze_skill_gap(llm, current_skills, target_role)`**
- First LLM call for gap analysis
- Returns JSON with matched/partial/missing skills and reasoning

**`generate_learning_plan(llm, gap_analysis, target_role, daily_hours)`**
- Second LLM call for plan generation
- Returns JSON with 30-day structured plan

**`export_to_markdown()` / `export_to_text()`**
- Formats learning plan for export
- Returns formatted string ready for download

---

##  API Key Setup

### Getting a Groq API Key (Free)

1. Go to https://console.groq.com
2. Sign up for a free account
3. Navigate to API Keys section
4. Click "Create API Key"
5. Copy the key (format: `gsk_...`)

### Adding to Streamlit

**Local Development:**
Create `.streamlit/secrets.toml`:
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

##  Known Limitations

- **LLM Dependency**: Requires active internet connection and Groq API access
- **Response Variability**: LLM outputs may vary slightly between runs
- **Rate Limits**: Free tier Groq has rate limits (30 requests/minute)
- **Resource Accuracy**: Resources are AI-generated and should be verified by users
- **No User Accounts**: Plans are session-based and not saved permanently

---

##  Contributing

This project was created as a technical assessment. Contributions are welcome for educational purposes.

---

##  License

MIT License - Feel free to use this project for learning and portfolio purposes.

---

##  Author

**Jenil Shah**
- LinkedIn: [linkedin.com/in/jenil-shah](https://linkedin.com/in/jenil-shah)

---

##  Acknowledgments

- Built as a technical assessment for E2M Solutions Private Limited
- LLM powered by Groq (llama-3.3-70b-versatile)
- UI framework: Streamlit
- LLM orchestration: LangChain

---

**Note**: This is a demonstration application built for a technical assessment. It showcases AI-powered personalization, structured output generation, and clean UX design principles.
