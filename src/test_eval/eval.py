from typing import List, Dict
import json
import numpy as np
import sys
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent  
sys.path.append(str(PROJECT_ROOT))


from src.core.recommender import search_pinecone
test_queries=[


    {
        "query": "I am hiring for Java developers who can also collaborate effectively with my business teams. Looking for an assessment(s) that can be completed in 40 minutes.",
        "assessments": [
            "Automata - Fix (New) ",
            "Core Java (Entry Level) (New) ",
            "Java 8 (New) ",
            "Core Java (Advanced Level) (New) ",
            "Agile Software Development",
            "Technology Professional 8.0 - Job Focused Assessment",
            "Computer Science (New)"
        ]
    },
    {
        "query": "I want to hire new graduates for a sales role in my company, the budget is for about an hour for each test. Give me some options",
        "assessments": [
            "Entry Level Sales 7.1 ",
            "Entry Level Sales Sift Out 7.1 ",
            "Entry Level Sales Solution ",
            "Sales Representative Solution ",
            "Sales Support Specialist Solution ",
            "Technical Sales Associate Solution ",
            "SVAR Spoken English - Indian Accent (New) ",
            "Sales and Service Phone Solution ",
            "Sales and Service Phone Simulation ",
            "English Comprehension (New)"
        ]
    },
    {
        "query": "Content Writer required, expert in English and SEO.",
        "assessments": [
            "Drupal (New) ",
            "Search Engine Optimization (New)",
            "Administrative Professional - Short Form",
            "Entry Level Sales Sift Out 7.1 ",
            "General Entry Level Data Entry 7.0 - Solution "
        ]
    }
]


def normalize(text: str) -> str:
    return text.lower().strip()


def recall_at_k(relevant: List[str], retrieved: List[str], k: int = 3) -> float:
    """Calculate Recall@K metric"""
    relevant_set = set(relevant)
    retrieved_set = set(retrieved[:k])
    intersection = relevant_set & retrieved_set
    return len(intersection) / min(len(relevant_set), k) if relevant_set else 0.0

def map_at_k(relevant: List[str], retrieved: List[str], k: int = 3) -> float:
    """Calculate Mean Average Precision@K"""
    precision_scores = []
    num_relevant = 0
    
    for i, item in enumerate(retrieved[:k], 1):
        if item in relevant:
            num_relevant += 1
            precision_scores.append(num_relevant / i)
    
    return sum(precision_scores) / min(len(relevant), k) if relevant else 0.0

def evaluate() -> Dict[str, float]:
    """Run evaluation and return metrics"""
    recalls, maps = [], []
    failed_queries = 0

    for test in test_queries:
        query = test["query"]
        relevant = [normalize(a) for a in test["assessments"]]


        try:
            results = search_pinecone(query, top_k=3)
            retrieved = [normalize(f"{item['name']} | SHL") for item in results]
            
            if not retrieved:
                failed_queries += 1
                print(f"No results for: {query[:50]}...")
                continue

            recall = recall_at_k(relevant, retrieved)
            avg_precision = map_at_k(relevant, retrieved)

            recalls.append(recall)
            maps.append(avg_precision)

            print(f"\n Query: {query[:50]}...")
            print(f"Relevant: {relevant[:3]}...")
            print(f" Retrieved: {retrieved}")
            print(f" Recall@3: {recall:.2f} | MAP@3: {avg_precision:.2f}")

        except Exception as e:
            print(f"⚠️ Error processing query: {str(e)}")
            failed_queries += 1

    metrics = {
        "mean_recall@3": np.mean(recalls) if recalls else 0,
        "mean_map@3": np.mean(maps) if maps else 0,
        "success_rate": 1 - (failed_queries / len(test_queries)) if test_queries else 0
    }

    print("\n Evaluation Summary:")
    print(f" Mean Recall@3: {metrics['mean_recall@3']:.2f}")
    print(f" Mean MAP@3: {metrics['mean_map@3']:.2f}")
    print(f" Success Rate: {metrics['success_rate']:.1%}")
    print(f"⚠️  Failed queries: {failed_queries}/{len(test_queries)}")

    return metrics


if __name__ == "__main__":
    evaluation_results = evaluate()
    
    with open('evaluation_results.json', 'w') as f:
        json.dump(evaluation_results, f, indent=2)