ALLOWED_ACTIONS = {"navigate", "input", "click", "check", "wait"}

def validate_steps(steps):
    """
    Guardrail to validate AI-generated test steps
    before Selenium execution.
    """
    if not isinstance(steps, list):
        return False, "Steps must be a list"

    for step in steps:
        if "action" not in step:
            return False, "Missing action"

        if step["action"] not in ALLOWED_ACTIONS:
            return False, f"Invalid action: {step['action']}"

        if step["action"] in {"input", "click", "check"}:
            if "selector" not in step:
                return False, "Missing selector"

    return True, "Valid steps"


def evaluate(result, reason):
    if result == "PASS":
        return "Test passed. Observed behavior matches the requirement."
    else:
        return f"Test failed. {reason}"