# import necessary packages
from multiprocessing import Manager
from multiprocessing import Process
from imutils.video import VideoStream
from control.objcenter import ObjCenter
from control.pid import PID
import pantilthat as pth
import argparse
import signal
import time
import sys
import cv2
#import BIT

# define the range for the motors
servoRange = (-90, 90)

# function to handle keyboard interrupt
def signal_handler(sig, frame):
	# print a status message
	print("[INFO] You pressed `ctrl + c`! Exiting...")

	# disable the servos
	pth.servo_enable(1, False)
	pth.servo_enable(2, False)

	# exit
	sys.exit()

def obj_center(args, objX, objY, centerX, centerY, faceDetected):
	# signal trap to handle keyboard interrupt
	signal.signal(signal.SIGINT, signal_handler)

	# start the video stream and wait for the camera to warm up
	vs = VideoStream(usePiCamera=True).start()
	time.sleep(2.0)

	# initialize the object center finder
	obj = ObjCenter(args["cascade"])

	# loop indefinitely
	while True:
		# grab the frame from the threaded video stream and flip it
		# vertically (since our camera was upside down)
		frame = vs.read()
		frame = cv2.flip(frame, 0)

		# calculate the center of the frame as this is where we will
		# try to keep the object
		(H, W) = frame.shape[:2]
		centerX.value = W // 2
		centerY.value = H // 2

		# find the object's location
		objectLoc = obj.update(frame, (centerX.value, centerY.value))
		((objX.value, objY.value), rect) = objectLoc

		# extract the bounding box and draw it
		if rect is not None:
			faceDetected.value = 1
			(x, y, w, h) = rect
			cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0),
				2)
		else:
			faceDetected.value = 0
			
		# display the frame to the screen
		cv2.imshow("Pan-Tilt Face Tracking", frame)
		cv2.waitKey(1)

def pid_process(output, p, i, d, objCoord, centerCoord, faceDetected):
	# signal trap to handle keyboard interrupt
	signal.signal(signal.SIGINT, signal_handler)

	# create a PID and initialize it
	pid = PID(p.value, i.value, d.value)
	pid.initialize()
	first = True
	# loop indefinitely
	while True:
		# calculate the error
		if faceDetected.value == 1:
			error = centerCoord.value - objCoord.value
			#if first:
			#	_ = pid.update(error)
			#	first = False
				#time.sleep(2)
				#print("Hey")
			#else:
				# update the value			
			output.value = pid.update(error)
			#print("output ", output.value)
			#print(output.value)	
				#print("In else")		
		

def in_range(val, start, end):
	# determine the input value is in the supplied range
	return (val >= start and val <= end)

def set_servos(pan, tlt, faceDetected):
	# signal trap to handle keyboard interrupt
	signal.signal(signal.SIGINT, signal_handler)
	panAngle = pth.get_pan() + 90
	tiltAngle = 90 - pth.get_tilt()
	first = True
	#print(panAngle, tiltAngle)
	# loop indefinitely
	while True:
		if faceDetected.value == 1:
			# the pan and tilt angles are reversed
			'''panAngle = -1 * pan.value
			tiltAngle = -1 * tlt.value'''

			if first:
				time.sleep(3)
				first = False
				print("Ready")
			time.sleep(0.2)
			if (pan.value >= 2 or pan.value <= -2):
			#	print("tiltAngle: ", int(tiltAngle))
			#	print("Tlt value ", int(tlt.value))
				panAngle = panAngle - pan.value
				panAngle = max(0,min(180,panAngle))
			
				# if the pan angle is within the range, pan
				if in_range(panAngle - 90, servoRange[0], servoRange[1]):
					pth.pan(int(panAngle - 90))

			if (tlt.value >= 2 or tlt.value <= -2):	
				tiltAngle = tiltAngle + tlt.value
				tiltAngle = max(0,min(180,tiltAngle))

				# if the tilt angle is within the range, tilt
				if in_range(tiltAngle, servoRange[0], servoRange[1]):
					pth.tilt(int(90 - tiltAngle))

				'''print(pan.value, tlt.value)'''
			#	print(panAngle, tiltAngle)
					

def BIT():
	# Perform full servo movement and set starting position	
    pth.pan(-90)       
    pth.tilt(-90)
    time.sleep(1)
    for i in range(-90, 91):
        pth.pan(i)       
        pth.tilt(i)
        time.sleep(0.005)

    time.sleep(0.5)
    pth.tilt(60)
    pth.pan(0)
    time.sleep(1)

    print("Finished")

# check to see if this is the main body of execution
if __name__ == "__main__":
	# construct the argument parser and parse the arguments
	ap = argparse.ArgumentParser()
	ap.add_argument("-c", "--cascade", type=str, required=True,
		help="path to input Haar cascade for face detection")
	args = vars(ap.parse_args())

    # start a manager for managing process-safe variables
	with Manager() as manager:
		# enable the servos
		pth.servo_enable(1, True)
		pth.servo_enable(2, True)

		# set integer values for the object center (x, y)-coordinates
		centerX = manager.Value("i", 0)
		centerY = manager.Value("i", 0)

		# set integer values for the object's (x, y)-coordinates
		objX = manager.Value("i", 0)
		objY = manager.Value("i", 0)

		# pan and tilt values will be managed by independed PIDs
		pan = manager.Value("i", 60)
		tlt = manager.Value("i", 0)
		
        # set PID values for panning
		'''panP = manager.Value("f", 0.26)
		panI = manager.Value("f", 0.11)
		panD = manager.Value("f", 0.001)'''
		panP = manager.Value("f", 0.08)
		panI = manager.Value("f", 0.0033)
		panD = manager.Value("f", 0.0011)

		# set PID values for tilting
		'''tiltP = manager.Value("f", 0.20)
		tiltI = manager.Value("f", 0.11)
		tiltD = manager.Value("f", 0.001)'''
		tiltP = manager.Value("f", 0.08)
		tiltI = manager.Value("f", 0.003)
		tiltD = manager.Value("f", 0.001)
		
		faceDetected = manager.Value("i", 0)
		
		#BIT()
		processBIT = Process(target=BIT)
		processBIT.start()
		processBIT.join()		

        # we have 4 independent processes
		# 1. objectCenter  - finds/localizes the object
		# 2. panning       - PID control loop determines panning angle
		# 3. tilting       - PID control loop determines tilting angle
		# 4. setServos     - drives the servos to proper angles based
		#                    on PID feedback to keep object in center
		processObjectCenter = Process(target=obj_center,
			args=(args, objX, objY, centerX, centerY, faceDetected))		
		processPanning = Process(target=pid_process,
			args=(pan, panP, panI, panD, objX, centerX, faceDetected))
		processTilting = Process(target=pid_process,
			args=(tlt, tiltP, tiltI, tiltD, objY, centerY, faceDetected))
		processSetServos = Process(target=set_servos, args=(pan, tlt, faceDetected))

		# start all 4 processes
		processObjectCenter.start()		
		processPanning.start()
		processTilting.start()		
		processSetServos.start()		
		
		# join all 4 processes
		processObjectCenter.join()
		processPanning.join()
		processTilting.join()
		processSetServos.join()
        
		# disable the servos
		pth.servo_enable(1, False)
		pth.servo_enable(2, False)