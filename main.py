from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
import os
import random
import logging
from datetime import datetime
from collections import defaultdict, Counter

from groq import Groq
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Index
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize FastAPI with enhanced configuration
app = FastAPI(
    title="Smart Flashcard API",
    description="An intelligent flashcard system with automatic subject classification",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Subject classification mappings
SUBJECT_KEYWORDS = {
    "Physics": {
        "force", "mass", "acceleration", "velocity", "displacement", "energy", "work",
        "power", "momentum", "collision", "rotation", "torque", "gravity", "temperature",
        "heat", "thermodynamics", "charge", "electric", "field", "potential", "current",
        "resistance", "magnetic", "wave", "light", "reflection", "refraction", "optical",
        "atom", "nucleus", "radiation", "semiconductor", "newton", "law", "motion",
        "physics", "quantum", "mechanics", "relativity", "electromagnetic"
    },
    "Chemistry": {
        "atom", "molecule", "element", "compound", "reaction", "bond", "acid", "base",
        "equilibrium", "thermodynamics", "kinetics", "redox", "periodic", "ion", "gas",
        "liquid", "solid", "hydrocarbon", "functional", "alcohol", "aldehyde", "ketone",
        "amine", "isomer", "biomolecule", "polymer", "chemical", "formula", "solution",
        "mole", "molar", "grams", "oxygen", "hydrogen", "carbon", "nitrogen",
        "chemistry", "organic", "inorganic", "catalyst", "ph", "buffer"
    },
    "Mathematics": {
        "equation", "function", "limit", "derivative", "integral", "matrix", "vector",
        "probability", "geometry", "trigonometry", "sequence", "series", "quadratic",
        "circle", "parabola", "angle", "sine", "cosine", "tangent", "determinant",
        "coordinate", "algebra", "calculus", "theorem", "proof", "variable",
        "mathematics", "math", "statistics", "differential", "polynomial"
    },
    "Biology": {
        "cell", "tissue", "organ", "gene", "dna", "rna", "protein", "enzyme", "hormone",
        "photosynthesis", "respiration", "reproduction", "evolution", "ecosystem",
        "biodiversity", "circulation", "digestion", "excretion", "nervous", "kingdom",
        "virus", "bacteria", "plant", "animal", "organism", "species", "mitosis",
        "biology", "molecular", "genetics", "cellular", "metabolism", "homeostasis"
    }
}

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./flashcards.db")
engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Flashcard(Base):
    """Enhanced Flashcard model with indexing and metadata"""
    __tablename__ = "flashcards"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String, nullable=False, index=True)
    question = Column(String, nullable=False)
    answer = Column(String, nullable=False)
    subject = Column(String, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Composite indexes for better query performance
    __table_args__ = (
        Index('idx_student_subject', 'student_id', 'subject'),
        Index('idx_student_created', 'student_id', 'created_at'),
    )

# Create tables
Base.metadata.create_all(bind=engine)

# Pydantic models with enhanced validation
class FlashcardInput(BaseModel):
    """Input model for creating flashcards"""
    student_id: str = Field(..., min_length=1, max_length=50, description="Unique student identifier")
    question: str = Field(..., min_length=3, max_length=1000, description="Flashcard question")
    answer: str = Field(..., min_length=1, max_length=1000, description="Flashcard answer")
    
    @validator('student_id', 'question', 'answer')
    def validate_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Field cannot be empty or whitespace only')
        return v.strip()

class FlashcardResponse(BaseModel):
    """Response model for flashcard creation"""
    id: int
    message: str
    subject: str
    confidence: Optional[str] = None

class FlashcardOutput(BaseModel):
    """Output model for flashcard retrieval"""
    id: int
    question: str
    answer: str
    subject: str
    created_at: Optional[datetime] = None

class StudentStats(BaseModel):
    """Statistics model for student flashcards"""
    total_flashcards: int
    subjects: Dict[str, int]
    latest_addition: Optional[datetime] = None

# Database dependency
def get_db():
    """Database session dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Enhanced subject classification
class SubjectClassifier:
    """Intelligent subject classification system"""
    
    def __init__(self):
        self.groq_client = self._initialize_groq()
    
    def _initialize_groq(self) -> Optional[Groq]:
        """Initialize Groq client if API key is available"""
        api_key = os.getenv("GROQ_API_KEY")
        if api_key:
            try:
                return Groq(api_key=api_key)
            except Exception as e:
                logger.warning(f"Failed to initialize Groq client: {e}")
        return None
    
    def classify_subject(self, question: str, answer: str = "") -> tuple[str, str]:
        """
        Classify subject using hybrid approach: keywords + LLM fallback

    Returns:
            tuple: (subject, confidence_level)
        """
        # Try keyword-based classification first
        subject, confidence = self._classify_by_keywords(question, answer)
        
        # If keyword classification is uncertain and LLM is available, use it
        if confidence == "low" and self.groq_client:
            llm_subject = self._classify_by_llm(question, answer)
            if llm_subject in SUBJECT_KEYWORDS:
                return llm_subject, "medium"
        
        return subject, confidence
    
    def _classify_by_keywords(self, question: str, answer: str) -> tuple[str, str]:
        """Classify subject based on keyword matching"""
        text = f"{question} {answer}".lower()
        subject_scores = {}
        
        for subject, keywords in SUBJECT_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in text)
            if score > 0:
                subject_scores[subject] = score
        
        if not subject_scores:
            return "Other", "low"
        
        # Get the subject with highest score
        best_subject = max(subject_scores, key=subject_scores.get)
        max_score = subject_scores[best_subject]
        
        # Determine confidence based on score and competition
        if max_score >= 3:
            confidence = "high"
        elif max_score >= 2:
            confidence = "medium"
        else:
            confidence = "low"
        
        return best_subject, confidence
    
    def _classify_by_llm(self, question: str, answer: str) -> str:
        """Classify subject using LLM"""
        try:
            available_subjects = ", ".join(SUBJECT_KEYWORDS.keys())
            system_prompt = (
                f"You are an expert educational content classifier. "
                f"Classify the following flashcard into one of these subjects: {available_subjects}. "
                f"Respond with ONLY the subject name, exactly as listed. "
                f"If uncertain, respond with 'Other'."
            )
            
            user_prompt = f"Question: {question}\nAnswer: {answer}"
            
            response = self.groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model="llama-3.1-8b-instant",
                temperature=0.1,
                max_tokens=20
            )
            
            result = response.choices[0].message.content.strip()
            return result if result in SUBJECT_KEYWORDS else "Other"
            
        except Exception as e:
            logger.error(f"LLM classification failed: {e}")
        return "Other"

# Initialize classifier
classifier = SubjectClassifier()

# Enhanced flashcard retrieval logic
class FlashcardRetriever:
    """Smart flashcard retrieval with mixing algorithms"""
    
    @staticmethod
    def get_mixed_flashcards(flashcards: List[Flashcard], limit: int) -> List[FlashcardOutput]:
        """
        Retrieve mixed flashcards using intelligent distribution algorithm
        """
        if not flashcards:
            return []
        
        # Group by subject
        subject_groups = defaultdict(list)
        for fc in flashcards:
            subject_groups[fc.subject].append(fc)
        
        # Shuffle within each subject group
        for subject_cards in subject_groups.values():
            random.shuffle(subject_cards)
        
        # Calculate optimal distribution
        total_subjects = len(subject_groups)
        base_per_subject = limit // total_subjects
        extra_cards = limit % total_subjects
        
        selected = []
        subjects = list(subject_groups.keys())
        random.shuffle(subjects)  # Randomize subject order
        
        # Distribute cards fairly across subjects
        for i, subject in enumerate(subjects):
            cards_for_subject = base_per_subject + (1 if i < extra_cards else 0)
            available_cards = subject_groups[subject]
            
            cards_to_take = min(cards_for_subject, len(available_cards))
            selected.extend(available_cards[:cards_to_take])

        # Final shuffle for randomness
        random.shuffle(selected)
        
        return [
            FlashcardOutput(
                id=fc.id,
                question=fc.question,
                answer=fc.answer,
                subject=fc.subject,
                created_at=fc.created_at
            )
            for fc in selected[:limit]
        ]

retriever = FlashcardRetriever()

# API Endpoints
@app.post("/flashcard", response_model=FlashcardResponse)
async def create_flashcard(flashcard: FlashcardInput, db: Session = Depends(get_db)):
    """
    Create a new flashcard with automatic subject classification
    """
    try:
        # Check for duplicates
        existing = db.query(Flashcard).filter(
            Flashcard.student_id == flashcard.student_id,
            Flashcard.question == flashcard.question,
            Flashcard.answer == flashcard.answer
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=409, 
                detail="Flashcard with identical question and answer already exists for this student"
            )
        
        # Classify subject
        subject, confidence = classifier.classify_subject(flashcard.question, flashcard.answer)
        
        # Create flashcard
        db_flashcard = Flashcard(
            student_id=flashcard.student_id,
            question=flashcard.question,
            answer=flashcard.answer,
            subject=subject
        )
        
        db.add(db_flashcard)
        db.commit()
        db.refresh(db_flashcard)
        
        logger.info(f"Created flashcard {db_flashcard.id} for student {flashcard.student_id}")
        
        return FlashcardResponse(
            id=db_flashcard.id,
            message="Flashcard created successfully",
            subject=subject,
            confidence=confidence
        )
        
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database operation failed")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/get-subject", response_model=List[FlashcardOutput])
async def get_flashcards(
    student_id: str = Query(..., min_length=1, description="Student ID"),
    limit: int = Query(5, ge=1, le=50, description="Maximum number of flashcards to return"),
    subject: Optional[str] = Query(None, description="Filter by specific subject"),
    db: Session = Depends(get_db)
):
    """
    Retrieve mixed flashcards for a student with intelligent subject distribution
    """
    try:
        # Build query
        query = db.query(Flashcard).filter(Flashcard.student_id == student_id)
        
        if subject:
            if subject not in SUBJECT_KEYWORDS and subject != "Other":
                raise HTTPException(status_code=400, detail=f"Invalid subject: {subject}")
            query = query.filter(Flashcard.subject == subject)
        
        flashcards = query.order_by(Flashcard.created_at.desc()).all()
        
        if not flashcards:
            return []
        
        # Get mixed selection
        result = retriever.get_mixed_flashcards(flashcards, limit)
        
        logger.info(f"Retrieved {len(result)} flashcards for student {student_id}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving flashcards: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve flashcards")

@app.get("/")
async def root():
    """
    API information and available endpoints
    """
    return {
        "name": "Smart Flashcard API",
        "version": "2.0.0",
        "description": "Intelligent flashcard system with automatic subject classification",
        "endpoints": {
            "POST /flashcard": "Create a new flashcard",
            "GET /get-subject": "Get mixed flashcards for a student"
        },
        "features": [
            "Automatic subject classification",
            "Intelligent flashcard mixing",
            "Duplicate prevention",
            "Performance optimized",
            "Comprehensive error handling"
        ]
    }

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000, reload=True)