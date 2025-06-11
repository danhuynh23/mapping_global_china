"""CODE TO LIST THE MODELS THAT ARE AVAILABLE FOR USE, SO WE CAN PUT IT ON THE
'fill_description_gemini' CODE"""
import google.generativeai as genai

genai.configure(api_key='put the API key')

for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(m.name)
