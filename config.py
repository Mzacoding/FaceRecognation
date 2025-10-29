# Face Recognition Configuration
API_HOST = "0.0.0.0"
API_PORT = 8000
FACE_TOLERANCE = 0.6
ENCODING_MODEL = "large" 

# Database paths
ENCODINGS_PATH = "./encodings"
LOGS_PATH = "./logs"

# Security settings
CORS_ORIGINS = ["*"]   
MAX_FILE_SIZE = 10 * 1024 * 1024   

# Face detection settings
MIN_FACE_SIZE = (50, 50)
MAX_FACES_PER_IMAGE = 1