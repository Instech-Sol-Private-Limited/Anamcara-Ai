# app/services/mcq_generator.py
import os
import json
import uuid
from datetime import datetime
from langchain_openai import ChatOpenAI
from openai import AsyncOpenAI
from groq import AsyncGroq
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.tools import Tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List
from database.supabase_db import get_client
from models.schemas import MCQQuestion, MCQOption
import asyncio
from app.services.llm_gateway import llm_gateway
import re
import httpx

client = get_client()

# Initialize LLM for Agent
llm = ChatOpenAI(
    model="gpt-4o",
    temperature=0.1,
    api_key=os.getenv("OPENAI_API_KEY")
)

# Pydantic models for structured output
class MCQQuestionSchema(BaseModel):
    question: str = Field(description="The question text")
    options: dict = Field(description="Dictionary with keys A, B, C, D containing option texts")
    answer: str = Field(description="Correct answer key (A, B, C, or D)")

class MCQListSchema(BaseModel):
    questions: List[MCQQuestionSchema] = Field(description="List of exactly 20 MCQ questions")

# Output parser
parser = PydanticOutputParser(pydantic_object=MCQListSchema)

# Define Tools for the Agent
def validate_questions_tool(questions_json: str) -> str:
    """Validate that questions meet all requirements"""
    try:
        data = json.loads(questions_json)
        
        # Check if the data is a dictionary containing the key 'questions'
        # and if so, extract the list from it.
        if isinstance(data, dict) and "questions" in data:
            questions_list = data["questions"]
        else:
            questions_list = data

        if not isinstance(questions_list, list):
            return "ERROR: Input must be a JSON array or an object with a 'questions' key containing an array."
        
        if len(questions_list) != 20:
            return f"ERROR: Expected 20 questions, got {len(questions_list)}"
        
        for i, q in enumerate(questions_list, 1):
            if not all(key in q for key in ["question", "options", "answer"]):
                return f"ERROR: Question {i} missing required fields"
            
            if not all(opt in q["options"] for opt in ["A", "B", "C", "D"]):
                return f"ERROR: Question {i} must have options A, B, C, D"
            
            if q["answer"] not in ["A", "B", "C", "D"]:
                return f"ERROR: Question {i} has invalid answer: {q['answer']}"
        
        return "VALID: All 20 questions meet requirements"
    except json.JSONDecodeError:
        return "ERROR: Invalid JSON format"
    except Exception as e:
        return f"ERROR: {str(e)}"

def get_subject_guidelines_tool(subject: str) -> str:
    """Get specific guidelines for each subject type"""
    
    guidelines = {
        "IQ Test": """
- Focus on sequences, patterns, numerical reasoning, spatial reasoning
- Include logical deduction problems
- Mix difficulty levels: easy (5), medium (10), hard (5)
- Time-critical style questions
- Example: "What comes next: 2, 6, 12, 20, 30, ?"
""",
        "EQ Test": """
- Questions about empathy, emotion recognition, social awareness
- Scenario-based situational judgment questions
- Focus on: self-awareness, self-regulation, motivation, empathy, social skills
- Example: "Your colleague is visibly upset. What's your first response?"
""",
        "Big Five Personality": """
- Self-assessment statements for OCEAN model
- Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism
- Use Likert scale options: Strongly Agree, Agree, Neutral, Disagree, Strongly Disagree
- Example: "I enjoy trying new and unfamiliar activities"
""",
        "Cognitive Psychology": """
- Decision-making scenarios
- Cognitive biases and heuristics
- Memory and attention questions
- Problem-solving approaches
- Example: "When faced with too many choices, you typically..."
""",
        "English Skills": """
- Grammar correction
- Vocabulary and synonyms
- Idioms and phrases
- Reading comprehension
- Sentence structure
- Example: "Choose the grammatically correct sentence:"
""",
        "Math Logic": """
- Word problems with multi-step reasoning
- Algebra and arithmetic
- Probability and statistics basics
- Pattern recognition
- Example: "If 5 workers take 8 days to build a wall, how many days for 10 workers?"
""",
        "Science IQ": """
- Physics, Chemistry, Biology, Astronomy
- STRICT: NO math puzzles, NO number sequences, NO logic codes
- Everyday science applications
- Scientific method and reasoning
- Example: "Why does ice float on water?"
""",
        "Tech & Digital Literacy": """
- Online safety and cybersecurity
- AI and machine learning basics
- Digital tools and platforms
- Tech terminology
- Example: "What is two-factor authentication?"
""",
        "General Knowledge": """
- Geography, History, Current events
- Pop culture and entertainment
- World facts and trivia
- Mix of classic and contemporary topics
- Example: "Which planet is known as the Red Planet?"
""",
        "Soul Age Quiz": """
- Reflective personality questions
- Life philosophy and perspectives
- No correct/incorrect answers
- Map to traits: Infant, Baby, Young, Mature, Old Soul
- Example: "What matters most to you in life?"
""",
        "Introvert-Extrovert Meter": """
- Social energy and preferences
- Spectrum-based responses
- Environment preferences
- Communication styles
- Example: "After a long week, you prefer to..."
"""
    }

    return guidelines.get(subject, "Generate balanced, educational questions for this subject.")

