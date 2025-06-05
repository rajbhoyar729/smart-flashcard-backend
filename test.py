import requests
import json

BASE_URL = "http://localhost:8000"

def test_ambiguous_words():
    """Test how the system handles ambiguous/shared keywords"""
    
    print("🔍 Testing Ambiguous Word Classification\n")
    
    # Test cases with shared keywords
    test_cases = [
        {
            "question": "What is an atom?",
            "answer": "The smallest unit of matter",
            "expected_issue": "Both Physics and Chemistry use 'atom'"
        },
        {
            "question": "What is atomic structure in physics?", 
            "answer": "Electrons orbit the nucleus with specific energy levels",
            "expected": "Physics (context: energy levels, electrons, nucleus)"
        },
        {
            "question": "What is atomic bonding in chemistry?",
            "answer": "Atoms form bonds by sharing or transferring electrons to achieve stability",
            "expected": "Chemistry (context: bonding, sharing, stability)"
        },
        {
            "question": "What is organic matter?",
            "answer": "Living or once-living material",
            "expected_issue": "'Organic' appears in both Chemistry and Biology"
        },
        {
            "question": "What is organic chemistry?",
            "answer": "Study of carbon-based compounds and their reactions",
            "expected": "Chemistry (context: compounds, reactions)"
        },
        {
            "question": "What is organic evolution in biology?",
            "answer": "The process by which species change over time through natural selection",
            "expected": "Biology (context: species, natural selection)"
        },
        {
            "question": "What is energy?",
            "answer": "The ability to do work",
            "expected_issue": "'Energy' could be Physics, Chemistry, or Biology"
        },
        {
            "question": "What is kinetic energy in physics?",
            "answer": "Energy of motion, equal to half mass times velocity squared",
            "expected": "Physics (context: motion, mass, velocity)"
        }
    ]
    
    print("📊 Classification Results:\n")
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}: {test_case['question']}")
        
        # Test using the analyze endpoint first
        try:
            response = requests.get(f"{BASE_URL}/analyze-text", 
                                  params={"text": test_case['question'] + " " + test_case['answer']})
            
            if response.status_code == 200:
                result = response.json()
                
                print(f"   🎯 Result: {result['subject']}")
                print(f"   📈 Confidence: {result['confidence']:.2f}")
                print(f"   💭 Reasoning: {result['reasoning']}")
                
                if 'expected' in test_case:
                    print(f"   ✅ Expected: {test_case['expected']}")
                elif 'expected_issue' in test_case:
                    print(f"   ⚠️  Known Issue: {test_case['expected_issue']}")
                
            else:
                print(f"   ❌ Analysis failed: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print("❌ Connection failed. Make sure the server is running on localhost:8000")
            return
            
        print()
    
    # Test by actually adding flashcards
    print("📝 Adding Test Flashcards:\n")
    
    for i, test_case in enumerate(test_cases[:4], 1):  # Test first 4
        flashcard_data = {
            "student_id": "test_student",
            "question": test_case['question'],
            "answer": test_case['answer']
        }
        
        try:
            response = requests.post(f"{BASE_URL}/flashcard", json=flashcard_data)
            
            if response.status_code == 200:
                result = response.json()
                print(f"Flashcard {i}: {result['subject']} (Confidence: {result['confidence']:.2f})")
                print(f"   Reasoning: {result['reasoning']}")
            else:
                print(f"Failed to add flashcard {i}: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print("❌ Connection failed. Make sure the server is running on localhost:8000")
            return
        
        print()

def compare_simple_vs_advanced():
    """Compare how simple vs advanced classification would handle the same text"""
    
    print("⚖️  Simple vs Advanced Classification Comparison\n")
    
    ambiguous_examples = [
        "What is an atom made of?",
        "Explain organic compounds",
        "What is energy conservation?",
        "How do particles interact?"
    ]
    
    for example in ambiguous_examples:
        print(f"Text: '{example}'")
        
        try:
            response = requests.get(f"{BASE_URL}/analyze-text", params={"text": example})
            
            if response.status_code == 200:
                result = response.json()
                print(f"   Advanced: {result['subject']} (Confidence: {result['confidence']:.2f})")
                print(f"   Reasoning: {result['reasoning']}")
            else:
                print(f"   ❌ Analysis failed: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print("❌ Connection failed. Make sure the server is running on localhost:8000")
            return
            
        print()

if __name__ == "__main__":
    test_ambiguous_words()
    print("\n" + "="*60 + "\n")
    compare_simple_vs_advanced()