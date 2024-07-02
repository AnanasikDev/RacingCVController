import cv2
import numpy as np
import controller

# Open a connection to the front camera (usually camera 0, but it might be different on your system)
cap = cv2.VideoCapture(0)

SCREEN_WIDTH = 0
SCREEN_HEIGHT = 0

# Check if the camera opened successfully
if not cap.isOpened():
    print("Error: Could not open camera.")
    exit()

# Store the history of spot positions
positions = {'red': [], 'blue': [], 'green': []}

# Variable to cache the center point
cached_center = None

# Define areas as bottom-left and top-right corners
areas = {
    'steering': [(100, 350), (380, 470)],
    'gas': [(520, 0), (650, 500)],
    #'brake': [(500, 300), (650, 450)]
}

MIN_GAS = None
MAX_GAS = None


def calculate_center_of_rotation(positions):
    if len(positions) < 2:
        return None
    positions = np.array(positions)
    x = positions[:, 0]
    y = positions[:, 1]
    A = np.c_[x, y, np.ones(positions.shape[0])]
    b = x ** 2 + y ** 2
    coeff, _, _, _ = np.linalg.lstsq(A, b, rcond=None)
    cx, cy = coeff[0] / 2, coeff[1] / 2
    return int(cx), int(cy)

def calculate_absolute_rotation_angle(center, point):
    dx = point[0] - center[0]
    dy = point[1] - center[1]
    angle = np.arctan2(dy, dx)
    return np.degrees(angle)

