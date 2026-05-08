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
    - Do not include explanations
    - Do not include markdown
    - Do not include ```json
    - Each question must have exactly 4 options
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
                temperature=0.3
            )
        )

        # Get response text
        text = response.text.strip()

        # Remove markdown if Gemini adds it
        text = text.replace("```json", "")
        text = text.replace("```", "")

        # Debug print
        print("\nRAW GEMINI RESPONSE:\n")
        print(text)

        # Convert JSON string to Python dictionary
        quiz_data = json.loads(text)

        # Validate quiz structure
        if "quiz" not in quiz_data:
            raise ValueError("Invalid quiz format")

        return quiz_data

    except Exception as e:

        print("\nGEMINI ERROR:\n")
        print(e)

        # Fallback response
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