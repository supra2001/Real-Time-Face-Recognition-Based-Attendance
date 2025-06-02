import cv2
#img = cv2.imread('2.png')
#print("Template shape:", img.shape)


def click_event(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        print(f"Clicked at: ({x}, {y})")

img = cv2.imread("Background.jpg")
cv2.imshow("Click to Get Coordinates", img)
cv2.setMouseCallback("Click to Get Coordinates", click_event)
cv2.waitKey(0)
cv2.destroyAllWindows()
