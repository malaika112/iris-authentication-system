import logging

import cv2
import numpy as np
from django.conf import settings
from tensorflow.keras.models import load_model

logger = logging.getLogger(__name__)

# Constants (must match the training notebook)
IMG_HEIGHT = 150
IMG_WIDTH = 150
NUM_CLASSES = 2000

# Load the pre-trained iris model once, when the app starts
iris_model = load_model(settings.MODEL_PATH)


def resize_keep_aspect_ratio(img, target_height=IMG_HEIGHT, target_width=IMG_WIDTH, pad_value=255):
    """Resize to the target size while keeping the aspect ratio, padding the rest."""
    aspect_ratio = img.shape[1] / img.shape[0]

    if aspect_ratio > target_width / target_height:
        new_width = target_width
        new_height = int(target_width / aspect_ratio)
    else:
        new_height = target_height
        new_width = int(target_height * aspect_ratio)

    resized_img = cv2.resize(img, (new_width, new_height))
    preprocessed_img = np.full((target_height, target_width), pad_value, dtype=np.uint8)

    x_offset = (target_width - new_width) // 2
    y_offset = (target_height - new_height) // 2
    preprocessed_img[y_offset:y_offset + new_height, x_offset:x_offset + new_width] = resized_img

    return preprocessed_img


def preprocess_image(image_path):
    """Load an image as grayscale and prepare it for the model (1 x 150 x 150 x 1, scaled to 0-1)."""
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        logger.warning("Unable to load image at %s", image_path)
        return None
    img = resize_keep_aspect_ratio(img, IMG_HEIGHT, IMG_WIDTH)
    img = img / 255.0
    img = np.expand_dims(img, axis=(0, -1))  # Add batch and channel dimensions
    return img


def predict_class(img):
    """Return the predicted class index and the model's confidence as a percentage."""
    predictions = iris_model.predict(img, verbose=0)
    predicted_class_idx = int(np.argmax(predictions, axis=1)[0])
    confidence = round(float(np.max(predictions)) * 100, 2)
    return predicted_class_idx, confidence
