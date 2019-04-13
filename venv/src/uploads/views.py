from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.http import HttpResponse
from django.core.files.storage import FileSystemStorage
from django.contrib.auth.models import User
import io
from django.http import FileResponse
from reportlab.pdfgen import canvas
from uploads.models import Document
from uploads.forms import DocumentForm
# from uploads.webcam import *
import face_recognition
import cv2
import os
import glob
import pickle
import numpy as np
import dlib
from sklearn import svm
from celery import task

nme={}
nm={}
# fdlist=[]

from django.contrib.auth import logout

def logout_view(request):
    nme.clear()
    nm.clear()
    logout(request)
    return render(request,'end.html')



def results_view(request):
    if request.user.is_authenticated:
        # list_set = set(nme)
        # dist_set=set(fdlist)
    # convert the set to the list
        # unique_list = (list(list_set))
        # un_dist=(list(fdlist))
        if request.method=="POST":
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="results.pdf"'
            buffer = io.BytesIO()
            p = canvas.Canvas(buffer)
            p.drawString(50, 800, "<This is a system generated pdf document>")
            p.drawString(50, 775, "<contact@: shashanksinghchandel_k@srmuniv.edu.in>")
            p.drawString(
                150,730, "Welcome to Facial Recognition and Tracking System")
            p.drawString(60,700,"Hello user:"+str(request.user))
            documents = Document.objects.filter(
                profile_user=request.user).count()
            p.drawString(60, 650, "Total no. of identities uploaded by the user: "+str(documents))
            p.drawString(60, 625, "Total no. of individuals identified: "+str(len(nme)))
            p.drawString(60,600,"List of Individuals identified based on Face Recognition:")
            p.drawString(70, 575, "Individual")
            p.drawString(230, 575, "Face distance")
            p.drawString(390, 575, "Probability")
            i=540
            for name,dist in nme.items():
                p.drawString(70, i, str(name))
                p.drawString(230, i, '{:.5}'.format(str(dist)))
                i-=50

            i=540  
            for name,prob in nm.items():
                p.drawString(70, i, str(name))
                p.drawString(390, i, '{:.5}'.format(str(prob[0])))
                i -= 50
           
            
            # p.drawString(60, 700, "Hello user:"+str(request.user))
            p.showPage()
            p.save()
            pdf = buffer.getvalue()
            buffer.close()
            response.write(pdf)
            return response
        context= {
            'dist_tab':nme,
            'prob_tab':nm
            
            }
        
        # documents = Document.objects.filter(profile_user=request.user)
        return render(request,'results.html',context)
    else:
        return redirect("login")


def delete_view(request,id):
    if request.user.is_authenticated:
        if request.method == 'POST':
            doc = Document.objects.get(id=id)
            doc.delete()
            return redirect("home")
    else:
        return redirect("login")


# cv2.FONT_HERSHEY_COMPLEX_SMALL



def home(request):
    if request.user.is_authenticated:
        documents = Document.objects.filter(profile_user=request.user)
        return render(request, 'home.html', {'documents': documents})
    else :
        return redirect("login")
    #     # return render(request, 'home.html', {})

def simple_upload(request):
    if request.method == 'POST' and request.FILES['myfile']:
        myfile = request.FILES['myfile']
        fs = FileSystemStorage()
        filename = fs.save(myfile.name, myfile)
        uploaded_file_url = fs.url(filename)
        return render(request, 'simple_upload.html', {
            'uploaded_file_url': uploaded_file_url
        })
    return render(request, 'simple_upload.html')


def model_form_upload(request):
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            newdoc=form.save(commit=False)
            newdoc.profile_user=request.user
            newdoc.keep_owner(request.user)
            newdoc.save()
            return redirect('home')
    else:
        form = DocumentForm()
    return render(request, 'model_form_upload.html', {
        'form': form
    })


