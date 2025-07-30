import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
MOUSE_MOVE_STEP = int(os.getenv("MOUSE_MOVE_STEP", 50))
MOUSE_MOVE_ACCELERATED = int(os.getenv("MOUSE_MOVE_ACCELERATED", 150))
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN", "")
