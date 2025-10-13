
# app/test_service.py
from datetime import datetime, timedelta
from typing import List
from database.supabase_db import get_client
from models.schemas import SubmitAnswer, QuestionResult, TestStatus

client = get_client()


async def start_test_timer(test_id: str):
    """Start the test timer - 11 minutes duration"""
    
    # Check if test exists and is in generated status
    result = client.table("tests").select("*").eq("test_id", test_id).execute()
    
    if not result.data:
        raise ValueError("Test not found")
    
    test = result.data[0]
    
    if test["status"] != "generated":
        raise ValueError(f"Test cannot be started. Current status: {test['status']}")
    
    # Use timezone-naive datetime for consistency
    start_time = datetime.now()
    end_time = start_time + timedelta(minutes=11)
    
    # Update test status and timing
    update_data = {
        "status": "started",
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat()
    }
    
    client.table("tests").update(update_data).eq("test_id", test_id).execute()
    
    return start_time, end_time

# Even simpler version - no time checks at all
async def submit_test_answers(test_id: str, answers: List[SubmitAnswer]):
    """Submit test answers - accepts anytime after test starts"""
    
    # Get test data
    result = client.table("tests").select("*").eq("test_id", test_id).execute()
    
    if not result.data:
        raise ValueError("Test not found")
    
    test = result.data[0]
    
    # # Only check if test was started (no time limits)
    # if test["status"] != "started":
    #     raise ValueError(f"Test cannot be submitted. Current status: {test['status']}")
    
    # Calculate time taken
    current_time = datetime.now()
    start_time_str = test["start_time"]
    start_time_clean = start_time_str.split('+')[0].split('Z')[0].split('.')[0]
    start_time = datetime.fromisoformat(start_time_clean)
    time_taken_seconds = int((current_time - start_time).total_seconds())
    
    # Get correct answers
    questions_data = test["questions_data"]
    
    # Create answer mapping
    submitted_answers = {answer.question_id: answer.selected_answer for answer in answers}
    
    # Calculate results
    results = []
    correct_count = 0
    
    for i, question_data in enumerate(questions_data, 1):
        question_id = i
        correct_answer = question_data["answer"]
        selected_answer = submitted_answers.get(question_id, "")
        is_correct = selected_answer == correct_answer
        
        if is_correct:
            correct_count += 1
        
        result = QuestionResult(
            question_id=question_id,
            question=question_data["question"],
            selected_answer=selected_answer,
            correct_answer=correct_answer,
            is_correct=is_correct
        )
        results.append(result)
    
    # Calculate score and percentage
    total_questions = len(questions_data)
    percentage = (correct_count / total_questions) * 100
    

    
    # Store submission in database
    submission_data = {
        "test_id": test_id,
        "submitted_answers": [answer.dict() for answer in answers],
        "score": correct_count,
        "total_questions": total_questions,
        "percentage": percentage,
        "time_taken_seconds": time_taken_seconds,
        "submitted_at": current_time.isoformat()
    }
    
    client.table("submissions").insert(submission_data).execute()
    
    # Update test status
    client.table("tests").update({
    "status": TestStatus.SUBMITTED,           # <-- ADD THIS LINE
    "submitted_at": current_time.isoformat()
    }).eq("test_id", test_id).execute()
    
    print(f"Test {test_id} submission completed. Score: {correct_count}/{total_questions} ({percentage}%)")
    
    return correct_count, total_questions, percentage, time_taken_seconds, results