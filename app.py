"""
INTERVIEW MIRROR
Flask + MySQL + OpenAI
Corrected complete app.py

IMPORTANT:
- Keep OPENAI_API_KEY only in .env
- Never paste the API key directly into this file
"""

import os
import re
import json

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    jsonify,
    session,
    url_for
)


import mysql.connector
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# =========================================================
# LOAD ENVIRONMENT
# =========================================================

load_dotenv()



# =========================================================
# OPENAI CONFIGURATION
# =========================================================

from dotenv import load_dotenv
from openai import OpenAI
import os

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")

if not OPENAI_API_KEY:
    print("WARNING: OPENAI_API_KEY is missing.")
    client = None
else:
    try:
        client = OpenAI(
            api_key=OPENAI_API_KEY
        )
        print("OpenAI client initialized successfully.")
    except Exception as error:
        print("OpenAI client initialization error:", repr(error))
        client = None




# =========================================================
# EMAIL VALIDATION
# =========================================================

def valid_email(email):
    if not email:
        return False

    return bool(
        re.match(
            r"^[^\s@]+@[^\s@]+\.[^\s@]+$",
            email
        )
    )


# =========================================================
# DATABASE
# =========================================================

def get_db_connection():
    return mysql.connector.connect(
        host=os.environ.get(
            "DB_HOST",
            "localhost"
        ),
        port=int(
            os.environ.get(
                "DB_PORT",
                "3306"
            )
        ),
        user=os.environ.get(
            "DB_USER",
            "root"
        ),
        password=os.environ.get(
            "DB_PASSWORD",
            "root"
        ),
        database=os.environ.get(
            "DB_NAME",
            "my_project"
        ),
        connection_timeout=5,
        use_pure=True
    )


def close_db(db=None, cursor=None):
    try:
        if cursor is not None:
            cursor.close()
    except Exception:
        pass

    try:
        if db is not None:
            db.close()
    except Exception:
        pass


# =========================================================
# LOGIN CHECK
# =========================================================

def login_required():
    return bool(
        session.get("user_id")
    )


# =========================================================
# ERROR PAGE
# =========================================================

def error_page(title, message, back_url="/"):
    safe_title = str(title)
    safe_message = str(message)
    safe_back_url = str(back_url)

    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{safe_title}</title>

<style>
* {{
    box-sizing: border-box;
}}

