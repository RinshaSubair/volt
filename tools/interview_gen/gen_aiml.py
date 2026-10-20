# tools/interview_gen/gen_aiml.py
# Combines all 40 AI & Machine Learning Interview Questions (iv-aiml-101 to iv-aiml-140)

from .gen_aiml_p1 import get_aiml_questions as p1
from .gen_aiml_p2 import get_aiml_p2 as p2

def get_all_aiml_questions():
    all_qs = {}
    all_qs.update(p1())
    all_qs.update(p2())
    return all_qs

if __name__ == "__main__":
    qs = get_all_aiml_questions()
    print(f"Total AI/ML Questions Generated: {len(qs)}")
    ids = sorted(list(qs.keys()))
    print(f"ID Range: {ids[0]} to {ids[-1]}")
