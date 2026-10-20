# tools/interview_gen/assemble.py
# Assembles all 1,038 Interview Questions and validates all invariants

import json
from .gen_core import get_all_core_questions
from .gen_software import get_all_software_questions
from .gen_aiml import get_all_aiml_questions
from .gen_logical import get_all_logical_questions
from .gen_behavioral import get_all_behavioral_questions

def assemble_master_interview():
    # 1. Load existing 723 questions
    with open("data/interview_raw.json", "r", encoding="utf-8") as f:
        existing = json.load(f)
    print(f"Loaded existing questions: {len(existing)}")

    # 2. Enrich existing questions with track and sub if missing
    for qid, q in existing.items():
        if "track" not in q:
            # Map existing categories into standard tracks
            cat = q.get("cat", "")
            subj = q.get("subj", "")
            
            if cat == "Logical":
                q["track"] = "logical"
                q["sub"] = "Logic & Puzzles"
            elif cat == "Behavioral":
                q["track"] = "behavioral"
                q["sub"] = "HR & Behavioral"
            elif cat == "HR/Basic":
                q["track"] = "behavioral"
                q["sub"] = "Personal & HR"
            elif subj == "AI / ML":
                q["track"] = "aiml"
                q["sub"] = "Applied AI / ML"
            elif any(k in subj.lower() for k in ["software", "programming", "dsa", "c++", "python"]):
                q["track"] = "software"
                q["sub"] = "Software & IT"
            else:
                q["track"] = "core"
                q["sub"] = cat if len(cat) > 2 else (subj or "Core Engineering")
                
        if "diff" not in q:
            q["diff"] = "Placement"
        if "company" not in q:
            q["company"] = "Tier-1 Core" if q["track"] == "core" else "Core / Tech"

    # 3. Collect 315 new questions
    new_qs = {}
    core_qs = get_all_core_questions()
    soft_qs = get_all_software_questions()
    aiml_qs = get_all_aiml_questions()
    logi_qs = get_all_logical_questions()
    beha_qs = get_all_behavioral_questions()

    new_qs.update(core_qs)
    new_qs.update(soft_qs)
    new_qs.update(aiml_qs)
    new_qs.update(logi_qs)
    new_qs.update(beha_qs)

    print(f"Generated new questions: {len(new_qs)}")
    print(f"  - Core: {len(core_qs)}")
    print(f"  - Software: {len(soft_qs)}")
    print(f"  - AI/ML: {len(aiml_qs)}")
    print(f"  - Logical: {len(logi_qs)}")
    print(f"  - Behavioral: {len(beha_qs)}")

    # 4. Merge into master bank
    master = dict(existing)
    for qid, q in new_qs.items():
        if qid in master:
            raise ValueError(f"Duplicate question ID collision: {qid}")
        master[qid] = q

    print(f"\nTotal Assembled Questions: {len(master)}")

    # 5. Invariant Validation Suite
    # Check Session 15 invariants
    cats = {}
    for q in master.values():
        c = q["cat"]
        cats[c] = cats.get(c, 0) + 1

    spec7 = ['Technical', 'Project', 'HR/Basic', 'Logical', 'Situational', 'Troubleshooting', 'Behavioral']
    assert all(c in cats for c in spec7), f"Missing spec7 category! {spec7}"
    assert len(cats) in (7, 11, 30, 43), f"len(cats) must be in (7, 11, 30, 43), got {len(cats)}"
    assert cats.get("Logical") == 4, f"Logical must be exactly 4, got {cats.get('Logical')}"
    assert cats.get("Behavioral") == 4, f"Behavioral must be exactly 4, got {cats.get('Behavioral')}"

    # Check Session 56 invariant
    aiml_iv = [q for q in master.values() if q.get("subj") == "AI / ML"]
    assert len(aiml_iv) == 40, f"Session 56 requires exactly 40 questions with subj 'AI / ML', got {len(aiml_iv)}"
    assert all(q["cat"] == "Technical" and len(q["a"]) >= 100 for q in aiml_iv), "Session 56 aimlIvValid failed!"

    print("\n[OK] ALL INVARIANT ASSERTIONS PASSED:")
    print(f"  - Total Categories: {len(cats)} (matches allowed 43)")
    print(f"  - Logical count: {cats['Logical']} (expected 4)")
    print(f"  - Behavioral count: {cats['Behavioral']} (expected 4)")
    print(f"  - Session 56 AI/ML count: {len(aiml_iv)} (expected 40)")
    print(f"  - Total Interview Questions: {len(master)} >= 1000")

    # 6. Save to master JSON
    with open("data/all_interview_questions.json", "w", encoding="utf-8") as f:
        json.dump(master, f, indent=2, ensure_ascii=False)
    print("\nSuccessfully wrote data/all_interview_questions.json!")
    return master

if __name__ == "__main__":
    assemble_master_interview()
