TIERS = {
    "essential_plus": {"q_per_doc": 25, "irr_per_doc": 20, "general_q": 20, "general_ir": 10},
    "complete_pro":   {"q_per_doc": 25, "irr_per_doc": 20, "general_q": 25, "general_ir": 12},
    "expert_audit":   {"q_per_doc": 30, "irr_per_doc": 25, "general_q": 30, "general_ir": 15},
}

def pick_tier(n_docs: int) -> str:
    if n_docs <= 3:
        return "essential_plus"
    if n_docs <= 6:
        return "complete_pro"
    return "expert_audit"



