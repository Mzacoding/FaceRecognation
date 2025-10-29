import cv2
import face_recognition
import pickle
import numpy as np
import os

class FaceRecognizer:
    def __init__(self, encodings_path="./encodings"):
        self.encodings_path = encodings_path
        self.known_encodings = []
        self.known_names = []
        self.load_encodings()
    
    def load_encodings(self):
        """Load all face encodings from pickle files"""
        if not os.path.exists(self.encodings_path):
            os.makedirs(self.encodings_path)
            return
        
        self.known_encodings = []
        self.known_names = []
        
        for filename in os.listdir(self.encodings_path):
            if filename.endswith('.pickle'):
                try:
                    with open(os.path.join(self.encodings_path, filename), 'rb') as f:
                        encoding = pickle.load(f)
                        if isinstance(encoding, np.ndarray) and encoding.shape == (128,):
                            self.known_encodings.append(encoding)
                            self.known_names.append(filename[:-7])  # Remove .pickle extension
                except Exception as e:
                    print(f"Error loading {filename}: {e}")
    
    def recognize_face(self, image, tolerance=0.6):
        """Recognize face in image and return name and confidence"""
        # Find face encodings in the image
        face_encodings = face_recognition.face_encodings(image)
        
        if len(face_encodings) == 0:
            return None, False, 0.0
        
        # Use the first face found
        face_encoding = face_encodings[0]
        
        if len(self.known_encodings) == 0:
            return "unknown", False, 0.0
        
        # Compare with known faces
        matches = face_recognition.compare_faces(self.known_encodings, face_encoding, tolerance=tolerance)
        face_distances = face_recognition.face_distance(self.known_encodings, face_encoding)
        
        if True in matches:
            best_match_index = np.argmin(face_distances)
            if matches[best_match_index]:
                name = self.known_names[best_match_index]
                confidence = 1 - face_distances[best_match_index]
                return name, True, confidence
        
        return "unknown", False, 0.0
    
    def add_new_face(self, image, name):
        """Add a new face encoding to the database"""
        face_encodings = face_recognition.face_encodings(image)
        
        if len(face_encodings) == 0:
            return False, "No face detected in image"
        
        # Use the first face found
        face_encoding = face_encodings[0]
        
        # Save encoding to pickle file
        filepath = os.path.join(self.encodings_path, f"{name}.pickle")
        try:
            with open(filepath, 'wb') as f:
                pickle.dump(face_encoding, f)
            
            # Reload encodings to include the new one
            self.load_encodings()
            return True, "Face registered successfully"
        except Exception as e:
            return False, f"Error saving face: {e}"