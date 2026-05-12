import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER", "")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_INTAKE_AGENT_ID = os.getenv("ELEVENLABS_INTAKE_AGENT_ID", "")
ELEVENLABS_DISPATCH_AGENT_ID = os.getenv("ELEVENLABS_DISPATCH_AGENT_ID", "")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./uproad.db")
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")  # Set to Railway URL in production
SECRET_KEY = os.getenv("SECRET_KEY", "uproad-secret-key-change-in-prod")
