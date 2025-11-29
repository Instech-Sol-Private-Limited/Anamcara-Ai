from fastapi import APIRouter, HTTPException, BackgroundTasks, Body
from database.supabase_db import get_client
from app.services.test_services import start_test_timer, submit_test_answers
from datetime import datetime, timedelta, timezone
from models.schemas import (
    GenerateTestRequest, GenerateTestResponse, 
    StartTestRequest, StartTestResponse,
    SubmitTestRequest, SubmitTestResponse, 
    TestStatus, ChallengeRequest, ChallengeJoinRequest
)
from app.services.mcq_generator import generate_mcq_questions
import io
import uuid
from typing import Optional
from fastapi.responses import StreamingResponse
import fitz  
import requests
from bs4 import BeautifulSoup

router = APIRouter()
client = get_client()

@router.post("/generate-test", response_model=GenerateTestResponse)
async def generate_test(request: GenerateTestRequest):
    """Generate a new MCQ test with 20 questions using LangChain Agent"""
    try:
        test_id, questions = await generate_mcq_questions(
            subject=request.subject,
            student_name=request.student_name,
            student_email=request.student_email
        )
        
        return GenerateTestResponse(
            test_id=test_id,
            subject=request.subject,
            student_name=request.student_name,
            questions=questions,
            status=TestStatus.GENERATED
        )
    except Exception as e:
        error_message = str(e)

        # Check if the error is due to insufficient quota
        if "insufficient_quota" in error_message or "You exceeded your current quota" in error_message or "429" in error_message:
            raise HTTPException(
                status_code=402,
                detail="Credits expired. Please contact the administrator."
            )
        
        # General error
        raise HTTPException(
            status_code=500,
            detail=f"Generation failed: {error_message}"
        )

