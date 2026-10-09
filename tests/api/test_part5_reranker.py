import pytest
from app.services.reranker import reranker

def test_reranker_sorting_logic(monkeypatch):
    # Mock the predict method to return a controlled score
    def mock_predict(pairs):
        # Let's say pairs are [ [query, doc] ]
        scores = []
        for q, d in pairs:
            if "high" in d:
                scores.append(0.9)
            elif "medium" in d:
                scores.append(0.5)
            else:
                scores.append(0.1)
        return scores
        
    class MockModel:
        def predict(self, pairs):
            return mock_predict(pairs)
            
    # Load the actual class but mock the inner model
    reranker._model = MockModel()

    candidates = [
        {"id": 1, "text": "This is a low match."},
        {"id": 2, "text": "This is a high match."},
        {"id": 3, "text": "This is a medium match."}
    ]
    
    reranked = reranker.rerank("Query", candidates, lambda c: c["text"])
    
    assert len(reranked) == 3
    # Check ordering
    assert reranked[0][0]["id"] == 2  # high
    assert reranked[1][0]["id"] == 3  # medium
    assert reranked[2][0]["id"] == 1  # low
    assert reranked[0][1] == 0.9
    assert reranked[1][1] == 0.5
    
def test_reranker_empty_list():
    reranked = reranker.rerank("Query", [], lambda c: c["text"])
    assert reranked == []

@pytest.mark.skip(reason="Smoke test - runs actual local model if enabled")
def test_reranker_smoke():
    """Integration test that actually loads the model."""
    candidates = [
        {"id": 1, "text": "Apples are delicious fruits."},
        {"id": 2, "text": "The company policy is to be good."}
    ]
    
    reranker._model = None # Force actual load
    reranked = reranker.rerank("What is the company policy?", candidates, lambda c: c["text"])
    
    assert reranked[0][0]["id"] == 2
