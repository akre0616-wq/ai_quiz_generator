import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def generate_quiz(content, num_questions):

    prompt = f"""
    Generate {num_questions} multiple choice quiz questions from the following content.

    Return valid JSON format like:
    {{
      "quiz": [
        {{
          "question": "...",
          "options": ["A", "B", "C", "D"],
          "answer": "A"
        }}
      ]
    }}

    Content:
    {content}
    """

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")

        response = model.generate_content(prompt)

        text = response.text

        # Remove markdown formatting if present
        text = text.replace("```json", "").replace("```", "")

        quiz_data = json.loads(text)

        return quiz_data

    except Exception as e:
        print("Gemini Error:", e)
        return {"quiz": []}