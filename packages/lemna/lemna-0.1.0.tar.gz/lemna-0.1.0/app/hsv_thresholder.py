# Source: https://stackoverflow.com/a/59906154
import cv2
import numpy as np


class HsvThresolder:
    def __init__(self, image_path):
        self.image = cv2.imread(image_path)

    def threshold(self, width=1200):
        # Create a window
        window_name ='image (press \'q\' quit)'
        cv2.namedWindow(window_name)
        def nothing(x):
            pass


        # Create trackbars for color change
        # Hue is from 0-179 for Opencv
        cv2.createTrackbar('HMin', window_name, 0, 179, nothing)
        cv2.createTrackbar('SMin', window_name, 0, 255, nothing)
        cv2.createTrackbar('VMin', window_name, 0, 255, nothing)
        cv2.createTrackbar('HMax', window_name, 0, 179, nothing)
        cv2.createTrackbar('SMax', window_name, 0, 255, nothing)
        cv2.createTrackbar('VMax', window_name, 0, 255, nothing)

        # Set default value for Max HSV trackbars
        cv2.setTrackbarPos('HMax', window_name, 179)
        cv2.setTrackbarPos('SMax', window_name, 255)
        cv2.setTrackbarPos('VMax', window_name, 255)

        # Initialize HSV min/max values
        hMin = sMin = vMin = hMax = sMax = vMax = 0
        phMin = psMin = pvMin = phMax = psMax = pvMax = 0

        while(1):
            # Get current positions of all trackbars
            hMin = cv2.getTrackbarPos('HMin', window_name)
            sMin = cv2.getTrackbarPos('SMin', window_name)
            vMin = cv2.getTrackbarPos('VMin', window_name)
            hMax = cv2.getTrackbarPos('HMax', window_name)
            sMax = cv2.getTrackbarPos('SMax', window_name)
            vMax = cv2.getTrackbarPos('VMax', window_name)

            # Set minimum and maximum HSV values to display
            lower = np.array([hMin, sMin, vMin])
            upper = np.array([hMax, sMax, vMax])

            # Convert to HSV format and color threshold
            hsv = cv2.cvtColor(self.image, cv2.COLOR_BGR2HSV)
            mask = cv2.inRange(hsv, lower, upper)
            result = cv2.bitwise_and(self.image, self.image, mask=mask)

            # Print if there is a change in HSV value
            if((phMin != hMin) | (psMin != sMin) | (pvMin != vMin) | (phMax != hMax) | (psMax != sMax) | (pvMax != vMax) ):
                print("(hMin = %d , sMin = %d, vMin = %d), (hMax = %d , sMax = %d, vMax = %d)" % (hMin , sMin , vMin, hMax, sMax , vMax))
                phMin = hMin
                psMin = sMin
                pvMin = vMin
                phMax = hMax
                psMax = sMax
                pvMax = vMax

            display_image = cv2.resize(result, (width, int(result.shape[0] * (width / result.shape[1]))))
            # Display result image
            cv2.imshow(window_name, display_image)
            if cv2.waitKey(10) & 0xFF == ord('q'):
                break

        cv2.destroyAllWindows()
        return (hMin, sMin, vMin), (hMax, sMax, vMax)