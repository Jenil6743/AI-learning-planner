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
    - Strips markdown code fences
    - Tries standard json.loads first
    - Falls back to json_repair for minor malformed JSON
    - Last resort: trims to last complete closing brace
    """
    cleaned = re.sub(r'```(?:json)?\s*', '', response_text)
    cleaned = re.sub(r'```', '', cleaned).strip()

    json_match = re.search(r'\{.*\}', cleaned, re.DOTALL)
    if not json_match:
        return None

    raw = json_match.group()

    # Attempt 1: standard parse
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # Attempt 2: json_repair handles truncated JSON, missing commas, stray characters
    try:
        from json_repair import repair_json
        repaired = repair_json(raw)
        return json.loads(repaired)
    except Exception:
        pass

    # Attempt 3: trim to last complete closing brace
    try:
        last_brace = raw.rfind('}')
        if last_brace != -1:
            return json.loads(raw[:last_brace + 1])
    except Exception:
        pass

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


def _plan_chunk(llm, target_role, missing_skills, partial_gaps, priority_order,
                daily_hours, difficulty_level, difficulty_guidance, day_start, day_end, phase_label):
    """
    Internal helper — calls the LLM for a subset of days.
    Splitting the 30-day plan into two 15-day requests prevents response
    truncation which causes JSON parse errors.
    """
    prompt_template = """
You are an expert learning path designer.

Target Role: {target_role}
Missing Skills: {missing_skills}
Skills Needing Improvement: {partial_gaps}
Priority Order: {priority_order}
Daily Time: {daily_hours} hour(s)
Level: {difficulty_level}
Guidance: {difficulty_guidance}

Generate ONLY Days {day_start} to {day_end}.
Phase: {phase_label}

Keep tasks realistic for {daily_hours} hour(s)/day.
Use real resource names (docs, tutorials, courses).

Respond ONLY with valid JSON:
{{
    "daily_plan": [
        {{
            "day": {day_start},
            "objective": "objective here",
            "topics": ["topic1", "topic2"],
            "tasks": ["task1", "task2", "task3"],
            "resources": ["resource1", "resource2"],
            "time_breakdown": "X min reading, Y min practice"
        }}
    ]
}}
No extra text.
"""
    prompt = ChatPromptTemplate.from_template(prompt_template)
    formatted = prompt.format(
        target_role=target_role,
        missing_skills=missing_skills,
        partial_gaps=partial_gaps,
        priority_order=priority_order,
        daily_hours=daily_hours,
        difficulty_level=difficulty_level,
        difficulty_guidance=difficulty_guidance,
        day_start=day_start,
        day_end=day_end,
        phase_label=phase_label,
    )
    response = llm.invoke(formatted)
    response_text = response.content if hasattr(response, 'content') else str(response)
    return extract_json(response_text)


def generate_learning_plan(llm, gap_analysis, target_role, daily_hours, difficulty_level):
    """
    Generates the 30-day plan using 3 focused LLM calls:
      - Call 1: Plan summary (focus areas + weekly milestones)
      - Call 2: Days 1–15
      - Call 3: Days 16–30
    Splitting into smaller calls eliminates the JSON truncation error that
    occurs when asking for all 30 days in a single large response.
    """
    difficulty_guidance = {
        "Beginner":     "Start from scratch. Explain concepts clearly, include setup steps, use simple exercises.",
        "Intermediate": "Skip basics. Focus on tool-specific patterns and hands-on projects.",
        "Advanced":     "Target architecture, best practices, performance, and production-grade implementations.",
    }

    missing_skills = ", ".join(gap_analysis.get('missing_skills', []))
    partial_gaps   = ", ".join(gap_analysis.get('partial_gaps', []))
    priority_order = ", ".join(gap_analysis.get('learning_priority', []))
    guidance       = difficulty_guidance.get(difficulty_level, "")

    # ── Call 1: Summary ──────────────────────────────────────────────────────
    summary_template = """
Create a high-level learning plan summary for this profile.
Target Role: {target_role}
Missing Skills: {missing_skills}
Difficulty: {difficulty_level}

