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
    cap = cv2.VideoCapture("http://192.168.1.177:8080/video")
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


def get_minimum_change(config, iterations):
    hard_moves = [("a1a3", ((0, 7-0), (0, 7-2))),
                  ("h1h3", ((7, 7-0), (7, 7-2))), ("a8a6", ((0, 7), (0, 5))), ("h8h6", ((7, 7), (7, 5)))]
    current_max = 0
    for move in hard_moves:
        print(f"New move out of 4")
        for i in range(iterations):
            print(f"Iteration {i+1} out of {iterations}")
            reader = Reader(config)
            reader.match_with_previous()
            reader.submit_previous()
            out(f"Doe zet {move[0]}")
            input("Press enter to continue...")
            results = reader.match_with_previous()
            reader.submit_previous()
            print(results)
            for set in range(2):
                for result in results:
                    if result[0] == move[1][set][0] and result[1] == move[1][set][1]:
                        if result[2] > current_max:
                            current_max = result[2]
                            print("NEw current max", current_max)
                        break

            out("Reset het bord.")
            input("Press enter to continue...")
            results = reader.match_with_previous()
            reader.submit_previous()
            for set in range(2):
                for result in results:
                    if result[0] == move[1][set][0] and results[1] == move[1][set][1]:
                        if result[2] > current_max:
                            current_max = result[2]
                            print("NEw current max", current_max)
                        break
            config.minimum_change = current_max
    return current_max * 1.1


def calibrate() -> Config:
    global clicked, mouseX, mouseY
    clicked = False
    mouseX = 0
    mouseY = 0

    points = get_points()

    config = Config(points, 0, 15, (256, 256))
    print(get_minimum_change(config, 3))


print(">>> [green on black]ChessDetector[/green on black] <<<")
print("Detects your chess moves!")


if os.path.exists("config.tpl"):
    with open("config.tpl", "rb") as f:
        config = pickle.load(f)
        print(config.positions)
else:
    # with open("config.tpl", "wb") as f:
    config = calibrate()
    # pickle.dump(config, f)


# while True:
#     print(f"[green]Done: {reader.wait_for_move()}")

chesser = Chesser(config)
chesser.mainloop()
