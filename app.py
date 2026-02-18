import streamlit as st
import os
from datetime import datetime
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
import json
import re

# ─── Page Configuration ──────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Personal Learning Planner",
    page_icon="🎓",
    layout="wide"
)

# ─── Custom CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Main background */
    .stApp {
        background-color: #0f1117;
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #1a1d27;
        border-right: 1px solid #2d2f3e;
    }

    /* Card-style containers */
    .skill-card {
        background: #1e2130;
        border-radius: 12px;
        padding: 16px 20px;
        margin: 8px 0;
        border-left: 4px solid #4f8ef7;
        font-size: 15px;
        color: #e0e0e0;
    }
    .skill-card.green  { border-left-color: #2ecc71; }
    .skill-card.yellow { border-left-color: #f1c40f; }
    .skill-card.red    { border-left-color: #e74c3c; }
    .skill-card.blue   { border-left-color: #4f8ef7; }

    /* Day card */
    .day-card {
        background: #1e2130;
        border-radius: 14px;
        padding: 20px 24px;
        margin: 12px 0;
        border: 1px solid #2d2f3e;
    }
    .day-card h4 {
        color: #4f8ef7;
        margin-bottom: 8px;
        font-size: 17px;
    }
    .day-card .tag {
        display: inline-block;
        background: #2d3250;
        color: #a0b4e8;
        border-radius: 20px;
        padding: 2px 12px;
        font-size: 12px;
        margin: 3px 3px 6px 0;
    }
    .day-card .task-item {
        color: #c8d3e8;
        margin: 4px 0;
        font-size: 14px;
    }
    .day-card .resource-item {
        color: #7eb3f7;
        margin: 3px 0;
        font-size: 13px;
    }
    .day-card .time-badge {
        background: #252840;
        color: #8899cc;
        border-radius: 8px;
        padding: 4px 12px;
        font-size: 12px;
        margin-top: 10px;
        display: inline-block;
    }

    /* Milestone card */
    .milestone-card {
        background: linear-gradient(135deg, #1e2130, #252840);
        border-radius: 12px;
        padding: 16px 20px;
        margin: 8px 0;
        border: 1px solid #3a3f5c;
        color: #c8d3e8;
    }
    .milestone-card .week-label {
        color: #4f8ef7;
        font-weight: 700;
        font-size: 14px;
        margin-bottom: 4px;
    }

    /* Section header */
    .section-header {
        font-size: 20px;
        font-weight: 700;
        color: #e0e6f8;
        margin: 18px 0 10px 0;
        padding-bottom: 6px;
        border-bottom: 2px solid #2d2f3e;
    }

    /* Welcome feature boxes */
    .feature-box {
        background: #1e2130;
        border-radius: 14px;
        padding: 22px;
        text-align: center;
        border: 1px solid #2d2f3e;
        height: 100%;
    }
    .feature-box .icon { font-size: 32px; margin-bottom: 10px; }
    .feature-box h3 { color: #e0e6f8; font-size: 16px; margin-bottom: 6px; }
    .feature-box p  { color: #8899cc; font-size: 13px; margin: 0; }

    /* Step boxes */
    .step-box {
        background: #1e2130;
        border-radius: 12px;
        padding: 16px;
        border: 1px solid #2d2f3e;
        text-align: center;
    }
    .step-box .step-num {
        background: #4f8ef7;
        color: white;
        border-radius: 50%;
        width: 30px;
        height: 30px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 14px;
        margin-bottom: 8px;
    }
    .step-box p { color: #a0b4e8; font-size: 13px; margin: 0; }

    /* Reasoning box */
    .reasoning-box {
        background: #1a2035;
        border: 1px solid #3a4a7a;
        border-radius: 12px;
        padding: 18px 22px;
        color: #b0c4e8;
        font-size: 14px;
        line-height: 1.7;
    }

    /* Priority number badge */
    .priority-badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        background: #4f8ef7;
        color: white;
        border-radius: 50%;
        width: 26px;
        height: 26px;
        font-size: 13px;
        font-weight: 700;
        margin-right: 10px;
        flex-shrink: 0;
    }
    .priority-row {
        display: flex;
        align-items: center;
        padding: 8px 0;
        color: #c8d3e8;
        font-size: 14px;
        border-bottom: 1px solid #1e2130;
    }

    /* Metrics row */
    [data-testid="stMetric"] {
        background: #1e2130;
        border-radius: 12px;
        padding: 16px;
        border: 1px solid #2d2f3e;
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #1a1d27;
        border-radius: 10px;
        padding: 4px;
        gap: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        color: #8899cc;
        padding: 8px 20px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #4f8ef7 !important;
        color: white !important;
    }

    /* Sidebar button */
    .stButton > button {
        border-radius: 8px;
        font-size: 13px;
        transition: all 0.2s;
    }
    div[data-testid="stSidebar"] .stButton > button {
        background: #252840;
        color: #a0b4e8;
        border: 1px solid #3a3f5c;
        width: 100%;
    }
    div[data-testid="stSidebar"] .stButton > button:hover {
        background: #2d3260;
        color: #e0e6f8;
        border-color: #4f8ef7;
    }

    /* Primary button */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #4f8ef7, #6a5af9) !important;
        color: white !important;
        border: none !important;
        font-weight: 600 !important;
        font-size: 15px !important;
        padding: 12px !important;
        border-radius: 10px !important;
    }

    /* Expander */
    details {
        background: #1a1d27;
        border: 1px solid #2d2f3e;
        border-radius: 10px;
        margin: 6px 0;
    }

    /* Download buttons */
    .stDownloadButton > button {
        background: #1e2a40 !important;
        border: 1px solid #4f8ef7 !important;
        color: #7eb3f7 !important;
        border-radius: 10px !important;
        padding: 12px !important;
        font-weight: 600 !important;
        width: 100%;
    }
    .stDownloadButton > button:hover {
        background: #253555 !important;
        color: #a8d0ff !important;
    }

    /* Hide Streamlit branding */
    #MainMenu, footer { visibility: hidden; }
    header[data-testid="stHeader"] { background: transparent; }
</style>
""", unsafe_allow_html=True)


# ─── Helper Functions ────────────────────────────────────────────────────────

def get_api_key(key_name):
    """Get API key from Streamlit secrets or environment variables"""
    try:
        if key_name in st.secrets:
            return st.secrets[key_name]
    except Exception:
        pass
    if key_name in os.environ:
        return os.environ[key_name]
    st.error(f"⚠️ Missing API key: {key_name}. Please add it to your Streamlit secrets or environment variables.")
    return None


def initialize_llm():
    """Initialize the Groq LLM client"""
    api_key = get_api_key("GROQ_API_KEY")
    if not api_key:
        return None
    return ChatGroq(
        api_key=api_key,
        model='llama-3.3-70b-versatile',
        temperature=0.7
    )


def normalize_skills(skills_input):
    """Normalize and clean comma-separated skill inputs"""
    if not skills_input:
        return []
    skills = [s.strip() for s in skills_input.split(',')]
    return [s for s in skills if s]


def extract_json(response_text):
    """
    Robustly extract JSON from LLM response.
    Handles markdown code fences (```json ... ```) and bare JSON objects.
    """
    # Strip markdown code fences if present
    cleaned = re.sub(r'```(?:json)?\s*', '', response_text)
    cleaned = re.sub(r'```', '', cleaned).strip()

    # Extract the outermost JSON object
    json_match = re.search(r'\{.*\}', cleaned, re.DOTALL)
    if json_match:
        return json.loads(json_match.group())
    return None


def analyze_skill_gap(llm, current_skills, target_role, difficulty_level):
    """
    LLM Call #1 — Analyze skill gaps between current skills and target role.
    Difficulty level is passed so the analysis reflects the user's starting point.
    """
    prompt_template = """
You are an expert career advisor analyzing skill gaps for career development.

Target Role: {target_role}
Current Skills: {current_skills}
User's Self-Assessed Level: {difficulty_level}

Analyze the skill gap with the user's level in mind. A Beginner needs more foundational context,
an Intermediate user can skip basics they may already know, and an Advanced user needs only 
cutting-edge or specialist skills highlighted.

Provide a structured response in the following JSON format:

{{
    "required_skills": ["skill1", "skill2", "skill3"],
    "skills_matched": ["matched_skill1", "matched_skill2"],
    "partial_gaps": ["skill_that_needs_improvement1"],
    "missing_skills": ["completely_missing_skill1", "completely_missing_skill2"],
    "learning_priority": ["highest_priority_skill", "second_priority"],
    "reasoning": "Brief explanation of why these skills matter for {target_role} at the {difficulty_level} level"
}}

Be specific and realistic. Focus on technical skills, tools, and frameworks for {target_role}.
Order missing_skills and learning_priority from most fundamental to most advanced.

Respond ONLY with valid JSON. No additional text.
"""
    prompt = ChatPromptTemplate.from_template(prompt_template)

    try:
        with st.spinner("🔍 Analyzing your skill gaps..."):
            formatted_prompt = prompt.format(
                target_role=target_role,
                current_skills=", ".join(current_skills),
                difficulty_level=difficulty_level
            )
            response = llm.invoke(formatted_prompt)
            response_text = response.content if hasattr(response, 'content') else str(response)
            result = extract_json(response_text)
            if result:
                return result
            st.error("❌ Could not parse the skill analysis response. Please try again.")
            return None
    except Exception as e:
        st.error(f"❌ Error during skill gap analysis: {e}")
        return None


def generate_learning_plan(llm, gap_analysis, target_role, daily_hours, difficulty_level):
    """
    LLM Call #2 — Generate a 30-day learning plan.
    Both daily_hours AND difficulty_level influence the plan structure and depth.
    """
    # Map difficulty to descriptive guidance for the prompt
    difficulty_guidance = {
        "Beginner": "Include clear explanations of concepts. Start with setup, terminology, and simple exercises. Avoid assuming prior knowledge of the field.",
        "Intermediate": "Assume familiarity with programming basics. Focus on tool-specific skills, patterns, and hands-on projects. Skip trivial beginner steps.",
        "Advanced": "Focus on architecture, best practices, performance, and production-grade implementations. Include complex projects and advanced concepts."
    }

    prompt_template = """
You are an expert learning path designer creating a personalized 30-day plan.

Target Role: {target_role}
Missing Skills to Learn: {missing_skills}
Skills That Need Improvement: {partial_gaps}
Learning Priority Order: {priority_order}
Daily Time Available: {daily_hours} hour(s)
Difficulty Level: {difficulty_level}

Difficulty Guidance: {difficulty_guidance}

Create a detailed 30-day learning plan. For each day (Day 1 to Day 30) provide:
- Day number
- Clear learning objective
- Topics to cover
- Specific tasks (2-4 actionable tasks scaled to {daily_hours} hour(s))
- Recommended resources (real tutorials, docs, or course names with URLs where possible)
- Estimated time breakdown adding up to {daily_hours} hour(s)

Structure the plan with appropriate depth for a {difficulty_level} learner:
- Days 1-10: Foundational concepts (calibrated to {difficulty_level})
- Days 11-20: Intermediate topics and hands-on practice
- Days 21-30: Advanced concepts and mini-projects

Output format — respond ONLY with valid JSON:

{{
    "plan_summary": {{
        "total_days": 30,
        "focus_areas": ["area1", "area2", "area3"],
        "weekly_milestones": ["week1 goal", "week2 goal", "week3 goal", "week4 goal"]
    }},
    "daily_plan": [
        {{
            "day": 1,
            "objective": "Clear objective for the day",
            "topics": ["topic1", "topic2"],
            "tasks": [
                "Specific task 1",
                "Specific task 2",
                "Specific task 3"
            ],
            "resources": [
                "Resource name or link with description",
                "Another resource"
            ],
            "time_breakdown": "30 min reading, 30 min practice"
        }}
    ]
}}

Respond ONLY with valid JSON. No additional text before or after.
"""
    prompt = ChatPromptTemplate.from_template(prompt_template)

    try:
        with st.spinner("📅 Building your personalized 30-day plan..."):
            formatted_prompt = prompt.format(
                target_role=target_role,
                missing_skills=", ".join(gap_analysis.get('missing_skills', [])),
                partial_gaps=", ".join(gap_analysis.get('partial_gaps', [])),
                priority_order=", ".join(gap_analysis.get('learning_priority', [])),
                daily_hours=daily_hours,
                difficulty_level=difficulty_level,
                difficulty_guidance=difficulty_guidance.get(difficulty_level, "")
            )
            response = llm.invoke(formatted_prompt)
            response_text = response.content if hasattr(response, 'content') else str(response)
            result = extract_json(response_text)
            if result:
                return result
            st.error("❌ Could not parse the learning plan response. Please try again.")
            return None
    except Exception as e:
        st.error(f"❌ Error generating learning plan: {e}")
        return None


def export_to_markdown(gap_analysis, learning_plan, target_role, current_skills, daily_hours, difficulty_level):
    """Export learning plan to Markdown format"""
    md = f"""# 🎓 AI Personal Learning Planner

**Generated on:** {datetime.now().strftime('%B %d, %Y')}

---

## Your Profile
| Field | Value |
|---|---|
| **Target Role** | {target_role} |
| **Current Skills** | {', '.join(current_skills)} |
| **Daily Commitment** | {daily_hours} hour(s) |
| **Difficulty Level** | {difficulty_level} |

---

## Skill Gap Analysis

### ✅ Skills You Already Have
{', '.join(gap_analysis.get('skills_matched', ['None identified']))}

### 🔄 Skills That Need Improvement
{', '.join(gap_analysis.get('partial_gaps', ['None identified']))}

### 📚 Skills You Need to Learn
{', '.join(gap_analysis.get('missing_skills', ['None identified']))}

### 💡 Why These Skills Matter
{gap_analysis.get('reasoning', 'No reasoning provided')}

---

## 30-Day Learning Plan

**Focus Areas:** {', '.join(learning_plan.get('plan_summary', {}).get('focus_areas', []))}

### Weekly Milestones
"""
    for i, milestone in enumerate(learning_plan.get('plan_summary', {}).get('weekly_milestones', []), 1):
        md += f"- **Week {i}:** {milestone}\n"

    md += "\n---\n\n## Daily Learning Schedule\n\n"

    for day_plan in learning_plan.get('daily_plan', []):
        day_num = day_plan.get('day', 0)
        md += f"### Day {day_num}: {day_plan.get('objective', 'No objective')}\n\n"
        md += f"**Topics:** {', '.join(day_plan.get('topics', []))}\n\n"
        md += "**Tasks:**\n"
        for task in day_plan.get('tasks', []):
            md += f"- [ ] {task}\n"
        md += "\n**Resources:**\n"
        for resource in day_plan.get('resources', []):
            md += f"- {resource}\n"
        md += f"\n**Time Breakdown:** {day_plan.get('time_breakdown', 'Not specified')}\n\n---\n\n"

    return md


def export_to_text(gap_analysis, learning_plan, target_role, current_skills, daily_hours, difficulty_level):
    """Export learning plan to plain text format"""
    sep = "=" * 60
    thin = "-" * 60

    txt = f"""AI PERSONAL LEARNING PLANNER
Generated on: {datetime.now().strftime('%B %d, %Y')}

{sep}

YOUR PROFILE
Target Role     : {target_role}
Current Skills  : {', '.join(current_skills)}
Daily Hours     : {daily_hours} hour(s)
Difficulty Level: {difficulty_level}

{sep}

SKILL GAP ANALYSIS

[OK] Skills You Already Have:
  {', '.join(gap_analysis.get('skills_matched', ['None identified']))}

[~]  Skills That Need Improvement:
  {', '.join(gap_analysis.get('partial_gaps', ['None identified']))}

[X]  Skills You Need to Learn:
  {', '.join(gap_analysis.get('missing_skills', ['None identified']))}

Why These Skills Matter:
{gap_analysis.get('reasoning', 'No reasoning provided')}

{sep}

30-DAY LEARNING PLAN

Focus Areas: {', '.join(learning_plan.get('plan_summary', {}).get('focus_areas', []))}

Weekly Milestones:
"""
    for i, milestone in enumerate(learning_plan.get('plan_summary', {}).get('weekly_milestones', []), 1):
        txt += f"  Week {i}: {milestone}\n"

    txt += f"\n{sep}\n\nDAILY LEARNING SCHEDULE\n\n"

    for day_plan in learning_plan.get('daily_plan', []):
        day_num = day_plan.get('day', 0)
        txt += f"\nDAY {day_num}: {day_plan.get('objective', 'No objective')}\n{thin}\n"
        txt += f"Topics: {', '.join(day_plan.get('topics', []))}\n\nTasks:\n"
        for i, task in enumerate(day_plan.get('tasks', []), 1):
            txt += f"  {i}. {task}\n"
        txt += "\nResources:\n"
        for resource in day_plan.get('resources', []):
            txt += f"  - {resource}\n"
        txt += f"\nTime Breakdown: {day_plan.get('time_breakdown', 'Not specified')}\n"

    return txt


# ─── Main App ────────────────────────────────────────────────────────────────

def main():

    # ── Header ──
    st.markdown("""
    <div style="text-align:center; padding: 10px 0 4px 0;">
        <span style="font-size:42px;">🎓</span>
        <h1 style="color:#e0e6f8; font-size:32px; margin:6px 0 4px 0;">AI Personal Learning Planner</h1>
        <p style="color:#8899cc; font-size:15px; margin:0;">
            Enter your skills and target role → get a personalized 30-day roadmap
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<hr style='border-color:#2d2f3e; margin:16px 0 10px 0;'>", unsafe_allow_html=True)

    # ── LLM Init ──
    llm = initialize_llm()
    if not llm:
        st.warning("⚠️ Please configure your **GROQ_API_KEY** in Streamlit secrets to use this app.")
        st.stop()

    # ── Session State ──
    defaults = {
        'gap_analysis': None,
        'learning_plan': None,
        'current_skills_input': "",
        'target_role_input': "",
        'daily_hours': 1,
        'difficulty_level': "Beginner",
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

    # ─────────────────────────────────────────────────────
    # SIDEBAR
    # ─────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("""
        <div style="text-align:center; padding:16px 0 10px 0;">
            <div style="color:#e0e6f8; font-weight:700; font-size:17px; margin-top:6px;">Your Learning Profile</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<hr style='border-color:#2d2f3e; margin:0 0 12px 0;'>", unsafe_allow_html=True)

        # Quick Start Examples
        st.markdown("<div style='color:#8899cc; font-size:12px; font-weight:600; letter-spacing:1px; margin-bottom:8px;'>QUICK START EXAMPLES</div>", unsafe_allow_html=True)

        examples = [
            ("🔹 Backend Developer", "Python, SQL, Git", "Backend Engineer"),
            ("🔹 Data Analyst",      "Excel, Basic SQL, Statistics", "Data Analyst"),
            ("🔹 ML Engineer",       "Python, NumPy, Pandas", "Machine Learning Engineer"),
        ]
        for label, skills, role in examples:
            if st.button(label, use_container_width=True):
                st.session_state.current_skills_input = skills
                st.session_state.target_role_input = role
                st.rerun()

        st.markdown("<hr style='border-color:#2d2f3e; margin:14px 0;'>", unsafe_allow_html=True)

        # Inputs
        st.markdown("<div style='color:#8899cc; font-size:12px; font-weight:600; letter-spacing:1px; margin-bottom:8px;'>YOUR INFORMATION</div>", unsafe_allow_html=True)

        current_skills_input = st.text_area(
            "Current Skills",
            value=st.session_state.current_skills_input,
            placeholder="e.g., Python, SQL, Git, HTML",
            height=90,
            help="List skills you currently have, separated by commas"
        )

        target_role = st.text_input(
            "Target Role",
            value=st.session_state.target_role_input,
            placeholder="e.g., Data Scientist, Backend Engineer",
            help="The job role you want to work towards"
        )

        st.markdown("<hr style='border-color:#2d2f3e; margin:14px 0;'>", unsafe_allow_html=True)
        st.markdown("<div style='color:#8899cc; font-size:12px; font-weight:600; letter-spacing:1px; margin-bottom:8px;'>LEARNING PREFERENCES</div>", unsafe_allow_html=True)

        daily_hours = st.select_slider(
            "Daily Time Commitment",
            options=[0.5, 1, 1.5, 2, 3],
            value=st.session_state.daily_hours,
            help="Hours per day you can dedicate to learning"
        )

        difficulty_level = st.selectbox(
            "Difficulty Level",
            ["Beginner", "Intermediate", "Advanced"],
            index=["Beginner", "Intermediate", "Advanced"].index(st.session_state.difficulty_level),
            help="Your current proficiency in this field — this shapes both the gap analysis and the plan depth"
        )

        # Difficulty explanation
        diff_colors = {"Beginner": "#2ecc71", "Intermediate": "#f1c40f", "Advanced": "#e74c3c"}
        diff_desc   = {
            "Beginner":     "Plan will start from fundamentals and explain core concepts.",
            "Intermediate": "Plan will skip basics and focus on tools and hands-on projects.",
            "Advanced":     "Plan targets architecture, performance, and production-grade skills."
        }
        st.markdown(f"""
        <div style="background:#1a2030; border-left:3px solid {diff_colors[difficulty_level]};
                    border-radius:6px; padding:8px 12px; margin-top:4px; font-size:12px; color:#a0b4c8;">
            {diff_desc[difficulty_level]}
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        generate_btn = st.button("🚀 Generate My Learning Plan", type="primary", use_container_width=True)

        if generate_btn:
            if not current_skills_input.strip():
                st.error("⚠️ Please enter your current skills.")
            elif not target_role.strip():
                st.error("⚠️ Please enter your target role.")
            else:
                # Persist to session state
                st.session_state.current_skills_input = current_skills_input
                st.session_state.target_role_input    = target_role
                st.session_state.daily_hours          = daily_hours
                st.session_state.difficulty_level     = difficulty_level
                st.session_state.gap_analysis         = None
                st.session_state.learning_plan        = None

                current_skills = normalize_skills(current_skills_input)

                # Step 1: Skill gap analysis
                gap_analysis = analyze_skill_gap(llm, current_skills, target_role, difficulty_level)

                if gap_analysis:
                    st.session_state.gap_analysis = gap_analysis

                    # Step 2: Learning plan
                    learning_plan = generate_learning_plan(
                        llm, gap_analysis, target_role, daily_hours, difficulty_level
                    )

                    if learning_plan:
                        st.session_state.learning_plan = learning_plan
                        st.success("✅ Your plan is ready!")
                        st.rerun()

        # Show current config summary if plan exists
        if st.session_state.gap_analysis and st.session_state.learning_plan:
            st.markdown("<hr style='border-color:#2d2f3e; margin:16px 0;'>", unsafe_allow_html=True)
            st.markdown(f"""
            <div style="background:#1a2030; border-radius:10px; padding:12px 14px; font-size:12px; color:#8899cc;">
                <div style="color:#4f8ef7; font-weight:600; margin-bottom:6px;">📌 Current Plan</div>
                <div>🎯 Role: <span style="color:#c8d3e8;">{st.session_state.target_role_input}</span></div>
                <div>⏱ Hours/day: <span style="color:#c8d3e8;">{st.session_state.daily_hours}</span></div>
                <div>📊 Level: <span style="color:{diff_colors[st.session_state.difficulty_level]};">{st.session_state.difficulty_level}</span></div>
            </div>
            """, unsafe_allow_html=True)

    # ─────────────────────────────────────────────────────
    # MAIN CONTENT
    # ─────────────────────────────────────────────────────

    if st.session_state.gap_analysis and st.session_state.learning_plan:

        gap_analysis   = st.session_state.gap_analysis
        learning_plan  = st.session_state.learning_plan
        current_skills = normalize_skills(st.session_state.current_skills_input)
        target_role    = st.session_state.target_role_input
        daily_hours    = st.session_state.daily_hours
        difficulty_level = st.session_state.difficulty_level

        tab1, tab2, tab3 = st.tabs(["📊  Skill Gap Analysis", "📅  30-Day Plan", "📥  Export"])

        # ── TAB 1: Skill Gap Analysis ─────────────────────
        with tab1:
            st.markdown("<div class='section-header'>Skill Gap Analysis</div>", unsafe_allow_html=True)

            col1, col2 = st.columns(2, gap="large")

            with col1:
                st.markdown("<div style='color:#2ecc71; font-weight:700; font-size:15px; margin-bottom:8px;'>✅ Skills You Already Have</div>", unsafe_allow_html=True)
                matched = gap_analysis.get('skills_matched', [])
                if matched:
                    for skill in matched:
                        st.markdown(f"<div class='skill-card green'>✓ {skill}</div>", unsafe_allow_html=True)
                else:
                    st.info("No matching skills identified")

                st.markdown("<div style='color:#f1c40f; font-weight:700; font-size:15px; margin:16px 0 8px 0;'>🔄 Skills That Need Improvement</div>", unsafe_allow_html=True)
                partial = gap_analysis.get('partial_gaps', [])
                if partial:
                    for skill in partial:
                        st.markdown(f"<div class='skill-card yellow'>~ {skill}</div>", unsafe_allow_html=True)
                else:
                    st.info("No partial gaps identified")

            with col2:
                st.markdown("<div style='color:#e74c3c; font-weight:700; font-size:15px; margin-bottom:8px;'>📚 Skills You Need to Learn</div>", unsafe_allow_html=True)
                missing = gap_analysis.get('missing_skills', [])
                if missing:
                    for skill in missing:
                        st.markdown(f"<div class='skill-card red'>✗ {skill}</div>", unsafe_allow_html=True)
                else:
                    st.info("No missing skills — you're well prepared!")

                st.markdown("<div style='color:#4f8ef7; font-weight:700; font-size:15px; margin:16px 0 8px 0;'>🎯 Learning Priority Order</div>", unsafe_allow_html=True)
                priority = gap_analysis.get('learning_priority', [])
                if priority:
                    for i, skill in enumerate(priority[:6], 1):
                        st.markdown(f"""
                        <div class='priority-row'>
                            <span class='priority-badge'>{i}</span>{skill}
                        </div>
                        """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("<div style='color:#4f8ef7; font-weight:700; font-size:15px; margin-bottom:8px;'>💡 Why These Skills Matter</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='reasoning-box'>{gap_analysis.get('reasoning', 'No reasoning provided')}</div>", unsafe_allow_html=True)

        # ── TAB 2: 30-Day Plan ────────────────────────────
        with tab2:
            summary = learning_plan.get('plan_summary', {})

            # Metrics row
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Days", summary.get('total_days', 30))
            col2.metric("Focus Areas", len(summary.get('focus_areas', [])))
            col3.metric("Hours / Day", daily_hours)
            col4.metric("Level", difficulty_level)

            # Focus areas
            st.markdown("<div class='section-header' style='margin-top:20px;'>Focus Areas</div>", unsafe_allow_html=True)
            focus_cols = st.columns(min(len(summary.get('focus_areas', [])), 3))
            for i, area in enumerate(summary.get('focus_areas', [])):
                with focus_cols[i % 3]:
                    st.markdown(f"<div class='skill-card blue' style='text-align:center;'>{area}</div>", unsafe_allow_html=True)

            # Weekly milestones
            st.markdown("<div class='section-header' style='margin-top:20px;'>Weekly Milestones</div>", unsafe_allow_html=True)
            milestones = summary.get('weekly_milestones', [])
            mcols = st.columns(len(milestones)) if milestones else [st.container()]
            for i, (col, milestone) in enumerate(zip(mcols, milestones), 1):
                with col:
                    st.markdown(f"""
                    <div class='milestone-card'>
                        <div class='week-label'>Week {i}</div>
                        <div>{milestone}</div>
                    </div>
                    """, unsafe_allow_html=True)

            # Daily schedule
            st.markdown("<div class='section-header' style='margin-top:20px;'>Daily Schedule</div>", unsafe_allow_html=True)

            daily_plans = learning_plan.get('daily_plan', [])
            week_groups = {
                "Week 1 — Foundations (Days 1–7)":          daily_plans[0:7],
                "Week 2 — Building Up (Days 8–14)":         daily_plans[7:14],
                "Week 3 — Hands-On Practice (Days 15–21)":  daily_plans[14:21],
                "Week 4 — Advanced & Projects (Days 22–30)": daily_plans[21:30],
            }

            for week_name, week_plans in week_groups.items():
                with st.expander(week_name, expanded=(week_name.startswith("Week 1"))):
                    for day_plan in week_plans:
                        topics_html = "".join(f"<span class='tag'>{t}</span>" for t in day_plan.get('topics', []))
                        tasks_html  = "".join(f"<div class='task-item'>☐ {t}</div>" for t in day_plan.get('tasks', []))
                        res_html    = "".join(f"<div class='resource-item'>🔗 {r}</div>" for r in day_plan.get('resources', []))

                        st.markdown(f"""
                        <div class='day-card'>
                            <h4>Day {day_plan.get('day', '')}: {day_plan.get('objective', '')}</h4>
                            <div style='margin-bottom:10px;'>{topics_html}</div>
                            <div style='margin-bottom:10px;'><b style='color:#8899cc; font-size:12px;'>TASKS</b>{tasks_html}</div>
                            <div style='margin-bottom:6px;'><b style='color:#8899cc; font-size:12px;'>RESOURCES</b>{res_html}</div>
                            <div class='time-badge'>⏱ {day_plan.get('time_breakdown', 'Time not specified')}</div>
                        </div>
                        """, unsafe_allow_html=True)

        # ── TAB 3: Export ─────────────────────────────────
        with tab3:
            st.markdown("<div class='section-header'>Export Your Learning Plan</div>", unsafe_allow_html=True)
            st.markdown("<p style='color:#8899cc; font-size:14px;'>Download your personalized plan and refer to it offline anytime.</p>", unsafe_allow_html=True)

            col1, col2 = st.columns(2, gap="large")

            with col1:
                st.markdown("""
                <div style='background:#1a2035; border-radius:12px; padding:20px; border:1px solid #2d2f3e; margin-bottom:12px;'>
                    <div style='font-size:28px; margin-bottom:8px;'>📄</div>
                    <div style='color:#e0e6f8; font-weight:600; margin-bottom:6px;'>Markdown (.md)</div>
                    <div style='color:#8899cc; font-size:13px;'>Best for GitHub, Notion, Obsidian, and other Markdown viewers. Includes tables, checkboxes, and formatted headers.</div>
                </div>
                """, unsafe_allow_html=True)
                md_content = export_to_markdown(gap_analysis, learning_plan, target_role, current_skills, daily_hours, difficulty_level)
                st.download_button(
                    label="⬇️ Download Markdown",
                    data=md_content,
                    file_name=f"learning_plan_{target_role.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.md",
                    mime="text/markdown",
                    use_container_width=True
                )

            with col2:
                st.markdown("""
                <div style='background:#1a2035; border-radius:12px; padding:20px; border:1px solid #2d2f3e; margin-bottom:12px;'>
                    <div style='font-size:28px; margin-bottom:8px;'>📝</div>
                    <div style='color:#e0e6f8; font-weight:600; margin-bottom:6px;'>Plain Text (.txt)</div>
                    <div style='color:#8899cc; font-size:13px;'>Universal format that works everywhere — email, notes apps, or any text editor.</div>
                </div>
                """, unsafe_allow_html=True)
                txt_content = export_to_text(gap_analysis, learning_plan, target_role, current_skills, daily_hours, difficulty_level)
                st.download_button(
                    label="⬇️ Download Text",
                    data=txt_content,
                    file_name=f"learning_plan_{target_role.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.txt",
                    mime="text/plain",
                    use_container_width=True
                )

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("""
            <div style='background:#1a2030; border-left:3px solid #4f8ef7; border-radius:8px; padding:14px 18px; color:#8899cc; font-size:13px;'>
                💡 <b style='color:#c8d3e8;'>Pro tip:</b> Save your plan and tick off tasks daily. 
                Consistent 1-hour sessions beat occasional marathon study. 
                Review your weekly milestone every Sunday to stay on track.
            </div>
            """, unsafe_allow_html=True)

    else:
        # ── Welcome Screen ────────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)

        # How it works — step boxes
        st.markdown("<div style='color:#e0e6f8; font-weight:700; font-size:18px; margin-bottom:14px; text-align:center;'>How It Works</div>", unsafe_allow_html=True)
        s1, s2, s3, s4 = st.columns(4, gap="small")
        steps = [
            ("1", "Enter your current skills"),
            ("2", "Set your target role"),
            ("3", "Choose your level & hours"),
            ("4", "Get your 30-day roadmap"),
        ]
        for col, (num, desc) in zip([s1, s2, s3, s4], steps):
            with col:
                st.markdown(f"""
                <div class='step-box'>
                    <div class='step-num'>{num}</div>
                    <p>{desc}</p>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Feature highlights
        st.markdown("<div style='color:#e0e6f8; font-weight:700; font-size:18px; margin-bottom:14px; text-align:center;'>What You'll Get</div>", unsafe_allow_html=True)
        f1, f2, f3, f4 = st.columns(4, gap="small")
        features = [
            ("🎯", "Skill Gap Analysis",  "See exactly what you know, what needs work, and what to learn next."),
            ("📅", "30-Day Daily Plan",   "A structured day-by-day schedule with clear objectives and tasks."),
            ("📚", "Curated Resources",   "Real tutorials, docs, and courses — no generic recommendations."),
            ("📥", "Export Your Plan",    "Download as Markdown or Text to use anywhere, anytime."),
        ]
        for col, (icon, title, desc) in zip([f1, f2, f3, f4], features):
            with col:
                st.markdown(f"""
                <div class='feature-box'>
                    <div class='icon'>{icon}</div>
                    <h3>{title}</h3>
                    <p>{desc}</p>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div style='text-align:center; background:#1a2030; border-radius:14px; padding:24px; border:1px dashed #3a4a7a;'>
            <div style='color:#e0e6f8; font-size:16px; font-weight:600;'>Use the sidebar to get started</div>
            <div style='color:#8899cc; font-size:13px; margin-top:6px;'>Try a quick-start example or enter your own skills and role</div>
        </div>
        """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
