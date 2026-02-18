import streamlit as st
import os
from datetime import datetime, timedelta
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
    if key_name in st.secrets:
        return st.secrets[key_name]
    elif key_name in os.environ:
        return os.environ[key_name]
    else:
        st.error(f"Missing API key: {key_name}. Please add it to your secrets.")
        return None


def initialize_llm():
    """Initialize the LLM (Groq)"""
    api_key = get_api_key("GROQ_API_KEY")
    if not api_key:
        return None
    
    return ChatGroq(
        api_key=api_key,
        model='llama-3.3-70b-versatile',
        temperature=0.7
    )


def normalize_skills(skills_input):
    """Normalize and clean skill inputs"""
    if not skills_input:
        return []
    
    # Split by comma and clean
    skills = [s.strip() for s in skills_input.split(',')]
    skills = [s for s in skills if s]  # Remove empty strings
    return skills


def analyze_skill_gap(llm, current_skills, target_role):
    """Analyze skill gaps between current skills and target role"""
    
    prompt_template = """
You are an expert career advisor analyzing skill gaps for career development.

Target Role: {target_role}
Current Skills: {current_skills}

Analyze the skill gap and provide a structured response in the following JSON format:

{{
    "required_skills": ["skill1", "skill2", "skill3", ...],
    "skills_matched": ["matched_skill1", "matched_skill2", ...],
    "partial_gaps": ["skill_that_needs_improvement1", ...],
    "missing_skills": ["completely_missing_skill1", "completely_missing_skill2", ...],
    "learning_priority": ["highest_priority_skill", "second_priority", ...],
    "reasoning": "Brief explanation of why these skills matter for this role"
}}

Be specific and realistic. Focus on technical skills, tools, and frameworks commonly required for {target_role}.
Order missing_skills and learning_priority from most fundamental to most advanced.

Respond ONLY with valid JSON. No additional text.
"""
    
    prompt = ChatPromptTemplate.from_template(prompt_template)
    
    try:
        with st.spinner("Analyzing skill gaps..."):
            formatted_prompt = prompt.format(
                target_role=target_role,
                current_skills=", ".join(current_skills)
            )
            
            response = llm.invoke(formatted_prompt)
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                gap_analysis = json.loads(json_match.group())
                return gap_analysis
            else:
                st.error("Failed to parse skill gap analysis")
                return None
                
    except Exception as e:
        st.error(f"Error during skill gap analysis: {e}")
        return None


def generate_learning_plan(llm, gap_analysis, target_role, daily_hours=1):
    """Generate a structured 30-day learning plan"""
    
    prompt_template = """
You are an expert learning path designer creating personalized 30-day learning plans.

Target Role: {target_role}
Missing Skills to Learn: {missing_skills}
Skills That Need Improvement: {partial_gaps}
Learning Priority Order: {priority_order}
Daily Time Available: {daily_hours} hour(s)

Create a detailed 30-day learning plan with the following structure:

For each day (Day 1 to Day 30), provide:
- Day number
- Clear learning objective
- Topics to cover
- Specific tasks (2-4 actionable tasks)
- Recommended resources (articles, documentation, tutorials with actual names)
- Estimated time breakdown

Organize the plan logically:
- Days 1-10: Foundational concepts and basics
- Days 11-20: Intermediate topics and hands-on practice
- Days 21-30: Advanced concepts and mini-projects

Make tasks realistic for {daily_hours} hour(s) per day.
Be specific with resource recommendations (mention actual tutorials, documentation sites, or well-known courses).

Output format (respond ONLY with valid JSON):

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
        }},
        ...
    ]
}}

Respond ONLY with valid JSON. No additional text before or after.
"""
    
    prompt = ChatPromptTemplate.from_template(prompt_template)
    
    try:
        with st.spinner("Generating your personalized 30-day learning plan..."):
            formatted_prompt = prompt.format(
                target_role=target_role,
                missing_skills=", ".join(gap_analysis.get('missing_skills', [])),
                partial_gaps=", ".join(gap_analysis.get('partial_gaps', [])),
                priority_order=", ".join(gap_analysis.get('learning_priority', [])),
                daily_hours=daily_hours
            )
            
            response = llm.invoke(formatted_prompt)
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            # Extract JSON
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                learning_plan = json.loads(json_match.group())
                return learning_plan
            else:
                st.error("Failed to parse learning plan")
                return None
                
    except Exception as e:
        st.error(f"Error generating learning plan: {e}")
        return None