def draw_rotated_circle(frame, angle):
    h, w = frame.shape[:2]
    radius = min(h, w) // 4
    center = (w // 2, h // 2)
    # Create a blank image with a circle
    circle_img = np.zeros_like(frame)
    cv2.circle(circle_img, center, radius, (255, 255, 255), 2)
    # Calculate the end point of the line based on the angle
    end_point = (int(center[0] + radius * np.cos(np.radians(angle))),
                 int(center[1] + radius * np.sin(np.radians(angle))))
    # Draw the radius line
    cv2.line(circle_img, center, end_point, (0, 255, 0), 2)
    return circle_img

def detect_color_spots(hsv, lower_bound, upper_bound, area):
    mask = cv2.inRange(hsv, lower_bound, upper_bound)
    mask = mask[area[0][1]:area[1][1], area[0][0]:area[1][0]]
    contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        largest_contour = max(contours, key=cv2.contourArea)
        M = cv2.moments(largest_contour)
        if M["m00"] != 0:
            cX = int(M["m10"] / M["m00"]) + area[0][0]
            cY = int(M["m01"] / M["m00"]) + area[0][1]
            return (cX, cY)
    return None

def draw_areas(frame, areas):
    colors = {'steering': (255, 0, 0), 'gas': (0, 255, 0), 'brake': (0, 0, 255)}
    for area, corners in areas.items():
        cv2.rectangle(frame, corners[0], corners[1], colors[area], 2)
        cv2.putText(frame, area.capitalize(), (corners[0][0], corners[0][1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, colors[area], 2)
    return frame

def detect_gas_state(hsv, area):
    # Define the red color range for the gas stripe
    lower_red = np.array([0, 120, 70])
    upper_red = np.array([10, 255, 255])
    mask = cv2.inRange(hsv, lower_red, upper_red)
    mask = mask[area[0][1]:area[1][1], area[0][0]:area[1][0]]
    contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        largest_contour = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(largest_contour)
        stripe_center_y = y + h / 2
        #area_height = area[1][1] - area[0][1]
        #gas_value = 1.0 - (stripe_center_y / area_height)

        gas_value = SCREEN_HEIGHT - float(stripe_center_y)# / SCREEN_HEIGHT

        return gas_value
    return 0.0

def scale_gas_value(value, min_value, max_value):

    if min_value == None or max_value == None:
        return value

    # Ensure value is within bounds
    value = max(min(value, max_value), min_value)

    # Scale the value to the range [0, 1]
    scaled_value = (value - min_value) / (max_value - min_value)

    return scaled_value

CURRENT_GAS = 0

# Continuously capture frames from the camera
while True:
    # Capture frame-by-frame
    ret, frame = cap.read()
    frame = cv2.flip(frame, 1)
    SCREEN_HEIGHT, SCREEN_WIDTH = frame.shape[:2]

    # If frame is read correctly, ret is True
    if not ret:
        print("Error: Can't receive frame (stream end?). Exiting ...")
        break

    # Get the dimensions of the frame
    h, w = frame.shape[:2]

    # Convert the frame to the HSV color space
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Define the ranges for detecting red, blue, and green colors in HSV
    color_ranges = {
        'red': [(np.array([0, 120, 70]), np.array([10, 255, 255]))],
        'blue': [(np.array([100, 150, 70]), np.array([140, 255, 255]))],
        'green': [(np.array([40, 70, 70]), np.array([80, 255, 255]))]
    }

    detected_positions = {'red': None, 'blue': None, 'green': None}

    # Detect color spots based on whether center is cached or not
    if cached_center is None:
        # Only detect red spot
        for lower, upper in color_ranges['red']:
            spot_position = detect_color_spots(hsv, lower, upper, areas['steering'])
            if spot_position:
                detected_positions['red'] = spot_position
                positions['red'].append(spot_position)
                break
    else:
        # Detect red, blue, and green spots
        for color, ranges in color_ranges.items():
            for lower, upper in ranges:
                spot_position = detect_color_spots(hsv, lower, upper, areas['steering'])
                if spot_position:
                    detected_positions[color] = spot_position
                    positions[color].append(spot_position)
                    break

    # Limit the history to the last 50 positions for each color
    for color in positions:
        if len(positions[color]) > 50:
            positions[color].pop(0)

    # Calculate the center of rotation if not cached
    if cached_center is None:
        all_positions = []
        for color in positions:
            all_positions.extend(positions[color])
        center_of_rotation = calculate_center_of_rotation(all_positions)
    else:
        center_of_rotation = cached_center

    if center_of_rotation is not None:
        for color, spot in detected_positions.items():
            if spot:
                cX, cY = spot
                # Draw the line from the color spot to the center of rotation
                cv2.line(frame, (cX, cY), center_of_rotation, (255, 0, 0), 2)

                # Display the centers
                cv2.putText(frame, f"{color.capitalize()} Spot Center: ({cX}, {cY})", (cX + 10, cY),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

                # Draw the center of rotation
                cv2.circle(frame, center_of_rotation, 5, (0, 255, 0), -1)

                # Calculate the angle between the vertical axis and the radius to the color spot
                angle = calculate_absolute_rotation_angle(center_of_rotation, (cX, cY))
                controller.angle_to_joystick(angle)

                # Draw the rotated circle on a new window
                rotated_circle_img = draw_rotated_circle(frame, angle)
                cv2.imshow('Rotated Circle', rotated_circle_img)

    # Detect gas state
    CURRENT_GAS = scale_gas_value(detect_gas_state(hsv, areas['gas']) * 2, MIN_GAS, MAX_GAS)
    print(CURRENT_GAS)
    controller.pull_gas(CURRENT_GAS)

    # Display the gas value
    cv2.putText(frame, f"Gas Value: {CURRENT_GAS:.2f}", (areas['gas'][0][0], areas['gas'][0][1] - 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    # Draw and display the defined areas
    frame_with_areas = draw_areas(frame.copy(), areas)
    cv2.imshow('Areas', frame_with_areas)

    # Display the resulting frame
    cv2.imshow('Front Camera', frame)

    # Wait for key events
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord(' '):
        # Cache the center of rotation when spacebar is pressed
        cached_center = center_of_rotation
    elif key == ord('1'):
        MIN_GAS = CURRENT_GAS
    elif key == ord('2'):
        MAX_GAS = CURRENT_GAS


# When everything is done, release the capture
cap.release()
cv2.destroyAllWindows()
