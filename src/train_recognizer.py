import os
import pickle
import face_recognition
import cv2
import numpy as np
from datetime import datetime
import time
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

class FaceTrainer:
    def __init__(self, encodings_path="./encodings", images_path="./training_images"):
        self.encodings_path = encodings_path
        self.images_path = images_path
        
        # Create directories if they don't exist
        for path in [self.encodings_path, self.images_path]:
            if not os.path.exists(path):
                os.makedirs(path)
    
    def train_from_images_folder(self):
        """Train face recognition from a folder of images"""
        print("Starting face recognition training...")
        
        known_encodings = []
        known_names = []
        
        # Process each subdirectory (each person)
        for person_name in os.listdir(self.images_path):
            person_path = os.path.join(self.images_path, person_name)
            
            if not os.path.isdir(person_path):
                continue
            
            print(f"Processing images for {person_name}...")
            person_encodings = []
            
            # Process each image for this person
            for image_file in os.listdir(person_path):
                if image_file.lower().endswith(('.png', '.jpg', '.jpeg')):
                    image_path = os.path.join(person_path, image_file)
                    
                    # Load and process image
                    image = cv2.imread(image_path)
                    if image is None:
                        print(f"Could not load {image_path}")
                        continue
                    
                    # Convert BGR to RGB
                    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                    
                    # Find face encodings
                    face_encodings = face_recognition.face_encodings(rgb_image)
                    
                    if len(face_encodings) > 0:
                        person_encodings.append(face_encodings[0])
                        print(f"  Processed {image_file}")
                    else:
                        print(f"  No face found in {image_file}")
            
            # Average the encodings for this person
            if len(person_encodings) > 0:
                avg_encoding = np.mean(person_encodings, axis=0)
                self.save_person_encoding(person_name, avg_encoding)
                known_encodings.append(avg_encoding)
                known_names.append(person_name)
                print(f"Saved encoding for {person_name} ({len(person_encodings)} images)")
        
        print(f"Training completed! Processed {len(known_names)} people.")
        return len(known_names)
    
    def save_person_encoding(self, person_name, encoding):
        """Save individual person's encoding"""
        filepath = os.path.join(self.encodings_path, f"{person_name}.pickle")
        try:
            with open(filepath, 'wb') as f:
                pickle.dump(encoding, f)
            return True
        except Exception as e:
            print(f"Error saving encoding for {person_name}: {e}")
            return False
    
    def validate_encodings(self):
        """Validate all saved encodings"""
        print("Validating saved encodings...")
        
        valid_count = 0
        invalid_files = []
        
        for filename in os.listdir(self.encodings_path):
            if filename.endswith('.pickle'):
                filepath = os.path.join(self.encodings_path, filename)
                try:
                    with open(filepath, 'rb') as f:
                        encoding = pickle.load(f)
                    
                    if isinstance(encoding, np.ndarray) and encoding.shape == (128,):
                        valid_count += 1
                        print(f"  ✓ {filename[:-7]}")
                    else:
                        invalid_files.append(filename)
                        print(f"  ✗ {filename[:-7]} - Invalid encoding shape")
                
                except Exception as e:
                    invalid_files.append(filename)
                    print(f"  ✗ {filename[:-7]} - Error: {e}")
        
        print(f"Validation complete: {valid_count} valid, {len(invalid_files)} invalid")
        return valid_count, invalid_files
    
    def create_sample_structure(self):
        """Create sample directory structure for training"""
        sample_structure = """
        To use this trainer, organize your images like this:

        training_images/
        ├── John_Doe/
        │   ├── john1.jpg
        │   ├── john2.jpg
        │   └── john3.jpg
        ├── Jane_Smith/
        │   ├── jane1.jpg
        │   ├── jane2.jpg
        │   └── jane3.jpg
        └── Bob_Johnson/
            ├── bob1.jpg
            └── bob2.jpg

        Each person should have their own folder with multiple face images.
        """
        print(sample_structure)

        # Create sample directories
        sample_people = ["John_Doe", "Jane_Smith", "Bob_Johnson"]
        for person in sample_people:
            person_dir = os.path.join(self.images_path, person)
            if not os.path.exists(person_dir):
                os.makedirs(person_dir)
                print(f"Created directory: {person_dir}")

    def load_encodings(self):
        """Load all stored face encodings"""
        known_encodings = []
        known_names = []

        for filename in os.listdir(self.encodings_path):
            if filename.endswith('.pickle'):
                filepath = os.path.join(self.encodings_path, filename)
                try:
                    with open(filepath, 'rb') as f:
                        encoding = pickle.load(f)
                    if isinstance(encoding, np.ndarray) and encoding.shape == (128,):
                        known_encodings.append(encoding)
                        known_names.append(filename[:-7])  # Remove .pickle
                except Exception as e:
                    print(f"Error loading {filename}: {e}")

        return known_encodings, known_names

    def recognize_face(self, image_bytes):
        """Recognize face from image bytes and toggle clock status"""
        # Ensure logs directory exists
        logs_dir = "./logs"
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)

        # Load known encodings
        known_encodings, known_names = self.load_encodings()
        if not known_encodings:
            raise HTTPException(status_code=400, detail="No encodings found. Please train the system first.")

        # Convert bytes to numpy array
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if image is None:
            raise HTTPException(status_code=400, detail="Invalid image file.")

        # Convert BGR to RGB
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Find faces in image
        face_locations = face_recognition.face_locations(rgb_image)
        face_encodings = face_recognition.face_encodings(rgb_image, face_locations)

        if not face_encodings:
            return {"recognized": False, "message": "No face detected in the image."}

        # Use the first face found
        face_encoding = face_encodings[0]

        # Compare with known encodings
        matches = face_recognition.compare_faces(known_encodings, face_encoding, tolerance=0.6)
        name = "Unknown"

        if True in matches:
            first_match_index = matches.index(True)
            name = known_names[first_match_index]

            # Clock in/out logic (toggle per user)
            # Load or initialize clock status
            clock_status_file = os.path.join(logs_dir, "clock_status.pickle")
            if os.path.exists(clock_status_file):
                with open(clock_status_file, 'rb') as f:
                    clock_status = pickle.load(f)
            else:
                clock_status = {n: 0 for n in known_names}

            clock_status[name] += 1
            status = "IN" if clock_status[name] % 2 == 1 else "OUT"

            # Save updated status
            with open(clock_status_file, 'wb') as f:
                pickle.dump(clock_status, f)

            # Log to CSV
            epoch_time = time.time()
            date = time.strftime('%Y%m%d', time.localtime(epoch_time))
            log_file = os.path.join(logs_dir, f'{date}.csv')
            with open(log_file, 'a') as f:
                f.write(f'{name},{datetime.now()},{status}\n')

            return {"recognized": True, "name": name, "status": status, "timestamp": str(datetime.now())}
        else:
            return {"recognized": False, "message": "Face not recognized."}

    def clock_in_out(self):
        """Real-time face recognition for clocking in/out"""
        print("Starting clock in/out system...")

        # Ensure logs directory exists
        logs_dir = "./logs"
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)

        # Load known encodings
        known_encodings, known_names = self.load_encodings()
        if not known_encodings:
            print("No encodings found. Please train the system first.")
            return

        # Track clock status per user (simple toggle: even = in, odd = out)
        clock_status = {name: 0 for name in known_names}

        # Open webcam
        video_capture = cv2.VideoCapture(0)
        if not video_capture.isOpened():
            print("Could not open webcam.")
            return

        print("Press 'q' to quit.")

        while True:
            ret, frame = video_capture.read()
            if not ret:
                break

            # Convert BGR to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Find faces in frame
            face_locations = face_recognition.face_locations(rgb_frame)
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

            for face_encoding, face_location in zip(face_encodings, face_locations):
                # Compare with known encodings
                matches = face_recognition.compare_faces(known_encodings, face_encoding, tolerance=0.6)
                name = "Unknown"

                if True in matches:
                    first_match_index = matches.index(True)
                    name = known_names[first_match_index]

                    # Clock in/out logic
                    clock_status[name] += 1
                    status = "IN" if clock_status[name] % 2 == 1 else "OUT"

                    # Log to file
                    epoch_time = time.time()
                    date = time.strftime('%Y%m%d', time.localtime(epoch_time))
                    log_file = os.path.join(logs_dir, f'{date}.csv')
                    with open(log_file, 'a') as f:
                        f.write(f'{name},{datetime.now()},{status}\n')

                    print(f"{name} clocked {status}")

                # Draw rectangle and name
                top, right, bottom, left = face_location
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2)

            # Display the frame
            cv2.imshow('Face Recognition - Clock In/Out', frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        video_capture.release()
        cv2.destroyAllWindows()
        print("Clock in/out system stopped.")

# FastAPI app
app = FastAPI(title="Face Recognition API", description="API for face recognition and clocking in/out")

trainer = FaceTrainer()

@app.post("/recognize")
async def recognize_face(file: UploadFile = File(...)):
    """Recognize face from uploaded image and toggle clock status"""
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image.")

    image_bytes = await file.read()
    result = trainer.recognize_face(image_bytes)
    return JSONResponse(content=result)

# Example usage
if __name__ == "__main__":
    # Uncomment below for training/validation
    # trainer = FaceTrainer()
    # trainer.create_sample_structure()
    # trainer.train_from_images_folder()
    # trainer.validate_encodings()

    # Run the API
    uvicorn.run(app, host="0.0.0.0", port=8000)
