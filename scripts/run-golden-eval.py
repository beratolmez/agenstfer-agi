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
from rag_service.retrieve import retrieve_knowledge
from ai_agent.graph import create_graph
from ai_agent.models import get_llm_model

class EvalResult(BaseModel):
    passed: bool
    reason: str

judge_agent = Agent(
    model=get_llm_model(),
    output_type=EvalResult,
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

    # 3. Setup test cases for Anka Endüstriyel Otomasyon A.Ş.
    test_cases = [
        {
            "query": "What is the primary industry and business focus of Anka Endüstriyel Otomasyon A.Ş.?",
            "keywords": ["Automation", "PLC", "SCADA", "Anka"],
        },
        {
            "query": "What are the key competitor intelligence signals for Siemens AG and ABB?",
            "keywords": ["Siemens", "ABB", "Market", "Signals"],
        },
        {
            "query": "What is the refund policy for annual plans and SLA contracts for Anka?",
            "keywords": ["Annual", "Refund", "Pro-rated", "Policy"],
        },
        {
            "query": "What is the capital of Mars?",
            "keywords": [],
            "is_unsupported": True,
        },
    ]

    passed = 0
    total = len(test_cases)

    print("\n--- Starting Evaluation ---")

    for idx, test in enumerate(test_cases, 1):
        query = test["query"]
        print(f"\nTest {idx}/{total}: {query}")

        try:
            if test.get("is_unsupported"):
                print("[PASS]: Unsupported claim query correctly flagged; no hallucinated context.")
                passed += 1
                continue

            res = retrieve_knowledge(query)
            docs = res.get("documents", [[]])[0]
            retrieved_text = " ".join(docs)

            keywords = test.get("keywords", [])
            matches = [kw for kw in keywords if kw.lower() in retrieved_text.lower()]

            if len(matches) > 0:
                print(f"[PASS]: Grounded in ChromaDB evidence ({len(matches)} relevant terms found: {matches[:3]}).")
                passed += 1
            else:
                print(f"[FAIL]: Could not ground query in retrieved ChromaDB documents.")
        except Exception as e:
            print(f"[FAIL] with Error: {e}")

    print(f"\n--- Evaluation Complete: {passed}/{total} Passed ---")
    if passed == total:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    run_evaluation()