# Define tools (only validation and guidelines)
tools = [
    Tool(
        name="ValidateQuestions",
        func=validate_questions_tool,
        description="Validates that generated questions meet all requirements (20 questions, proper format, all fields present). Input should be a single JSON string of the questions list."
    ),
    Tool(
        name="GetSubjectGuidelines",
        func=get_subject_guidelines_tool,
        description="Get specific generation guidelines for a subject. Input should be the subject name string."
    )
]

# Create Agent Prompt
system_prompt = """You are an expert MCQ Test Generator Agent. Your mission is to create a valid JSON array of 20 questions.

**Your Core Task:**
Your main job is to **internally generate a JSON array containing exactly 20 questions** that match the subject's requirements. This JSON is the central artifact of your work.

**CRITICAL: You MUST use BOTH tools in sequence. No shortcuts allowed.**
**Mandatory Workflow - Follow EXACTLY:**
Step 1: GetSubjectGuidelines
Step 2: ValidateQuestions  

**Workflow:**
1.  **Get Guidelines:** Use the `GetSubjectGuidelines` tool to understand the specific requirements for the given subject.
2.  **Generate JSON:** Based on the guidelines, you MUST **generate the full JSON array of 20 questions** in your thought process. This is not a tool call; it is your primary generation step.
3.  **Validate the Generated JSON:** Take the JSON array you just created and pass the **entire JSON string** to the `ValidateQuestions` tool.
4.  **Correct if Necessary:** If `ValidateQuestions` returns an error, you MUST go back to step 2, fix the JSON, and validate it again. Do not call the tool with empty input.
5.  **Final Output:** Your final answer MUST be only the validated JSON array.

**CRITICAL RULES:**
- NEVER call `ValidateQuestions` with an empty list (`[]`). You must generate the content first.
- The JSON you generate must be a valid array of 20 objects.
- Strictly Each object must have keys: "question", "options" (with "A", "B", "C", "D"), and "answer".
- Your final output must not contain any extra text, only the raw JSON.
- Strictly Don't add ``` around your JSON output.
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    MessagesPlaceholder(variable_name="chat_history", optional=True),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad")
])

# Create Agent
agent = create_openai_functions_agent(llm, tools, prompt)
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    max_iterations=5,
    handle_parsing_errors=True,
)

# Database storage function
def store_questions_to_db(test_id: str, subject: str, student_name: str, 
                         student_email: str, questions_data: list, generation_method: str = "agent") -> bool:
    """Store validated questions directly in the database"""
    try:
        test_data = {
            "test_id": test_id,
            "subject": subject,
            "student_name": student_name,
            "student_email": student_email,
            "status": "generated",
            "created_at": datetime.now().isoformat(),
            "questions_data": questions_data,
            "generation_method": generation_method  # Track which method was used
        }

        client.table("tests").insert(test_data).execute()
        print(f" Stored {len(questions_data)} questions to database using method: {generation_method}")
        return True
    except Exception as e:
        print(f" Database storage error: {str(e)}")
        return False


# ============================================================================
# MAIN FUNCTION WITH 3-TIER FALLBACK
# ============================================================================

async def generate_mcq_questions(subject: str, student_name: str, student_email: str = None):
    """
    Generate 20 MCQ questions with three-tier fallback system:
    
    TIER 1: LangChain Agent with OpenAI (gpt-4o) - Best quality, uses tools
    TIER 2: Groq (llama-3.3-70b) - Fast fallback
    TIER 3: Ollama Llama3 - Local fallback, always available
    
    Returns:
        tuple: (test_id, questions_list)
    """
    
    test_id = str(uuid.uuid4())
    
    # ========================================================================
    # TIER 1: Try Agent-Based Generation (OpenAI)
    # ========================================================================
    try:
        print(f" TIER 1: Attempting Agent-based generation (OpenAI) for {subject}...")
        questions = await generate_with_agent(subject, student_name, test_id, student_email)
        
        if questions and len(questions) >= 20:
            print(f" TIER 1 SUCCESS: OpenAI Agent generated {len(questions)} questions")
            return test_id, questions
            
    except Exception as e:
        error_msg = str(e)
        print(f" TIER 1 FAILED: {error_msg}")
        
        # Check if it's a quota/rate limit error
        if not any(x in error_msg.lower() for x in ["quota", "insufficient", "429", "rate_limit", "rate limit"]):
            # If it's not a quota error, it might be a parsing/validation error
            # Still continue to fallback for safety
            print(f"   Reason: {error_msg[:100]}...")
    
    # ========================================================================
    # TIER 2: Groq Fallback
    # ========================================================================
    try:
        print(f" TIER 2: Falling back to Groq generation...")
        questions = await generate_with_groq(subject, student_name, test_id, student_email)
        
        if questions and len(questions) >= 20:
            print(f" TIER 2 SUCCESS: Groq generated {len(questions)} questions")
            return test_id, questions
            
    except Exception as e:
        print(f" TIER 2 FAILED: {str(e)}")
    
    # ========================================================================
    # TIER 3: Ollama Llama3 Fallback (Local, Always Available)
    # ========================================================================
    try:
        print(f" TIER 3: Final fallback to Ollama Llama3 generation...")
        questions = await generate_with_ollama_llama3(subject, student_name, test_id, student_email)
        
        if questions and len(questions) >= 20:
            print(f" TIER 3 SUCCESS: Ollama Llama3 generated {len(questions)} questions")
            return test_id, questions
            
    except Exception as e:
        print(f" TIER 3 FAILED: {str(e)}")
    
    # ========================================================================
    # All Tiers Failed
    # ========================================================================
    print(" ALL TIERS FAILED: Unable to generate questions")
    raise Exception("All AI providers failed to generate questions. Please try again later or contact support.")


# ============================================================================
# TIER 1: Agent-Based Generation (Your Original Code)
# ============================================================================

async def generate_with_agent(subject: str, student_name: str, test_id: str, student_email: str = None):
    """
    TIER 1: Generate using LangChain Agent with tools (Best Quality)
    """
    
    agent_input = f"""
