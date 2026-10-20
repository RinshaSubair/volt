# Master Builder for 315 Placement-Grade Interview Questions
# Expands repository from 723 to 1,038+ Questions across 5 Structured Pillars:
# 1. Core Engineering (100)
# 2. Software & IT (90)
# 3. AI & Machine Learning (40)
# 4. Logical Reasoning & Puzzles (40)
# 5. Behavioral & HR with Full Coaching & Model Answers (45)

import json, os

def make_tech_ans(concept, tech, tip):
    return (
        f"<div class='iv-ans-block'>"
        f"<div class='iv-lead'><strong>💡 Core Concept:</strong> {concept}</div>"
        f"<div class='iv-tech'><strong>⚙️ Technical Mechanics &amp; Details:</strong> {tech}</div>"
        f"<div class='iv-tips'><strong>🎯 Interviewer Key Takeaway &amp; Traps:</strong> {tip}</div>"
        f"</div>"
    )

def make_hr_ans(intent, framework, model_answer, mistakes):
    return (
        f"<div class='iv-ans-block iv-behavioral-block'>"
        f"<div class='iv-intent'><strong>🧠 What the Interviewer is Really Evaluating:</strong> {intent}</div>"
        f"<div class='iv-framework'><strong>📐 Recommended Answering Framework:</strong> {framework}</div>"
        f"<div class='iv-model'><strong>💬 Word-for-Word Exemplar Model Answer:</strong><br><em>\"{model_answer}\"</em></div>"
        f"<div class='iv-mistakes'><strong>⚠️ Fatal Mistakes &amp; Red Flags to Avoid:</strong> {mistakes}</div>"
        f"</div>"
    )

# Let's verify imports
print("Helper functions defined successfully.")
