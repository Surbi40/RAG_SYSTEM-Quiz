"""
API Test Script
===============

Run this to verify the Quiz Generator API is working correctly.

Usage:
    python test_api.py
    
Make sure the API server is running first:
    python api.py
"""

import requests
import json
import sys
import os

API_BASE = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("\n[TEST] Health Check...")
    try:
        response = requests.get(f"{API_BASE}/api/health", timeout=5)
        data = response.json()
        
        if response.status_code == 200:
            print(f"  [OK] Status: {data['status']}")
            print(f"  [OK] Database Ready: {data['database_ready']}")
            return True
        else:
            print(f"  [FAIL] Status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("  [FAIL] Cannot connect to API. Is the server running?")
        return False

def test_topics():
    """Test topics endpoint"""
    print("\n[TEST] Get Topics...")
    try:
        response = requests.get(f"{API_BASE}/api/topics", timeout=5)
        data = response.json()
        
        if response.status_code == 200 and data.get('success'):
            print(f"  [OK] Found {len(data['topics'])} suggested topics")
            for t in data['topics'][:3]:
                print(f"       - {t['topic']} ({t['relevance']})")
            return True
        else:
            print(f"  [FAIL] Unexpected response")
            return False
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False

def test_quiz_generation():
    """Test quiz generation endpoint"""
    print("\n[TEST] Quiz Generation...")
    try:
        payload = {
            "topic": "postpartum depression",
            "num_questions": 2
        }
        
        print(f"  Requesting quiz on '{payload['topic']}'...")
        response = requests.post(
            f"{API_BASE}/api/quiz/generate",
            json=payload,
            timeout=120  # Quiz generation can take time
        )
        data = response.json()
        
        if response.status_code == 200:
            if data.get('success') and data.get('questions'):
                print(f"  [OK] Generated {data['total_questions']} questions")
                print(f"\n  Sample Question:")
                q = data['questions'][0]
                print(f"  Q: {q['question'][:80]}...")
                print(f"  Options:")
                for opt in q['options']:
                    mark = "*" if opt['is_correct'] else " "
                    print(f"    [{mark}] {opt['letter']}. {opt['text'][:50]}...")
                return True
            else:
                print(f"  [WARN] Quiz generated but no questions: {data.get('message')}")
                return False
        else:
            print(f"  [FAIL] Status code: {response.status_code}")
            print(f"  Response: {data}")
            return False
            
    except requests.exceptions.Timeout:
        print("  [FAIL] Request timed out (>120s)")
        return False
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False

def test_ingest_html():
    """Test HTML ingestion"""
    print("\n[TEST] HTML Ingestion...")
    # Create a dummy HTML file for testing
    html_content = "<html><body><h1>Maternal Health</h1><p>Postpartum care is essential for new mothers.</p></body></html>"
    temp_file = "test_ingest.html"
    with open(temp_file, "w") as f:
        f.write(html_content)
    
    try:
        with open(temp_file, "rb") as f:
            files = {"file": (temp_file, f, "text/html")}
            response = requests.post(f"{API_BASE}/api/ingest", files=files, timeout=10)
        
        data = response.json()
        if response.status_code == 200 and data.get("success"):
            print(f"  [OK] Successfully ingested HTML")
            return True
        else:
            print(f"  [FAIL] Status code: {response.status_code}, Msg: {data.get('message')}")
            return False
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)

def test_anonymous_article():
    """Test anonymous article submission"""
    print("\n[TEST] Anonymous Article Submission...")
    payload = {
        "text": "Regular exercise and a balanced diet are important for baby's development during pregnancy.",
        "title": "Baby Health Tip"
    }
    try:
        response = requests.post(f"{API_BASE}/api/articles/anonymous", json=payload, timeout=10)
        data = response.json()
        if response.status_code == 200 and data.get("success"):
            print(f"  [OK] Successfully submitted anonymous article")
            return True
        else:
            print(f"  [FAIL] Status code: {response.status_code}, Msg: {data.get('message')}")
            return False
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False

def test_ondemand_quiz():
    """Test on-demand quiz generation (generic topic)"""
    print("\n[TEST] On-Demand Quiz Generation...")
    payload = {
        "topic": "take quiz",
        "num_questions": 3
    }
    try:
        response = requests.post(f"{API_BASE}/api/quiz/generate", json=payload, timeout=120)
        data = response.json()
        if response.status_code == 200 and data.get("success"):
            print(f"  [OK] Successfully generated on-demand quiz with {data.get('total_questions')} questions")
            return True
        else:
            print(f"  [FAIL] Status code: {response.status_code}, Msg: {data.get('message')}")
            return False
    except Exception as e:
        print(f"  [FAIL] {e}")
        return False

def main():
    print("="*60)
    print("Quiz Generator API Test Suite")
    print("="*60)
    print(f"Testing API at: {API_BASE}")
    
    results = []
    
    # Run tests
    results.append(("Health Check", test_health()))
    results.append(("Get Topics", test_topics()))
    results.append(("Quiz Generation", test_quiz_generation()))
    results.append(("HTML Ingestion", test_ingest_html()))
    results.append(("Anonymous Article", test_anonymous_article()))
    results.append(("On-Demand Quiz", test_ondemand_quiz()))
    
    # Summary
    print("\n" + "="*60)
    print("RESULTS SUMMARY")
    print("="*60)
    
    passed = 0
    for name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"  {name}: {status}")
        if result:
            passed += 1
    
    print(f"\n  Total: {passed}/{len(results)} tests passed")
    print("="*60)
    
    if passed == len(results):
        print("\n[SUCCESS] All tests passed! API is ready for integration.")
        return 0
    else:
        print("\n[WARNING] Some tests failed. Check the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