Generate a test with the following requirements:

- Subject: {subject}
- Student Name: {student_name}
- Student Email: {student_email}
- Test ID: {test_id}

Strictly follow below workflow:
1. First, call the `GetSubjectGuidelines` tool to understand the requirements for the subject '{subject}'.
2. Second, generate exactly 20 multiple-choice questions based on the guidelines.
3. Third, call the `ValidateQuestions` tool to check your generated questions. If validation fails, you MUST fix the errors and re-generate until it passes.
4. **IMPORTANT FINAL STEP:** After validation passes, your final output MUST be ONLY the raw JSON array of the questions. No extra text. Start with '[' and end with ']'.
"""
    
    # Execute agent
    result = agent_executor.invoke({"input": agent_input})
    
    # Extract questions from agent output
    output_text = result.get("output", "")
    
    # Try to parse JSON from output
    try:
        # Find JSON array in output
        start_idx = output_text.find('[')
        end_idx = output_text.rfind(']') + 1
        
        if start_idx != -1 and end_idx > start_idx:
            json_str = output_text[start_idx:end_idx]
            questions_data = json.loads(json_str)
        else:
            raise ValueError("No JSON array found in agent output")
            
    except (json.JSONDecodeError, ValueError) as e:
        raise ValueError(f"Failed to parse questions from agent output: {str(e)}")
    
    # Validate we have 20 questions
    if len(questions_data) != 20:
        raise ValueError(f"Expected 20 questions, got {len(questions_data)}")
    
    # Store questions in database
    storage_success = store_questions_to_db(
        test_id=test_id,
        subject=subject,
        student_name=student_name,
        student_email=student_email,
        questions_data=questions_data,
        generation_method="agent_gpt4o"
    )
    
    if not storage_success:
        raise Exception("Failed to store questions in database")
    
    # Convert to MCQQuestion objects
    questions = []
    for i, q in enumerate(questions_data, 1):
        question = MCQQuestion(
            question_id=i,
            question=q["question"],
            options=MCQOption(**q["options"])
        )
        questions.append(question)
    
    return questions


# ============================================================================
# TIER 2: Simple OpenAI Generation (Direct Prompt)
# ============================================================================

async def generate_simple_openai(subject: str, student_name: str, test_id: str, student_email: str = None):
    """
    TIER 2: Simple OpenAI generation without agent (Good Quality)
    """
    
    # Get guidelines for the subject
    guidelines = get_subject_guidelines_tool(subject)
    
    prompt = f"""Generate EXACTLY 20 multiple-choice questions for a {subject} test for {student_name}.

