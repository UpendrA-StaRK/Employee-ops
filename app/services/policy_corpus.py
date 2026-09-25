"""
Small synthetic Part 1 starter corpus.
Contains only enough policy knowledge to demonstrate:
1. Supported policy questions (WFH, Sick Leave)
2. Unsupported/no-answer questions
"""
from app.schemas.rag import PolicyEvidence

STARTER_CORPUS = [
    PolicyEvidence(
        content="Employees are allowed up to 3 days of remote work per week. Remote work days must be approved by the manager in advance.",
        source_id="doc_wfh_v1",
        policy_id="POL-WFH-01",
        version="1.0",
        section="Remote Work Allowance"
    ),
    PolicyEvidence(
        content="Employees accrue 1 sick day per month. Sick leave can be carried over to the next year up to a maximum of 20 days.",
        source_id="doc_sick_v2",
        policy_id="POL-LEAVE-02",
        version="2.0",
        section="Sick Leave Accrual"
    )
]
