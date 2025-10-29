# Face Recognition Clocking System Integration

This document explains how the face recognition system integrates with the clocking system backend and web application.

## System Architecture

```
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│   Web Application   │    │  Backend API        │    │ Face Recognition    │
│   (Angular)         │◄──►│  (Django)           │◄──►│ Service (FastAPI)   │
│   Port: 4200        │    │  Port: 8001         │    │ Port: 8000          │
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘
```

## Integration Flow

### 1. Clock In Process
1. User clicks "Clock In" button in web application
2. Camera opens and captures face image
3. Image is sent to Face Recognition Service (port 8000)
4. Face Recognition Service:
   - Recognizes the face
   - Calls Backend API to perform clock-in
   - Returns result to web application
5. Web application updates UI with clock-in status

### 2. Clock Out Process
1. User clicks "Clock Out" button in web application
2. Camera opens and captures face image
3. Image is sent to Face Recognition Service (port 8000)
4. Face Recognition Service:
   - Recognizes the face
   - Calls Backend API to perform clock-out
   - Calculates total hours worked
   - Returns result to web application
5. Web application updates UI with clock-out status and hours worked

## API Endpoints

### Face Recognition Service (Port 8000)
- `POST /login` - Clock in with face recognition
- `POST /logout` - Clock out with face recognition
- `POST /recognize` - Face recognition only
- `POST /register_new_user` - Register new face

### Backend API (Port 8001)
- `POST /api/face-recognition/clock-in/` - Clock in via face recognition
- `POST /api/face-recognition/clock-out/` - Clock out via face recognition
- `GET /api/employees/search/` - Search employees by name
- `GET /api/simple/overview/` - Get employee dashboard data

### Web Application (Port 4200)
- Employee dashboard with face recognition clocking interface
- Real-time status updates
- Activity logging and timesheet display

## Setup Instructions

### 1. Install Dependencies

**Face Recognition Service:**
```bash
cd FaceRecognation
pip install -r requirements.txt
```

**Backend API:**
```bash
cd Clocking-System-Backend
pip install -r requirements.txt
python manage.py migrate
```

**Web Application:**
```bash
cd Clocking-Web-Application
npm install
```

### 2. Start All Services

Run the integrated startup script:
```bash
cd FaceRecognation
start_integrated_system.bat
```

Or start manually:

**Terminal 1 - Face Recognition:**
```bash
cd FaceRecognation
python main.py
```

**Terminal 2 - Backend:**
```bash
cd Clocking-System-Backend
python manage.py runserver 127.0.0.1:8001
```

**Terminal 3 - Web App:**
```bash
cd Clocking-Web-Application
ng serve --port 4200
```

### 3. Access the System

- Web Application: http://localhost:4200
- Backend API: http://127.0.0.1:8001/api
- Face Recognition API: http://127.0.0.1:8000

## Features

### ✅ Integrated Features
- Face recognition for clock in/out
- Real-time status updates
- Employee authentication via face
- Automatic timesheet calculation
- Activity logging
- Backend data persistence

### 🔄 Data Flow
1. **Face Recognition** → Identifies employee
2. **Backend Integration** → Updates employee records
3. **Web Application** → Displays real-time updates
4. **Database** → Stores all clock data permanently

### 🛡️ Security
- Face recognition for secure authentication
- No image storage (privacy-focused)
- Backend API validation
- Employee data protection

## Troubleshooting

### Common Issues

1. **Camera not working:**
   - Check browser permissions
   - Ensure HTTPS or localhost access

2. **Face not recognized:**
   - Ensure good lighting
   - Register face encodings first
   - Check face recognition service logs

3. **Backend connection failed:**
   - Verify backend is running on port 8001
   - Check CORS settings
   - Ensure employee exists in database

4. **Port conflicts:**
   - Face Recognition: 8000
   - Backend API: 8001
   - Web Application: 4200

### Logs Location
- Face Recognition: Console output
- Backend: `server.log`
- Web Application: Browser console

## Employee Registration

To register new employees for face recognition:

1. Add employee to backend database
2. Use face registration endpoint:
```bash
curl -X POST -F "file=@photo.jpg" -F "text=EmployeeName" http://127.0.0.1:8000/register_new_user
```

## System Requirements

- Python 3.8+
- Node.js 16+
- Angular CLI
- Camera access
- Modern web browser

## Production Deployment

For production deployment:
1. Use HTTPS for all services
2. Configure proper CORS settings
3. Set up database backups
4. Monitor face recognition accuracy
5. Implement proper logging and monitoring