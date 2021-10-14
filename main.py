import os
import time
import cv2
import numpy as np
from imutils.video import VideoStream
import counter_measure
import target_tracking


def main():
    set_filename = 'data/settings.csv'

    cv = target_tracking.ComputerVision(_buffer=128)
    aim = counter_measure.AimingCalc()

    # calibrate counter_measure device
    aim.set_delay()

    # variables to link to kinect camera
    vs = VideoStream(src=0).start()

    # warm up
    time.sleep(1.0)

    # find upper and lower HSV value
    if not (os.path.exists(set_filename)):
        colorLower, colorUpper = cv.HSVRange(vs)
    else:
        colorLower, colorUpper = np.loadtxt(set_filename, delimiter=',', dtype=int)

    # keep looping
    while True:
        if cv.isDetected():
            if len(cv.pts) > 5 and cv.pts[0] is not None and cv.pts[1] is not None:
                intercept = cv.predict(aim.get_delay())

        # grab the current frame
        frame = vs.read()

        # clean the frame to see just the target size of frame is 400x300pts
        frame, mask = cv.CleanUp(frame, colorLower, colorUpper)

        # Find the ball
        cv.detect(mask)

        # draw the tracked points as a line
        for i in range(1, len(cv.pts)):
            # Ignore None points
            if cv.pts[i - 1] is None or cv.pts[i] is None:
                continue
            # compute thickness based on place in queue
            thickness = int(np.sqrt(cv.buffer / float(i + 1)) * 2.5)
            # draw connecting lines between points
            cv2.line(frame, cv.pts[i - 1], cv.pts[i], (0, 0, 255), thickness)

        if cv.targetData[0] is not None:
            # draw a circle around the target
            cv2.circle(frame, (cv.targetData[0], cv.targetData[1]), cv.targetData[2], [255, 0, 0], 2)

        if len(cv.pred_pts) > 0 and cv.targetData[2] is not None:
            for i in range(len(cv.pred_pts)):
                if cv.pred_pts[i] is None:
                    continue
                # draw prediction circle
                if intercept is not None and intercept[0] == cv.pred_pts[i][0] and intercept[1] == cv.pred_pts[i][1]:
                    color = [0, 255, 0]
                else:
                    color = [114, 42, 203]
                cv2.circle(frame, (cv.pred_pts[i][0], cv.pred_pts[i][1]), (int(cv.targetData[2] / 2)), color, 2)

        # show the frame to our screen
        cv2.imshow("Frame", frame)

        # 'q' to quit
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break

        # time.sleep(0.01)


    # stop video stream
    vs.stop()

    # close all windows
    cv2.destroyAllWindows()

    # save settings
    settings = np.asarray([colorLower, colorUpper])
    np.savetxt('data/settings.csv', settings, delimiter=',')


if __name__ == '__main__':
    main()