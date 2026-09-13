"""OpenCV preprocessing for OCR.

Pipeline: resize → grayscale → denoise → threshold.
This module only prepares images. It does not interpret medical meaning.
"""

from __future__ import annotations

import cv2
import numpy as np

TARGET_WIDTH = 1400


def decode_image_bytes(image_bytes: bytes) -> np.ndarray:
    array = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(array, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("The uploaded file could not be read as an image.")
    return image


def resize_for_ocr(image: np.ndarray, target_width: int = TARGET_WIDTH) -> np.ndarray:
    height, width = image.shape[:2]
    if width <= 0 or height <= 0:
        raise ValueError("The image has an invalid size.")
    if width == target_width:
        return image
    scale = target_width / float(width)
    new_size = (target_width, max(1, int(height * scale)))
    interpolation = cv2.INTER_CUBIC if scale > 1 else cv2.INTER_AREA
    return cv2.resize(image, new_size, interpolation=interpolation)


def to_grayscale(image: np.ndarray) -> np.ndarray:
    if len(image.shape) == 2:
        return image
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def denoise(gray: np.ndarray) -> np.ndarray:
    return cv2.fastNlMeansDenoising(gray, None, h=12, templateWindowSize=7, searchWindowSize=21)


def threshold(gray: np.ndarray) -> np.ndarray:
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    adaptive = cv2.adaptiveThreshold(
        blurred,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        9,
    )
    _otsu_value, otsu = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    # Prefer the version with more ink (fewer white pixels) for typical printed labels.
    if int(np.mean(adaptive)) > int(np.mean(otsu)):
        return otsu
    return adaptive


def preprocess_for_ocr(image_bgr: np.ndarray) -> dict[str, np.ndarray]:
    resized = resize_for_ocr(image_bgr)
    gray = to_grayscale(resized)
    denoised = denoise(gray)
    binary = threshold(denoised)
    return {
        "resized": resized,
        "gray": gray,
        "denoise": denoised,
        "threshold": binary,
    }
