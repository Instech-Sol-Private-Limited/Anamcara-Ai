# app/mcq_generator.py
import os
import json
import uuid
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.tools import Tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List
from database.supabase_db import get_client
from models.schemas import MCQQuestion, MCQOption
import asyncio

client = get_client()

# Initialize LLM
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

# NEW: Direct database storage function
def store_questions_to_db(test_id: str, subject: str, student_name: str, 
                         student_email: str, questions_data: list) -> bool:
    """Store validated questions directly in the database"""
    try:
        test_data = {
            "test_id": test_id,
            "subject": subject,
            "student_name": student_name,
            "student_email": student_email,
            "status": "generated",
            "created_at": datetime.now().isoformat(),
            "questions_data": questions_data
        }

        client.table("tests").insert(test_data).execute()
        return True
    except Exception as e:
        print(f"Database storage error: {str(e)}")
        return False

async def generate_mcq_questions(subject: str, student_name: str, student_email: str = None):
    """Generate 20 MCQ questions using LangChain Agent and store in DB"""
    
    try:
        # Generate unique test ID
        test_id = str(uuid.uuid4())
        
        # Agent input - simplified without StoreQuestions step
        agent_input = f"""
Generate a test with the following requirements:

- Subject: {subject}
- Student Name: {student_name}
- Student Email: {student_email}
- Test ID: {test_id}

Strictly follow below workflow:
Here is the exact workflow you MUST follow:
1. First, call the `GetSubjectGuidelines` tool to understand the requirements for the subject '{subject}'.
2. Second, generate exactly 20 multiple-choice questions based on the guidelines.
3. Third, call the `ValidateQuestions` tool to check your generated questions. If validation fails, you MUST fix the errors and re-generate until it passes. Do not give up.
4. **IMPORTANT FINAL STEP:** After validation passes, your final, conclusive output MUST be ONLY the raw JSON array of the questions you generated. Do not include any other text, greetings, summaries, or explanations. The entire response should start with '[' and end with ']'.
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
            questions_data=questions_data
        )
        
        if not storage_success:
            raise Exception("Failed to store questions in database")
        
        # Convert to MCQQuestion objects (without answers for response)
        questions = []
        for i, q in enumerate(questions_data, 1):
            question = MCQQuestion(
                question_id=i,
                question=q["question"],
                options=MCQOption(**q["options"])
            )
            questions.append(question)
        
        return test_id, questions
        
    except Exception as e:
        raise Exception(f"Agent failed to generate questions: {str(e)}")