body {{
    margin: 0;
    min-height: 100vh;
    display: flex;
    justify-content: center;
    align-items: center;
    font-family: Arial, sans-serif;
    background: linear-gradient(135deg, #020817, #031a43, #020b24);
    color: white;
}}

.box {{
    width: 90%;
    max-width: 650px;
    padding: 35px;
    text-align: center;
    background: linear-gradient(145deg, #071b42, #04102a);
    border: 1px solid #079cff;
    border-radius: 15px;
    box-shadow: 0 0 30px rgba(0,140,255,.35);
}}

h2 {{
    color: #36aaff;
}}

p {{
    color: #d7e7f7;
    line-height: 1.6;
    word-break: break-word;
}}

a {{
    display: inline-block;
    margin-top: 20px;
    padding: 12px 24px;
    background: linear-gradient(90deg, #006eff, #00aaff);
    color: white;
    text-decoration: none;
    border-radius: 7px;
    font-weight: bold;
}}
</style>

</head>

<body>

<div class="box">
    <h2>{safe_title}</h2>
    <p>{safe_message}</p>
    <a href="{safe_back_url}">Go Back</a>
</div>

</body>
</html>
"""


# =========================================================
# JSON ERROR
# =========================================================

def json_error(message, status_code=400):
    return jsonify({
        "success": False,
        "message": str(message)
    }), status_code


# =========================================================
# ALERT REDIRECT
# =========================================================

def alert_redirect(message, url):
    message_json = json.dumps(str(message))
    url_json = json.dumps(str(url))

    return f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Interview Mirror</title>
</head>

<body>

<script>
alert({message_json});
window.location.href = {url_json};
</script>

</body>
</html>
"""


# =========================================================
# SUPPORT TABLES
# =========================================================

def create_support_tables():
    db = None
    cursor = None

    try:
        db = get_db_connection()
        cursor = db.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS login (
                login_id INT AUTO_INCREMENT PRIMARY KEY,
                email VARCHAR(200) NOT NULL,
                password VARCHAR(255) NOT NULL,
                login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contact_messages (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(150) NOT NULL,
                email VARCHAR(200) NOT NULL,
                subject VARCHAR(255) NOT NULL,
                message TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS question_report_answers (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                setup_id INT NOT NULL,
                question_id INT NULL,
                question TEXT NOT NULL,
                user_answer TEXT,
                correct TINYINT(1) DEFAULT 0,
                explanation TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            SELECT COUNT(*)
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = 'question_report_answers'
            AND COLUMN_NAME = 'explanation'
        """)

        row = cursor.fetchone()

        if not row or row[0] == 0:
            cursor.execute("""
                ALTER TABLE question_report_answers
                ADD COLUMN explanation TEXT NULL
            """)

        db.commit()

        print("SUPPORT TABLES READY")

    except mysql.connector.Error as error:
        print("SUPPORT TABLE ERROR:", repr(error))

    except Exception as error:
        print("SUPPORT TABLE GENERAL ERROR:", repr(error))

    finally:
        close_db(db, cursor);


# =========================================================
# HOME
# =========================================================
app = Flask(__name__)

app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY",
    "interview_mirror_secret_key_2026"
)

app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

UPLOAD_FOLDER = "static/resumes"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(
    app.config["UPLOAD_FOLDER"],
    exist_ok=True
)

ALLOWED_EXTENSIONS = {"pdf", "doc", "docx"}

def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )

@app.route("/")
def index():
    return render_template("index.html")


# =========================================================
# ABOUT
# =========================================================

@app.route("/aboutus")
def aboutus():
    return render_template("aboutus.html")


# =========================================================
# SERVICES
# =========================================================

@app.route("/services")
def services():
    return render_template("services.html")


# =========================================================
# CONTACT
# =========================================================

@app.route("/contact", methods=["GET", "POST"])
def contact():

    if request.method == "GET":
        return render_template("contact.html")

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    subject = request.form.get("subject", "").strip()
    message = request.form.get("message", "").strip()

    if not all([name, email, subject, message]):
        return alert_redirect(
            "Please fill all contact fields.",
            "/contact"
        )

    if not valid_email(email):
        return alert_redirect(
            "Please enter a valid email address.",
            "/contact"
        )

    db = None
    cursor = None

    try:
        db = get_db_connection()
        cursor = db.cursor()

        cursor.execute("""
            INSERT INTO contact_messages
            (name, email, subject, message)
            VALUES (%s, %s, %s, %s)
        """, (
            name,
            email,
            subject,
            message
        ))

        db.commit()

        return alert_redirect(
            "Your message has been submitted successfully.",
            "/contact"
        )

    except mysql.connector.Error as error:

        if db:
            db.rollback()

        return error_page(
            "Contact Database Error",
            str(error),
            "/contact"
        )

    except Exception as error:

        if db:
            db.rollback()

        return error_page(
            "Contact Error",
            str(error),
            "/contact"
        )

    finally:
        close_db(db, cursor)


# =========================================================
# CONTACT REPORT
# =========================================================

@app.route("/contact_report")
def contact_report():

    db = None
    cursor = None

    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                id,
                name,
                email,
                subject,
                message,
                created_at
            FROM contact_messages
            ORDER BY id DESC
        """)

        contacts = cursor.fetchall()

        return render_template(
            "contact_report.html",
            contacts=contacts
        )

    except Exception as error:

        return error_page(
            "Contact Report Error",
            str(error),
            "/contact"
        )

    finally:
        close_db(db, cursor)


# =========================================================
# SIGN UP
# =========================================================

@app.route("/signup")
def signup():
    return render_template("signup.html")


# =========================================================
# REGISTER
# =========================================================

@app.route("/register", methods=["POST"])
def register():

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    mobile = request.form.get("mobile", "").strip()
    gender = request.form.get("gender", "").strip()
    password = request.form.get("password", "")
    confirm_password = request.form.get("confirmPassword", "")
    address = request.form.get("address", "").strip()

    resume_file = request.files.get("resume")

    if not all([
        name,
        email,
        mobile,
        gender,
        password,
        confirm_password,
        address
    ]):
        return alert_redirect(
            "Please fill all required fields.",
            "/signup"
        )

    if len(name) < 3 or len(name) > 50:
        return alert_redirect(
            "Name must contain 3 to 50 characters.",
            "/signup"
        )

    if not re.match(r"^[A-Za-z ]+$", name):
        return alert_redirect(
            "Name should contain only letters and spaces.",
            "/signup"
        )

    if not valid_email(email):
        return alert_redirect(
            "Please enter a valid email address.",
            "/signup"
        )

    if not re.match(r"^[6-9][0-9]{9}$", mobile):
        return alert_redirect(
            "Please enter a valid 10 digit mobile number.",
            "/signup"
        )

    if len(password) < 8 or len(password) > 20:
        return alert_redirect(
            "Password must contain 8 to 20 characters.",
            "/signup"
        )

    if not re.search(r"[A-Z]", password):
        return alert_redirect(
            "Password must contain at least one uppercase letter.",
            "/signup"
        )

    if not re.search(r"[a-z]", password):
        return alert_redirect(
            "Password must contain at least one lowercase letter.",
            "/signup"
        )

    if not re.search(r"[0-9]", password):
        return alert_redirect(
            "Password must contain at least one number.",
            "/signup"
        )

    if password != confirm_password:
        return alert_redirect(
            "Password and Confirm Password do not match!",
            "/signup"
        )

    if len(address) < 3 or len(address) > 200:
        return alert_redirect(
            "Address must contain 3 to 200 characters.",
            "/signup"
        )

    if not resume_file or not resume_file.filename:
        return alert_redirect(
            "Please upload your resume.",
            "/signup"
        )
        

    if not allowed_file(resume_file.filename):
        return alert_redirect(
            "Only PDF, DOC and DOCX resume files are allowed.",
            "/signup"
        )

    db = None
    cursor = None
    resume_path = None

    try:
        db = get_db_connection()
        cursor = db.cursor()

        cursor.execute("""
            SELECT id
            FROM candidates
            WHERE email = %s
            LIMIT 1
        """, (email,))

        if cursor.fetchone():
            return alert_redirect(
                "Email already registered. Please Sign In.",
                "/signin"
            )

        cursor.execute("""
            INSERT INTO candidates
            (name, email, password)
            VALUES (%s, %s, %s)
        """, (
            name,
            email,
            password
        ))

        candidate_id = cursor.lastrowid

        original_filename = secure_filename(
            resume_file.filename
        )

        resume_filename = (
            f"{candidate_id}_{original_filename}"
        )

        resume_path = os.path.join(
            app.config["UPLOAD_FOLDER"],
            resume_filename
        )

        resume_file.save(resume_path)

        cursor.execute("""
            INSERT INTO candidate_profiles
            (
                candidate_id,
                full_name,
                phone,
                gender,
                location,
                resume
            )
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            candidate_id,
            name,
            mobile,
            gender,
            address,
            resume_filename
        ))

        db.commit()

        return alert_redirect(
            "Registration successful! Please Sign In.",
            "/signin"
        )

    except mysql.connector.Error as error:

        if db:
            db.rollback()

        if resume_path and os.path.exists(resume_path):
            try:
                os.remove(resume_path)
            except OSError:
                pass

        return error_page(
            "Registration Database Error",
            str(error),
            "/signup"
        )

    except Exception as error:

        if db:
            db.rollback()

        if resume_path and os.path.exists(resume_path):
            try:
                os.remove(resume_path)
            except OSError:
                pass

        return error_page(
            "Registration Error",
            str(error),
            "/signup"
        )

    finally:
        close_db(db, cursor)


# =========================================================
# SIGN IN
# =========================================================

@app.route("/signin", methods=["GET", "POST"])
def signin():

    if request.method == "GET":
        return render_template("signin.html")

    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    if not email or not password:
        return alert_redirect(
            "Please enter Email and Password.",
            "/signin"
        )

    db = None
    cursor = None

    try:
        db = get_db_connection()
        cursor = db.cursor()

        cursor.execute("""
            SELECT id, name, email
            FROM candidates
            WHERE email = %s
            AND password = %s
            LIMIT 1
        """, (
            email,
            password
        ))

        user = cursor.fetchone()

        if not user:
            return alert_redirect(
                "Invalid Email or Password.",
                "/signin"
            )

        session.clear()

        session["user_id"] = user[0]
        session["user_name"] = user[1]
        session["user_email"] = user[2]

        try:
            cursor.execute("""
                INSERT INTO login
                (email, password)
                VALUES (%s, %s)
            """, (
                email,
                password
            ))

            db.commit()

        except mysql.connector.Error as login_error:

            print(
                "LOGIN HISTORY ERROR:",
                repr(login_error)
            )

            db.rollback()

        return redirect("/interviewsetup")

    except mysql.connector.Error as error:

        return error_page(
            "Sign In Database Error",
            str(error),
            "/signin"
        )

    except Exception as error:

        return error_page(
            "Sign In Error",
            str(error),
            "/signin"
        )

    finally:
        close_db(db, cursor)


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


# =========================================================
# PROFILE
# =========================================================

@app.route("/profile")
def profile():

    user_id = session.get("user_id")

    if not user_id:
        return redirect("/signin")

    db = None
    cursor = None

    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                c.id,
                c.name,
                c.email,
                p.candidate_id,
                p.full_name,
                p.phone,
                p.gender,
                p.location,
                p.resume,
                p.updated_at
            FROM candidates c
            LEFT JOIN candidate_profiles p
                ON c.id = p.candidate_id
            WHERE c.id = %s
            LIMIT 1
        """, (user_id,))

        profile_data = cursor.fetchone()

        if not profile_data:
            return error_page(
                "Profile Not Found",
                "Your profile could not be found.",
                "/"
            )

        return render_template(
            "profile.html",
            profile=profile_data
        )

    except mysql.connector.Error as error:

        return error_page(
            "Profile Database Error",
            str(error),
            "/"
        )

    except Exception as error:

        return error_page(
            "Profile Error",
            str(error),
            "/"
        )

    finally:
        close_db(db, cursor)


# =========================================================
# INTERVIEW INSTRUCTION
# =========================================================

@app.route("/Interviewinstruction")
def Interviewinstruction():

    if not login_required():
        return redirect("/signin")

    return render_template(
        "Interviewinstruction.html"
    )


@app.route("/interviewinstruction")
def interviewinstruction():

    if not login_required():
        return redirect("/signin")

    return render_template(
        "Interviewinstruction.html"
    )


# =========================================================
# INTERVIEW SETUP
# =========================================================

@app.route("/interviewsetup")
def interviewsetup():

    if not login_required():
        return redirect("/signin")

    return render_template(
        "interviewsetup.html"
    )


# =========================================================
# SAVE INTERVIEW SETUP
# =========================================================

@app.route("/save_setup", methods=["POST"])
def save_setup():

    user_id = session.get("user_id")

    if not user_id:
        return redirect("/signin")

    department = request.form.get("department", "").strip()
    domain = request.form.get("domain", "").strip()
    category = request.form.get("category", "").strip()
    difficulty = request.form.get("difficulty", "").strip()

    if not all([
        department,
        domain,
        category,
        difficulty
    ]):
        return alert_redirect(
            "Please select all Interview Setup details.",
            "/interviewsetup"
        )

    db = None
    cursor = None

    try:
        db = get_db_connection()
        cursor = db.cursor()

        cursor.execute("""
            INSERT INTO setup
            (
                user_id,
                department,
                domain,
                category,
                difficulty
            )
            VALUES (%s, %s, %s, %s, %s)
        """, (
            user_id,
            department,
            domain,
            category,
            difficulty
        ))

        setup_id = cursor.lastrowid

        db.commit()

        session["setup_data"] = {
            "setup_id": setup_id,
            "user_id": user_id,
            "department": department,
            "domain": domain,
            "category": category,
            "difficulty": difficulty
        }

        session.pop("result_data", None)
        session.pop("interview_questions", None)
        session.pop("current_question_index", None)

        return redirect("/questions")

    except mysql.connector.Error as error:

        if db:
            db.rollback()

        return error_page(
            "Save Setup Database Error",
            str(error),
            "/interviewsetup"
        )

    except Exception as error:

        if db:
            db.rollback()

        return error_page(
            "Save Setup Error",
            str(error),
            "/interviewsetup"
        )

    finally:
        close_db(db, cursor)


# =========================================================
# CURRENT SETUP
# =========================================================

def get_current_setup(cursor, user_id):

    setup_data = session.get("setup_data")

    if (
        setup_data
        and setup_data.get("user_id") == user_id
    ):
        return setup_data

    cursor.execute("""
        SELECT
            setup_id,
            user_id,
            department,
            domain,
            category,
            difficulty
        FROM setup
        WHERE user_id = %s
        ORDER BY setup_id DESC
        LIMIT 1
    """, (user_id,))

    row = cursor.fetchone()

    if not row:
        return None

    setup = {
        "setup_id": row[0],
        "user_id": row[1],
        "department": row[2],
        "domain": row[3],
        "category": row[4],
        "difficulty": row[5]
    }

    session["setup_data"] = setup

    return setup


# =========================================================
# FETCH QUESTIONS
# =========================================================

def fetch_questions(
    cursor,
    department,
    domain,
    category,
    difficulty
):

    cursor.execute("""
        SELECT
            question_id,
            department,
            domain,
            category,
            difficulty,
            question
        FROM interview_questions
        WHERE LOWER(TRIM(department))
            = LOWER(TRIM(%s))
        AND LOWER(TRIM(domain))
            = LOWER(TRIM(%s))
        AND LOWER(TRIM(category))
            = LOWER(TRIM(%s))
        AND LOWER(TRIM(difficulty))
            = LOWER(TRIM(%s))
        ORDER BY question_id ASC
    """, (
        department,
        domain,
        category,
        difficulty
    ))

    rows = cursor.fetchall()

    return [
        {
            "question_id": row[0],
            "department": row[1],
            "domain": row[2],
            "category": row[3],
            "difficulty": row[4],
            "question": row[5]
        }
        for row in rows
    ]


# =========================================================
# QUESTIONS PAGE
# =========================================================

@app.route("/questions")
def questions():

    if not login_required():
        return redirect("/signin")

    db = None
    cursor = None

    try:
        db = get_db_connection()
        cursor = db.cursor()

        user_id = session.get("user_id")

        setup = get_current_setup(
            cursor,
            user_id
        )

        if not setup:
            return alert_redirect(
                "Please complete Interview Setup first.",
                "/interviewsetup"
            )

        questions_data = fetch_questions(
            cursor,
            setup["department"],
            setup["domain"],
            setup["category"],
            setup["difficulty"]
        )

        print("========================================")
        print("QUESTIONS ROUTE")
        print("SETUP ID:", setup["setup_id"])
        print("DEPARTMENT:", setup["department"])
        print("DOMAIN:", setup["domain"])
        print("CATEGORY:", setup["category"])
        print("DIFFICULTY:", setup["difficulty"])
        print("QUESTIONS FOUND:", len(questions_data))
        print("========================================")

        if not questions_data:
            return error_page(
                "No Questions Found",
                (
                    "No questions are available for "
                    f"{setup['department']} / "
                    f"{setup['domain']} / "
                    f"{setup['category']} / "
                    f"{setup['difficulty']}."
                ),
                "/interviewsetup"
            )

        session["interview_questions"] = questions_data
        session["current_question_index"] = 0

        return render_template(
            "questions.html",
            questions=questions_data,
            setup=setup
        )

    except mysql.connector.Error as error:

        return error_page(
            "Questions Database Error",
            str(error),
            "/interviewsetup"
        )

    except Exception as error:

        return error_page(
            "Questions Error",
            str(error),
            "/interviewsetup"
        )

    finally:
        close_db(db, cursor)


# =========================================================
# QUESTIONS API
# =========================================================

@app.route("/api/questions")
def api_questions():

    if not login_required():
        return json_error(
            "Please sign in first.",
            401
        )

    db = None
    cursor = None

    try:
        db = get_db_connection()
        cursor = db.cursor()

        user_id = session.get("user_id")

        setup = get_current_setup(
            cursor,
            user_id
        )

        if not setup:
            return json_error(
                "Interview setup not found.",
                400
            )

        questions_data = fetch_questions(
            cursor,
            setup["department"],
            setup["domain"],
            setup["category"],
            setup["difficulty"]
        )

        return jsonify({
            "success": True,
            "setup": setup,
            "questions": questions_data
        })

    except Exception as error:

        print(
            "API QUESTIONS ERROR:",
            repr(error)
        )

        return json_error(
            str(error),
            500
        )

    finally:
        close_db(db, cursor)


# =========================================================
# AI JSON PARSER
# =========================================================

def parse_ai_json(text):

    if not text:
        raise ValueError(
            "OpenAI returned an empty response."
        )

    cleaned = str(text).strip()

    cleaned = re.sub(
        r"^```(?:json)?\s*",
        "",
        cleaned,
        flags=re.IGNORECASE
    )

    cleaned = re.sub(
        r"\s*```$",
        "",
        cleaned
    ).strip()

    try:
        parsed = json.loads(cleaned)

        if isinstance(parsed, dict):
            return parsed

    except json.JSONDecodeError:
        pass

    start = cleaned.find("{")
    end = cleaned.rfind("}")

    if start != -1 and end != -1 and end > start:

        possible_json = cleaned[start:end + 1]

        try:
            parsed = json.loads(possible_json)

            if isinstance(parsed, dict):
                return parsed

        except json.JSONDecodeError:
            pass

    raise ValueError(
        "AI response was not valid JSON."
    )


# =========================================================
# AI ANSWER EVALUATION
# =========================================================

def evaluate_answer_with_ai(question, answer):
    if not question:
        raise ValueError("Question is required.")

    if not answer:
        raise ValueError("Answer is required.")

    if client is None:
        raise RuntimeError(
            "OpenAI client is not initialized. "
            "Check OPENAI_API_KEY in .env and restart Flask."
        )

    prompt = f"""
You are an AI interview evaluator for an application called Interview Mirror.

Evaluate the candidate's answer against the interview question.

QUESTION:
{question}

CANDIDATE ANSWER:
{answer}

Return ONLY a valid JSON object.

Use exactly these keys:

{{
    "correct": true,
    "score": 0,
    "feedback": "short constructive feedback",
    "explanation": "clear explanation",
    "ideal_answer": "a concise ideal interview answer"
}}

Rules:
- correct must be true only when the answer is substantially correct.
- score must be an integer from 0 to 100.
- Give partial credit when appropriate.
- Do not require exact wording.
- Judge meaning and technical correctness.
- Keep feedback useful for an interview candidate.
"""

    try:
        response = client.responses.create(
            model=OPENAI_MODEL,
            input=prompt,
            max_output_tokens=800
        )

        output_text = getattr(
            response,
            "output_text",
            None
        )

        if not output_text:
            raise RuntimeError(
                "OpenAI returned an empty response."
            )

        print("========================================")
        print("AI RAW RESPONSE:")
        print(output_text)
        print("========================================")

        evaluation = parse_ai_json(output_text)

        correct = evaluation.get("correct", False)

        if isinstance(correct, str):
            correct = (
                correct.strip().lower()
                in {"true", "1", "yes", "correct"}
            )
        else:
            correct = bool(correct)

        score = evaluation.get("score", 0)

        try:
            score = int(float(score))
        except Exception:
            score = 0

        score = max(0, min(100, score))

        return {
            "correct": correct,
            "score": score,
            "feedback": str(
                evaluation.get("feedback", "")
            ).strip(),
            "explanation": str(
                evaluation.get("explanation", "")
            ).strip(),
            "ideal_answer": str(
                evaluation.get("ideal_answer", "")
            ).strip()
        }

    except Exception as error:
        print("========================================")
        print("OPENAI EVALUATION ERROR:")
        print(type(error).__name__)
        print(str(error))
        print("========================================")

        raise RuntimeError(
            "OpenAI evaluation failed: " + str(error)
        )

        # =========================================================
# AI ANSWER EVALUATION API
# =========================================================

@app.route("/evaluate_answer", methods=["POST"])
def evaluate_answer():

    if not login_required():
        return json_error(
            "Please sign in first.",
            401
        )

    try:

        data = request.get_json(
            silent=True
        )

        if not isinstance(data, dict):
            return json_error(
                "Invalid JSON request.",
                400
            )

        question = str(
            data.get("question", "")
        ).strip()

        answer = str(
            data.get("answer", "")
        ).strip()

        if not question:
            return json_error(
                "Question is required.",
                400
            )

        if not answer:
            return json_error(
                "Answer is required.",
                400
            )

        print("========================================")
        print("EVALUATING ANSWER")
        print("QUESTION:", question)
        print("ANSWER:", answer)
        print("========================================")

        # ---------------------------------------------
        # CALL OPENAI
        # ---------------------------------------------

        evaluation = evaluate_answer_with_ai(
            question,
            answer
        )

        # ---------------------------------------------
        # RETURN VALID JSON
        # ---------------------------------------------

        return jsonify({
            "success": True,
            "correct": bool(
                evaluation.get(
                    "correct",
                    False
                )
            ),
            "score": int(
                evaluation.get(
                    "score",
                    0
                )
            ),
            "feedback": str(
                evaluation.get(
                    "feedback",
                    ""
                )
            ),
            "explanation": str(
                evaluation.get(
                    "explanation",
                    ""
                )
            ),
            "ideal_answer": str(
                evaluation.get(
                    "ideal_answer",
                    ""
                )
            )
        }), 200

    except Exception as error:

        print("========================================")
        print("EVALUATE ANSWER ERROR:")
        print(
            type(error).__name__
        )
        print(
            str(error)
        )
        print("========================================")

        return json_error(
            str(error),
            500
        )


# =========================================================
# SAVE ANSWER API
# =========================================================

@app.route("/save_answer", methods=["POST"])
def save_answer():

    if not login_required():
        return json_error(
            "Please sign in first.",
            401
        )

    db = None
    cursor = None

    try:

        data = request.get_json(
            silent=True
        )

        if not isinstance(data, dict):
            data = request.form.to_dict()

        if not isinstance(data, dict):
            data = {}

        question = str(
            data.get(
                "question",
                ""
            )
        ).strip()

        answer = str(
            data.get(
                "answer",
                ""
            )
        ).strip()

        question_id = data.get(
            "question_id"
        )

        evaluation = data.get(
            "evaluation"
        )

        if isinstance(evaluation, str):
            try:
                evaluation = json.loads(
                    evaluation
                )
            except Exception:
                evaluation = {}

        if not isinstance(evaluation, dict):
            evaluation = {}

        if not question:
            return json_error(
                "Question is required.",
                400
            )

        setup = session.get(
            "setup_data"
        )

        if not setup:
            return json_error(
                "Interview setup not found.",
                400
            )

        try:
            question_id_value = (
                int(question_id)
                if question_id not in (
                    None,
                    "",
                    "null"
                )
                else None
            )
        except Exception:
            question_id_value = None

        correct_value = evaluation.get(
            "correct",
            False
        )

        if isinstance(correct_value, str):
            correct_value = (
                correct_value.lower()
                in {
                    "true",
                    "1",
                    "yes",
                    "correct"
                }
            )
        else:
            correct_value = bool(
                correct_value
            )

        explanation = str(
            evaluation.get(
                "explanation",
                ""
            )
        ).strip()

        feedback = str(
            evaluation.get(
                "feedback",
                ""
            )
        ).strip()

        if feedback:

            if explanation:
                explanation = (
                    explanation
                    + "\n\nFeedback: "
                    + feedback
                )
            else:
                explanation = (
                    "Feedback: "
                    + feedback
                )

        db = get_db_connection()
        cursor = db.cursor()

        cursor.execute("""
            INSERT INTO question_report_answers
            (
                user_id,
                setup_id,
                question_id,
                question,
                user_answer,
                correct,
                explanation
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            session.get("user_id"),
            setup.get("setup_id"),
            question_id_value,
            question,
            answer,
            1 if correct_value else 0,
            explanation
        ))

        db.commit()

        return jsonify({
            "success": True,
            "message": "Answer saved successfully.",
            "answer_id": cursor.lastrowid
        }), 200

    except mysql.connector.Error as error:

        if db:
            db.rollback()

        print(
            "SAVE ANSWER DATABASE ERROR:",
            repr(error)
        )

        return json_error(
            str(error),
            500
        )

    except Exception as error:

        if db:
            db.rollback()

        print(
            "SAVE ANSWER ERROR:",
            repr(error)
        )

        return json_error(
            str(error),
            500
        )

    finally:
        close_db(db, cursor)


# =========================================================
# SUBMIT FINAL INTERVIEW RESULT
# =========================================================
@app.route("/submit_result", methods=["POST"])
def submit_result():

    if not session.get("user_id"):
        return jsonify({
            "success": False,
            "message": "Please sign in first."
        }), 401

    db = None
    cursor = None

    try:

        # -------------------------------------------------
        # GET JSON DATA
        # -------------------------------------------------
        data = request.get_json(silent=True) or {}

        questions = data.get("questions", [])

        if not isinstance(questions, list):
            return jsonify({
                "success": False,
                "message": "Invalid questions data."
            }), 400

        if not questions:
            return jsonify({
                "success": False,
                "message": "No interview answers received."
            }), 400

        # -------------------------------------------------
        # USER + SETUP
        # -------------------------------------------------
        user_id = session.get("user_id")

        setup_data = session.get("setup_data", {})

        setup_id = setup_data.get("setup_id")

        if not setup_id:
            return jsonify({
                "success": False,
                "message": "Interview setup not found."
            }), 400

        # -------------------------------------------------
        # DATABASE CONNECTION
        # -------------------------------------------------
        db = get_db_connection()
        cursor = db.cursor()

        # =================================================
        # SAVE EACH INTERVIEW ANSWER
        # =================================================

        insert_answer_query = """
            INSERT INTO interview_answers
            (
                user_id,
                setup_id,
                question_id,
                question,
                answer,
                correct,
                score,
                feedback,
                explanation,
                ideal_answer
            )
            VALUES
            (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s
            )
        """

        total_questions = 0
        correct_answers = 0
        total_score = 0

        for item in questions:

            # ---------------------------------------------
            # QUESTION
            # ---------------------------------------------
            question_id = item.get("question_id")

            question = str(
                item.get("question", "")
            ).strip()

            # ---------------------------------------------
            # USER ANSWER
            # ---------------------------------------------
            answer = str(
                item.get(
                    "answer",
                    item.get("user_answer", "")
                )
            ).strip()

            # ---------------------------------------------
            # CORRECT
            # ---------------------------------------------
            correct_value = item.get("correct", False)

            if isinstance(correct_value, str):
                correct = (
                    correct_value.strip().lower()
                    in {"true", "1", "yes", "correct"}
                )
            else:
                correct = bool(correct_value)

            correct_db = 1 if correct else 0

            # ---------------------------------------------
            # SCORE
            # AI SCORE IS 0 - 100
            # ---------------------------------------------
            score = item.get("score", 0)

            try:
                score = int(float(score))
            except (ValueError, TypeError):
                score = 0

            score = max(0, min(100, score))

            # ---------------------------------------------
            # FEEDBACK
            # ---------------------------------------------
            feedback = str(
                item.get("feedback", "")
            ).strip()

            # ---------------------------------------------
            # EXPLANATION
            # ---------------------------------------------
            explanation = str(
                item.get("explanation", "")
            ).strip()

            # ---------------------------------------------
            # IDEAL ANSWER
            # ---------------------------------------------
            ideal_answer = str(
                item.get("ideal_answer", "")
            ).strip()

            # ---------------------------------------------
            # INSERT ANSWER
            # ---------------------------------------------
            cursor.execute(
                insert_answer_query,
                (
                    user_id,
                    setup_id,
                    question_id,
                    question,
                    answer,
                    correct_db,
                    score,
                    feedback,
                    explanation,
                    ideal_answer
                )
            )

            # ---------------------------------------------
            # RESULT CALCULATION
            # ---------------------------------------------
            total_questions += 1

            if correct:
                correct_answers += 1

            total_score += score

        # =================================================
        # CALCULATE FINAL RESULT
        # =================================================

        if total_questions > 0:

            percentage = round(
                total_score / total_questions,
                2
            )

        else:

            percentage = 0

        incorrect_answers = (
            total_questions - correct_answers
        )

        # =================================================
        # SAVE INTERVIEW HISTORY SUMMARY
        # =================================================

        insert_history_query = """
            INSERT INTO interview_history_summary
            (
                user_id,
                interviewer_name,
                total_interviews,
                interview_date,
                interview_time,
                result
            )
            VALUES
            (
                %s,
                %s,
                %s,
                CURDATE(),
                CURTIME(),
                %s
            )
        """

  
               # Count previous completed interviews
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM interview_history_summary
            WHERE user_id = %s
            """,
            (user_id,)
        )

        previous_count = cursor.fetchone()[0]

        total_interviews = previous_count + 1

        cursor.execute(
            insert_history_query,
            (
                user_id,
                session.get("user_name", "User"),
                total_interviews,
                percentage
            )
        )
    
   

        # =================================================
        # COMMIT EVERYTHING
        # =================================================

        db.commit()

        # =================================================
        # RESULT DATA
        # =================================================

        result_data = {
            "overall_score": percentage,
            "total_questions": total_questions,
            "correct_answers": correct_answers,
            "incorrect_answers": incorrect_answers,
            "percentage": percentage,

            "department": setup_data.get(
                "department", ""
            ),

            "domain": setup_data.get(
                "domain", ""
            ),

            "category": setup_data.get(
                "category", ""
            ),

            "difficulty": setup_data.get(
                "difficulty", ""
            )
        }

        # Save result in session
        session["result_data"] = result_data

        # =================================================
        # SUCCESS RESPONSE
        # =================================================

        return jsonify({
            "success": True,
            "message": "Interview result saved successfully.",
            "result": result_data,
            "redirect": url_for("result")
        }), 200

    # =====================================================
    # DATABASE ERROR
    # =====================================================

    except mysql.connector.Error as error:

        if db:
            db.rollback()

        print("SUBMIT RESULT DATABASE ERROR:")
        print(repr(error))

        return jsonify({
            "success": False,
            "message": str(error)
        }), 500

    # =====================================================
    # GENERAL ERROR
    # =====================================================

    except Exception as error:

        if db:
            db.rollback()

        print("SUBMIT RESULT ERROR:")
        print(type(error).__name__)
        print(str(error))

        return jsonify({
            "success": False,
            "message": str(error)
        }), 500

    # =====================================================
    # CLOSE DATABASE
    # =====================================================

    finally:

        close_db(
            db,
            cursor
        )
#

# =========================================================
# HISTORY
# =========================================================

@app.route("/history")
def history():

    if "user_id" not in session:
        return redirect(url_for("signin"))

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            history_id,
            user_id,
            interviewer_name,
            total_interviews,
            interview_date,
            interview_time,
            result,
            created_at
        FROM interview_history_summary
        ORDER BY history_id ASC
    """)

    history = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template(
        "history.html",
        history=history
    )
# =========================================================
# USERS REPORT
# =========================================================

@app.route("/usersreport")
def users_report():

    if "user_id" not in session:
        return redirect(url_for("signin"))

    db = None
    cursor = None

    try:

        db = get_db_connection()

        cursor = db.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                c.id AS id,
                c.name AS name,
                c.email AS email,
                p.phone AS phone,
                p.gender AS gender,
                p.location AS location,
                p.resume AS resume

            FROM candidates c

            LEFT JOIN candidate_profiles p
                ON c.id = p.candidate_id

            WHERE c.id = %s
        """, (session["user_id"],))

        users = cursor.fetchall()

        print("CURRENT USER REPORT:")
        print(users)

        return render_template(
            "usersreport.html",
            users=users
        )

    except Exception as error:

        print("USERS REPORT ERROR:", error)

        return f"""
        <h2>Users Report Error</h2>
        <p>{error}</p>
        """

    finally:

        if cursor:
            cursor.close()

        if db:
            db.close()
# =========================================================
# REPORT DETAILS
# =========================================================

@app.route("/report/<int:setup_id>")
def report_details(setup_id):

    if not login_required():
        return redirect("/signin")

    db = None
    cursor = None

    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)

        user_id = session.get("user_id")

        cursor.execute("""
            SELECT
                setup_id,
                user_id,
                department,
                domain,
                category,
                difficulty
            FROM setup
            WHERE setup_id = %s
            AND user_id = %s
            LIMIT 1
        """, (
            setup_id,
            user_id
        ))

        setup = cursor.fetchone()

        if not setup:
            return error_page(
                "Report Not Found",
                "This interview report was not found.",
                "/report"
            )

        cursor.execute("""
            SELECT
                id,
                question_id,
                question,
                user_answer,
                correct,
                explanation,
                created_at
            FROM question_report_answers
            WHERE setup_id = %s
            AND user_id = %s
            ORDER BY id ASC
        """, (
            setup_id,
            user_id
        ))

        answers = cursor.fetchall()

        total = len(answers)

        correct = sum(
            1
            for answer in answers
            if answer["correct"]
        )

        incorrect = total - correct

        percentage = (
            round(
                correct / total * 100,
                2
            )
            if total
            else 0
        )

        result_data = {
            "setup": setup,
            "answers": answers,
            "total_questions": total,
            "correct_answers": correct,
            "incorrect_answers": incorrect,
            "percentage": percentage
        }

        return render_template(
            "result.html",
            result=result_data,
            answers=answers,
            setup=setup
        )

    except mysql.connector.Error as error:

        return error_page(
            "Report Database Error",
            str(error),
            "/report"
        )

    except Exception as error:

        return error_page(
            "Report Error",
            str(error),
            "/report"
        )

    finally:
        close_db(db, cursor)


# =========================================================
# CURRENT USER API
# =========================================================

@app.route("/api/current_user")
def current_user():

    if not login_required():
        return jsonify({
            "success": True,
            "logged_in": False
        }), 200

    return jsonify({
        "success": True,
        "logged_in": True,
        "user_id": session.get("user_id"),
        "name": session.get("user_name"),
        "email": session.get("user_email")
    }), 200


# =========================================================
# CURRENT SETUP API
# =========================================================

@app.route("/api/current_setup")
def current_setup_api():

    if not login_required():
        return json_error(
            "Please sign in first.",
            401
        )

    db = None
    cursor = None

    try:
        db = get_db_connection()
        cursor = db.cursor()

        setup = get_current_setup(
            cursor,
            session.get("user_id")
        )

        if not setup:
            return json_error(
                "Setup not found.",
                404
            )

        return jsonify({
            "success": True,
            "setup": setup
        }), 200

    except Exception as error:

        print(
            "CURRENT SETUP API ERROR:",
            repr(error)
        )

        return json_error(
            str(error),
            500
        )

    finally:
        close_db(db, cursor)


# =========================================================
# CLEAR CURRENT INTERVIEW
# =========================================================

@app.route("/clear_interview", methods=["POST"])
def clear_interview():

    if not login_required():
        return json_error(
            "Please sign in first.",
            401
        )

    setup = session.get(
        "setup_data"
    )

    if not setup:
        return json_error(
            "No active setup.",
            400
        )

    db = None
    cursor = None

    try:
        db = get_db_connection()
        cursor = db.cursor()

        cursor.execute("""
            DELETE FROM question_report_answers
            WHERE user_id = %s
            AND setup_id = %s
        """, (
            session.get("user_id"),
            setup.get("setup_id")
        ))

        deleted_count = cursor.rowcount

        db.commit()

        session.pop(
            "result_data",
            None
        )

        return jsonify({
            "success": True,
            "message": "Interview answers cleared.",
            "deleted": deleted_count
        }), 200

    except Exception as error:

        if db:
            db.rollback()

        return json_error(
            str(error),
            500
        )

    finally:
        close_db(db, cursor)


# =========================================================
# ERROR HANDLERS
# =========================================================

@app.errorhandler(404)
def page_not_found(error):

    return error_page(
        "404 - Page Not Found",
        "The page you requested could not be found.",
        "/"
    ), 404


@app.errorhandler(413)
def file_too_large(error):

    return error_page(
        "File Too Large",
        "Resume file size must be 5 MB or less.",
        "/signup"
    ), 413


@app.errorhandler(500)
def internal_server_error(error):

    return error_page(
        "Internal Server Error",
        "Something went wrong on the server.",
        "/"
    ), 500


# =========================================================
# START APPLICATION
# =========================================================
if __name__ == "__main__":
    print("")
    print("========================================")
    print("        INTERVIEW MIRROR")
    print("========================================")
    print("Starting Flask application...")
    print(
        "Database:",
        os.environ.get("DB_NAME", "my_project")
    )
    print("OpenAI Model:", OPENAI_MODEL)

    if OPENAI_API_KEY:
        print("OpenAI API Key: CONFIGURED")
    else:
        print("OpenAI API Key: NOT CONFIGURED")

    print("========================================")
    print("")

    create_support_tables()

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )