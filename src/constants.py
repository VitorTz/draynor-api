from dotenv import load_dotenv
import os


load_dotenv()


class Constants:

    API_NAME = "Draynor"
    API_DESCR = "Manga Reader"
    API_VERSION = "1.0.0"
    IS_PRODUCTION = os.getenv("ENV", "DEV") == "PROD"

    ALGORITHM = os.getenv("ALGORITHM")
    SECRET_KEY = os.getenv("SECRET_KEY")

    PERMISSIONS_POLICY_HEADER = (
        "geolocation=(), "
        "microphone=(), "
        "camera=(), "
        "payment=(), "
        "usb=(), "
        "magnetometer=(), "
        "gyroscope=(), "
        "accelerometer=()"
    )
    
    SENSITIVE_PATHS = ["/auth/", "/admin/"]

    MAX_BODY_SIZE = 20 * 1024 * 1024
    MAX_REQUESTS = 300 if os.getenv("ENV", "DEV") == "PROD" else 999_999_999
    WINDOW = 30