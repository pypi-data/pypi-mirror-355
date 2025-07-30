import numpy as np
import cv2


class WellAnalyzer:
    def __init__(self, image, hsv_lower_bound, hsv_upper_bound):
        self.image = image
        self.hsv_lower_bound = hsv_lower_bound
        self.hsv_upper_bound = hsv_upper_bound

    def create_well_mask(self, x, y, r):
        mask = np.zeros(self.image.shape[:2], dtype=np.uint8)
        cv2.circle(mask, (x, y), r, 255, -1)
        return mask

    def analyze_plant_area(self, x, y, r):
        mask = self.create_well_mask(x, y, r)
        well_region = cv2.bitwise_and(self.image, self.image, mask=mask)
        hsv_well = cv2.cvtColor(well_region, cv2.COLOR_BGR2HSV)

        mask = cv2.inRange(hsv_well, self.hsv_lower_bound, self.hsv_upper_bound)

        # Find contours of the green areas
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        filtered_contours = [cnt for cnt in contours if cv2.contourArea(cnt) >= 200]
        total_area = sum(cv2.contourArea(c) for c in filtered_contours)

        return filtered_contours, total_area
