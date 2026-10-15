import os
from dotenv import load_dotenv

load_dotenv()

class Settings():
    DataBaseUrl=os.getenv("DataBaseUrl")
    GeminiApiKey=os.getenv("GeminiApiKey")
    TalivyApi=os.getenv("TAVILY_API_KEY" or None)
    JwtSecretKey=os.getenv("JwtSecretKey" or None)
    HashAlgorithm=os.getenv("Algorithm" or None)
    ExpirationTime=os.getenv("ExpirationTime" or None)
    GeminiModel=os.getenv("GeminiModel" or None)


settings=Settings()