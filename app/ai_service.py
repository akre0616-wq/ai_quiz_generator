import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))


def generate_quiz(content, num_questions):

    prompt = f"""
Generate {num_questions} multiple choice quiz questions from the following content.

Return ONLY valid JSON in this exact format:

{{
  "quiz": [
    {{
      "question": "Question text",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "answer": "Correct Option"
    }}
  ]
}}

Rules:
- No markdown
- No explanations
- No extra text
- Exactly 4 options per question
- Answer must exactly match one option

Content:
{content}
"""

    try:

        # Load Gemini model
        model = genai.GenerativeModel("gemini-1.5-flash")

        # Generate response
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.2
            )
        )

        # Extract text safely
        text = response.text.strip()

        # Remove markdown if Gemini adds it
        text = text.replace("```json", "")
        text = text.replace("```", "")
        text = text.strip()

        print("\nRAW GEMINI RESPONSE:\n")
        print(text)

        # Convert to Python dictionary
        quiz_data = json.loads(text)

        # Validate structure
        if "quiz" not in quiz_data:
            raise ValueError("Quiz key missing")

        return quiz_data

    except json.JSONDecodeError as json_error:

        print("\nJSON ERROR:\n")
        print(json_error)

        return {
            "quiz": [
                {
                    "question": "JSON parsing failed.",
                    "options": [
                        "Invalid Gemini Response",
                        "Formatting Error",
                        "Retry Quiz",
                        "Server Error"
                    ],
                    "answer": "Retry Quiz"
                }
            ]
        }

    except Exception as e:

        print("\nGEMINI ERROR:\n")
        print(e)

        return {
            "quiz": [
                {
                    "question": "Quiz generation failed.",
                    "options": [
                        "Check API Key",
                        "Check Internet",
                        "Retry Again",
                        "Server Error"
                    ],
                    "answer": "Retry Again"
                }
            ]
        }