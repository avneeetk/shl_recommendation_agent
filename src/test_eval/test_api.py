import requests

BASE_URL = "http://your-api-url" 

def test_health_check():
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_recommendations():
    test_queries = [...]  
    
    for query_data in test_queries:
        response = requests.post(
            f"{BASE_URL}/recommend",
            json={"query": query_data["query"]}
        )
        
        assert response.status_code == 200
        results = response.json()
        
        # Validate response structure
        assert "recommended_assessments" in results
        for assessment in results["recommended_assessments"]:
            assert all(key in assessment for key in [
                "url", "adaptive_support", "description",
                "duration", "remote_support", "test_type"
            ])

if __name__ == "__main__":
    test_health_check()
    test_recommendations()
    print("All API tests passed!")