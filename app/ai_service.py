import json
from google import genai
from google.genai import types

# Paste your BRAND NEW key inside the quotes below
client = genai.Client(api_key="AIzaSyBnA1EsbeBEsT2RshBbsUK1BP07TEGJrAY")

def generate_quiz(content, num_questions):
    prompt = f"""
    Generate {num_questions} multiple choice questions based on the following content.
    Return ONLY a valid JSON object. Do not include any introductory text or markdown backticks.
    
    Format:
    {{
        "quiz": [
            {{
                "question": "Question text",
                "options": ["A", "B", "C", "D"],
                "answer": "Correct Option"
            }}
        ]
    }}

    Content:
    {content}
    """

    try:
        # Upgraded to the new 2.5 flash model
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )

        # Clean the response just in case the AI wraps it in backticks
        clean_text = response.text.strip()
        if clean_text.startswith("```"):
            clean_text = clean_text.split("```")[1]
            if clean_text.startswith("json"):
                clean_text = clean_text[4:]
        
        return json.loads(clean_text)

    except Exception as e:
        print(f"ERROR IN AI SERVICE: {e}")
        return {"quiz": []}