def export_to_markdown(gap_analysis, learning_plan, target_role, current_skills):
    """Export learning plan to Markdown format"""
    
    md_content = f"""# AI Personal Learning Planner

**Generated on:** {datetime.now().strftime('%B %d, %Y')}

## Your Profile
- **Target Role:** {target_role}
- **Current Skills:** {', '.join(current_skills)}

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

### Overview
**Focus Areas:** {', '.join(learning_plan.get('plan_summary', {}).get('focus_areas', []))}

### Weekly Milestones
"""
    
    for i, milestone in enumerate(learning_plan.get('plan_summary', {}).get('weekly_milestones', []), 1):
        md_content += f"- **Week {i}:** {milestone}\n"
    
    md_content += "\n---\n\n## Daily Learning Schedule\n\n"
    
    for day_plan in learning_plan.get('daily_plan', []):
        day_num = day_plan.get('day', 0)
        md_content += f"""### Day {day_num}: {day_plan.get('objective', 'No objective')}

**Topics:** {', '.join(day_plan.get('topics', []))}

**Tasks:**
"""
        for task in day_plan.get('tasks', []):
            md_content += f"- [ ] {task}\n"
        
        md_content += f"\n**Resources:**\n"
        for resource in day_plan.get('resources', []):
            md_content += f"- {resource}\n"
        
        md_content += f"\n**Time Breakdown:** {day_plan.get('time_breakdown', 'Not specified')}\n\n---\n\n"
    
    return md_content


def export_to_text(gap_analysis, learning_plan, target_role, current_skills):
    """Export learning plan to plain text format"""
    
    txt_content = f"""AI PERSONAL LEARNING PLANNER
Generated on: {datetime.now().strftime('%B %d, %Y')}

═══════════════════════════════════════════════════════════════

YOUR PROFILE
Target Role: {target_role}
Current Skills: {', '.join(current_skills)}

═══════════════════════════════════════════════════════════════

SKILL GAP ANALYSIS

✓ Skills You Already Have:
  {', '.join(gap_analysis.get('skills_matched', ['None identified']))}

○ Skills That Need Improvement:
  {', '.join(gap_analysis.get('partial_gaps', ['None identified']))}

✗ Skills You Need to Learn:
  {', '.join(gap_analysis.get('missing_skills', ['None identified']))}

Why These Skills Matter:
{gap_analysis.get('reasoning', 'No reasoning provided')}

═══════════════════════════════════════════════════════════════

30-DAY LEARNING PLAN

Overview:
Focus Areas: {', '.join(learning_plan.get('plan_summary', {}).get('focus_areas', []))}

Weekly Milestones:
"""
    
    for i, milestone in enumerate(learning_plan.get('plan_summary', {}).get('weekly_milestones', []), 1):
        txt_content += f"Week {i}: {milestone}\n"
    
    txt_content += "\n═══════════════════════════════════════════════════════════════\n\nDAILY LEARNING SCHEDULE\n\n"
    
    for day_plan in learning_plan.get('daily_plan', []):
        day_num = day_plan.get('day', 0)
        txt_content += f"""
DAY {day_num}: {day_plan.get('objective', 'No objective')}
{'─' * 60}

Topics: {', '.join(day_plan.get('topics', []))}

Tasks:
"""
        for i, task in enumerate(day_plan.get('tasks', []), 1):
            txt_content += f"  {i}. {task}\n"
        
        txt_content += f"\nResources:\n"
        for resource in day_plan.get('resources', []):
            txt_content += f"  • {resource}\n"
        
        txt_content += f"\nTime Breakdown: {day_plan.get('time_breakdown', 'Not specified')}\n"
    
    return txt_content


# ─── Main App ────────────────────────────────────────────────────────────────

