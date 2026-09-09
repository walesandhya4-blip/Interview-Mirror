```python
import os

from dotenv import load_dotenv
from openai import OpenAI


# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================

load_dotenv()


# =========================================================
# GET OPENAI API KEY
# =========================================================

API_KEY = os.getenv("OPENAI_API_KEY", "").strip()

if not API_KEY:
    raise RuntimeError(
        "OPENAI_API_KEY is missing. "
        "Please add it to your .env file."
    )


# =========================================================
# CREATE OPENAI CLIENT
# =========================================================

client = OpenAI(
    api_key=Sk-proj-aq7CH6c40vLcdXvlD64zlJytsAZANlooRKS8nwPcggUvG0zaGdLwYRG31Ayq45WOUNF1b_5TgbT3BlbkFJSfpu1LvRYaK3iujmp1R9EtK8nkUIa9fOblW7LdGaswov7jF0QhbIZQGY3z07mOtqDC4Z6_JY0A
)


# =========================================================
# OPENAI MODEL
# =========================================================

OPENAI_MODEL = os.getenv(
    "OPENAI_MODEL",
    "gpt-5-mini"
).strip()


# =========================================================
# GENERATE INTERVIEW QUESTION
# =========================================================

def generate_interview_question(
    department,
    domain,
    category,
    difficulty
):

    prompt = f"""
You are an AI interviewer for an application called Interview Mirror.

Generate ONE interview question based on:

Department: {department}
Domain: {domain}
Category: {category}
Difficulty: {difficulty}

Rules:
- Return only the interview question.
- Do not add numbering.
- Do not add explanations.
- Do not use markdown.
- Make the question suitable for an interview.
"""

    try:

        response = client.responses.create(
            model=OPENAI_MODEL,
            input=prompt
        )

        question = response.output_text.strip()

        return question

    except Exception as e:

        print(
            "OpenAI question generation error:",
            repr(e)
        )

        return None


# =========================================================
# GENERATE INTERVIEW FEEDBACK
# =========================================================

def generate_interview_feedback(
    question,
    answer
):

    prompt = f"""
You are an AI interview evaluator for an application called Interview Mirror.

Interview Question:
{question}

Candidate Answer:
{answer}

Evaluate the candidate's answer.

Return the result in this exact structure:

Score: <number out of 10>

Strengths:
<short points>

Improvements:
<short points>

Suggested Answer:
<a better sample answer>

Keep the feedback clear, useful and suitable for interview practice.
"""

    try:

        response = client.responses.create(
            model=OPENAI_MODEL,
            input=prompt
        )

        feedback = response.output_text.strip()

        return feedback

    except Exception as e:

        print(
            "OpenAI feedback generation error:",
            repr(e)
        )

        return None


# =========================================================
# GENERAL AI RESPONSE
# =========================================================

def ask_ai(prompt):

    try:

        response = client.responses.create(
            model=OPENAI_MODEL,
            input=prompt
        )

        return response.output_text.strip()

    except Exception as e:

        print(
            "OpenAI API error:",
            repr(e)
        )

        return None
```
