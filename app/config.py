from dotenv import load_dotenv
import os

# Load .env from project root if present
load_dotenv()

# Redis
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# Qdrant
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "startups")

# Admin
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")

# LLM / extraction settings
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
EXTRACTION_MODE = os.getenv("EXTRACTION_MODE", "llm")

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./startup_intel.db")
