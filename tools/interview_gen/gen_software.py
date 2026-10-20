# tools/interview_gen/gen_software.py
# Combines all 90 Software & IT Interview Questions (iv-soft-101 to iv-soft-190)

from .gen_software_p1 import get_software_p1 as p1
from .gen_software_p2 import get_software_p2 as p2
from .gen_software_p3 import get_software_p3 as p3

def get_all_software_questions():
    all_qs = {}
    all_qs.update(p1())
    all_qs.update(p2())
    all_qs.update(p3())
    return all_qs

if __name__ == "__main__":
    qs = get_all_software_questions()
    print(f"Total Software Questions Generated: {len(qs)}")
    ids = sorted(list(qs.keys()))
    print(f"ID Range: {ids[0]} to {ids[-1]}")
