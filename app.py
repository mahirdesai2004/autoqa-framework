import sys
import os
sys.path.insert(0, os.path.abspath("backend"))

import streamlit as st
from ai_agent import generate_test_steps, explain_failure
from selenium_runner import run_test
from evaluation_layer import evaluate, validate_steps
from notifier import notify_user

# --- PAGE CONFIG ---
st.set_page_config(page_title="AutoQA | AI Test Automation", page_icon="⚡", layout="centered")

# --- CUSTOM CSS INJECTION ---
st.markdown("""
<style>
/* Adaptive Color Variables (Relying on Streamlit's Native Theme Options) */
:root {
    --glass-bg: rgba(150, 150, 150, 0.05);
    --glass-border: rgba(150, 150, 150, 0.15);
    --hover-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
}

@media (prefers-color-scheme: dark) {
    :root {
        --glass-bg: rgba(30, 41, 59, 0.4);
        --glass-border: rgba(255, 255, 255, 0.1);
        --hover-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    }
}

/* Base Clean Subdued Background (Overrides previous aggressive black) */
.stApp {
    background-image: radial-gradient(var(--glass-border) 1px, transparent 1px);
    background-size: 24px 24px;
}

/* Subtle Floating Ambient Gloom (Highly Opacity Reduced) */
.blob1, .blob2 {
    position: fixed;
    border-radius: 50%;
    filter: blur(140px);
    z-index: -1;
    opacity: 0.15; /* Subdued for readability */
    animation: float 30s infinite ease-in-out alternate;
}
.blob1 {
    width: 600px; height: 600px;
    background: #3b82f6;
    top: -200px; left: -200px;
}
.blob2 {
    width: 500px; height: 500px;
    background: #8b5cf6;
    bottom: -100px; right: -100px;
    animation-delay: -15s;
}

@keyframes float {
    0% { transform: translate(0, 0) scale(1); }
    100% { transform: translate(30px, 30px) scale(1.05); }
}

/* Vercel-Style Typography & Hierarchy */
.header-container {
    text-align: center;
    margin-top: 1rem;
    margin-bottom: 2.5rem;
}
.hero-title {
    font-size: 2.5rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    margin-bottom: 0.5rem;
}
.hero-subtitle {
    font-size: 1.05rem;
    color: #64748b;
    font-weight: 400;
}

/* Elegant Badges */
.badge-group {
    display: flex;
    justify-content: center;
    gap: 12px;
    margin-top: 1.2rem;
}
.saas-badge {
    padding: 0.25rem 0.75rem;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    display: flex;
    align-items: center;
    gap: 6px;
    background: var(--glass-bg);
    border: 1px solid var(--glass-border);
}

/* Input Containers & Forms */
div[data-testid="stForm"] {
    background: var(--glass-bg) !important;
    border: 1px solid var(--glass-border) !important;
    border-radius: 12px !important;
    padding: 2rem !important;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
}

/* Clean Form Inputs */
div[data-testid="stTextInput"] > div:first-child,
div[data-testid="stTextArea"] > div:first-child {
    background: transparent !important;
    border-radius: 6px;
}

/* Premium CTA Button */
div[data-testid="stFormSubmitButton"] button {
    width: 100%;
    background: linear-gradient(135deg, #0f172a, #1e293b) !important;
    color: white !important;
    font-weight: 500 !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 6px !important;
    padding: 0.6rem 0 !important;
    transition: all 0.2s ease !important;
}
@media (prefers-color-scheme: light) {
    div[data-testid="stFormSubmitButton"] button {
        background: linear-gradient(135deg, #ffffff, #f8fafc) !important;
        color: #0f172a !important;
        border: 1px solid #e2e8f0 !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1) !important;
    }
}
div[data-testid="stFormSubmitButton"] button:hover {
    transform: translateY(-1px) !important;
    box-shadow: var(--hover-shadow) !important;
}

/* Result Cards */
.result-card {
    background: var(--glass-bg);
    border: 1px solid var(--glass-border);
    border-radius: 8px;
    padding: 1.5rem;
    margin-top: 1rem;
    margin-bottom: 1rem;
}
</style>

<!-- Inject Ambient Subdued Blobs -->
<div class="blob1"></div>
<div class="blob2"></div>
""", unsafe_allow_html=True)

