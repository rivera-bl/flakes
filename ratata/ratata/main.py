import pyautogui
import time

def start():
    while True:
        for i in range(0,100):
            pyautogui.moveTo(1000,i*10)
            time.sleep(5) 
