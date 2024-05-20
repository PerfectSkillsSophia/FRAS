import base64
import os
from io import BytesIO
import cv2
import face_recognition
import numpy as np
from PIL import Image
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, JsonResponse, StreamingHttpResponse
from django.shortcuts import render
from .models import Student


uploads_dir = 'uploads'  # Subdirectory under MEDIA_ROOT for storing faces


def index(request):
    return render(request, 'index.html')

def ensure_dir(file_path):
    if not os.path.exists(file_path):
        os.makedirs(file_path)



def videofacerecog(request):
    if request.method == 'POST':
        file = request.FILES['media']
        fs = FileSystemStorage()
        filename = fs.save(file.name, file)
        uploaded_file_url = fs.url(filename)
        media_path = fs.path(filename)
        
        ensure_dir(os.path.join(settings.MEDIA_ROOT, uploads_dir))  # Ensure the directory exists

        if 'image' in file.content_type:
            # Handle image uploads
            image = face_recognition.load_image_file(media_path)
            face_locations = face_recognition.face_locations(image)
            pil_image = Image.fromarray(image)
            face_files = []
            for (top, right, bottom, left) in face_locations:
                face_image = pil_image.crop((left, top, right, bottom))
                face_image.thumbnail((200, 200))
                face_file_path = os.path.join(settings.MEDIA_ROOT, uploads_dir, f"{filename}-{top}.jpg")
                face_image.save(face_file_path)
                face_files.append(fs.url(os.path.join(uploads_dir, f"{filename}-{top}.jpg")))

            return render(request, 'show_faces.html', {
                'original_image': uploaded_file_url,
                'faces': face_files
            })

        elif 'video' in file.content_type:
            # Handle video uploads using the provided function
            face_files = extract_and_save_unique_faces(media_path)
            face_files_urls = [fs.url(os.path.join(uploads_dir, face_file)) for face_file in face_files]
            return render(request, 'show_faces.html', {
                'original_video': uploaded_file_url,  # Add original video URL
                'faces': face_files_urls
            })

    return render(request, 'videofacerecog.html')

def extract_and_save_unique_faces(video_path):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return []

    fps = cap.get(cv2.CAP_PROP_FPS)
    frames_per_two_seconds = int(fps * 2)
    saved_faces = []
    face_encodings = []
    two_second_count = 0

    while True:
        frame_index = two_second_count * frames_per_two_seconds
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        ret, frame = cap.read()
        if not ret:
            break

        face_locations = face_recognition.face_locations(frame)
        face_encs = face_recognition.face_encodings(frame, face_locations)

        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encs):
            matches = face_recognition.compare_faces(face_encodings, face_encoding, tolerance=0.6)
            if not any(matches):
                face_encodings.append(face_encoding)
                face_image = frame[top:bottom, left:right]
                face_filename = f"unique_face_{len(face_encodings)}.jpg"
                face_path = os.path.join(settings.MEDIA_ROOT, uploads_dir, face_filename)
                cv2.imwrite(face_path, face_image)
                saved_faces.append(face_filename)

        two_second_count += 1

    cap.release()
    return saved_faces




def upload_images(request):
    if request.method == 'POST':
        name = request.POST['name']
        image1 = request.FILES['image1']
        image2 = request.FILES['image2']
        image3 = request.FILES['image3']
        image4 = request.FILES['image4']

        # Save images
        student = Student(name=name, image1=image1, image2=image2, image3=image3, image4=image4)
        student.save()

        # Load images and encode faces
        image_paths = [student.image1.path, student.image2.path, student.image3.path, student.image4.path]
        encodings = []

        for path in image_paths:
            image = face_recognition.load_image_file(path)
            encoding = face_recognition.face_encodings(image)[0]
            encodings.append(encoding)

        # Combine encodings
        combined_encoding = np.mean(encodings, axis=0)
        student.face_encoding = combined_encoding.tobytes()
        student.save()

        return render(request, 'upload.html', {'success': True})

    return render(request, 'upload.html')

def webcam_template(request):
    return render(request, 'webcam.html')

def recognize_image(request):
    if request.method == 'POST':
        data = request.POST.get('image')
        image_data = base64.b64decode(data.split(',')[1])
        image = Image.open(BytesIO(image_data)).convert('RGB')  # Ensure image is in RGB format
        image = np.array(image)

        students = Student.objects.all()
        known_encodings = [np.frombuffer(student.face_encoding, dtype=np.float64) for student in students]
        known_names = [student.name for student in students]

        face_locations = face_recognition.face_locations(image)
        face_encodings = face_recognition.face_encodings(image, face_locations)

        results = []
        for face_encoding, face_location in zip(face_encodings, face_locations):
            matches = face_recognition.compare_faces(known_encodings, face_encoding)
            name = "Unknown"

            face_distances = face_recognition.face_distance(known_encodings, face_encoding)
            best_match_index = np.argmin(face_distances)
            if matches[best_match_index]:
                name = known_names[best_match_index]

            results.append({"name": name, "location": face_location})

        return JsonResponse({"results": results})

    return HttpResponse("Only POST method is allowed")

def get_encodings(request):
    students = Student.objects.all()
    encodings = {student.name: list(np.frombuffer(student.face_encoding, dtype=np.float64)) for student in students}
    return JsonResponse(encodings)