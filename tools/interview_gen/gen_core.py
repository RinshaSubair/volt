# tools/interview_gen/gen_core.py
# Combines all 100 Core Engineering Interview Questions (iv-core-101 to iv-core-200)

from .gen_core_p1 import get_core_questions as p1
from .gen_core_p2 import get_core_p2 as p2
from .gen_core_p3 import get_core_p3 as p3
from .gen_core_p4 import get_core_p4 as p4
from .gen_core_p5 import get_core_p5 as p5

def get_all_core_questions():
    all_qs = {}
    all_qs.update(p1())
    all_qs.update(p2())
    all_qs.update(p3())
    all_qs.update(p4())
    all_qs.update(p5())
    return all_qs

if __name__ == "__main__":
    qs = get_all_core_questions()
    print(f"Total Core Questions Generated: {len(qs)}")
    ids = sorted(list(qs.keys()))
    print(f"ID Range: {ids[0]} to {ids[-1]}")