def main():
    # Header
    st.title("🎓 AI Personal Learning Planner")
    st.markdown("*Get a personalized 30-day learning roadmap to achieve your career goals*")
    st.markdown("---")
    
    # Initialize LLM
    llm = initialize_llm()
    if not llm:
        st.warning("Please configure your GROQ_API_KEY in Streamlit secrets to use this app.")
        st.stop()
    
    # Initialize session state
    if 'gap_analysis' not in st.session_state:
        st.session_state.gap_analysis = None
    if 'learning_plan' not in st.session_state:
        st.session_state.learning_plan = None
    if 'current_skills_input' not in st.session_state:
        st.session_state.current_skills_input = ""
    if 'target_role_input' not in st.session_state:
        st.session_state.target_role_input = ""
    
    # Sidebar - Input Section
    with st.sidebar:
        st.header("📝 Your Learning Profile")
        
        # Sample inputs
        st.markdown("### Quick Start Examples")
        if st.button("🔹 Example 1: Backend Developer"):
            st.session_state.current_skills_input = "Python, SQL, Git"
            st.session_state.target_role_input = "Backend Engineer"
            st.rerun()
        
        if st.button("🔹 Example 2: Data Analyst"):
            st.session_state.current_skills_input = "Excel, Basic SQL, Statistics"
            st.session_state.target_role_input = "Data Analyst"
            st.rerun()
        
        if st.button("🔹 Example 3: ML Engineer"):
            st.session_state.current_skills_input = "Python, NumPy, Pandas"
            st.session_state.target_role_input = "Machine Learning Engineer"
            st.rerun()
        
        st.markdown("---")
        
        # User inputs
        st.markdown("### Your Information")
        
        current_skills_input = st.text_area(
            "Current Skills (comma-separated)",
            value=st.session_state.current_skills_input,
            placeholder="e.g., Python, SQL, Git, HTML, CSS",
            height=100,
            help="List the skills you currently have, separated by commas"
        )
        
        target_role = st.text_input(
            "Target Role",
            value=st.session_state.target_role_input,
            placeholder="e.g., Data Scientist, Full Stack Developer",
            help="The job role you want to work towards"
        )
        
        st.markdown("### Learning Preferences")
        
        daily_hours = st.select_slider(
            "Daily Time Commitment",
            options=[0.5, 1, 1.5, 2, 3],
            value=1,
            help="How many hours per day can you dedicate to learning?"
        )
        
        difficulty_level = st.selectbox(
            "Starting Difficulty Level",
            ["Beginner", "Intermediate", "Advanced"],
            index=0,
            help="Your current proficiency level in the field"
        )
        
        st.markdown("---")
        
        # Generate button
        generate_btn = st.button("🚀 Generate My Learning Plan", type="primary", use_container_width=True)
        
        if generate_btn:
            # Validation
            if not current_skills_input.strip():
                st.error("⚠️ Please enter your current skills")
            elif not target_role.strip():
                st.error("⚠️ Please enter your target role")
            else:
                # Save to session state
                st.session_state.current_skills_input = current_skills_input
                st.session_state.target_role_input = target_role
                
                # Normalize skills
                current_skills = normalize_skills(current_skills_input)
                
                # Step 1: Analyze skill gap
                gap_analysis = analyze_skill_gap(llm, current_skills, target_role)
                
                if gap_analysis:
                    st.session_state.gap_analysis = gap_analysis
                    
                    # Step 2: Generate learning plan
                    learning_plan = generate_learning_plan(
                        llm, 
                        gap_analysis, 
                        target_role, 
                        daily_hours
                    )
                    
                    if learning_plan:
                        st.session_state.learning_plan = learning_plan
                        st.success("✅ Learning plan generated successfully!")
                        st.rerun()
    
    # Main Content Area
    if st.session_state.gap_analysis and st.session_state.learning_plan:
        gap_analysis = st.session_state.gap_analysis
        learning_plan = st.session_state.learning_plan
        current_skills = normalize_skills(st.session_state.current_skills_input)
        target_role = st.session_state.target_role_input
        
        # Display tabs
        tab1, tab2, tab3 = st.tabs(["📊 Skill Gap Analysis", "📅 30-Day Plan", "📥 Export"])
        
        # Tab 1: Skill Gap Analysis
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
                        st.warning(f"○ {skill}")
                else:
                    st.info("No partial gaps identified")
            
            with col2:
                st.subheader("📚 Skills You Need to Learn")
                missing = gap_analysis.get('missing_skills', [])
                if missing:
                    for skill in missing:
                        st.error(f"✗ {skill}")
                else:
                    st.info("No missing skills identified")
                
                st.subheader("🎯 Learning Priority")
                priority = gap_analysis.get('learning_priority', [])
                if priority:
                    for i, skill in enumerate(priority[:5], 1):
                        st.markdown(f"**{i}.** {skill}")
            
            st.markdown("---")
            st.subheader("💡 Why These Skills Matter")
            st.info(gap_analysis.get('reasoning', 'No reasoning provided'))
        
        # Tab 2: 30-Day Plan
        with tab2:
            st.header("Your 30-Day Learning Journey")
            
            # Summary
            summary = learning_plan.get('plan_summary', {})
            
            st.subheader("📋 Plan Overview")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Days", summary.get('total_days', 30))
            with col2:
                st.metric("Focus Areas", len(summary.get('focus_areas', [])))
            
            st.markdown("**Focus Areas:**")
            for area in summary.get('focus_areas', []):
                st.markdown(f"- {area}")
            
            st.markdown("---")
            
            # Weekly Milestones
            st.subheader("🎯 Weekly Milestones")
            milestones = summary.get('weekly_milestones', [])
            for i, milestone in enumerate(milestones, 1):
                st.markdown(f"**Week {i}:** {milestone}")
            
            st.markdown("---")
            
            # Daily Plan
            st.subheader("📅 Daily Learning Schedule")
            
            daily_plans = learning_plan.get('daily_plan', [])
            
            # Group by weeks
            weeks = {
                "Week 1 (Days 1-7)": daily_plans[0:7],
                "Week 2 (Days 8-14)": daily_plans[7:14],
                "Week 3 (Days 15-21)": daily_plans[14:21],
                "Week 4 (Days 22-30)": daily_plans[21:30]
            }
            
            for week_name, week_plans in weeks.items():
                with st.expander(f"📖 {week_name}", expanded=(week_name == "Week 1 (Days 1-7)")):
                    for day_plan in week_plans:
                        day_num = day_plan.get('day', 0)
                        
                        st.markdown(f"### Day {day_num}: {day_plan.get('objective', '')}")
                        
                        st.markdown("**Topics:**")
                        st.markdown(", ".join(day_plan.get('topics', [])))
                        
                        st.markdown("**Tasks:**")
                        for task in day_plan.get('tasks', []):
                            st.markdown(f"- [ ] {task}")
                        
                        st.markdown("**Resources:**")
                        for resource in day_plan.get('resources', []):
                            st.markdown(f"- {resource}")
                        
                        st.caption(f"⏱️ {day_plan.get('time_breakdown', 'Time not specified')}")
                        st.markdown("---")
        
        # Tab 3: Export
        with tab3:
            st.header("📥 Export Your Learning Plan")
            
            st.markdown("Download your personalized learning plan in your preferred format:")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Markdown export
                md_content = export_to_markdown(
                    gap_analysis, 
                    learning_plan, 
                    target_role, 
                    current_skills
                )
                
                st.download_button(
                    label="📄 Download as Markdown (.md)",
                    data=md_content,
                    file_name=f"learning_plan_{target_role.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.md",
                    mime="text/markdown",
                    use_container_width=True
                )
            
            with col2:
                # Text export
                txt_content = export_to_text(
                    gap_analysis, 
                    learning_plan, 
                    target_role, 
                    current_skills
                )
                
                st.download_button(
                    label="📝 Download as Text (.txt)",
                    data=txt_content,
                    file_name=f"learning_plan_{target_role.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
            
            st.markdown("---")
            st.info("💡 **Tip:** Save this plan and track your daily progress. Set reminders to stay consistent!")
    
    else:
        # Welcome screen
        st.markdown("""
        ## Welcome! 👋
        
        This AI-powered learning planner helps you create a **personalized 30-day roadmap** to achieve your career goals.
        
        ### How it works:
        
        1. **Tell us your current skills** - What do you already know?
        2. **Share your target role** - Where do you want to be?
        3. **Get your plan** - Receive a detailed day-by-day learning schedule
        
        ### What you'll get:
        
        ✅ **Skill Gap Analysis** - See exactly what you need to learn  
        ✅ **30-Day Structured Plan** - Daily tasks and objectives  
        ✅ **Curated Resources** - Specific tutorials and documentation  
        ✅ **Downloadable Format** - Export as Markdown or Text  
        
        ---
        
        ### 🚀 Get Started
        
        Use the sidebar on the left to:
        - Try a **quick start example**, or
        - Enter your own skills and target role
        
        Then click **"Generate My Learning Plan"** to begin your journey!
        """)
        
        # Feature highlights
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("### 🎯 Personalized")
            st.markdown("Plans tailored to your current skill level and learning pace")
        
        with col2:
            st.markdown("### 📚 Structured")
            st.markdown("Day-by-day breakdown with clear objectives and tasks")
        
        with col3:
            st.markdown("### 🔗 Resourceful")
            st.markdown("Curated learning materials and hands-on practice")


if __name__ == "__main__":
    main()
