
from concurrent.futures import ThreadPoolExecutor
import pygame
from gtts import gTTS

pygame.mixer.init()


def out(text, wait=True):
    if wait:
        with ThreadPoolExecutor(max_workers=1) as e:
            e.submit(out_, text)
    else:
        out_(text)


def out_(text):
    print(text)
    if text:
        speech = gTTS(text=text, lang="nl", slow=False)
        speech.save("speech.mp3")
        pygame.mixer.music.load("speech.mp3")
        pygame.mixer.music.play()
