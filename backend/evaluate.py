import time
import requests
import pandas as pd
import json
import logging

# --- Configuration ---
API_URL = "http://localhost:8000/api/generate-query"
OUTPUT_FILE = "evaluation_results.csv"

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# --- 1. Define the "Golden Dataset" ---
# These are questions with known facts. The 'expected_keywords' list 
# contains words that MUST appear in the answer for it to be considered "relevant/correct".
test_cases = [
    {
        "category": "Simple Fact",
        "question": "What team does LeBron James play for?",
        "expected_keywords": ["Lakers", "Los Angeles"]
    },
    {
        "category": "Simple Fact", 
        "question": "What position does Stephen Curry play?",
        "expected_keywords": ["Guard", "G"]
    },
    {
        "category": "Multi-hop / Relationship",
        "question": "Which conference is the team Miami Heat in?",
        "expected_keywords": ["East", "Eastern"]
    },
    {
        "category": "Numerical / Stats",
        "question": "What is the jersey number of Luka Doncic?",
        "expected_keywords": ["77"]
    },
    {
        "category": "Negative Test (Missing Info)",
        "question": "What team does Michael Jordan play for right now?",
        "expected_keywords": ["not", "no information", "retired", "cannot answer"]
    },
    {
        "category": "Calculation",
        "question": "What is 25 plus 30?",
        "expected_keywords": ["55"]
    }
]

def run_evaluation():
    results = []
    print(f"🚀 Starting Evaluation on {len(test_cases)} test cases...\n")

    for index, case in enumerate(test_cases):
        question = case["question"]
        expected = case["expected_keywords"]
        category = case["category"]
        
        print(f"[{index+1}/{len(test_cases)}] Testing: {question}")
        
        start_time = time.time()
        
        try:
            # Send request to your FastAPI backend
            response = requests.post(API_URL, json={"question": question})
            
            # Calculate Latency
            end_time = time.time()
            latency = end_time - start_time
            
            if response.status_code == 200:
                data = response.json()
                actual_answer = data.get("output", "").strip()
                
                # --- Grading Logic ---
                # Check if ANY of the expected keywords are in the answer (Case Insensitive)
                # For a more advanced grade, you could use an LLM here to compare semantics.
                is_correct = any(keyword.lower() in actual_answer.lower() for keyword in expected)
                
                status = "✅ PASS" if is_correct else "❌ FAIL"
                
            else:
                actual_answer = f"Error: Status Code {response.status_code}"
                latency = 0
                is_correct = False
                status = "⚠️ ERROR"

        except Exception as e:
            actual_answer = f"Exception: {str(e)}"
            latency = 0
            is_correct = False
            status = "⚠️ CRITICAL"

        print(f"   -> Result: {status} | Latency: {latency:.2f}s")
        print(f"   -> Agent Answer: {actual_answer}\n")

        # Store result
        results.append({
            "Category": category,
            "Question": question,
            "Expected Keywords": ", ".join(expected),
            "Actual Output": actual_answer,
            "Latency (s)": round(latency, 4),
            "Correct": is_correct
        })

    # --- 2. Calculate & Display Metrics ---
    df = pd.DataFrame(results)
    
    # Save detailed logs to CSV
    df.to_csv(OUTPUT_FILE, index=False)
    
    print("="*40)
    print("📊 EVALUATION SUMMARY")
    print("="*40)
    
    total_tests = len(df)
    passed_tests = df["Correct"].sum()
    accuracy = (passed_tests / total_tests) * 100
    avg_latency = df["Latency (s)"].mean()
    
    print(f"Total Questions: {total_tests}")
    print(f"Correct Answers: {passed_tests}")
    print(f"Accuracy Rate:   {accuracy:.2f}%")
    print(f"Average Latency: {avg_latency:.4f} seconds")
    print("="*40)
    print(f"Detailed results saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    # Ensure the API is running before executing
    try:
        requests.get("http://localhost:8000/health")
        run_evaluation()
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to the API.") 
        print("Please make sure your FastAPI server is running at localhost:8000")