# --- DETERMINE ACTIVE PROVIDERS ---
configured_providers = []
if os.getenv("GEMINI_API_KEY"): configured_providers.append("Gemini")
if os.getenv("MISTRAL_API_KEY"): configured_providers.append("Mistral")
if os.getenv("GROQ_API_KEY"): configured_providers.append("Groq")
provider_text = " → ".join(configured_providers) if configured_providers else "None Configured"

# --- HERO SECTION ---
st.markdown(f"""
<div class="header-container">
    <div class="hero-title">AutoQA</div>
    <div class="hero-subtitle">Resilient Agentic DOM Parsing & E2E Validation</div>
    <div class="badge-group">
        <div class="saas-badge"><span style="color:#10b981;">●</span> Engine Online</div>
        <div class="saas-badge"><span style="color:#3b82f6;">●</span> Routing: {provider_text}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# --- PRIMARY INPUT CARD (USING FORM FOR BATCHING) ---
with st.form("execution_form", clear_on_submit=False):
    st.markdown("##### Task Configuration")
    requirement = st.text_area(
        "Software Requirement Context",
        "User should be able to search for a product",
        help="Describe what the user should be able to do or what should be validated.",
        height=100
    )
    
    test_url = st.text_input(
        "Target Validation URL",
        "https://example.com",
        help="The fully qualified URL where the test should begin."
    )
    
    submitted = st.form_submit_button("Run Automation Pipeline")

# --- EXECUTION STATUS & PIPELINE ---
if submitted:
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 1. Pipeline Timeline
    with st.status("Initializing Execution Pipeline...", expanded=True) as status:
        st.write("🤖 Orchestrator analyzing DOM and generating execution plan...")
        try:
            steps = generate_test_steps(requirement, test_url)
            st.write("✅ Execution plan generated successfully.")
        except Exception as e:
            status.update(label="Pipeline Halted (Generation Failed)", state="error", expanded=True)
            st.error(f"Execution Pipeline Halted: {str(e)}")
            st.stop()

        st.write("🔍 Validating JSON syntax and safety constraints...")
        is_valid, msg = validate_steps(steps)
        if not is_valid:
            status.update(label="Pipeline Halted (Validation Failed)", state="error", expanded=True)
            st.error(f"Validation Error: {msg}")
            notify_user(f"AI output validation failed: {msg}")
            st.stop()
        st.write("✅ Plan validated. Sandbox secure.")

        st.write("⚡ Injecting Selenium WebDrivers and executing interactions...")
        try:
            result, reason, screenshot_path = run_test(steps, test_url)
            st.write("✅ Browser execution completed.")
            status.update(label="Execution Complete", state="complete", expanded=False)
        except Exception as e:
            status.update(label="Pipeline Halted (Browser Crash)", state="error", expanded=True)
            st.error(f"Browser Execution Failed: {str(e)}")
            st.stop()

    # 2. Results Section
    st.markdown("### 📊 Telemetry Report")
    
    if result == "PASS":
        st.success("✅ **Validation Passed**")
        with st.container():
            st.markdown(f"<div class='result-card'>{evaluate(result, reason)}</div>", unsafe_allow_html=True)
    else:
        st.error(f"❌ **Validation Failed:** {reason}")
        with st.spinner("Generating AI Diagnostic Analysis..."):
            try:
                detailed_explanation = explain_failure(requirement, steps, reason)
                st.markdown(f"**Root Cause Analysis:**\n<div class='result-card'>{detailed_explanation}</div>", unsafe_allow_html=True)
            except Exception as e:
                st.warning(f"Failed to generate diagnostic report: {str(e)}")

    # 3. Artifacts / Logs
    if screenshot_path or steps:
        st.markdown("#### Execution Artifacts")
        col1, col2 = st.columns(2)
        
        with col1:
            if screenshot_path:
                with st.expander("📸 View Final DOM Snapshot", expanded=True):
                    st.image(screenshot_path, use_container_width=True)
                    notify_user(f"Screenshot captured at {screenshot_path}")
        
        with col2:
            if steps:
                with st.expander("🛠️ View Raw JSON Execution Plan"):
                    st.json(steps)

    notify_user(f"Test completed with status: {result}")

# --- FOOTER ---
st.markdown("""
<div style="text-align: center; margin-top: 4rem; padding-top: 1rem; border-top: 1px solid var(--glass-border); color: #64748b; font-size: 0.8rem;">
    AutoQA Framework • Multi-Provider Edge Orchestration • Deployment: Streamlit Cloud
</div>
""", unsafe_allow_html=True)
