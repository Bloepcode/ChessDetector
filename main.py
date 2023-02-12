from dataclass import Config
from out import out
from reader import Reader
from rich import print
import os
import cv2
from chesser import Chesser
from time import sleep
import pickle


def click(event, x, y, flags, param):
    global clicked, mouseX, mouseY
    if event == cv2.EVENT_LBUTTONDOWN:
        mouseX, mouseY = x, y
        clicked = True


def get_points():
    global clicked, mouseX, mouseY
    # Get the camera
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Cannot open camera")
        exit()
    sleep(0.3)
    ret, frame = cap.read()

    out("Klik op de 4 punten van het schaakbord", wait=False)
    points = []
    cv2.namedWindow("Chess select")
    cv2.imshow("Chess select", frame)
    cv2.setMouseCallback('Chess select', click)
    for i in range(4):
        while not clicked:
            cv2.waitKey(20)
        clicked = False
        cv2.rectangle(frame, (mouseX, mouseY),
                      (mouseX, mouseY), (235, 183, 89), 10)
        cv2.imshow("Chess select", frame)
        print(mouseX, mouseY)
        points.append((mouseX, mouseY))
    cv2.destroyWindow("Chess select")
    return points


def calibrate():
    global clicked, mouseX, mouseY
    clicked = False
    mouseX = 0
    mouseY = 0
    return get_points()


print(">>> [green on black]ChessDetector[/green on black] <<<")
print("Detects your chess moves!")


if os.path.exists("config.tpl"):
    with open("config.tpl", "rb") as f:
        config = pickle.load(f)
        print(config.positions)
else:
    config = Config(calibrate(), 0.8, (256, 256))
    with open("config.tpl", "wb") as f:
        pickle.dump(config, f)


# while True:
#     print(f"[green]Done: {reader.wait_for_move()}")

chesser = Chesser(config)
chesser.mainloop()
