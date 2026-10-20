# Helper functions for formatting placement-grade interview Q&A
import html

def make_tech_ans(concept, tech, tip):
    """Formats technical interview questions with 3 structured placement tiers."""
    return (
        f"<div class='iv-ans-block'>"
        f"<div class='iv-lead'><strong>💡 Core Concept:</strong> {concept}</div>"
        f"<div class='iv-tech'><strong>⚙️ Technical Mechanics &amp; Details:</strong> {tech}</div>"
        f"<div class='iv-tips'><strong>🎯 Interviewer Key Takeaway &amp; Traps:</strong> {tip}</div>"
        f"</div>"
    )

def make_puzzle_ans(logic, step_by_step, takeaway):
    """Formats logical reasoning and math puzzles."""
    return (
        f"<div class='iv-ans-block iv-puzzle-block'>"
        f"<div class='iv-lead'><strong>🧠 Key Logical Insight:</strong> {logic}</div>"
        f"<div class='iv-tech'><strong>🧩 Step-by-Step Analytical Deduction:</strong> {step_by_step}</div>"
        f"<div class='iv-tips'><strong>💡 Interviewer Takeaway &amp; Generalization:</strong> {takeaway}</div>"
        f"</div>"
    )

def make_hr_ans(intent, framework, model_answer, mistakes):
    """Formats behavioral and personal HR questions."""
    return (
        f"<div class='iv-ans-block iv-behavioral-block'>"
        f"<div class='iv-intent'><strong>🧠 What the Interviewer is Really Evaluating:</strong> {intent}</div>"
        f"<div class='iv-framework'><strong>📐 Recommended Answering Framework:</strong> {framework}</div>"
        f"<div class='iv-model'><strong>💬 Word-for-Word Exemplar Model Answer:</strong><br><em>\"{model_answer}\"</em></div>"
        f"<div class='iv-mistakes'><strong>⚠️ Fatal Mistakes &amp; Red Flags to Avoid:</strong> {mistakes}</div>"
        f"</div>"
    )
