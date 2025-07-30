import cv2
import numpy as np
from app.plate import Plate
from sklearn.cluster import DBSCAN

class WellDetector:
    def __init__(self, blurred_image):
        self.blurred_image = blurred_image

    def detect_wells(self, dp=1, minDist=250, param1=45, param2=30, minRadius=155, maxRadius=180):
        circles = cv2.HoughCircles(
            self.blurred_image, 
            cv2.HOUGH_GRADIENT, 
            dp, 
            minDist,
            param1=param1,
            param2=param2, 
            minRadius=minRadius, 
            maxRadius=maxRadius    
        )
        return np.round(circles[0, :]).astype("int") if circles is not None else []

    def sort_circles(self, circles):
        circles_sorted = sorted(circles, key=lambda c: c[1])
        row_threshold = 40
        rows = []
        current_row = []
        previous_y = circles_sorted[0][1] if circles_sorted else 0

        for circle in circles_sorted:
            x, y, r = circle
            if abs(y - previous_y) > row_threshold:
                rows.append(sorted(current_row, key=lambda c: c[0]))
                current_row = [circle]
                previous_y = y
            else:
                current_row.append(circle)
                previous_y = y

        if current_row:
            rows.append(sorted(current_row, key=lambda c: c[0]))

        return [circle for row in rows for circle in row]

    def group_wells_into_plates(self, circles, plate_rows=6, plate_cols=4, eps=350):
        well_centers = [(x, y) for x, y, r in circles]
        well_centers_np = np.array(well_centers)
        expected_well_count = plate_rows * plate_cols

        # Use DBSCAN to cluster the wells based on proximity
        dbscan = DBSCAN(eps=eps, min_samples=2)
        labels = dbscan.fit_predict(well_centers_np)

        # Group wells by cluster
        clusters = {}
        for label, circle in zip(labels, circles):
            if label == -1:  # Noise, wells not part of any cluster
                continue
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(circle)  # Store the original circle (x, y, r)

        # Filter clusters by expected well count
        plates = []
        plate_count = 0;
        for cluster in clusters.values():
            # if len(cluster) == expected_well_count:
            plate_count += 1
            plate = Plate(
                label=f"Plate {plate_count}",
                rows=plate_rows, 
                cols=plate_cols, 
                wells=cluster)
            plates.append(plate)
        return plates

    def draw_plates(self, image, plates):
        for plate in plates:
            plate_np = np.array([(circle[0], circle[1]) for circle in plate], dtype=np.int32)

            # Calculate the bounding rectangle
            x, y, w, h = cv2.boundingRect(plate_np)

            # Draw the bounding rectangle on the image
            cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)

            # Show the annotated image
            cv2.imshow('Detected Plates', image)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
