import sys
import os
import glob
import re
from pydantic import BaseModel
from pydantic_ai import Agent

# Ensure modules can be imported
sys.path.insert(0, os.path.abspath('apps/services/rag'))
sys.path.insert(0, os.path.abspath('apps/services/ai-agent'))

import chromadb
from rag_service.ingest import ingest_markdown_file
from ai_agent.graph import create_graph
from ai_agent.models import get_llm_model

class EvalResult(BaseModel):
    passed: bool
    reason: str

judge_agent = Agent(
    model=get_llm_model(),
    result_type=EvalResult,
    system_prompt="You are an expert evaluator assessing an AI agent's output. Determine if the output meets the evaluation criteria. Return passed=True if it does, and passed=False otherwise, along with a reason."
)

def run_evaluation():
    # 1. Clear ChromaDB
    chroma_client = chromadb.PersistentClient(path="./chroma_db")
    try:
        chroma_client.delete_collection("okf_wiki")
        print("Cleared okf_wiki collection.")
    except ValueError:
        print("Collection okf_wiki does not exist yet.")
    except Exception as e:
        print(f"Error clearing collection: {e}")

    # 2. Ingest mock data
    mock_data_dir = os.path.abspath('mock_data')
    md_files = glob.glob(os.path.join(mock_data_dir, "*.md"))
    if not md_files:
        print(f"No markdown files found in {mock_data_dir}")
        sys.exit(1)
        
    for file_path in md_files:
        ingest_markdown_file(file_path)

    # 3. Setup test cases
    test_cases = [
        {
            "query": "What is the Net Profit for Q3 2026?",
            "criteria": "The response must state the Net Profit is 450,000 and include a valid source locator."
        },
        {
            "query": "What is the churn risk for GlobalBank?",
            "criteria": "The response must state the churn risk is High and include a valid source locator."
        },
        {
            "query": "What is the refund policy for annual plans?",
            "criteria": "The response must mention a pro-rated policy and include a valid source locator."
        },
        {
            "query": "What is the capital of Mars?",
            "criteria": "The response must explicitly state that the information is unsupported or unavailable, and must not provide a made-up answer."
        }
    ]

    # 4. Create graph and evaluate
    graph = create_graph()
    
    passed = 0
    total = len(test_cases)
    
    print("\n--- Starting Evaluation ---")
    
    for idx, test in enumerate(test_cases, 1):
        query = test["query"]
        print(f"\nTest {idx}/{total}: {query}")
        
        try:
            result = graph.invoke({"messages": [query]})
            final_review = result.get("messages", [""])[-1] if result.get("messages") else ""
            if hasattr(final_review, 'content'):
                final_review_text = final_review.content
            else:
                final_review_text = str(final_review)
                
            # Programmatic check for source locators
            sources = re.findall(r'\[Source: (.*?)\]', final_review_text)
            missing_sources = []
            for source in sources:
                source_clean = source.strip()
                # Check if exact file exists, or if it matches an ingested file
                if not os.path.exists(source_clean) and not any(source_clean in md_file for md_file in md_files):
                    missing_sources.append(source_clean)
            
            if missing_sources:
                print(f"❌ FAIL: Source locator validation failed. Missing/invalid sources: {missing_sources}")
                print(f"   Agent Output: {final_review_text}")
                continue
                
            judge_prompt = f"Query: {query}\n\nAgent Output:\n{final_review_text}\n\nCriteria:\n{test['criteria']}"
            eval_result = judge_agent.run_sync(judge_prompt).data
            
            if eval_result.passed:
                print(f"✅ PASS: {eval_result.reason}")
                passed += 1
            else:
                print(f"❌ FAIL: {eval_result.reason}")
                print(f"   Agent Output: {final_review_text}")
        except Exception as e:
            print(f"❌ FAIL with Error: {e}")

    print(f"\n--- Evaluation Complete: {passed}/{total} Passed ---")
    if passed == total:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    run_evaluation()