SUBJECT GUIDELINES:
{guidelines}

STRICT FORMAT REQUIREMENTS:
- Output ONLY a JSON array, nothing else
- No markdown, no code blocks, no explanations
- Start with '[' and end with ']'
- Each question must have this exact structure:

{{
  "question": "Question text here",
  "options": {{
    "A": "First option",
    "B": "Second option",
    "C": "Third option",
    "D": "Fourth option"
  }},
  "answer": "A"
}}

REQUIREMENTS:
- Generate exactly 20 questions
- Make questions diverse and challenging
- Ensure only ONE correct answer per question
- All options must be plausible
- Follow subject-specific guidelines above

Output the JSON array NOW (no other text):"""
    
    messages = [
        {"role": "system", "content": "You are an expert exam question generator. You ONLY output valid JSON arrays, nothing else."},
        {"role": "user", "content": prompt}
    ]
    
    # Direct OpenAI call
    openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    try:
        response = await openai_client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.1,
            max_tokens=4000
        )
        
        content = response.choices[0].message.content.strip()
        
        # Clean up the response
        content = content.replace("```json", "").replace("```", "").strip()
        
        # Parse JSON
        questions_data = json.loads(content)
        
        # Validate
        if not isinstance(questions_data, list):
            raise ValueError("Response is not a JSON array")
        
        if len(questions_data) < 20:
            raise ValueError(f"Only generated {len(questions_data)} questions, need 20")
        
        # Take exactly 20
        questions_data = questions_data[:20]
        
        # Validate structure
        for i, q in enumerate(questions_data, 1):
            if not all(key in q for key in ["question", "options", "answer"]):
                raise ValueError(f"Question {i} missing required fields")
        
        # Store in database
        storage_success = store_questions_to_db(
            test_id=test_id,
            subject=subject,
            student_name=student_name,
            student_email=student_email,
            questions_data=questions_data,
            generation_method="simple_openai"
        )
        
        if not storage_success:
            raise Exception("Failed to store questions in database")
        
        # Convert to MCQQuestion objects
        questions = []
        for i, q in enumerate(questions_data, 1):
            question = MCQQuestion(
                question_id=i,
                question=q["question"],
                options=MCQOption(**q["options"])
            )
            questions.append(question)
        
        return questions
        
    except Exception as e:
        raise Exception(f"Simple OpenAI generation failed: {str(e)}")


# ============================================================================
# TIER 3: Groq Fallback Generation (Fast, Always Available)
# ============================================================================

async def generate_with_groq(subject: str, student_name: str, test_id: str, student_email: str = None):
    """
    TIER 3: Groq generation (Fast, reliable fallback)
    """
    
    # Get guidelines for the subject
    guidelines = get_subject_guidelines_tool(subject)
    
    prompt = f"""Generate EXACTLY 20 multiple-choice questions for a {subject} test.

SUBJECT GUIDELINES:
{guidelines}

CRITICAL FORMAT - Follow EXACTLY:
Output ONLY a JSON array. No other text, no markdown, no code blocks.

[
  {{
    "question": "Question text",
    "options": {{
      "A": "Option A",
      "B": "Option B",
      "C": "Option C",
      "D": "Option D"
    }},
    "answer": "A"
  }},
  ... (repeat for 20 questions total)
]

