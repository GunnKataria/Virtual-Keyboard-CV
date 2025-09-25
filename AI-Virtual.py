import cv2
from HandTrackingModule import HandDetector
from time import sleep
from pynput.keyboard import Controller, Key

# --- ADD THIS NEW SECTION FOR YOUR COLOR THEME ---
# Define colors as BGR tuples (Blue, Green, Red)
BUTTON_COLOR = (255, 191, 0)    # Light Blue
BORDER_COLOR = (255, 191, 0)    # Light Blue
HOVER_COLOR = (200, 150, 0)     # Darker Blue
CLICK_COLOR = (0, 255, 255)     # Cyan / Yellowish-Green for contrast
TEXT_COLOR = (255, 255, 255)  # White
TEXT_BOX_COLOR= (255, 191, 0)    # Light Blue
# ----------------------------------------------------

# Initialize the webcam
cap = cv2.VideoCapture(0)
cap.set(3, 1280)  # Width
cap.set(4, 720)   # Height

# Initialize hand detector
detector = HandDetector(detectionCon=0.8, maxHands=1)

# New keyboard layout with numbers and backspace
keys = [["1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "<-"],
        ["Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P"],
        ["A", "S", "D", "F", "G", "H", "J", "K", "L", ";"],
        ["Z", "X", "C", "V", "B", "N", "M", ",", ".", "/"]]

# String to hold the typed text
finalText = ""

# Initialize keyboard controller
keyboard = Controller()


# Redesigned function for a transparent UI
def drawAllButtons(img, buttonList):
    overlay = img.copy()
    for button in buttonList:
        x, y = button.pos
        w, h = button.size
        # Draw the transparent rectangle on the overlay
        cv2.rectangle(overlay, button.pos, (x + w, y + h), BUTTON_COLOR, cv2.FILLED)

    # Blend the overlay with the original image
    alpha = 0.4  # Transparency factor
    img = cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0)

    # Now draw the borders and text on the blended image
    for button in buttonList:
        x, y = button.pos
        w, h = button.size
        # Draw the button border
        cv2.rectangle(img, button.pos, (x + w, y + h), BORDER_COLOR, 3)
        # Draw the button text
        cv2.putText(img, button.text, (x + 20, y + 65),
                    cv2.FONT_HERSHEY_PLAIN, 4, TEXT_COLOR, 4)

    return img


# Class to define a Button
class Button():
    def __init__(self, pos, text, size=[85, 85]):
        self.pos = pos
        self.size = size
        self.text = text


# Create all the button objects
buttonList = []
for i in range(len(keys)):
    for j, key in enumerate(keys[i]):
        buttonList.append(Button([100 * j + 50, 100 * i + 50], key))

# Main loop
while True:
    success, img = cap.read()
    # Image flip is removed to prevent mirroring
    # img = cv2.flip(img, 1)

    # Detect hands and find landmarks, with flipType=False for non-mirrored view
    hands, img = detector.findHands(img)
    lmList, bboxInfo = detector.findPosition(img, draw=False)

    # Draw the keyboard UI
    img = drawAllButtons(img, buttonList)

    if lmList:
        # Gesture for the spacebar (middle finger + thumb)
        space_length, _, _ = detector.findDistance(lmList[12], lmList[4], img)
        if space_length < 40:
            keyboard.press(Key.space)
            finalText += " "
            sleep(0.5)

        # Logic for typing letters and backspace (index finger + thumb)
        for button in buttonList:
            x, y = button.pos
            w, h = button.size

            # Check if index finger tip is inside a button
            if x < lmList[8][0] < x + w and y < lmList[8][1] < y + h:
                # Highlight the button on hover
                cv2.rectangle(img, (x - 5, y - 5), (x + w + 5, y + h + 5), HOVER_COLOR, cv2.FILLED)
                cv2.putText(img, button.text, (x + 20, y + 65),
                            cv2.FONT_HERSHEY_PLAIN, 4, TEXT_COLOR, 4)

                # Check for click gesture
                click_length, _, _ = detector.findDistance(lmList[8], lmList[4], img)
                if click_length < 40:
                    # Handle backspace key
                    if button.text == "<-":
                        keyboard.press(Key.backspace)
                        finalText = finalText[:-1]
                    # Handle all other keys
                    else:
                        keyboard.press(button.text)
                        finalText += button.text

                    # Highlight the button on click
                    cv2.rectangle(img, button.pos, (x + w, y + h), CLICK_COLOR, cv2.FILLED)
                    cv2.putText(img, button.text, (x + 20, y + 65),
                                cv2.FONT_HERSHEY_PLAIN, 4, TEXT_COLOR, 4)
                    sleep(0.5)

    # Responsive Text Box Logic
    font = cv2.FONT_HERSHEY_PLAIN
    font_scale = 5
    font_thickness = 5
    padding = 20
    box_start_pos = (50, 500)

    (text_w, text_h), baseline = cv2.getTextSize(finalText, font, font_scale, font_thickness)
    min_box_width = 300
    box_w = max(min_box_width, text_w + padding * 2)
    box_h = text_h + baseline + padding * 2
    
    p1 = box_start_pos
    p2 = (box_start_pos[0] + box_w, box_start_pos[1] + box_h)
    cv2.rectangle(img, p1, p2, TEXT_BOX_COLOR, cv2.FILLED)

    text_pos = (box_start_pos[0] + padding, box_start_pos[1] + text_h + padding)
    cv2.putText(img, finalText, text_pos, font, font_scale, TEXT_COLOR, font_thickness)

    cv2.imshow("Image", img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# When the loop breaks, save the final text to a file
with open("typed_text.txt", "w") as f:
    f.write(finalText)
print("Successfully saved text to typed_text.txt")

cap.release()
cv2.destroyAllWindows()