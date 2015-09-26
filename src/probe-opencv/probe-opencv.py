import cv2

MIN_AREA = 300
MAX_AREA = 1200
RECTANGLE_COLOR = (0, 255, 0)
THRESHOLD_PERCENT = 0.8

cap = cv2.VideoCapture(0)

while (cap.isOpened()):
    ret, frame = cap.read()

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    [minVal, maxVal, minLoc, maxLoc] = cv2.minMaxLoc(gray)
    print minVal, maxVal, minLoc, maxLoc

    # Threshold at 80%
    margin = THRESHOLD_PERCENT
    thresh = int(maxVal * margin)
    print "Threshold: " + thresh

    ret, thresh_img = cv2.threshold(gray, thresh, 255, cv2.THRESH_BINARY)

    contours, hierarchy = cv2.findContours(thresh_img, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)

    for c in contours:
        area = cv2.contourArea(c)
        if (area >= MIN_AREA and area <= MAX_AREA):
            x, y, w, h = cv2.boundingRect(c)
            cv2.rectangle(frame, (x, y), (x + w, y + h), RECTANGLE_COLOR, 2)

    cv2.imshow('TrashImage', thresh_img)
    cv2.imshow('FrameImage', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()