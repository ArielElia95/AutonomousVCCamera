#!/usr/bin/env python

import math
import time

import pantilthat

def BIT():
    t = 0.0
    counter = 0   

    pantilthat.pan(-90)       
    pantilthat.tilt(-90)
    time.sleep(1)
    for i in range(-90, 91):
        pantilthat.pan(i)       
        pantilthat.tilt(i)
        time.sleep(0.005)

    time.sleep(0.5)
    pantilthat.tilt(60)
    pantilthat.pan(-90)
    time.sleep(1)

    print("Finished")
    return

