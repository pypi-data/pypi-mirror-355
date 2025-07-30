import cv2
import numpy as np

class ImageProcessor:
    def __init__(self, image_path):
        self.image = cv2.imread(image_path)
        self.gray_image = self._convert_to_grayscale()
        self.equalized_image = self._equalize_brightness(self.adaptive_threshold(self.gray_image))

    def _convert_to_grayscale(self):
        return cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)

    def _equalize_brightness(self, gray_image):
        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=20, tileGridSize=(8, 8))
        return clahe.apply(gray_image)

    def get_blurred_image(self, kernel_size=(7, 7), sigma=1.5):
        return cv2.GaussianBlur(self.equalized_image, kernel_size, sigma)

    def adaptive_threshold(self, gray_image):
        return cv2.adaptiveThreshold(gray_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                 cv2.THRESH_BINARY, 11, 2)

    def get_original_image(self):
        return self.image

    def get_resized_image(self, width):
        height = int(self.image.shape[0] * (width / self.image.shape[1]))  # Maintain aspect ratio
        return cv2.resize(self.image, (width, height))