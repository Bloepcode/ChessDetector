import numpy as np
import cv2
from time import sleep
from dataclass import Config
from rich import print


THRESH = 2

NUMS = []
for x in range(8):
    row = []
    for y in range(8):
        row.append(f"{x},{y}")
    NUMS.append(row)

FONT = cv2.FONT_HERSHEY_SIMPLEX


class Square:
    def __init__(self, start: cv2.Mat, square_size: int):
        self.prev = start
        self.square_size = square_size

    def match(self, next: cv2.Mat):
        """
        Match the next square with the previous

        Parameters
        ----------
        next : Mat
            The square to compare to the previous square
        """

        errorL2 = cv2.norm(self.prev, next, cv2.NORM_L2)

        return (errorL2 / (next.shape[0] * next.shape[0]))

        # diff_frame = cv2.absdiff(src1=next, src2=self.prev)

        # kernel = np.ones((5, 5))

        # diff_frame = cv2.dilate(diff_frame, kernel, 1)

        # thresh_frame = cv2.threshold(
        #     src=diff_frame, thresh=20, maxval=255, type=cv2.THRESH_BINARY)[1]

        # self.prev = next

        # return thresh_frame.mean(axis=0).mean(axis=0)[1]


class Reader:
    def __init__(self, config: Config) -> None:
        self.config = config

        self.box_outlines, self.square_size = self.get_box_outlines(
            self.config.process_image_size[0])

        # Get the camera
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("Cannot open camera")
            exit()
        sleep(0.3)
        ret, self.frame = self.cap.read()

        self.frame = self.crop_board(
            config.positions, self.frame, config.process_image_size)

        boxes = self.gen_boxes(self.frame)

        # Generate the squares
        self.squares = [[None for _ in range(8)] for _ in range(8)]
        for x in range(8):
            for y in range(8):
                self.squares[x][y] = Square(boxes[x][y], self.square_size)

    def draw_grid(self, img, values):
        for x in range(8):
            for y in range(8):
                box = self.box_outlines[x][y]
                cv2.rectangle(img, box[0], box[1], (255, 255, 0), 1)
                if not isinstance(values, type(None)):
                    cv2.putText(img, values[x][y],
                                (box[0][0] + 6, box[1][1] - 10), FONT, 0.25, (255, 0, 255), 1)

        return img

    def crop_board(self, positions: (int), image: cv2.Mat, size: (int)):
        """
        Crop the board using 4 points

        Parameters
        ----------
        positions : ((int; 2); 4)
            Positions to crop: top-left, top-right, bottom-right and bottom-left in a tuple
        image : Mat
            Image to crop
        size : (int; 2)
            The final size of the image to be returned

        Returns : Mat
            The cropped image following the `positions` and the `size` parameters
        """
        rect = np.float32(positions)  # positions = (tl, tr, br, bl)
        dst = np.float32(
            ((0, 0), (image.shape[0], 0), (image.shape[0], image.shape[1]), (0, image.shape[1])))

        # compute the perspective transform matrix and then apply it
        matrix = cv2.getPerspectiveTransform(
            rect, dst)
        warped = cv2.warpPerspective(
            image, matrix, (image.shape[0], image.shape[1]))

        # return the warped image

        return cv2.resize(warped, size)

    def get_box_outlines(self, w: int):
        """
        Get the outlines of every box in a 8x8 grid of size `w`

        Parameters
        ----------
        w : int
            The width of the used image

        Returns : ([((int; 2); 3); 8*8], int)
            A list with tuples where the first item is the xy start pos, second is the xy end pos and third is the width and height.
            And it returns the size of every square.
        """
        box_outlines = [[None for _ in range(8)] for _ in range(8)]
        grid_size = int(w / 8)
        size = int(grid_size / 3)
        offset = int((grid_size - size) / 2)

        for x in range(8):
            for y in range(8):
                box_outlines[x][y] = ((x*grid_size + offset, y*grid_size + offset), (x*grid_size +
                                                                                     size + offset, y*grid_size+size + offset), (size, size))

        return box_outlines, size

    def gen_boxes(self, img):
        """
        Generate every box image from the `box_outlines` and an image

        Parameters
        ----------
        img : Mat
            The cropped image used for generating every box

        Returns : [[Mat; 8]; 8]
            Every box in a 2d list
        """
        squares = [[None for _ in range(8)] for _ in range(8)]
        for x in range(8):
            for y in range(8):
                box_pos = self.box_outlines[x][y]
                squares[x][y] = img[box_pos[0][1]: box_pos[1]
                                    [1], box_pos[0][0]: box_pos[1][0]]
        return squares

    def wait_for_move(self):
        matched = 0
        self.submit_previous()
        while True:
            matched = 0
            stills = 0
            _, frame = self.cap.read()
            prev = frame
            while True:
                cv2.waitKey(50)
                _, frame = self.cap.read()
                sim = self.match_self(prev, frame)
                prev = frame
                if sim < 30:
                    stills += 1
                else:
                    stills = 0

                if stills >= 8:
                    break
            print("[green]NEW")
            for _ in range(5):
                print("[cyan]Matching now...")
                matches = self.match_with_previous()
                print(f"[cyan]Done matching, results: [blue]{matches}[/blue]!")
                if matches[0][2] > THRESH and matches[1][2] > THRESH:
                    matched += 1
                if matches[4][2] > THRESH or matches[5][2] > THRESH:
                    matched = 0
                    break
            # print(matched)
            if matched == 5:
                matches = self.match_with_previous()
                if matches[0][2] > THRESH and matches[1][2] > THRESH:
                    self.submit_previous()
                    return matches[:2]
            self.submit_previous()

    def match_self(self, prev, next):
        next = self.crop_board(self.config.positions,
                               next, self.config.process_image_size)
        prev = self.crop_board(self.config.positions,
                               prev, self.config.process_image_size)

        prev = cv2.cvtColor(prev, cv2.COLOR_BGR2GRAY)
        next = cv2.cvtColor(next, cv2.COLOR_BGR2GRAY)

        prev = cv2.GaussianBlur(src=prev, ksize=(5, 5), sigmaX=0)
        next = cv2.GaussianBlur(src=next, ksize=(5, 5), sigmaX=0)

        diff_frame = cv2.absdiff(src1=next, src2=prev)

        kernel = np.ones((5, 5))

        diff_frame = cv2.dilate(diff_frame, kernel, 1)

        thresh_frame = cv2.threshold(
            src=diff_frame, thresh=3, maxval=255, type=cv2.THRESH_BINARY)[1]

        return thresh_frame.mean(axis=0).mean(axis=0)

    def match_with_previous(self):
        """
        Compare the previous squares to the next squared for the biggest difference

        Parameters
        ----------
        next : [[Mat; 8]; 8]
            The next boxes to check

        Returns : [(int; 2); 4]
            The xy positions of the 4 changed squares
        """

        _, frame = self.cap.read()

        frame = self.crop_board(self.config.positions,
                                frame, self.config.process_image_size)

        boxes = self.gen_boxes(frame)

        results = []

        for x in range(8):
            for y in range(8):
                results.append(
                    (7-x, 7-y, self.squares[x][y].match(boxes[x][y].copy())))

        return sorted(results, reverse=True,  key=lambda x: x[2])[:6]

    def submit_previous(self):
        _, frame = self.cap.read()

        frame = self.crop_board(self.config.positions,
                                frame, self.config.process_image_size)

        boxes = self.gen_boxes(frame)

        for x in range(8):
            for y in range(8):
                self.squares[x][y].prev = boxes[x][y]
