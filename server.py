import face_recognition
import cv2
import numpy as np
import os
from pathlib import Path

PATH_TO_REF = "/home/Felipe/Downloads/20250918_170624.jpg"

def get_next_filename(folder, base_name, extension="npy"):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)

    n = 0
    while True:
        file_path = folder / f"{base_name}_{n}.{extension}"

        if not file_path.exists():
            return file_path

        n += 1

def save_encodings(folder, base_name, encodings, names):
    for encode, name in zip(encodings, names):
        file_name = get_next_filename(folder, base_name)

        data = np.array(
            {
                "encoding": encode,
                "name": name
            },
            dtype=object
        )

        np.save(f'{file_name}', data)
        print(f"Encoding saved for {file_name}")
    
def load_encodings(folder, base_name, extension="npy"):
    folder = Path(folder)

    encodings = []
    names = []
    
    n = 0
    while True:
        file_path = folder / f"{base_name}_{n}.{extension}"

        if not file_path.exists():
            break;

        data = np.load(f'{file_path}', allow_pickle=True).item()

        encodings.append(data["encoding"])
        names.append(data["name"])

        print(f"Encoding loaded for {file_path}")
        n += 1

    return encodings, names


def process_video():
    pass

def main():
    video_capture = cv2.VideoCapture(0)

    # Load a sample picture and learn how to recognize it.
    #ref_image = face_recognition.load_image_file(PATH_TO_REF)
    #ref_face_encoding = face_recognition.face_encodings(ref_image)[0]

    #The data about my faces
    #known_face_encodings = [ref_face_encoding]
    known_face_encodings = []
    known_face_names = []
    
    base_path = os.path.join(os.getcwd(), "faces")
    basename = "saved_img"

    face_locations = []
    face_encodings = []
    face_names = []
    process_this_frame = True
    save = True

    while True:
        ret, frame = video_capture.read()#Pick up a frame of the video
        if process_this_frame and ret:
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
            
            if save and face_encodings:
                for face_encoding in face_encodings:
                    name = input("Digite seu nome: ")
                    known_face_names.append(name)

                save_encodings(base_path, basename, face_encodings, known_face_names)
                known_face_encodings, known_face_names = load_encodings(base_path, basename)
                save = False

            
            face_names = []
            #See the encodings for each face IN the FRAME
            for face_encoding in face_encodings:
                # See if the face is a match for the known face(s)
                matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
                name = "Unknown"

           
                # Or instead, use the known face with the smallest distance to the new face
                face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index]:
                    name = known_face_names[best_match_index]
                
                face_names.append(name)


        process_this_frame = not process_this_frame #Only process every other frame, to save time
        # Display the results
        for (top, right, bottom, left), name in zip(face_locations, face_names):
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4

            #Draw a box around the face
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

            #Draw a label with a name below the face
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
            font = cv2.FONT_HERSHEY_DUPLEX
            cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)

        #Display the resulting image
        cv2.imshow('Video', frame)

        #Hit 'q' on the keyboard to quit!
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    #Release handle to the webcam
    video_capture.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