@router.post("/retake-test/{test_id}", response_model=GenerateTestResponse)
async def retake_test(test_id: str):
    """Retake an existing test - generates new questions with same subject"""
    try:
        # Get original test
        result = client.table("tests").select("*").eq("test_id", test_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Original test not found")
        
        original_test = result.data[0]
        
        # Check if test was submitted
        if original_test["status"] != "submitted":
            raise HTTPException(
                status_code=400, 
                detail="Can only retake completed tests. Please submit the current test first."
            )
        
        # Generate new test with same subject
        new_test_id, questions = await generate_mcq_questions(
            subject=original_test["subject"],
            student_name=original_test["student_name"],
            student_email=original_test.get("student_email")
        )
        
        # Link retake to original test
        client.table("tests").update({
            "retake_of": test_id,
            "retake_number": original_test.get("retake_number", 0) + 1
        }).eq("test_id", new_test_id).execute()
        
        return GenerateTestResponse(
            test_id=new_test_id,
            subject=original_test["subject"],
            student_name=original_test["student_name"],
            questions=questions,
            status=TestStatus.GENERATED,
            message=f"Retake test generated (Attempt #{original_test.get('retake_number', 0) + 2})"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/start-test", response_model=StartTestResponse)
async def start_test(request: StartTestRequest):
    """Start the test timer"""
    try:
        start_time, end_time = await start_test_timer(request.test_id)
        time_remaining = int((end_time - start_time).total_seconds())
        
        return StartTestResponse(
            test_id=request.test_id,
            start_time=start_time,
            end_time=end_time,
            time_remaining_seconds=time_remaining,
            message="Test started successfully. Timer is running."
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/submit-test", response_model=SubmitTestResponse)
async def submit_test(request: SubmitTestRequest):
    """Submit test answers and get results"""
    try:
        score, total_questions, percentage, time_taken, results = await submit_test_answers(
            test_id=request.test_id,
            answers=request.answers
        )
        
        return SubmitTestResponse(
            test_id=request.test_id,
            score=score,
            total_questions=total_questions,
            percentage=percentage,
            time_taken_seconds=time_taken,
            results=results,
            status=TestStatus.SUBMITTED
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test-status/{test_id}")
async def get_test_status(test_id: str):
    """Get current test status and remaining time"""
    try:
        result = client.table("tests").select("*").eq("test_id", test_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Test not found")
        
        test = result.data[0]
        
        response = {
            "test_id": test_id,
            "status": test["status"],
            "subject": test["subject"],
            "student_name": test["student_name"],
            "retake_number": test.get("retake_number", 0)
        }
        
        if test["status"] == "started" and test.get("start_time") and test.get("end_time"):
            current_time = datetime.now(timezone.utc)  
            end_time = datetime.fromisoformat(test["end_time"])
            
            # if stored time is naive, attach UTC
            if end_time.tzinfo is None:
                end_time = end_time.replace(tzinfo=timezone.utc)
            
            if current_time > end_time:
                client.table("tests").update({"status": "expired"}).eq("test_id", test_id).execute()
                response["status"] = "expired"
                response["time_remaining_seconds"] = 0
            else:
                time_remaining = int((end_time - current_time).total_seconds())
                response["time_remaining_seconds"] = max(0, time_remaining)
                response["end_time"] = end_time.isoformat()
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test-results/{test_id}")
async def get_test_results(test_id: str):
    """Get test results if submitted"""
    try:
        result = client.table("submissions").select("*").eq("test_id", test_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Test results not found")
        
        return result.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/test-history/{student_email}")
async def get_test_history(student_email: str):
    """Get all tests taken by a student"""
    try:
        tests = client.table("tests").select("*").eq("student_email", student_email).order("created_at", desc=True).execute()
        
        history = []
        for test in tests.data:
            # Get submission if exists
            submission = client.table("submissions").select("*").eq("test_id", test["test_id"]).execute()
            
            history.append({
                "test_id": test["test_id"],
                "subject": test["subject"],
                "status": test["status"],
                "created_at": test["created_at"],
                "retake_number": test.get("retake_number", 0),
                "score": submission.data[0].get("score") if submission.data else None,
                "percentage": submission.data[0].get("percentage") if submission.data else None
            })
        
        return {"student_email": student_email, "test_history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/certificate/{test_id}")
async def generate_certificate(test_id: str):
    """
    Generate a certificate by properly replacing the template name with student name.
    Uses image overlay technique for better results with styled fonts.
    """
    try:
        # --- Step 1: Fetch dynamic data ---
        test_res = client.table("tests").select("student_name").eq("test_id", test_id).execute()
        if not test_res.data:
            raise HTTPException(status_code=404, detail="Test not found")
        test = test_res.data[0]
        student_name = test.get("student_name", "Anonymous")

        # --- Step 2: Load the PDF template ---
        template_path = "cert.pdf"
        doc = fitz.open(template_path)
        page = doc[0]

        # --- Step 3: Search for the placeholder name text ---
        placeholder_text = "Claudia Alves"
        text_instances = page.search_for(placeholder_text)
        
        if text_instances:
            name_rect = text_instances[0]
            
            # --- Step 4: Completely remove the old name ---
            # Method 1: Use redaction (most thorough)
            redact_rect = fitz.Rect(
                name_rect.x0 - 20,
                name_rect.y0 - 20,
                name_rect.x1 + 20,
                name_rect.y1 + 20
            )
            page.add_redact_annot(redact_rect, fill=(0, 0, 0))
            page.apply_redactions()
            
            # Method 2: Additional black rectangle overlay for extra coverage
            page.draw_rect(redact_rect, color=(0, 0, 0), fill=(0, 0, 0), overlay=True)
            
            # --- Step 5: Position new text precisely ---
            # Calculate center point of the original text
            center_x = name_rect.x0 + (name_rect.width / 2)
            baseline_y = name_rect.y1 - (name_rect.height * 0.25)  # Baseline position
            
            # Font settings - matching the cyan glow style
            font_size = 52  # Adjust based on your name length
            fontname = "tibo"  # Times Bold Italic (closest to script)
            text_color = (0.3, 0.88, 0.92)  # Cyan color
            
            # Calculate text dimensions for centering
            text_width = fitz.get_text_length(student_name, fontname=fontname, fontsize=font_size)
            
            # Center the text horizontally
            text_x = center_x - (text_width / 2)
            text_position = fitz.Point(text_x, baseline_y)
            
            # Insert the new name
            page.insert_text(
                text_position,
                student_name,
                fontsize=font_size,
                fontname=fontname,
                color=text_color,
                rotate=0,
            )
            
        else:
            # --- Fallback: Manual positioning if search fails ---
            # These coordinates are based on typical certificate layouts
            # Adjust if needed for your specific template
            
            # Define the name area manually (approximate based on image)
            manual_rect = fitz.Rect(180, 370, 420, 320)
            
            # Cover the area
            page.draw_rect(manual_rect, color=(0, 0, 0), fill=(0, 0, 0))
            
            # Calculate positioning
            center_x = manual_rect.x0 + (manual_rect.width / 2)
            baseline_y = manual_rect.y1 - (manual_rect.height * 0.3)
            
            font_size = 52
            fontname = "tibo"
            text_color = (0.3, 0.88, 0.92)
            
            text_width = fitz.get_text_length(student_name, fontname=fontname, fontsize=font_size)
            text_x = center_x - (text_width / 2)
            text_position = fitz.Point(text_x, baseline_y)
            
            page.insert_text(
                text_position,
                student_name,
                fontsize=font_size,
                fontname=fontname,
                color=text_color,
                rotate=0,
            )

        # --- Step 6: Save to buffer ---
        buffer = io.BytesIO()
        doc.save(buffer)
        doc.close()
        buffer.seek(0)

        # --- Step 7: Return PDF ---
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=certificate_{test_id}.pdf"
            },
        )

    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Certificate template not found.")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Certificate generation failed: {str(e)}"
        )
# # ==================== ATHENA CLASH & SOUL ARENA ====================
            # manual_rect = fitz.Rect(180, 370, 420, 320)

@router.post("/challenge/create")
async def create_challenge(
    subject: str,
    mode: str,  # "1v1", "1v1_ai", "2v2", "team"
    team_size: int,
    created_by: str,
    duration_minutes: int = 11
):
    """Create a new challenge"""
    try:
        if mode not in ["1v1", "1v1_ai", "2v2", "team"]:
            raise HTTPException(status_code=400, detail="Invalid mode")
        
        challenge_id = str(uuid.uuid4())
        challenge = {
            "id": challenge_id,
            "subject": subject,
            "mode": mode,
            "team_size": team_size,
            "created_by": created_by,
            "status": "pending",
            "duration_minutes": duration_minutes,
            "created_at": datetime.utcnow().isoformat()
        }

        res = client.table("challenges").insert(challenge).execute()
        if not res.data:
            raise HTTPException(status_code=500, detail="Failed to create challenge")

        # Auto-add creator as participant
        participant = {
            "challenge_id": challenge_id,
            "user_id": created_by,
            "team": 1,
            "score": 0,
            "finished": False,
            "joined_at": datetime.utcnow().isoformat()
        }
        client.table("challenge_participants").insert(participant).execute()

        # Auto-add AI for 1v1_ai mode
        if mode == "1v1_ai":
            ai_participant = {
                "challenge_id": challenge_id,
                "user_id": "AI_ATHENA",
                "team": 2,
                "score": 0,
                "finished": False,
                "joined_at": datetime.utcnow().isoformat()
            }
            client.table("challenge_participants").insert(ai_participant).execute()

        return {"challenge_id": challenge_id, "message": "Challenge created", "status": "pending"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/challenge/join")
async def join_challenge(challenge_id: str, user_id: str, team: int):
    """Join an existing challenge"""
    try:
        # Get challenge
        challenge_res = client.table("challenges").select("*").eq("id", challenge_id).execute()
        if not challenge_res.data:
            raise HTTPException(status_code=404, detail="Challenge not found")
        
        challenge = challenge_res.data[0]
        
        if challenge["status"] != "pending":
            raise HTTPException(status_code=400, detail=f"Challenge is {challenge['status']}")
        
        # Check if user already joined
        existing = client.table("challenge_participants").select("*").eq("challenge_id", challenge_id).eq("user_id", user_id).execute()
        if existing.data:
            raise HTTPException(status_code=400, detail="Already joined this challenge")
        
        # Get current team size
        team_count = client.table("challenge_participants").select("*").eq("challenge_id", challenge_id).eq("team", team).execute()
        if len(team_count.data) >= challenge["team_size"]:
            raise HTTPException(status_code=400, detail=f"Team {team} is full")
        
        # Add participant
        participant = {
            "challenge_id": challenge_id,
            "user_id": user_id,
            "team": team,
            "score": 0,
            "finished": False,
            "joined_at": datetime.utcnow().isoformat()
        }
        
        client.table("challenge_participants").insert(participant).execute()
        
        # Check if challenge is ready to start
        all_participants = client.table("challenge_participants").select("*").eq("challenge_id", challenge_id).execute()
        
        required_players = challenge["team_size"] * 2
        if challenge["mode"] == "1v1_ai":
            required_players = 2  # User + AI
        
        if len(all_participants.data) >= required_players:
            # Auto-start challenge
            client.table("challenges").update({"status": "ready"}).eq("id", challenge_id).execute()
            return {"message": "Joined successfully. Challenge is ready to start!", "challenge_id": challenge_id, "status": "ready"}
        
        return {"message": "Joined successfully. Waiting for more players...", "challenge_id": challenge_id, "status": "pending"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/challenge/test-update/{challenge_id}")
async def test_update_challenge(challenge_id: str):
    """Test endpoint to verify database updates work"""
    try:
        # Try a simple update
        result = client.table("challenges").update({
            "status": "active"
        }).eq("id", challenge_id).execute()
        
        return {
            "success": bool(result.data),
            "data": result.data,
            "count": len(result.data) if result.data else 0
        }
    except Exception as e:
        return {"error": str(e)}

@router.post("/challenge/start/{challenge_id}")
async def start_challenge(challenge_id: str, background_tasks: BackgroundTasks):
    """Start the challenge and generate questions"""
    try:
        # Get challenge
        challenge_res = client.table("challenges").select("*").eq("id", challenge_id).execute()
        if not challenge_res.data:
            raise HTTPException(status_code=404, detail="Challenge not found")
        
        challenge = challenge_res.data[0]
        
        if challenge["status"] not in ["pending", "ready"]:
            raise HTTPException(status_code=400, detail=f"Challenge already {challenge['status']}")
        
        # Generate test questions using agent
        test_id, questions_objects = await generate_mcq_questions(
            subject=challenge["subject"],
            student_name=f"Challenge_{challenge_id}",
            student_email=None
        )
        
        # Convert questions to dict format
        questions = []
        for q in questions_objects:
            questions.append({
                "question_id": q.question_id,
                "question": q.question,
                "options": {
                    "A": q.options.A,
                    "B": q.options.B,
                    "C": q.options.C,
                    "D": q.options.D
                }
            })
        
        # Calculate end time
        start_time = datetime.utcnow()
        end_time = start_time + timedelta(minutes=challenge["duration_minutes"])
        print("Is the status is update", test_id, challenge_id, start_time, end_time, )
        # Update challenge
        update_result = client.table("challenges").update({
            "status": "active",
            "test_id": test_id,
            "started_at": start_time.isoformat(),
            "ends_at": end_time.isoformat()
        }).eq("id", challenge_id).execute()
        print("Status updated successfully:", update_result)
        # Handle AI auto-play for 1v1_ai mode
        if challenge["mode"] == "1v1_ai":
            background_tasks.add_task(ai_auto_play, challenge_id, test_id)
        print("status222 is updated")

        return {
            "challenge_id": challenge_id,
            "test_id": test_id,
            "questions": questions,
            "status": "active",
            "ends_at": end_time.isoformat(),
            "duration_seconds": challenge["duration_minutes"] * 60
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start challenge: {str(e)}")

async def ai_auto_play(challenge_id: str, test_id: str):
    """Background task for AI to automatically answer questions"""
    import random
    import asyncio
    
    await asyncio.sleep(2)  # Small delay
    
    try:
        # Get questions from test
        test_res = client.table("tests").select("questions_data").eq("test_id", test_id).execute()
        if not test_res.data:
            return
        
        questions = test_res.data[0]["questions_data"]
        
        # AI answers with 60-70% accuracy
        ai_answers = {}
        ai_score = 0
        
        for i, q in enumerate(questions):
            correct_answer = q.get("answer")
            
            # 65% chance to answer correctly
            if random.random() < 0.75 and correct_answer:
                ai_answers[str(i)] = correct_answer
                ai_score += 1
            else:
                # Pick wrong answer
                options = list(q.get("options", {}).keys())
                wrong_opts = [opt for opt in options if opt != correct_answer]
                ai_answers[str(i)] = random.choice(wrong_opts) if wrong_opts else correct_answer
        
        # Update AI participant
        client.table("challenge_participants").update({
            "score": ai_score,
            "finished": True,
            "answers": ai_answers,
            "finished_at": datetime.utcnow().isoformat()
        }).eq("challenge_id", challenge_id).eq("user_id", "AI_ATHENA").execute()
        
        print(f"AI completed challenge {challenge_id} with score {ai_score}/{len(questions)}")
        
    except Exception as e:
        print(f"AI auto-play error: {str(e)}")
from pydantic import BaseModel

class ChallengeSubmission(BaseModel):
    challenge_id: str
    user_id: str
    answers: dict
@router.post("/challenge/submit")
async def submit_challenge(submission: ChallengeSubmission):
    """Submit answers for a challenge"""
    try:
        challenge_id = submission.challenge_id
        user_id = submission.user_id
        answers = submission.answers
        # Get challenge
        print("this is the data",challenge_id, user_id, answers)
        challenge_res = client.table("challenges").select("*").eq("id", challenge_id).execute()
        if not challenge_res.data:
            raise HTTPException(status_code=404, detail="Challenge not found")
        print("this is the data in vhas",challenge_res)
        challenge = challenge_res.data[0]
        
        if challenge["status"] != "active":
            raise HTTPException(status_code=400, detail=f"Challenge is {challenge['status']}")
        print("this is the data333")
        # Check if user is participant
        participant_res = client.table("challenge_participants").select("*").eq("challenge_id", challenge_id).eq("user_id", user_id).execute()
        if not participant_res.data:
            raise HTTPException(status_code=403, detail="Not a participant")
        
        participant = participant_res.data[0]
        print("this is the datafffff")
        if participant["finished"]:
            raise HTTPException(status_code=400, detail="Already submitted")
        print("this is the ddsdsdsatafffff")
        # Get correct answers from test
        test_id = challenge["test_id"]
        test_res = client.table("tests").select("questions_data").eq("test_id", test_id).execute()
        print("this ifdfdfdfdfdfdfs the datafffff")
        if not test_res.data:
            raise HTTPException(status_code=500, detail="Test data not found")
        
        questions = test_res.data[0]["questions_data"]
        print("this is dfdfdfdfdfdfdfdfthe datafffff")
        # Calculate score
        score = 0
        for i, q in enumerate(questions):
            correct_answer = q.get("answer")
            user_answer = answers.get(str(i))
            
            if user_answer == correct_answer:
                score += 1
        print("this is the ")
        # Update participant
        client.table("challenge_participants").update({
            "score": score,
            "finished": True,
            "answers": answers,
            "finished_at": datetime.utcnow().isoformat()
        }).eq("challenge_id", challenge_id).eq("user_id", user_id).execute()
        
        # Check if all participants finished
        all_participants = client.table("challenge_participants").select("*").eq("challenge_id", challenge_id).execute()
        
        all_finished = all(p["finished"] for p in all_participants.data)
        
        if all_finished:
            # Mark challenge as finished
            client.table("challenges").update({
                "status": "finished",
                "finished_at": datetime.utcnow().isoformat()
            }).eq("id", challenge_id).execute()
        
        return {
            "message": "Submission recorded",
            "score": score,
            "total": len(questions),
            "percentage": (score / len(questions)) * 100,
            "challenge_status": "finished" if all_finished else "active"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/challenge/results/{challenge_id}")
async def get_challenge_results(challenge_id: str):
    """Get challenge results and determine winner"""
    try:
        # Get challenge
        challenge_res = client.table("challenges").select("*").eq("id", challenge_id).execute()
        if not challenge_res.data:
            raise HTTPException(status_code=404, detail="Challenge not found")
        
        challenge = challenge_res.data[0]
        
        # Get all participants
        participants_res = client.table("challenge_participants").select("*").eq("challenge_id", challenge_id).execute()
        
        if not participants_res.data:
            raise HTTPException(status_code=404, detail="No participants found")
        
        participants = participants_res.data
        
        # Calculate team scores
        team_scores = {}
        for p in participants:
            team = p["team"]
            if team not in team_scores:
                team_scores[team] = {
                    "total_score": 0,
                    "members": []
                }
            
            team_scores[team]["total_score"] += p["score"]
            team_scores[team]["members"].append({
                "user_id": p["user_id"],
                "score": p["score"],
                "finished": p["finished"]
            })
        
        # Determine winner
        winner = None
        max_score = -1
        
        for team, data in team_scores.items():
            if data["total_score"] > max_score:
                max_score = data["total_score"]
                winner = f"Team {team}"
            elif data["total_score"] == max_score:
                winner = "Draw"
        
        return {
            "challenge_id": challenge_id,
            "subject": challenge["subject"],
            "mode": challenge["mode"],
            "status": challenge["status"],
            "winner": winner,
            "team_scores": team_scores,
            "started_at": challenge.get("started_at"),
            "finished_at": challenge.get("finished_at")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/challenge/status/{challenge_id}")
async def get_challenge_status(challenge_id: str):
    """Get real-time challenge status"""
    try:
        challenge_res = client.table("challenges").select("*").eq("id", challenge_id).execute()
        if not challenge_res.data:
            raise HTTPException(status_code=404, detail="Challenge not found")
        
        challenge = challenge_res.data[0]
        
        # Get participants
        participants = client.table("challenge_participants").select("*").eq("challenge_id", challenge_id).execute()
        
        # Calculate remaining time
        time_remaining = None
        if challenge["status"] == "active" and challenge.get("finished_at"):
            end_time = datetime.fromisoformat(challenge["finished_at"])
            current_time = datetime.utcnow()
            
            if current_time > end_time:
                # Auto-finish challenge
                client.table("challenges").update({
                    "status": "finished",
                    "finished_at": datetime.utcnow().isoformat()
                }).eq("id", challenge_id).execute()
                time_remaining = 0
            else:
                time_remaining = int((end_time - current_time).total_seconds())
        
        return {
            "challenge_id": challenge_id,
            "status": challenge["status"],
            "subject": challenge["subject"],
            "mode": challenge["mode"],
            "time_remaining_seconds": time_remaining,
            "participants_count": len(participants.data),
            "participants_finished": sum(1 for p in participants.data if p["finished"]),
            "started_at": challenge.get("started_at"),
            "finished_at": challenge.get("finished_at")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/challenges/active")
async def get_active_challenges():
    """Get all active/pending challenges"""
    try:
        challenges = client.table("challenges").select("*").in_("status", ["pending", "ready", "active"]).order("created_at", desc=True).execute()
        
        result = []
        for c in challenges.data:
            participants = client.table("challenge_participants").select("*").eq("challenge_id", c["id"]).execute()
            
            result.append({
                "challenge_id": c["id"],
                "subject": c["subject"],
                "mode": c["mode"],
                "status": c["status"],
                "team_size": c["team_size"],
                "created_by": c["created_by"],
                "participants_count": len(participants.data),
                "created_at": c["created_at"]
            })
        
        return {"challenges": result}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user/challenges/{user_id}")
async def get_user_challenges(user_id: str):
    """Get all challenges for a specific user"""
    try:
        # Get user's participations
        participations = client.table("challenge_participants").select("challenge_id").eq("user_id", user_id).execute()
        
        challenge_ids = [p["challenge_id"] for p in participations.data]
        
        if not challenge_ids:
            return {"user_id": user_id, "challenges": []}
        
        # Get challenge details
        challenges = client.table("challenges").select("*").in_("id", challenge_ids).order("created_at", desc=True).execute()
        
        result = []
        for c in challenges.data:
            # Get user's score
            user_data = client.table("challenge_participants").select("*").eq("challenge_id", c["id"]).eq("user_id", user_id).execute()
            
            result.append({
                "challenge_id": c["id"],
                "subject": c["subject"],
                "mode": c["mode"],
                "status": c["status"],
                "user_score": user_data.data[0]["score"] if user_data.data else 0,
                "user_finished": user_data.data[0]["finished"] if user_data.data else False,
                "created_at": c["created_at"]
            })
        
        return {"user_id": user_id, "challenges": result}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== HEALTH & INFO ====================

@router.get("/")
async def root():
    return {
        "message": "Athena MCQ & Challenge System",
        "version": "2.0.0",
        "features": {
            "premium_tests": [
                "IQ Test", "EQ Test", "Big Five Personality",
                "Cognitive Psychology", "English Skills", "Math Logic",
                "Science IQ", "Tech Literacy", "General Knowledge",
                "Soul Age Quiz", "Introvert-Extrovert Meter"
            ],
            "challenge_modes": [
                "1v1 User vs User",
                "1v1 User vs AI (Athena)",
                "2v2 Team Battle",
                "Team Battle (up to 5v5)"
            ]
        },
        "endpoints": {
            "tests": {
                "generate": "POST /generate-test",
                "retake": "POST /retake-test/{test_id}",
                "start": "POST /start-test",
                "submit": "POST /submit-test",
                "status": "GET /test-status/{test_id}",
                "results": "GET /test-results/{test_id}",
                "history": "GET /test-history/{student_email}",
                "certificate": "GET /certificate/{test_id}"
            },
            "challenges": {
                "create": "POST /challenge/create",
                "join": "POST /challenge/join",
                "start": "POST /challenge/start/{challenge_id}",
                "submit": "POST /challenge/submit",
                "results": "GET /challenge/results/{challenge_id}",
                "status": "GET /challenge/status/{challenge_id}",
                "active": "GET /challenges/active",
                "user_challenges": "GET /user/challenges/{user_id}"
            }
        }
    }

@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "database": "connected",
            "ai_agent": "active"
        }
    }
