# authentication/views.py
import logging
import os

from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.core.files.storage import FileSystemStorage
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import redirect, render

from authentication.models import CustomUser

from .forms import CustomUserCreationForm
from .utils import predict_class, preprocess_image

logger = logging.getLogger(__name__)

# A login is accepted only when the predicted class belongs to a registered user
# and the model is more than 90% confident.
CONFIDENCE_THRESHOLD = 90
MAX_CLASS_INDEX = 99
MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5 MB
ALLOWED_IMAGE_TYPES = {'image/jpeg', 'image/png', 'image/bmp'}


def home_view(request):
    return render(request, 'home.html')


def signup_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('login')
        logger.info("Signup form invalid: %s", form.errors.as_json())
        return render(request, 'authentication/signup.html',
                      {'form': form, 'error': 'Signup failed. Please check the form for errors.'})
    form = CustomUserCreationForm()
    return render(request, 'authentication/signup.html', {'form': form})


def login_view(request):
    if request.method == 'POST' and request.FILES.get('iris_image'):
        iris_image = request.FILES['iris_image']

        if iris_image.size > MAX_UPLOAD_BYTES or iris_image.content_type not in ALLOWED_IMAGE_TYPES:
            return JsonResponse({'status': 'error', 'error': 'Please upload a JPEG, PNG or BMP image under 5 MB.'})

        fs = FileSystemStorage()
        filename = fs.save(iris_image.name, iris_image)  # Save the uploaded image temporarily
        file_path = fs.path(filename)

        try:
            # Step 1: Preprocessing
            preprocessed_image = preprocess_image(file_path)
            if preprocessed_image is None:
                return JsonResponse({'status': 'error', 'error': 'Failed to process image. Please try again.'})

            # Step 2: Prediction
            predicted_class_idx, confidence = predict_class(preprocessed_image)
            logger.info("Predicted class %s with confidence %s%%", predicted_class_idx, confidence)
            request.session['confidence'] = float(confidence)

            # Step 3: Check that the predicted class is valid and belongs to a user
            if 0 <= predicted_class_idx <= MAX_CLASS_INDEX and confidence > CONFIDENCE_THRESHOLD:
                try:
                    user = CustomUser.objects.get(Q(user_id_1=predicted_class_idx) | Q(user_id_2=predicted_class_idx))
                except CustomUser.DoesNotExist:
                    return JsonResponse({'status': 'error', 'error': 'User not found.'})

                # Store the latest login image and confidence for the dashboard
                if user.image_1:
                    fs.delete(user.image_1.path)
                user.image_1 = iris_image
                user.percentage_1 = confidence
                user.save()

                login(request, user)
                return JsonResponse({'status': 'login_success', 'confidence': float(confidence), 'redirect_url': '/dashboard'})

            return JsonResponse({'status': 'error', 'error': 'Invalid user or low confidence. Please try again.'})

        except Exception:
            logger.exception("Error during iris login")
            return JsonResponse({'status': 'error', 'error': 'An error occurred during login. Please try again.'})
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)  # Never keep the temporary upload

    return render(request, 'authentication/login.html')


def custom_logout(request):
    logout(request)
    return redirect('login')


@login_required
def dashboard_view(request):
    return render(request, 'authentication/dashboard.html')
