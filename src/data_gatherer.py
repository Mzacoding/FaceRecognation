import cv2
import os
import face_recognition
import pickle
from datetime import datetime

class FaceDataGatherer:
    def __init__(self, encodings_path="./encodings"):
        self.encodings_path = encodings_path
        if not os.path.exists(self.encodings_path):
            os.makedirs(self.encodings_path)
    
    def capture_from_camera(self, employee_name, num_samples=5):
        """Capture face samples from camera for training"""
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            return False, "Could not open camera"
        
        print(f"Capturing {num_samples} samples for {employee_name}")
        print("Press SPACE to capture, ESC to cancel")
        
        samples_captured = 0
        face_encodings = []
        
        while samples_captured < num_samples:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Display frame
            cv2.putText(frame, f"Samples: {samples_captured}/{num_samples}", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(frame, "Press SPACE to capture", 
                       (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Draw face detection box
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_frame)
            
            for (top, right, bottom, left) in face_locations:
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            
            cv2.imshow('Face Capture', frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC key
                break
            elif key == 32:  # SPACE key
                if len(face_locations) > 0:
                    # Extract face encoding
                    encodings = face_recognition.face_encodings(rgb_frame)
                    if len(encodings) > 0:
                        face_encodings.append(encodings[0])
                        samples_captured += 1
                        print(f"Captured sample {samples_captured}")
                else:
                    print("No face detected, try again")
        
        cap.release()
        cv2.destroyAllWindows()
        
        if samples_captured > 0:
            # Average the encodings for better accuracy
            avg_encoding = sum(face_encodings) / len(face_encodings)
            return self.save_encoding(employee_name, avg_encoding)
        else:
            return False, "No samples captured"
    
    def process_image_file(self, image_path, employee_name):
        """Process a single image file and extract face encoding"""
        if not os.path.exists(image_path):
            return False, "Image file not found"
        
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            return False, "Could not load image"
        
        # Convert to RGB
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Extract face encoding
        face_encodings = face_recognition.face_encodings(rgb_image)
        
        if len(face_encodings) == 0:
            return False, "No face detected in image"
        
        # Use the first face found
        face_encoding = face_encodings[0]
        return self.save_encoding(employee_name, face_encoding)
    
    def save_encoding(self, employee_name, face_encoding):
        """Save face encoding to pickle file"""
        try:
            filepath = os.path.join(self.encodings_path, f"{employee_name}.pickle")
            with open(filepath, 'wb') as f:
                pickle.dump(face_encoding, f)
            
            # Log the registration
            log_entry = f"{datetime.now()}: Registered {employee_name}\n"
            with open(os.path.join(self.encodings_path, "registration_log.txt"), 'a') as log_file:
                log_file.write(log_entry)
            
            return True, f"Face encoding saved for {employee_name}"
        except Exception as e:
            return False, f"Error saving encoding: {e}"
    
    def list_registered_employees(self):
        """List all registered employees"""
        employees = []
        for filename in os.listdir(self.encodings_path):
            if filename.endswith('.pickle'):
                employees.append(filename[:-7])  # Remove .pickle extension
        return employees
    
    def delete_employee(self, employee_name):
        """Delete an employee's face encoding"""
        filepath = os.path.join(self.encodings_path, f"{employee_name}.pickle")
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                return True, f"Deleted {employee_name} from database"
            else:
                return False, f"Employee {employee_name} not found"
        except Exception as e:
            return False, f"Error deleting employee: {e}"

# Example usage
if __name__ == "__main__":
    gatherer = FaceDataGatherer()
    
    # Capture from camera
    # success, message = gatherer.capture_from_camera("John_Doe")
    # print(message)
    
    # Or process from image file
    # success, message = gatherer.process_image_file("path/to/image.jpg", "Jane_Smith")
    # print(message)