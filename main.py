import os
import json

from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from google import genai
from google.genai import types


# Load .env
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

if not API_KEY or API_KEY == "YOUR_API_KEY":
    raise RuntimeError(
        "GEMINI_API_KEY is missing. Please add your Gemini API key to .env"
    )

client = genai.Client(api_key=API_KEY)


# Create FastAPI app
app = FastAPI(
    title="EduGenie",
    description="Google Gemini Powered Learning Assistant",
    version="1.0.0"
)


# Static files
app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static"
)

templates = Jinja2Templates(directory="templates")


# Request models
class TextRequest(BaseModel):
    text: str


class QuestionRequest(BaseModel):
    question: str


class LearningRequest(BaseModel):
    topic: str
    level: str = "beginner"


# Gemini function
def ask_gemini(prompt: str) -> str:
    try:
        response = client.models.generate_content(
    model=MODEL_NAME,
    contents=prompt,
    config=types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(
            thinking_level="low"
        )
    )
)

        if not response.text:
            raise Exception("Gemini returned an empty response.")

        return response.text.strip()

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Gemini API error: {str(e)}"
        )


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={}
    )


# Health check
@app.get("/health")
async def health():
    return {
        "status": "ok",
        "app": "EduGenie",
        "model": MODEL_NAME
    }


# Question & Answer
@app.post("/qa")
async def question_answer(request: QuestionRequest):

    if not request.question.strip():
        raise HTTPException(
            status_code=400,
            detail="Please enter a question."
        )

    prompt = f"""
You are EduGenie, an educational AI assistant.

Answer the student's question clearly and accurately.

Question:
{request.question}

Instructions:
- Explain in simple language.
- Give a useful example if appropriate.
- Keep the answer educational.
- Use bullet points when useful.
"""

    result = ask_gemini(prompt)

    return {"result": result}


# Explain topic
@app.post("/explain")
async def explain(request: TextRequest):

    if not request.text.strip():
        raise HTTPException(
            status_code=400,
            detail="Please enter a topic to explain."
        )

    prompt = f"""
You are EduGenie, a learning assistant.

Explain this topic to a student in very simple language.

Topic:
{request.text}

Instructions:
- Start with a simple definition.
- Explain the important points.
- Give a simple real-world example.
- Avoid unnecessary technical language.
- Use headings and bullet points where useful.
"""

    result = ask_gemini(prompt)

    return {"result": result}


# Summarize text
@app.post("/summarize")
async def summarize(request: TextRequest):

    if not request.text.strip():
        raise HTTPException(
            status_code=400,
            detail="Please enter text to summarize."
        )

    prompt = f"""
You are EduGenie, an educational summarization assistant.

Summarize the following educational content.

Content:
{request.text}

Instructions:
- Keep the important information.
- Remove unnecessary repetition.
- Use simple language.
- Present the summary using short paragraphs or bullet points.
"""

    result = ask_gemini(prompt)

    return {"result": result}


# Generate quiz
@app.post("/quiz")
async def quiz(request: TextRequest):

    if not request.text.strip():
        raise HTTPException(
            status_code=400,
            detail="Please enter a topic or passage."
        )

    prompt = f"""
You are EduGenie, an educational quiz generator.

Create exactly 3 multiple-choice questions based on:

{request.text}

Each question must contain exactly 4 options.

Return ONLY valid JSON.

Use exactly this structure:

{{
    "questions": [
        {{
            "question": "Question text",
            "options": [
                "Option A",
                "Option B",
                "Option C",
                "Option D"
            ],
            "correct_answer": "One of the four options",
            "explanation": "Short explanation"
        }}
    ]
}}

Rules:
- Exactly 3 questions.
- Exactly 4 options per question.
- correct_answer must exactly match one option.
- Do not add markdown.
- Do not add text outside the JSON.
"""

    raw_result = ask_gemini(prompt)

    raw_result = raw_result.strip()

    if raw_result.startswith("```"):
        raw_result = raw_result.replace("```json", "")
        raw_result = raw_result.replace("```", "")
        raw_result = raw_result.strip()

    try:
        quiz_data = json.loads(raw_result)

    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500,
            detail="Gemini returned invalid quiz JSON."
        )

    questions = quiz_data.get("questions", [])

    if len(questions) != 3:
        raise HTTPException(
            status_code=500,
            detail="Quiz generation did not return exactly 3 questions."
        )

    for question in questions:

        if len(question.get("options", [])) != 4:
            raise HTTPException(
                status_code=500,
                detail="Each quiz question must have exactly 4 options."
            )

        if question.get("correct_answer") not in question.get("options"):
            raise HTTPException(
                status_code=500,
                detail="Correct answer must match one of the options."
            )

    return {"questions": questions}


# Learning path
@app.post("/learn/recommendations")
async def learning_recommendations(request: LearningRequest):

    if not request.topic.strip():
        raise HTTPException(
            status_code=400,
            detail="Please enter a learning topic."
        )

    valid_levels = [
        "beginner",
        "intermediate",
        "advanced"
    ]

    level = request.level.lower()

    if level not in valid_levels:
        level = "beginner"

    prompt = f"""
You are EduGenie, a personalized learning assistant.

Create a learning path for:

Topic:
{request.topic}

Student level:
{level}

Create a structured learning roadmap.

Include:
1. Beginner concepts
2. Intermediate concepts
3. Advanced concepts
4. Recommended learning order
5. Suggested timeline
6. Practice activities
7. Useful resources or resource types

Use simple language and clear headings.
"""

    result = ask_gemini(prompt)

    return {"result": result}


# App information
@app.get("/info")
async def info():

    return {
        "application": "EduGenie",
        "version": "1.0.0",
        "model": MODEL_NAME,
        "features": [
            "Question Answering",
            "Simple Explanation",
            "Quiz Generation",
            "Text Summarization",
            "Learning Path Recommendations"
        ]
    }