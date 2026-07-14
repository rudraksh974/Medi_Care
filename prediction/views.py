import os
import json
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import PredictionRecord
from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

api_key = os.getenv("GEMINI_API_KEY")

try:
    from google import genai
    from google.genai import types
    HAS_NEW_GENAI = True
except ImportError:
    HAS_NEW_GENAI = False
    try:
        import google.generativeai as old_genai
        if api_key:
            old_genai.configure(api_key=api_key)
    except ImportError:
        old_genai = None

def get_mock_prediction(symptoms):
    symptoms_lower = symptoms.lower()
    if "fever" in symptoms_lower and ("cough" in symptoms_lower or "throat" in symptoms_lower):
        return {
            "disease": "Common Cold / Influenza",
            "confidence": 85,
            "description": "Your symptoms of fever combined with cough or sore throat suggest a viral respiratory infection like the common cold or flu.",
            "precautions": [
                "Rest and stay hydrated with plenty of fluids",
                "Take over-the-counter fever reducers if needed",
                "Monitor your temperature regularly",
                "Wear a mask to protect family members"
            ],
            "specialist": "General Physician"
        }
    elif "chest pain" in symptoms_lower or "shortness of breath" in symptoms_lower or "heart" in symptoms_lower:
        return {
            "disease": "Potential Cardiovascular Issue",
            "confidence": 70,
            "description": "Chest tightness, pain, or shortness of breath are symptoms that warrant professional medical evaluation to rule out heart or lung conditions.",
            "precautions": [
                "Avoid any strenuous physical activity immediately",
                "Seek emergency medical care if the pain worsens or spreads",
                "Sit upright and try to stay calm",
                "Do not ignore or self-diagnose these symptoms"
            ],
            "specialist": "Cardiologist"
        }
    elif "rash" in symptoms_lower or "itch" in symptoms_lower or "skin" in symptoms_lower:
        return {
            "disease": "Allergic Dermatitis / Skin Condition",
            "confidence": 80,
            "description": "Skin irritation, localized itching, or redness indicates potential contact dermatitis, eczema, or an allergic reaction.",
            "precautions": [
                "Avoid scratching the affected area to prevent secondary infection",
                "Apply a cool compress or soothing calamine lotion",
                "Identify and avoid contact with potential allergen triggers",
                "Wash the skin gently with mild soap and lukewarm water"
            ],
            "specialist": "Dermatologist"
        }
    elif "stomach" in symptoms_lower or "nausea" in symptoms_lower or "vomit" in symptoms_lower or "diarrhea" in symptoms_lower:
        return {
            "disease": "Gastroenteritis / Food Poisoning",
            "confidence": 75,
            "description": "Abdominal discomfort, nausea, vomiting, or diarrhea points towards irritation or infection of the digestive tract, likely viral or food-borne.",
            "precautions": [
                "Drink plenty of electrolyte-rich fluids (ORS) to prevent dehydration",
                "Eat bland, soft foods like rice, bananas, and toast",
                "Avoid dairy, caffeine, alcohol, and fatty foods",
                "Wash your hands frequently to prevent spread"
            ],
            "specialist": "Gastroenterologist"
        }
    else:
        return {
            "disease": "Mild Viral Infection / General Fatigue",
            "confidence": 60,
            "description": "Your described symptoms are general and could indicate fatigue, a mild viral infection, or minor immune system response.",
            "precautions": [
                "Ensure you get 7-8 hours of sound sleep",
                "Stay hydrated with water and warm soups",
                "Avoid high-stress activities",
                "Consult a healthcare professional if symptoms persist beyond a few days"
            ],
            "specialist": "General Physician"
        }

def predict_symptoms_via_gemini(symptoms):
    if not api_key:
        return None
    
    prompt = f"""
    You are an expert clinical diagnosis AI assistant. Analyze the user's symptoms and provide a potential condition assessment.
    
    Symptoms description: "{symptoms}"
    
    You MUST respond with a single, valid JSON object following this schema exactly:
    {{
      "disease": "Name of the predicted disease or condition",
      "confidence": <integer between 10 and 99 representing your confidence percentage based on the symptom specificity>,
      "description": "A clear, professional 2-3 sentence explanation of why these symptoms match the condition and what it entails.",
      "precautions": ["precaution 1", "precaution 2", "precaution 3", "precaution 4"],
      "specialist": "The type of medical specialist they should consult (e.g., General Physician, Dermatologist, Cardiologist, Gastroenterologist, Neurologist, etc.)"
    }}
    
    IMPORTANT: Provide ONLY the JSON object. Do not include markdown code block formatting (e.g., do not wrap in ```json or ```).
    """
    try:
        if HAS_NEW_GENAI:
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            text = response.text.strip()
        elif old_genai:
            model = old_genai.GenerativeModel("gemini-2.5-flash-lite")
            response = model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            text = response.text.strip()
        else:
            return None
        
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        
        data = json.loads(text)
        if "disease" in data and "confidence" in data and "description" in data and "precautions" in data and "specialist" in data:
            return data
    except Exception as e:
        print(f"Gemini API Error: {e}")
    return None


def home(request):
    return render(request, 'prediction/home.html')

@login_required
def predict_disease(request):
    if request.method == 'POST':
        symptoms = request.POST.get('symptoms', '').strip()
        if not symptoms:
            return JsonResponse({'error': 'Please describe your symptoms.'}, status=400)
        
        # Call Gemini API
        result = predict_symptoms_via_gemini(symptoms)
        
        # Fallback to local heuristic rules
        if not result:
            result = get_mock_prediction(symptoms)
            
        # Save prediction record
        record = PredictionRecord.objects.create(
            user=request.user,
            symptoms=symptoms,
            predicted_disease=result.get("disease", "Unknown"),
            confidence=result.get("confidence", 50),
            description=result.get("description", ""),
            precautions=json.dumps(result.get("precautions", [])),
            specialist=result.get("specialist", "General Physician")
        )
        
        return JsonResponse({
            'disease': record.predicted_disease,
            'confidence': record.confidence,
            'description': record.description,
            'precautions': result.get("precautions", []),
            'specialist': record.specialist,
            'created_at': record.created_at.strftime("%b %d, %Y %I:%M %p")
        })
        
    # GET Request: Fetch history for the current user
    past_predictions = PredictionRecord.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'prediction/predict.html', {
        'past_predictions': past_predictions
    })
