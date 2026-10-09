import json
import time
import os
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.schemas.rag import MetadataFilters
from app.services.retriever import retrieve_evidence
from app.services.generator import generate_answer
from app.evaluation.metrics import (
    calculate_recall_at_k, 
    calculate_precision_at_k, 
    calculate_mrr, 
    evaluate_citations, 
    check_no_answer
)

def load_eval_cases(filepath: str = "data/evaluation/eval_cases.json") -> List[Dict[str, Any]]:
    if not os.path.exists(filepath):
        return []
    with open(filepath, "r") as f:
        return json.load(f)

def evaluate_configuration(
    db: Session, 
    eval_cases: List[Dict[str, Any]], 
    strategy: str,
    k: int = 3
) -> Dict[str, Any]:
    
    results = []
    total_recall = 0.0
    total_precision = 0.0
    total_mrr = 0.0
    valid_ground_truth_count = 0
    total_latency_retrieval = 0.0
    total_latency_generation = 0.0
    failures = []
    
    for case in eval_cases:
        case_id = case["id"]
        question = case["question"]
        expected_chunk_ids = case.get("expected_chunk_ids", [])
        expected_policy_ids = case.get("expected_policy_ids", [])
        constraints = case.get("constraints", {})
        answerability = case.get("answerability", "answerable")
        
        filters = MetadataFilters(**constraints) if constraints else None
        
        # 1. Measure Retrieval Latency
        t0 = time.perf_counter()
        try:
            evidence = retrieve_evidence(db, question, filters=filters, top_k=k, strategy=strategy)
        except Exception as e:
            failures.append({
                "test_case_id": case_id,
                "strategy": strategy,
                "failure_category": "retrieval",
                "observed_failure": str(e),
                "next_action": "investigate retrieval pipeline"
            })
            continue
            
        t1 = time.perf_counter()
        retrieval_latency = t1 - t0
        total_latency_retrieval += retrieval_latency
        
        retrieved_chunk_ids = [ev.chunk_id for ev in evidence if ev.chunk_id is not None]
        
        # Metrics
        if expected_chunk_ids:
            recall = calculate_recall_at_k(expected_chunk_ids, retrieved_chunk_ids, k)
            precision = calculate_precision_at_k(expected_chunk_ids, retrieved_chunk_ids, k)
            mrr = calculate_mrr(expected_chunk_ids, retrieved_chunk_ids, k)
            
            total_recall += recall
            total_precision += precision
            total_mrr += mrr
            valid_ground_truth_count += 1
            
            if recall < 1.0:
                failures.append({
                    "test_case_id": case_id,
                    "strategy": strategy,
                    "failure_category": "retrieval",
                    "observed_failure": f"Recall below 1.0 ({recall}). Expected: {expected_chunk_ids}, Retrieved: {retrieved_chunk_ids}",
                    "next_action": "Check embedding similarity or reranker scoring"
                })
        
        # 2. Measure Generation Latency
        t2 = time.perf_counter()
        try:
            response = generate_answer(question, evidence)
        except Exception as e:
            failures.append({
                "test_case_id": case_id,
                "strategy": strategy,
                "failure_category": "generation",
                "observed_failure": str(e),
                "next_action": "investigate generation path"
            })
            continue
            
        t3 = time.perf_counter()
        generation_latency = t3 - t2
        total_latency_generation += generation_latency
        
        # 3. Citation and No-Answer Checks
        generated_citations = [cit.policy_id for cit in response.citations]
        citations_valid = evaluate_citations(expected_policy_ids, generated_citations)
        if not citations_valid and answerability == "answerable":
            failures.append({
                "test_case_id": case_id,
                "strategy": strategy,
                "failure_category": "citation",
                "observed_failure": f"Generated citations {generated_citations} do not match expected policies {expected_policy_ids}",
                "next_action": "Verify context structure provided to generator"
            })
            
        no_answer_valid = check_no_answer(answerability, response.answer)
        if not no_answer_valid:
            failures.append({
                "test_case_id": case_id,
                "strategy": strategy,
                "failure_category": "generation",
                "observed_failure": f"No-answer check failed for answerability: {answerability}",
                "next_action": "Refine generator prompt or empty context handling"
            })
            
        results.append({
            "case_id": case_id,
            "retrieved_chunk_ids": retrieved_chunk_ids,
            "retrieval_latency": retrieval_latency,
            "generation_latency": generation_latency,
            "citations_valid": citations_valid,
            "no_answer_valid": no_answer_valid
        })

    num_cases = len(eval_cases)
    return {
        "strategy": strategy,
        "metrics": {
            "cases_evaluated": num_cases,
            "cases_with_ground_truth": valid_ground_truth_count,
            "avg_recall_at_k": total_recall / valid_ground_truth_count if valid_ground_truth_count > 0 else 0.0,
            "avg_precision_at_k": total_precision / valid_ground_truth_count if valid_ground_truth_count > 0 else 0.0,
            "mrr": total_mrr / valid_ground_truth_count if valid_ground_truth_count > 0 else 0.0,
            "avg_retrieval_latency_s": total_latency_retrieval / num_cases if num_cases > 0 else 0.0,
            "avg_generation_latency_s": total_latency_generation / num_cases if num_cases > 0 else 0.0
        },
        "failures": failures
    }

def run_evaluation():
    cases = load_eval_cases()
    if not cases:
        print("No evaluation cases found at data/evaluation/eval_cases.json")
        return
        
    db = SessionLocal()
    strategies = ["vector", "hybrid", "hybrid_rerank"]
    
    scorecard = {}
    all_failures = []
    
    try:
        for strategy in strategies:
            print(f"Evaluating strategy: {strategy}...")
            result = evaluate_configuration(db, cases, strategy, k=3)
            scorecard[strategy] = result["metrics"]
            all_failures.extend(result["failures"])
            
        with open("data/evaluation/scorecard.json", "w") as f:
            json.dump(scorecard, f, indent=4)
            
        with open("data/evaluation/failure_log.json", "w") as f:
            json.dump(all_failures, f, indent=4)
            
        print("Evaluation complete. Results saved to data/evaluation/.")
        
    finally:
        db.close()

if __name__ == "__main__":
    run_evaluation()