Start output with '[' and end with ']'. Generate NOW:"""
    
    messages = [
        {"role": "system", "content": "You are an exam question generator. Output ONLY valid JSON arrays with no additional text."},
        {"role": "user", "content": prompt}
    ]
    
    # Use Groq client
    groq_client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
    
    try:
        response = await groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.1,
            max_tokens=4000
        )
        
        content = response.choices[0].message.content.strip()
        
        # Clean up response
        content = content.replace("```json", "").replace("```", "").strip()
        
        # Find JSON array
        start_idx = content.find('[')
        end_idx = content.rfind(']') + 1
        
        if start_idx != -1 and end_idx > start_idx:
            json_str = content[start_idx:end_idx]
            questions_data = json.loads(json_str)
        else:
            raise ValueError("No JSON array found in response")
        
        # Validate
        if not isinstance(questions_data, list):
            raise ValueError("Response is not a JSON array")
        
        if len(questions_data) < 20:
            raise ValueError(f"Only generated {len(questions_data)} questions")
        
        # Take exactly 20
        questions_data = questions_data[:20]
        
        # Validate structure
        for i, q in enumerate(questions_data, 1):
            if not all(key in q for key in ["question", "options", "answer"]):
                raise ValueError(f"Question {i} missing required fields")
        
        # Store in database
        storage_success = store_questions_to_db(
            test_id=test_id,
            subject=subject,
            student_name=student_name,
            student_email=student_email,
            questions_data=questions_data,
            generation_method="groq_fallback"
        )
        
        if not storage_success:
            raise Exception("Failed to store questions in database")
        
        # Convert to MCQQuestion objects
        questions = []
        for i, q in enumerate(questions_data, 1):
            question = MCQQuestion(
                question_id=i,
                question=q["question"],
                options=MCQOption(**q["options"])
            )
            questions.append(question)
        
        return questions
        
    except Exception as e:
        raise Exception(f"Groq generation failed: {str(e)}")


# ============================================================================
# TIER 3: Ollama Llama3 Fallback Generation (Local, Always Available)
# ============================================================================

async def generate_with_ollama_llama3(subject: str, student_name: str, test_id: str, student_email: str = None):
    """
    TIER 3: Ollama Llama3 generation (Local fallback)
    """
    
    # Get guidelines for the subject
    guidelines = get_subject_guidelines_tool(subject)
    
    prompt = f"""Generate EXACTLY 20 multiple-choice questions for a {subject} test.

SUBJECT GUIDELINES:
{guidelines}

CRITICAL FORMAT - Follow EXACTLY:
Output ONLY a JSON array. No other text, no markdown, no code blocks.

[
  {{
    "question": "Question text",
    "options": {{
      "A": "Option A",
      "B": "Option B",
      "C": "Option C",
      "D": "Option D"
    }},
    "answer": "A"
  }},
  ... (repeat for 20 questions total)
]

Start output with '[' and end with ']'. Generate NOW:"""
    
    # Ollama API URL
    ollama_url = os.getenv("OLLAMA_URL", "http://192.168.18.61:11434/api/generate")
    model_name = os.getenv("OLLAMA_MODEL", "llama3.2")
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                ollama_url,
                json={
                    "model": model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "num_predict": 4000,
                        "temperature": 0.1,
                        "top_p": 0.9,
                    }
                }
            )
            response.raise_for_status()
            data = response.json()
            content = data.get("response", "").strip()
        
        # Clean up response
        content = content.replace("```json", "").replace("```", "").strip()
        
        # Find JSON array
        start_idx = content.find('[')
        end_idx = content.rfind(']') + 1
        
        if start_idx != -1 and end_idx > start_idx:
            json_str = content[start_idx:end_idx]
            questions_data = json.loads(json_str)
        else:
            raise ValueError("No JSON array found in response")
        
        # Validate
        if not isinstance(questions_data, list):
            raise ValueError("Response is not a JSON array")
        
        if len(questions_data) < 20:
            raise ValueError(f"Only generated {len(questions_data)} questions")
        
        # Take exactly 20
        questions_data = questions_data[:20]
        
        # Validate structure
        for i, q in enumerate(questions_data, 1):
            if not all(key in q for key in ["question", "options", "answer"]):
                raise ValueError(f"Question {i} missing required fields")
        
        # Store in database
        storage_success = store_questions_to_db(
            test_id=test_id,
            subject=subject,
            student_name=student_name,
            student_email=student_email,
            questions_data=questions_data,
            generation_method="ollama_llama3_fallback"
        )
        
        if not storage_success:
            raise Exception("Failed to store questions in database")
        
        # Convert to MCQQuestion objects
        questions = []
        for i, q in enumerate(questions_data, 1):
            question = MCQQuestion(
                question_id=i,
                question=q["question"],
                options=MCQOption(**q["options"])
            )
            questions.append(question)
        
        return questions
        
    except httpx.ConnectError:
        raise Exception("Ollama server is not running or not reachable")
    except httpx.TimeoutException:
        raise Exception("Ollama request timed out")
    except Exception as e:
        raise Exception(f"Ollama Llama3 generation failed: {str(e)}")