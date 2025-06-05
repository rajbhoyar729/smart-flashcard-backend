from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import nltk
from nltk.stem import PorterStemmer
import re
from collections import defaultdict
import datetime
import os
from groq import Groq
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy.exc import IntegrityError

# Load environment variables from .env file
load_dotenv()

# Initialize the FastAPI application
app = FastAPI(title="Smart Flashcard API", version="1.0.0")

# Download required NLTK data (run once)
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

# Initialize Groq client
# Ensure you have your GROQ_API_KEY set as an environment variable (in .env file or system-wide)
groq_api_key = os.getenv("GROQ_API_KEY")
if not groq_api_key:
    raise ValueError("GROQ_API_KEY environment variable not set.")
client = Groq(api_key=groq_api_key)

# Define subjects and their available names (used for LLM prompt context)
subjects = {
    "Physics": [
        "force", "mass", "acceleration", "velocity", "displacement", "energy", "work",
        "power", "momentum", "collision", "rotation", "torque", "gravity", "temperature",
        "heat", "thermodynamics", "charge", "electric", "field", "potential", "current",
        "resistance", "magnetic", "wave", "light", "reflection", "refraction", "optical",
        "atom", "nucleus", "radiation", "semiconductor", "newton", "law", "motion"
    ],
    "Chemistry": [
        "atom", "molecule", "element", "compound", "reaction", "bond", "acid", "base",
        "equilibrium", "thermodynamics", "kinetics", "redox", "periodic", "ion", "gas",
        "liquid", "solid", "hydrocarbon", "functional", "alcohol", "aldehyde", "ketone",
        "amine", "isomer", "biomolecule", "polymer", "chemical", "formula", "solution",
        "mole", "molar", "grams", "oxygen", "hydrogen", "carbon", "nitrogen"
    ],
    "Mathematics": [
        "equation", "function", "limit", "derivative", "integral", "matrix", "vector",
        "probability", "geometry", "trigonometry", "sequence", "series", "quadratic",
        "circle", "parabola", "angle", "sine", "cosine", "tangent", "determinant",
        "coordinate", "algebra", "calculus", "theorem", "proof", "variable"
    ],
    "Biology": [
        "cell", "tissue", "organ", "gene", "dna", "rna", "protein", "enzyme", "hormone",
        "photosynthesis", "respiration", "reproduction", "evolution", "ecosystem",
        "biodiversity", "circulation", "digestion", "excretion", "nervous", "kingdom",
        "virus", "bacteria", "plant", "animal", "organism", "species", "mitosis"
    ]
}

# SQLAlchemy Database Setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./flashcards.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Flashcard ORM Model
class Flashcard(Base):
    __tablename__ = "flashcards"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String, index=True)
    question = Column(String)
    answer = Column(String)
    subject = Column(String)

# Create database tables
Base.metadata.create_all(bind=engine)

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic models for flashcard input/output
class FlashcardInput(BaseModel):
    student_id: str
    question: str
    answer: str

class FlashcardResponse(BaseModel):
    message: str
    subject: str

class FlashcardOutput(BaseModel):
    question: str
    answer: str
    subject: str

# Function to infer the subject based on question and answer using LLM
def infer_subject(question: str, answer: str = "") -> str:
    """
    Infers the subject of a flashcard using an LLM (llama-3.1-8b-instant) via Groq.

    Args:
        question (str): The question text of the flashcard.
        answer (str, optional): The answer text of the flashcard. Defaults to "".

    Returns:
        str: The inferred subject, or "Other" if no subject matches or an error occurs.
    """
    available_subjects = ", ".join(subjects.keys())
    system_prompt = (
        f"You are a helpful assistant that identifies the subject of a flashcard. "
        f"Based on the provided question and answer, identify the most relevant subject "
        f"from the following list: {available_subjects}. "
        f"Your response MUST be only the subject name, exactly as it appears in the list. "
        f"Do NOT include any other text, punctuation, or explanations."
    )
    user_prompt = f"Question: {question}\nAnswer: {answer}"

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            model="llama-3.1-8b-instant",
            temperature=0.0, # Keep temperature low for deterministic output
            max_tokens=50, # Limit response to just the subject name
        )
        inferred_subject = chat_completion.choices[0].message.content.strip()

        # Validate if the inferred subject is one of the predefined subjects
        if inferred_subject in subjects:
            return inferred_subject
        else:
            return "Other"
    except Exception as e:
        print(f"Error inferring subject with LLM: {e}")
        return "Other" # Fallback in case of API error or invalid response

