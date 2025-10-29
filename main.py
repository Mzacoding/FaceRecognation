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
from integration_api import backend_integration

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
        # Authenticate with backend
        employee_data = backend_integration.authenticate_employee(user_name)
        if employee_data:
            # Check current status first
            current_status = backend_integration.get_employee_status(employee_data)
            
            # Perform clock in via backend
            result = backend_integration.clock_action(employee_data, 'clock_in')
            if result['success']:
                # Also log locally for backup
                epoch_time = time.time()
                date = time.strftime('%Y%m%d', time.localtime(epoch_time))
                with open(os.path.join(ATTENDANCE_LOG_DIR, f'{date}.csv'), 'a') as f:
                    f.write(f'{user_name},{datetime.datetime.now()},IN\n')
                
                # Get updated status
                updated_status = backend_integration.get_employee_status(employee_data)
                
                return {
                    'user': user_name, 
                    'match_status': match_status,
                    'backend_response': result['data'],
                    'employee_data': employee_data,
                    'status': updated_status,
                    'message': 'Successfully clocked in'
                }
            else:
                return {
                    'user': user_name, 
                    'match_status': match_status,
                    'error': 'Backend clock-in failed',
                    'details': result.get('error'),
                    'status': current_status
                }
        else:
            # Fallback to local logging if backend fails
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
        # Authenticate with backend
        employee_data = backend_integration.authenticate_employee(user_name)
        if employee_data:
            # Check current status first
            current_status = backend_integration.get_employee_status(employee_data)
            
            # Perform clock out via backend
            result = backend_integration.clock_action(employee_data, 'clock_out')
            if result['success']:
                # Also log locally for backup
                epoch_time = time.time()
                date = time.strftime('%Y%m%d', time.localtime(epoch_time))
                with open(os.path.join(ATTENDANCE_LOG_DIR, f'{date}.csv'), 'a') as f:
                    f.write(f'{user_name},{datetime.datetime.now()},OUT\n')
                
                # Get updated status
                updated_status = backend_integration.get_employee_status(employee_data)
                
                return {
                    'user': user_name, 
                    'match_status': match_status,
                    'backend_response': result['data'],
                    'employee_data': employee_data,
                    'status': updated_status,
                    'message': 'Successfully clocked out'
                }
            else:
                return {
                    'user': user_name, 
                    'match_status': match_status,
                    'error': 'Backend clock-out failed',
                    'details': result.get('error'),
                    'status': current_status
                }
        else:
            # Fallback to local logging if backend fails
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
    
    print(f"Recognition result: {user_name}, Match: {match_status}")
    
    # If recognized, get current status
    if match_status:
        employee_data = backend_integration.authenticate_employee(user_name)
        if employee_data:
            current_status = backend_integration.get_employee_status(employee_data)
            return {
                'user': user_name, 
                'match_status': match_status,
                'employee_data': employee_data,
                'status': current_status
            }

    return {'user': user_name, 'match_status': match_status}

@app.post("/break_start")
async def break_start(file: UploadFile = File(...)):
    contents = await file.read()
    
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    user_name, match_status = recognize(img)

    if match_status:
        employee_data = backend_integration.authenticate_employee(user_name)
        if employee_data:
            result = backend_integration.clock_action(employee_data, 'break_start')
            if result['success']:
                updated_status = backend_integration.get_employee_status(employee_data)
                return {
                    'user': user_name, 
                    'match_status': match_status,
                    'backend_response': result['data'],
                    'status': updated_status,
                    'message': 'Break started'
                }
            else:
                return {
                    'user': user_name, 
                    'match_status': match_status,
                    'error': 'Break start failed',
                    'details': result.get('error')
                }

    return {'user': user_name, 'match_status': match_status}

@app.post("/break_end")
async def break_end(file: UploadFile = File(...)):
    contents = await file.read()
    
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    user_name, match_status = recognize(img)

    if match_status:
        employee_data = backend_integration.authenticate_employee(user_name)
        if employee_data:
            result = backend_integration.clock_action(employee_data, 'break_end')
            if result['success']:
                updated_status = backend_integration.get_employee_status(employee_data)
                return {
                    'user': user_name, 
                    'match_status': match_status,
                    'backend_response': result['data'],
                    'status': updated_status,
                    'message': 'Break ended'
                }
            else:
                return {
                    'user': user_name, 
                    'match_status': match_status,
                    'error': 'Break end failed',
                    'details': result.get('error')
                }

    return {'user': user_name, 'match_status': match_status}

@app.get("/status/{username}")
async def get_status(username: str):
    """Get current status for a user"""
    employee_data = backend_integration.authenticate_employee(username)
    if employee_data:
        current_status = backend_integration.get_employee_status(employee_data)
        return {
            'user': username,
            'employee_data': employee_data,
            'status': current_status
        }
    return {'error': 'Employee not found'}

@app.get("/get_attendance_logs")
async def get_attendance_logs():
    filename = 'attendance_logs.zip'
    shutil.make_archive(filename[:-4], 'zip', ATTENDANCE_LOG_DIR)
    return starlette.responses.FileResponse(filename, media_type='application/zip', filename=filename)

def recognize(img):
    try:
        print("Starting face recognition...")
        
        # Extract face encoding from input image
        embeddings_unknown = face_recognition.face_encodings(img)
        if len(embeddings_unknown) == 0:
            print("No face found in image")
            return 'no_persons_found', False
        
        embeddings_unknown = embeddings_unknown[0]
        print(f"Face encoding extracted, shape: {embeddings_unknown.shape}")
        
        # Compare with stored encodings
        db_files = [f for f in os.listdir(DB_PATH) if f.endswith('.pickle')]
        print(f"Found {len(db_files)} stored face encodings: {db_files}")
        
        best_match = None
        best_distance = float('inf')
        
        for db_file in db_files:
            try:
                with open(os.path.join(DB_PATH, db_file), 'rb') as f:
                    stored_encoding = pickle.load(f)
                    
                if isinstance(stored_encoding, np.ndarray) and stored_encoding.shape == (128,):
                    # Calculate face distance (lower is better match)
                    distance = face_recognition.face_distance([stored_encoding], embeddings_unknown)[0]
                    name = db_file[:-7]  # Remove .pickle extension
                    
                    print(f"Comparing with {name}: distance = {distance:.3f}")
                    
                    # Check if this is the best match so far
                    if distance < best_distance:
                        best_distance = distance
                        best_match = name
                        
            except Exception as e:
                print(f"Error processing {db_file}: {e}")
                continue
        
        # Use stricter threshold for better accuracy
        threshold = 0.5  # Lower threshold = stricter matching
        
        if best_match and best_distance < threshold:
            print(f"Best match: {best_match} with distance {best_distance:.3f}")
            return best_match, True
        else:
            print(f"No good match found. Best was {best_match} with distance {best_distance:.3f} (threshold: {threshold})")
            return 'unknown_person', False
            
    except Exception as e:
        print(f"Recognition error: {e}")
        return 'error', False

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)