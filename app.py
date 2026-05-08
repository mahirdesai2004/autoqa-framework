import streamlit as st
import os
from ai_agent import generate_test_steps, explain_failure
from selenium_runner import run_test
from evaluation_layer import evaluate, validate_steps
from notifier import notify_user

# --- PAGE CONFIG ---
st.set_page_config(page_title="AutoQA Dashboard", page_icon="⚡", layout="wide")

# --- CUSTOM CSS INJECTION ---
st.markdown("""
<style>
/* Base Theme overrides for robust dark mode */
.stApp {
    background-color: #0b0f19;
    background-image: radial-gradient(rgba(255, 255, 255, 0.05) 1px, transparent 1px);
    background-size: 20px 20px;
    color: #e2e8f0;
}

/* Floating Ambient Blobs */
.blob1, .blob2 {
    position: fixed;
    border-radius: 50%;
    filter: blur(120px);
    z-index: -1;
    opacity: 0.4;
    animation: float 20s infinite ease-in-out alternate;
}
.blob1 {
    width: 600px;
    height: 600px;
    background: #3b82f6;
    top: -200px;
    left: -200px;
}
.blob2 {
    width: 500px;
    height: 500px;
    background: #8b5cf6;
    bottom: -100px;
    right: -100px;
    animation-delay: -10s;
}

@keyframes float {
    0% { transform: translate(0, 0) scale(1); }
    100% { transform: translate(60px, 60px) scale(1.1); }
}

/* Hero Section */
.hero-container {
    padding-top: 2rem;
    padding-bottom: 1rem;
}
.hero-title {
    font-size: 3.5rem;
    font-weight: 800;
    background: linear-gradient(90deg, #60a5fa, #c084fc);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.2rem;
    line-height: 1.2;
}
.hero-subtitle {
    color: #94a3b8;
    font-size: 1.1rem;
    font-weight: 400;
    margin-bottom: 1.5rem;
}

/* Status Badges */
.badge-container {
    display: flex;
    gap: 10px;
    margin-bottom: 2.5rem;
    flex-wrap: wrap;
}
.badge {
    padding: 0.3rem 0.8rem;
    border-radius: 999px;
    font-size: 0.85rem;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 6px;
}
.badge-green {
    background: rgba(16, 185, 129, 0.1);
    color: #34d399;
    border: 1px solid rgba(16, 185, 129, 0.2);
}
.badge-blue {
    background: rgba(59, 130, 246, 0.1);
    color: #60a5fa;
    border: 1px solid rgba(59, 130, 246, 0.2);
}

/* Glassmorphism Inputs */
div[data-testid="stTextInput"] > div:first-child,
div[data-testid="stTextArea"] > div:first-child {
    background: rgba(30, 41, 59, 0.6) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    backdrop-filter: blur(12px);
    border-radius: 8px;
    color: white !important;
}

/* Premium Button */
div[data-testid="stButton"] button {
    background: linear-gradient(90deg, #3b82f6, #8b5cf6) !important;
    border: none !important;
    color: white !important;
    font-weight: 600 !important;
    padding: 0.6rem 2rem !important;
    border-radius: 8px !important;
    transition: all 0.3s ease !important;
}
div[data-testid="stButton"] button:hover {
    box-shadow: 0 0 20px rgba(139, 92, 246, 0.6) !important;
    transform: translateY(-2px) !important;
}

/* JSON / Code Blocks */
pre {
    background: rgba(15, 23, 42, 0.8) !important;
    border: 1px solid rgba(255,255,255,0.05) !important;
    border-radius: 8px !important;
}
</style>

<!-- Inject Ambient Background Elements -->
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
<div class="hero-container">
    <div class="hero-title">AutoQA Engine</div>
    <div class="hero-subtitle">Agentic DOM Parsing & Multi-Provider LLM Orchestration</div>
    <div class="badge-container">
        <div class="badge badge-green">
            <span style="font-size: 10px;">🟢</span> System Online
        </div>
        <div class="badge badge-blue">
            <span style="font-size: 10px;">🧠</span> Active Routing: {provider_text}
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# --- INPUT SECTION ---
col1, col2 = st.columns([2, 1])

with col1:
    requirement = st.text_area(
        "Software Requirement Context",
        "User should not be able to login with wrong password",
        height=120
    )

with col2:
    test_url = st.text_input(
        "Target Validation URL",
        "http://localhost:8000"
    )

st.markdown("<br>", unsafe_allow_html=True)

# --- EXECUTION PIPELINE ---
if st.button("🚀 Initialize QA Automation"):
    try:
        with st.spinner("🤖 Orchestrator analyzing DOM and generating execution plan..."):
            steps = generate_test_steps(requirement, test_url)
            
        st.markdown("### 📋 Generated Execution Plan")
        st.json(steps)
    except Exception as e:
        st.error(f"Execution Pipeline Halted: {str(e)}")
        st.stop()

    is_valid, msg = validate_steps(steps)
    if not is_valid:
        st.error(f"Validation Error: {msg}")
        notify_user(f"AI output validation failed: {msg}")
        st.stop()

    with st.spinner("⚡ Injecting Selenium WebDrivers and executing..."):
        result, reason, screenshot_path = run_test(steps, test_url)
        
    st.markdown("---")
    st.markdown("### 🔬 Execution Telemetry")
    
    if result == "PASS":
        st.success("✅ Test Validation Passed")
        st.markdown(f"**Diagnostic Output:**\n{evaluate(result, reason)}")
    else:
        st.error(f"❌ Test Validation Failed: {reason}")
        st.markdown("### 🩺 Root Cause Analysis (AI Diagnostic)")
        try:
            with st.spinner("Generating deep failure analysis..."):
                detailed_explanation = explain_failure(requirement, steps, reason)
            st.info(detailed_explanation)
        except Exception as e:
            st.warning(f"Failed to generate diagnostic report: {str(e)}")

    if screenshot_path:
        st.markdown("### 📸 Final DOM Snapshot")
        st.image(screenshot_path, use_container_width=True)
        notify_user(f"Screenshot captured at {screenshot_path}")

    notify_user(f"Test completed with status: {result}")