# POST endpoint to add a flashcard
@app.post("/flashcard", response_model=FlashcardResponse)
def add_flashcard(flashcard: FlashcardInput, db: Session = Depends(get_db)):
    """
    Adds a new flashcard to the system and infers its subject.

    Args:
        flashcard (FlashcardInput): The flashcard data including student_id, question, and answer.

    Returns:
        FlashcardResponse: A response with a success message and the inferred subject.
    """
    # Check for duplicate flashcard for the same student, question, and answer
    existing_flashcard = db.query(Flashcard).filter(
        Flashcard.student_id == flashcard.student_id,
        Flashcard.question == flashcard.question,
        Flashcard.answer == flashcard.answer
    ).first()

    if existing_flashcard:
        raise HTTPException(status_code=409, detail="Flashcard with this question and answer already exists for this student.")

    # Infer the subject
    subject = infer_subject(flashcard.question, flashcard.answer)

    # Create new flashcard ORM object
    db_flashcard = Flashcard(
        student_id=flashcard.student_id,
        question=flashcard.question,
        answer=flashcard.answer,
        subject=subject
    )
    
    # Add to database and commit
    db.add(db_flashcard)
    db.commit()
    db.refresh(db_flashcard)

    # Return success response
    return FlashcardResponse(message="Flashcard added successfully", subject=subject)

# GET endpoint to retrieve a mixed batch of flashcards
@app.get("/get-subject", response_model=list[FlashcardOutput])
def get_flashcards(student_id: str, limit: int = 5, db: Session = Depends(get_db)):
    """
    Retrieves a mixed batch of flashcards for a student, ensuring variety in subjects.

    Args:
        student_id (str): The ID of the student whose flashcards are to be retrieved.
        limit (int, optional): The maximum number of flashcards to return. Defaults to 5.

    Returns:
        list[FlashcardOutput]: A list of flashcards, each containing question, answer, and subject.
    """
    # Filter flashcards for the specified student from the database
    student_flashcards = db.query(Flashcard).filter(Flashcard.student_id == student_id).all()

    if not student_flashcards:
        return []
    
    # Group flashcards by subject
    subject_groups = defaultdict(list)
    for fc in student_flashcards:
        subject_groups[fc.subject].append(FlashcardOutput(question=fc.question, answer=fc.answer, subject=fc.subject))
    
    # Select flashcards in a round-robin fashion to mix subjects
    selected = []
    subjects_list = list(subject_groups.keys())
    
    # Cycle through subjects to pick flashcards
    subject_indices = {subject: 0 for subject in subjects_list}
    total_subjects = len(subjects_list)
    current_subject_index = 0

    while len(selected) < limit and any(len(subject_groups[s]) > subject_indices[s] for s in subjects_list):
        subject_to_pick = subjects_list[current_subject_index]

        if subject_indices[subject_to_pick] < len(subject_groups[subject_to_pick]):
            selected.append(subject_groups[subject_to_pick][subject_indices[subject_to_pick]])
            subject_indices[subject_to_pick] += 1
        
        current_subject_index = (current_subject_index + 1) % total_subjects

    return selected

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint
    """
    try:
        nltk.data.find('tokenizers/punkt')
        nltk_status = "downloaded"
    except LookupError:
        nltk_status = "not downloaded"
    
    total_flashcards = db.query(Flashcard).count()

    return {
        "status": "healthy",
        "timestamp": datetime.datetime.now().isoformat(),
        "total_flashcards": total_flashcards,
        "nltk_punkt_tokenizer": nltk_status
    }

@app.get("/")
def root():
    """
    Root endpoint with API information
    """
    return {
        "message": "Smart Flashcard API",
        "version": "1.0.0",
        "endpoints": {
            "POST /flashcard": "Add a new flashcard",
            "GET /get-subject": "Get mixed flashcards for a student",
            "GET /health": "Health check",
            "GET /docs": "Interactive API documentation"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)