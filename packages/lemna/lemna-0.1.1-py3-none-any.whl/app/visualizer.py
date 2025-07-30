import cv2
import numpy as np
class Visualizer:
    def __init__(self, original_image):
        self.annotated_image = original_image.copy()

    def draw_circles(self, circles):
        for x, y, r in circles:
            cv2.circle(self.annotated_image, (x, y), r, (255, 0, 255), 2)

    def draw_contours(self, contours, color=(0, 0, 255), thickness=2):
        cv2.drawContours(self.annotated_image, contours, -1, color, thickness)

    def add_text(self, x, y, r, text):
        cv2.putText(self.annotated_image, text, (x - 20, y - r - 10), cv2.FONT_HERSHEY_SIMPLEX, 
                    1.0, (255, 0, 0), 2)

    def show_image(self, window_name, width):
        resized_image = cv2.resize(self.annotated_image, (width, int(self.annotated_image.shape[0] * (width / self.annotated_image.shape[1]))))
        cv2.imshow(window_name, resized_image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    def save_image(self, file_name):
        cv2.imwrite(file_name, self.annotated_image)
    
    def draw_plate_bounding_box(self, circles, label="Plate"):
        plate_np = np.array([(circle[0], circle[1]) for circle in circles], dtype=np.int32)

        # Calculate the bounding rectangle
        x, y, w, h = cv2.boundingRect(plate_np)

        # Draw the bounding rectangle on the image
        cv2.rectangle(self.annotated_image, (x, y), (x + w, y + h), (0, 255, 0), 2)

         # Set font and calculate the position for the label
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 1
        font_thickness = 3
        text_size = cv2.getTextSize(label, font, font_scale, font_thickness)[0]

        # Calculate position: top-left corner of the bounding box
        text_x = x
        text_y = y - 10 if y - 10 > 10 else y + text_size[1] + 10

        # Draw the label on the image
        cv2.putText(self.annotated_image, label, (text_x, text_y), font, font_scale, (255, 255, 0), font_thickness)