# Smart Flashcard API

This is a FastAPI application designed to manage and categorize flashcards for students. The API automatically infers the subject of a flashcard using a Large Language Model (LLM) and provides endpoints for adding flashcards, retrieving categorized flashcards, and a health check.

## Features

*   **LLM-Powered Subject Inference:** Automatically categorizes flashcards into relevant subjects (Mathematics, Physics, Chemistry, Biology) by leveraging `llama-3.1-8b-instant` via the Groq API.
*   **Client-Provided Student ID:** The client provides the `student_id` when adding a flashcard, maintaining student-specific flashcard management.
*   **SQLite Database Persistence:** All flashcard data is stored persistently in a local SQLite database (`flashcards.db`).
*   **Duplicate Flashcard Prevention:** Prevents adding flashcards with the same student ID, question, and answer combination.
*   **Mixed Flashcard Retrieval:** Provides an endpoint to retrieve a mixed batch of flashcards for a student, ensuring variety across subjects.
*   **Health Check:** A dedicated endpoint to monitor the API's status, including total flashcards in the database and NLTK data status.

## Setup and Running

To set up and run the application, follow these steps:

### 1. Clone the Repository (if applicable)

```bash
git clone <your-repo-url>
cd <your-project-directory>
```

### 2. Create and Activate a Virtual Environment

It's highly recommended to use a virtual environment to manage dependencies.

```bash
python -m venv env
```

*   **On Windows (PowerShell):**
    ```powershell
    .\env\Scripts\Activate
    ```
*   **On macOS/Linux:**
    ```bash
    source env/bin/activate
    ```

### 3. Install Dependencies

Install the required Python packages using the `requirements.txt` file:

```bash
pip install -r requirements.txt
```

### 4. Set Up Groq API Key

The API uses Groq for LLM inference. You need to obtain an API key from [Groq Console](https://console.groq.com/keys).

Create a `.env` file in the root directory of your project (same level as `main.py`) and add your API key with the variable name `GROQ_API_KEY`:

```
GROQ_API_KEY="your_actual_groq_api_key_here"
```

Replace `"your_actual_groq_api_key_here"` with your actual Groq API key.

### 5. Run the Application

```bash
fastapi run main.py
```

**Advanced Run Command (for specific host/port or auto-reload):**
```bash
fastapi run main.py --host 0.0.0.0 --port 8000 --reload
```
(Replace `0.0.0.0` with `localhost` if you only need local access, and `8000` with your desired port. `--reload` enables automatic reloading on code changes.)

The API will be accessible at `http://localhost:8000`. You can find interactive API documentation at `http://localhost:8000/docs`.

## API Endpoints

*   **`POST /flashcard`**
    *   **Description:** Adds a new flashcard to the system and infers its subject.
    *   **Request Body (JSON):**
```json
{
          "student_id": "your_student_id",
          "question": "What is the capital of France?",
          "answer": "Paris"
}
```
    *   **Response (JSON):** Includes a success message and the inferred subject.

*   **`GET /get-subject?student_id={your_student_id}&limit={number}`**
    *   **Description:** Retrieves a mixed batch of flashcards for a specific student, ensuring variety in subjects.
    *   **Query Parameters:**
        *   `student_id` (string, required): The ID of the student whose flashcards are to be retrieved.
        *   `limit` (integer, optional, default: 5): The maximum number of flashcards to return.
    *   **Response (JSON):** A list of flashcards, each containing `question`, `answer`, and `subject`.

*   **`GET /health`**
    *   **Description:** Health check endpoint.
    *   **Response (JSON):** Provides status, timestamp, total number of flashcards, and NLTK tokenizer status.

*   **`GET /`**
    *   **Description:** Root endpoint with API information.
    *   **Response (JSON):** Basic information about the API and available endpoints.

## Subject Classification

Subject classification is performed by a Large Language Model (LLM), specifically `llama-3.1-8b-instant` accessed via the Groq API. The LLM is prompted to identify the most relevant subject (Mathematics, Physics, Chemistry, Biology) based on the flashcard's question and answer.

## Data Storage

Flashcard data is stored persistently in an SQLite database file named `flashcards.db` in the project root directory. SQLAlchemy ORM is used to manage database interactions.

## Testing the API

### Using curl:

1. Add a flashcard:
```bash
curl -X POST http://localhost:8000/flashcard \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "stu001",
    "question": "What is photosynthesis?",
    "answer": "A process used by plants to convert light into energy"
  }'
```

2. Get flashcards:
```bash
curl "http://localhost:8000/get-subject?student_id=stu001&limit=3"
```

### Using Python requests:

```python
import requests

# Add flashcard
response = requests.post('http://localhost:8000/flashcard', json={
    "student_id": "stu001",
    "question": "What is Newton's Second Law?",
    "answer": "Force equals mass times acceleration"
})
print(response.json())

# Get flashcards
response = requests.get('http://localhost:8000/get-subject', params={
    "student_id": "stu001",
    "limit": 5
})
print(response.json())
```

### Using the Interactive Docs:
Visit `http://localhost:8000/docs` to test the API directly in your browser.

## Production Considerations

For production deployment, consider:

1. **Database Integration**: Replace SQLite with a more robust database like PostgreSQL/MySQL.
2. **Authentication**: Add user authentication and authorization.
3. **Caching**: Implement Redis for frequently accessed data.
4. **Rate Limiting**: Add API rate limiting.
5. **Logging**: Implement comprehensive logging.
6. **Error Handling**: Enhanced error handling and monitoring.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is open source and available under the MIT License.