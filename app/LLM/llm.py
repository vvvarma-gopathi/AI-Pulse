from charset_normalizer import api
from google import genai
from core.config import settings



client = genai.Client(api_key=settings.GeminiApiKey)