def face_recognition_view(request):
    # nme.clear()
    # fdlist.clear()
    img_dir = os.getcwd()
    pt = "media/user_"+str(request.user)
    img = os.path.join(img_dir, pt)
    # img_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "documents")
    face_locations = []
    face_encodings = []
    face_names = []
    known_face_encodings = []
    known_face_names = []
    process_this_frame = True
    if request.method == "POST":

        files = os.listdir(img)
        print(files)
        for file in files:
            print(file)
            sample_image = face_recognition.load_image_file(img+"/"+file)
            st = str(file).split(".jpg")[0]
            print(st)
            known_face_names.append(st)
            sample_face_encoding = face_recognition.face_encodings(sample_image)[
                0]
            known_face_encodings.append(sample_face_encoding)
        # vidtag=request.POST['videoInput']    
        video_capture = cv2.VideoCapture(0)
        while True:

            ret, frame = video_capture.read()
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb_small_frame = small_frame[:, :, ::-1]

            if process_this_frame:

                face_locations = face_recognition.face_locations(
                    rgb_small_frame, model='cnn')
                face_encodings = face_recognition.face_encodings(
                    rgb_small_frame, face_locations)

                face_names = []
                for face_encoding in face_encodings:

                    matches = face_recognition.compare_faces(
                        known_face_encodings, face_encoding, tolerance=0.5)

                    fdist= face_recognition.face_distance(known_face_encodings,face_encoding).tolist()    
                    print(fdist)
                    name = "Unknown"

                    
                    if True in matches:
                        first_match_index = matches.index(True)
                        name = known_face_names[first_match_index]
                        fd=fdist[first_match_index]

                    face_names.append(name)
                    nme[name]=fd
                    # fdlist.append(fd)

            process_this_frame = not process_this_frame

            
            for (top, right, bottom, left), name in zip(face_locations, face_names):
               
                top *= 4
                right *= 4
                bottom *= 4
                left *= 4

               
                cv2.rectangle(frame, (left, top),
                              (right, bottom), (255, 0, 0), 2)

                
                cv2.rectangle(frame, (left, bottom - 35),
                              (right, bottom), (255, 0, 0), cv2.FILLED)
                font = cv2.FONT_HERSHEY_DUPLEX
                cv2.putText(frame, name, (left + 6, bottom - 6),
                            font, 1.0, (255, 255, 255), 1)

            
            cv2.imshow('Press "q" for exiting video', frame)

            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        
        video_capture.release()
        cv2.destroyAllWindows()

        # return redirect("face_recognition")

    return render(request, "recognition.html", {})


