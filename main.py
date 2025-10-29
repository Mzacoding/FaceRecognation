import os
import pickle
import datetime
import time
import shutil
import numpy as np

import cv2
from fastapi import FastAPI, File, UploadFile, Form, Response
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import face_recognition
import starlette

ATTENDANCE_LOG_DIR = './logs'
DB_PATH = './encodings'
for dir_ in [ATTENDANCE_LOG_DIR, DB_PATH]:
    if not os.path.exists(dir_):
        os.mkdir(dir_)

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/login")
async def login(file: UploadFile = File(...)):
    contents = await file.read()
    
    # Process image directly from memory - NO FILE STORAGE
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    user_name, match_status = recognize(img)

    if match_status:
        epoch_time = time.time()
        date = time.strftime('%Y%m%d', time.localtime(epoch_time))
        with open(os.path.join(ATTENDANCE_LOG_DIR, f'{date}.csv'), 'a') as f:
            f.write(f'{user_name},{datetime.datetime.now()},IN\n')

    return {'user': user_name, 'match_status': match_status}

@app.post("/logout")
async def logout(file: UploadFile = File(...)):
    contents = await file.read()
    
    # Process image directly from memory - NO FILE STORAGE
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    user_name, match_status = recognize(img)

    if match_status:
        epoch_time = time.time()
        date = time.strftime('%Y%m%d', time.localtime(epoch_time))
        with open(os.path.join(ATTENDANCE_LOG_DIR, f'{date}.csv'), 'a') as f:
            f.write(f'{user_name},{datetime.datetime.now()},OUT\n')

    return {'user': user_name, 'match_status': match_status}

@app.post("/register_new_user")
async def register_new_user(file: UploadFile = File(...), text=None):
    contents = await file.read()

    # Process image directly from memory - NO FILE STORAGE
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    # Extract face encodings (no image storage)
    embeddings = face_recognition.face_encodings(img)

    if len(embeddings) > 0:
        # Only store the face encoding, not the image
        with open(os.path.join(DB_PATH, f'{text}.pickle'), 'wb') as f:
            pickle.dump(embeddings[0], f)

        return {'registration_status': 200}
    else:
        return {'registration_status': 400, 'error': 'No face detected'}

@app.post("/recognize")
async def recognize_face(file: UploadFile = File(...)):
    contents = await file.read()

    # Process image directly from memory - NO FILE STORAGE
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    user_name, match_status = recognize(img)

    return {'user': user_name, 'match_status': match_status}

@app.get("/get_attendance_logs")
async def get_attendance_logs():
    filename = 'attendance_logs.zip'
    shutil.make_archive(filename[:-4], 'zip', ATTENDANCE_LOG_DIR)
    return starlette.responses.FileResponse(filename, media_type='application/zip', filename=filename)

def recognize(img):
    try:
        # Extract face encoding from input image
        embeddings_unknown = face_recognition.face_encodings(img)
        if len(embeddings_unknown) == 0:
            return 'no_persons_found', False
        
        embeddings_unknown = embeddings_unknown[0]
        
        # Compare with stored encodings
        db_files = [f for f in os.listdir(DB_PATH) if f.endswith('.pickle') and len(f) > 7]
        
        for db_file in db_files:
            try:
                with open(os.path.join(DB_PATH, db_file), 'rb') as f:
                    stored_encoding = pickle.load(f)
                    
             
                if isinstance(stored_encoding, np.ndarray) and stored_encoding.shape == (128,):
                    # Compare encodings with tolerance
                    matches = face_recognition.compare_faces([stored_encoding], embeddings_unknown, tolerance=0.6)
                    
                    if len(matches) > 0 and matches[0]:  
                        return db_file[:-7], True  
            except Exception as e:
                print(f"Error processing {db_file}: {e}")
                continue
        
        return 'unknown_person', False
    except Exception as e:
        print(f"Recognition error: {e}")
        return 'error', False

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)