# tools/interview_gen/gen_behavioral.py
# Combines all 45 Placement-Grade Behavioral & HR Interview Questions (iv-hr-101 to iv-hr-145)

from .gen_hr_p1 import get_hr_p1 as p1
from .gen_hr_p2 import get_hr_p2 as p2

def get_all_behavioral_questions():
    all_qs = {}
    all_qs.update(p1())
    all_qs.update(p2())
    return all_qs

if __name__ == "__main__":
    qs = get_all_behavioral_questions()
    print(f"Total Behavioral Questions Generated: {len(qs)}")
    ids = sorted(list(qs.keys()))
    print(f"ID Range: {ids[0]} to {ids[-1]}")