Respond ONLY with valid JSON:
{{
    "plan_summary": {{
        "total_days": 30,
        "focus_areas": ["area1", "area2", "area3"],
        "weekly_milestones": ["week1 goal", "week2 goal", "week3 goal", "week4 goal"]
    }}
}}
"""
    try:
        with st.spinner("📋 Building plan overview..."):
            s_prompt = ChatPromptTemplate.from_template(summary_template)
            resp = llm.invoke(s_prompt.format(
                target_role=target_role,
                missing_skills=missing_skills,
                difficulty_level=difficulty_level,
            ))
            resp_text = resp.content if hasattr(resp, 'content') else str(resp)
            summary_result = extract_json(resp_text)
            plan_summary = summary_result.get('plan_summary', {}) if summary_result else {
                "total_days": 30, "focus_areas": [], "weekly_milestones": []
            }
            plan_summary['total_days'] = 30
    except Exception as e:
        st.error(f"❌ Error generating plan overview: {e}")
        return None

    # ── Call 2: Days 1–15 ────────────────────────────────────────────────────
    try:
        with st.spinner("📅 Generating Days 1–15..."):
            chunk1 = _plan_chunk(
                llm, target_role, missing_skills, partial_gaps, priority_order,
                daily_hours, difficulty_level, guidance,
                day_start=1, day_end=15,
                phase_label="Foundations (Days 1-10) and early intermediate topics (Days 11-15)"
            )
            days_1_15 = chunk1.get('daily_plan', []) if chunk1 else []
    except Exception as e:
        st.error(f"❌ Error generating Days 1–15: {e}")
        return None

    # ── Call 3: Days 16–30 ───────────────────────────────────────────────────
    try:
        with st.spinner("📅 Generating Days 16–30..."):
            chunk2 = _plan_chunk(
                llm, target_role, missing_skills, partial_gaps, priority_order,
                daily_hours, difficulty_level, guidance,
                day_start=16, day_end=30,
                phase_label="Intermediate hands-on practice (Days 16-20), advanced concepts and mini-projects (Days 21-30)"
            )
            days_16_30 = chunk2.get('daily_plan', []) if chunk2 else []
    except Exception as e:
        st.error(f"❌ Error generating Days 16–30: {e}")
        return None

    all_days = days_1_15 + days_16_30
    if not all_days:
        st.error("❌ Could not generate the learning plan. Please try again.")
        return None

    return {"plan_summary": plan_summary, "daily_plan": all_days}


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


# ─── Main App ────────────────────────────────────────────────────────────────

def main():

    st.title("🎓 AI Personal Learning Planner")
    st.caption("Get a personalized 30-day learning roadmap based on your current skills and career goals.")
    st.divider()

    # Initialize LLM
    llm = initialize_llm()
    if not llm:
        st.warning("Please configure your GROQ_API_KEY in Streamlit secrets to use this app.")
        st.stop()

    # Session state defaults
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

    # ── Sidebar ──────────────────────────────────────────────────────────────
    with st.sidebar:
        st.header("Your Learning Profile")

        st.markdown("**Quick Start Examples**")
        examples = [
            ("Backend Developer",       "Python, SQL, Git",            "Backend Engineer"),
            ("Data Analyst",            "Excel, Basic SQL, Statistics", "Data Analyst"),
            ("ML Engineer",             "Python, NumPy, Pandas",        "Machine Learning Engineer"),
        ]
        for label, skills, role in examples:
            if st.button(label, use_container_width=True):
                st.session_state.current_skills_input = skills
                st.session_state.target_role_input = role
                st.rerun()

        st.divider()

        st.markdown("**Your Information**")
        current_skills_input = st.text_area(
            "Current Skills (comma-separated)",
            value=st.session_state.current_skills_input,
            placeholder="e.g., Python, SQL, Git, HTML",
            height=90,
            help="List the skills you currently have, separated by commas"
        )
        target_role = st.text_input(
            "Target Role",
            value=st.session_state.target_role_input,
            placeholder="e.g., Data Scientist, Backend Engineer",
            help="The job role you want to work towards"
        )

        st.divider()

        st.markdown("**Learning Preferences**")
        daily_hours = st.select_slider(
            "Daily Time Commitment (hours)",
            options=[0.5, 1, 1.5, 2, 3],
            value=st.session_state.daily_hours,
            help="How many hours per day can you dedicate to learning?"
        )
        difficulty_level = st.selectbox(
            "Difficulty Level",
            ["Beginner", "Intermediate", "Advanced"],
            index=["Beginner", "Intermediate", "Advanced"].index(st.session_state.difficulty_level),
            help="Your current proficiency in this field — shapes both the gap analysis and plan depth"
        )

        diff_desc = {
            "Beginner":     "Plan starts from fundamentals and explains core concepts.",
            "Intermediate": "Plan skips basics and focuses on tools and hands-on projects.",
            "Advanced":     "Plan targets architecture, performance, and production-grade skills.",
        }
        st.caption(diff_desc[difficulty_level])

        st.divider()

        generate_btn = st.button("🚀 Generate My Learning Plan", type="primary", use_container_width=True)

        if generate_btn:
            if not current_skills_input.strip():
                st.error("Please enter your current skills.")
            elif not target_role.strip():
                st.error("Please enter your target role.")
            else:
                st.session_state.current_skills_input = current_skills_input
                st.session_state.target_role_input    = target_role
                st.session_state.daily_hours          = daily_hours
                st.session_state.difficulty_level     = difficulty_level
                st.session_state.gap_analysis         = None
                st.session_state.learning_plan        = None

                current_skills = normalize_skills(current_skills_input)

                gap_analysis = analyze_skill_gap(llm, current_skills, target_role, difficulty_level)
                if gap_analysis:
                    st.session_state.gap_analysis = gap_analysis
                    learning_plan = generate_learning_plan(llm, gap_analysis, target_role, daily_hours, difficulty_level)
                    if learning_plan:
                        st.session_state.learning_plan = learning_plan
                        st.success("✅ Your plan is ready!")
                        st.rerun()

        # Show current plan summary in sidebar
        if st.session_state.gap_analysis and st.session_state.learning_plan:
            st.divider()
            st.markdown("**Current Plan**")
            st.markdown(f"- 🎯 Role: {st.session_state.target_role_input}")
            st.markdown(f"- ⏱ Hours/day: {st.session_state.daily_hours}")
            st.markdown(f"- 📊 Level: {st.session_state.difficulty_level}")

    # ── Main Content ─────────────────────────────────────────────────────────

    if st.session_state.gap_analysis and st.session_state.learning_plan:

        gap_analysis     = st.session_state.gap_analysis
        learning_plan    = st.session_state.learning_plan
        current_skills   = normalize_skills(st.session_state.current_skills_input)
        target_role      = st.session_state.target_role_input
        daily_hours      = st.session_state.daily_hours
        difficulty_level = st.session_state.difficulty_level

        tab1, tab2, tab3 = st.tabs(["📊 Skill Gap Analysis", "📅 30-Day Plan", "📥 Export"])

        # ── Tab 1: Skill Gap Analysis ─────────────────────────────────────────
        with tab1:
            st.header("Skill Gap Analysis")

            col1, col2 = st.columns(2)

            with col1:
                st.subheader("✅ Skills You Already Have")
                matched = gap_analysis.get('skills_matched', [])
                if matched:
                    for skill in matched:
                        st.success(f"✓ {skill}")
                else:
                    st.info("No matching skills identified")

                st.subheader("🔄 Skills That Need Improvement")
                partial = gap_analysis.get('partial_gaps', [])
                if partial:
                    for skill in partial:
                        st.warning(f"~ {skill}")
                else:
                    st.info("No partial gaps identified")

            with col2:
                st.subheader("📚 Skills You Need to Learn")
                missing = gap_analysis.get('missing_skills', [])
                if missing:
                    for skill in missing:
                        st.error(f"✗ {skill}")
                else:
                    st.info("No missing skills — you're well prepared!")

                st.subheader("🎯 Learning Priority Order")
                priority = gap_analysis.get('learning_priority', [])
                if priority:
                    for i, skill in enumerate(priority[:6], 1):
                        st.markdown(f"**{i}.** {skill}")

            st.divider()
            st.subheader("💡 Why These Skills Matter")
            st.info(gap_analysis.get('reasoning', 'No reasoning provided'))

        # ── Tab 2: 30-Day Plan ────────────────────────────────────────────────
        with tab2:
            st.header("Your 30-Day Learning Journey")

            summary = learning_plan.get('plan_summary', {})

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Days", 30)
            col2.metric("Focus Areas", len(summary.get('focus_areas', [])))
            col3.metric("Hours / Day", daily_hours)
            col4.metric("Level", difficulty_level)

            st.subheader("Focus Areas")
            for area in summary.get('focus_areas', []):
                st.markdown(f"- {area}")

            st.divider()

            st.subheader("Weekly Milestones")
            milestones = summary.get('weekly_milestones', [])
            for i, milestone in enumerate(milestones, 1):
                st.markdown(f"**Week {i}:** {milestone}")

            st.divider()

            st.subheader("Daily Schedule")
            daily_plans = learning_plan.get('daily_plan', [])
            week_groups = {
                "Week 1 — Foundations (Days 1–7)":             daily_plans[0:7],
                "Week 2 — Building Up (Days 8–14)":            daily_plans[7:14],
                "Week 3 — Hands-On Practice (Days 15–21)":     daily_plans[14:21],
                "Week 4 — Advanced & Projects (Days 22–30)":   daily_plans[21:30],
            }

            for week_name, week_plans in week_groups.items():
                with st.expander(week_name, expanded=(week_name.startswith("Week 1"))):
                    for day_plan in week_plans:
                        st.markdown(f"### Day {day_plan.get('day', '')}: {day_plan.get('objective', '')}")

                        st.markdown(f"**Topics:** {', '.join(day_plan.get('topics', []))}")

                        st.markdown("**Tasks:**")
                        for task in day_plan.get('tasks', []):
                            st.markdown(f"- [ ] {task}")

                        st.markdown("**Resources:**")
                        for resource in day_plan.get('resources', []):
                            st.markdown(f"- {resource}")

                        st.caption(f"⏱ {day_plan.get('time_breakdown', 'Time not specified')}")
                        st.divider()

        # ── Tab 3: Export ─────────────────────────────────────────────────────
        with tab3:
            st.header("Export Your Learning Plan")
            st.write("Download your personalized plan in your preferred format.")

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("#### 📄 Markdown (.md)")
                st.caption("Best for GitHub, Notion, Obsidian, and other Markdown viewers.")
                md_content = export_to_markdown(gap_analysis, learning_plan, target_role, current_skills, daily_hours, difficulty_level)
                st.download_button(
                    label="⬇️ Download Markdown",
                    data=md_content,
                    file_name=f"learning_plan_{target_role.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.md",
                    mime="text/markdown",
                    use_container_width=True
                )

            with col2:
                st.markdown("#### 📝 Plain Text (.txt)")
                st.caption("Universal format — works in any text editor or notes app.")
                txt_content = export_to_text(gap_analysis, learning_plan, target_role, current_skills, daily_hours, difficulty_level)
                st.download_button(
                    label="⬇️ Download Text",
                    data=txt_content,
                    file_name=f"learning_plan_{target_role.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.txt",
                    mime="text/plain",
                    use_container_width=True
                )

            st.divider()
            st.info("💡 Tip: Save your plan and tick off tasks daily. Consistent 1-hour sessions beat occasional marathon study.")

    else:
        # ── Welcome Screen ────────────────────────────────────────────────────
        st.markdown("## Welcome! 👋")
        st.write("This AI-powered planner creates a personalized 30-day roadmap to help you reach your career goals.")

        st.divider()

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown("**1️⃣ Enter your skills**")
            st.caption("Tell us what you already know.")
        with col2:
            st.markdown("**2️⃣ Set your target role**")
            st.caption("Where do you want to be?")
        with col3:
            st.markdown("**3️⃣ Choose level & hours**")
            st.caption("We'll pace the plan for you.")
        with col4:
            st.markdown("**4️⃣ Get your roadmap**")
            st.caption("A full 30-day day-by-day plan.")

        st.divider()

        st.markdown("### What you'll get")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown("**📊 Skill Gap Analysis**")
            st.caption("See what you know, what needs work, and what to learn next.")
        with col2:
            st.markdown("**📅 30-Day Daily Plan**")
            st.caption("Structured day-by-day schedule with clear objectives.")
        with col3:
            st.markdown("**📚 Curated Resources**")
            st.caption("Real tutorials, docs, and courses — not generic advice.")
        with col4:
            st.markdown("**📥 Export Your Plan**")
            st.caption("Download as Markdown or Text to use anywhere.")

        st.divider()
        st.info("👈 Use the sidebar to enter your skills and target role, then click Generate.")


if __name__ == "__main__":
    main()
