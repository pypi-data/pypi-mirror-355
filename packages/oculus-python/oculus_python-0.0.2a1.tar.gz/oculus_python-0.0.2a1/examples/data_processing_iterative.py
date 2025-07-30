from bps_oculus import io, logger, core, oculus
from pathlib import Path
import cv2
import numpy as np


if __name__ == "__main__":
    # Get a file
    file = Path("../data/test.v2.oculus")
    # Determine the version
    input_version = logger.check_oculus_log_version(file)
    # Create an importer object
    I = io.importer[input_version](file)

    for i, (item_info, item_message, sonar_data, _) in enumerate(I.generate()):
        # Assigning the polar image for processing
        filtered_polar = sonar_data.polar_image

        # Apply a corrective TVG
        gain = -0.25  # this is some normalized analogue to dB/m
        tvg = sonar_data.ranging_table * gain
        filtered_polar = filtered_polar + tvg[:, None]

        # Apply lower thresholding
        thresh = 60
        filtered_polar = np.where(filtered_polar > thresh, filtered_polar, thresh)

        # Define a sharpening kernel along beams
        sharpening_kernel = np.array([[-1],
                                      [3],
                                      [-1]])

        # Apply the sharpening kernel
        filtered_polar = cv2.filter2D(src=filtered_polar, ddepth=-1, kernel=sharpening_kernel)

        # Apply lower thresholding to remove values that went below the threshold
        thresh = 60
        filtered_polar = np.where(filtered_polar > thresh, filtered_polar, thresh)

        # Normalize
        filtered_polar = cv2.normalize(filtered_polar, filtered_polar, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

        # Construct the OculusPolarImage data structure
        filtered_sonar_data = oculus.OculusPolarImage(filtered_polar,
                                                      sonar_data.bearing_table,
                                                      sonar_data.ranging_table,
                                                      sonar_data.gain_table)

        # Convert to cartesian coordinates
        cartesian = core.polar_to_cart(sonar_data)
        cartesian_filtered = core.polar_to_cart(filtered_sonar_data)

        cv2.imshow("comparison", np.c_[cartesian.cart_image, cartesian_filtered.cart_image])
        cv2.waitKey(30)
    cv2.waitKey()