def face_recognition_classify(request):
    
    # nm.clear()
   
    face_locations = []
    face_encodings = []
    face_names = []
    # known_face_encodings = []
    # known_face_names = []
    process_this_frame = True
    if request.method == "POST" and request.user.is_authenticated:

        classifier_filename = str(request.user)+'_classifier.pkl'
        
        model= pickle.load(open(classifier_filename,'rb'))

        video_capture = cv2.VideoCapture(0)
        while True:

            ret, frame = video_capture.read()
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb_small_frame = small_frame[:, :, ::-1]

            if process_this_frame:

                face_locations = face_recognition.face_locations(
                    rgb_small_frame, model='cnn')
                face_encodings = face_recognition.face_encodings(
                    rgb_small_frame, face_locations)

                face_names = []
                for face_encoding in face_encodings:

                    matches = model.predict(face_encoding.reshape(1, -1))
                    match = model.predict_proba(face_encoding.reshape(1, -1))
                    # ind = np.argmax(matches, axis=1)
                    # bsp = matches[np.arange(len(ind)), ind]
                    # print("indices", ind)
                    # print("bsp", bsp)
                    name = "Unknown"

                    if len(matches)!=0:
                        # first_match_index = matches.index(True)
                        # name = known_face_names[first_match_index]
                        # fd = fdist[first_match_index]

                        face_names=matches
                        ind = np.argmax(match, axis=1)
                        bsp = match[np.arange(len(ind)), ind]
                        nm[matches[0]]=bsp
                    else:
                        face_names.append(name)
                    # nme[name] = fd
                    # fdlist.append(fd)

            process_this_frame = not process_this_frame

            for (top, right, bottom, left), name in zip(face_locations, face_names):

                top *= 4
                right *= 4
                bottom *= 4
                left *= 4

                cv2.rectangle(frame, (left, top),
                              (right, bottom), (0, 255, 0), 2)

                cv2.rectangle(frame, (left, bottom - 35),
                              (right, bottom), (0, 255, 0), cv2.FILLED)
                font = cv2.FONT_HERSHEY_DUPLEX
                cv2.putText(frame, name, (left + 6, bottom - 6),
                            font, 1.0, (255, 255, 255), 1)

            cv2.imshow('Press "q" for exiting video', frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        video_capture.release()
        cv2.destroyAllWindows()

        return redirect("face_classify")

    return render(request, "train.html", {})

# @task
# def work_todo(request):
#     known_face_encodings = []
#     known_face_names = []
#     img_dir = os.getcwd()
#     pt = "media/user_"+str(request.user)
#     img = os.path.join(img_dir, pt)
#     files = os.listdir(img)
#     for file in files:
#         sample_image = face_recognition.load_image_file(img+"/"+file)
#         st = str(file).split(".jpg")[0]
#         print(st)
#         known_face_names.append(st)
#         sample_face_encoding = face_recognition.face_encodings(
#             sample_image, num_jitters=10)[0]
#         known_face_encodings.append(sample_face_encoding.tolist())

#     clf = svm.SVC(kernel='linear', probability=True)
# # clf = LinearDiscriminantAnalysis()
#     clf.fit(known_face_encodings, known_face_names)
#     classifier_filename = str(request.user)+'_classifier.pkl'
#     pickle.dump(clf, open(classifier_filename, 'wb'))




# def train_view(request):

#     # face_locations = []
#     # face_encodings = []
#     # face_names = []
#     # process_this_frame = True
#     # classifier_filename = './class/classifier.pkl'
    

#     if request.method == "POST" and request.user.is_authenticated:
#         work_todo(request).delay()


#     return render(request, 'classifier.html',{})





def train_view(request):

    # face_locations = []
    # face_encodings = []
    # face_names = []
    # process_this_frame = True
    # classifier_filename = './class/classifier.pkl'
    known_face_encodings = []
    known_face_names = []
    img_dir = os.getcwd()
    pt = "media/user_"+str(request.user)
    img = os.path.join(img_dir, pt)

    if request.method == "POST" and request.user.is_authenticated:
        files = os.listdir(img)
        for file in files:
            sample_image = face_recognition.load_image_file(img+"/"+file)
            st = str(file).split(".jpg")[0]
            print(st)
            known_face_names.append(st)
            sample_face_encoding = face_recognition.face_encodings(
                sample_image, num_jitters=10)[0]
            known_face_encodings.append(sample_face_encoding.tolist())

        clf = svm.SVC(kernel='linear', probability=True)
# clf = LinearDiscriminantAnalysis()
        clf.fit(known_face_encodings, known_face_names)
        classifier_filename = str(request.user)+'_classifier.pkl'
        pickle.dump(clf, open(classifier_filename, 'wb'))
        return redirect("train_view")

    return render(request, 'classifier.html', {})






















# def face_recognition_view(request):
#     nme.clear()
#     img_dir=os.getcwd()
#     pt="user_"+str(request.user)
#     img=os.path.join(img_dir,pt)
#     # img_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "documents")
#     face_locations = []
#     face_encodings = []
#     face_names = []
#     known_face_encodings = []
#     known_face_names = []
#     process_this_frame = True
#     if request.method == "POST":

#         files=os.listdir(img)
#         print(files)
#         for file in files:
#             print(file)
#             sample_image = face_recognition.load_image_file(img+"/"+file)
#             st=str(file).split(".jpg")[0]
#             print(st)
#             known_face_names.append(st)
#             sample_face_encoding = face_recognition.face_encodings(sample_image)[0]
#             known_face_encodings.append(sample_face_encoding)
#         video_capture = cv2.VideoCapture(0)
#         while True:

#             ret, frame = video_capture.read()
#             small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
#             rgb_small_frame = small_frame[:, :, ::-1]

#             if process_this_frame:

#                 face_locations = face_recognition.face_locations(rgb_small_frame,model='cnn')
#                 face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

#                 face_names = []
#                 for face_encoding in face_encodings:

#                     matches = face_recognition.compare_faces(known_face_encodings, face_encoding,tolerance=0.5)
#                     print(matches)
#                     name = "Unknown"

#                     # If a match was found in known_face_encodings, just use the first one.
#                     if True in matches:
#                         first_match_index = matches.index(True)
#                         name = known_face_names[first_match_index]

#                     face_names.append(name)
#                     nme.append(name)

#             process_this_frame = not process_this_frame


#             # Display the results
#             for (top, right, bottom, left), name in zip(face_locations, face_names):
#                 # Scale back up face locations since the frame we detected in was scaled to 1/4 size
#                 top *= 4
#                 right *= 4
#                 bottom *= 4
#                 left *= 4

#                 # Draw a box around the face
#                 cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

#                 # Draw a label with a name below the face
#                 cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
#                 font = cv2.FONT_HERSHEY_DUPLEX
#                 cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)

#             # Display the resulting image
#             # cv2.namedWindow('Video', cv2.WINDOW_NORMAL)
#             cv2.imshow('Video', frame)

#             # Hit 'q' on the keyboard to quit!
#             if cv2.waitKey(1) & 0xFF == ord('q'):
#                 break

#         # Release handle to the webcam
#         video_capture.release()
#         cv2.destroyAllWindows()

    
#         # return redirect("face_recognition")
       




#     return render(request, "recognition.html", {})
