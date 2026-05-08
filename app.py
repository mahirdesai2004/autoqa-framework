import streamlit as st
from ai_agent import generate_test_steps, explain_failure
from selenium_runner import run_test
from evaluation_layer import evaluate, validate_steps
from notifier import notify_user

st.title("AutoQA: AI Test Automation")

requirement = st.text_area(
    "Enter software requirement:",
    "User should not be able to login with wrong password"
)

test_url = st.text_input(
    "Enter website URL to test:",
    "http://localhost:8000"
)

if st.button("Run AI QA Test"):
    try:
        with st.spinner("🔍 Analyzing page and generating test steps..."):
            steps = generate_test_steps(requirement, test_url)
        st.subheader("Generated Test Steps")
        st.json(steps)
    except Exception as e:
        st.error(f"Error generating test steps: {str(e)}")
        st.stop()

    is_valid, msg = validate_steps(steps)
    if not is_valid:
        st.error(f"AI output validation failed: {msg}")
        notify_user(f"AI output validation failed: {msg}")
        st.stop()

    result, reason, screenshot_path = run_test(steps, test_url)
    st.subheader("Test Result")
    st.write(result)

    st.subheader("AI Explanation")

    if result == "PASS":
        st.write(evaluate(result, reason))
    else:
        detailed_explanation = explain_failure(requirement, steps, reason)
        st.write(detailed_explanation)

    if screenshot_path:
        st.subheader("📸 Test Screenshot")
        st.image(screenshot_path)
        notify_user(f"Screenshot captured at {screenshot_path}")

    notify_user(f"Test completed with status: {result}")
