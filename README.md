# RacingCVController
Computer Vision software in Python, allowing for controlling a virtual gamepad using a steering wheel and gas bar captured by PC camera

# How it's working

Video camera (in my case internal laptop front camera) constantly records video. There is support for two main elements of control for the user at the moment: a steering wheel and gas pedal. The steering wheel is tracked using a red spot on the disk, which revolves around the center of the wheel. This movement is what the algorithm then (with adjustments) sends onto a virtual gamepad. Gas pedal, in my case, is implemented using a rope that I can pull with my toe, which, thanks to a block, pulls a red marker upwards, triggering the program to gas more. It is tracked by a small red area on the marker which corresponds to the raw input value of the gas pedal.

# How to set up

First, this isn't a standalone application, it's just a bunch of scripts. So, they require:
1. Python 3 interpreter (ideally an IDE as well; I use PyCharm)
2. <a href="https://pypi.org/project/numpy/">Numpy</a>
3. <a href="https://pypi.org/project/opencv-python/">Open CV</a>
4. <a href="https://pypi.org/project/vgamepad/">VGamePad</a> (requires ViGEM Bus Driver; for more details see vgamepad setup)

Second, this exact code I provide is specific for my room and might need tweaks if you don't have an opportunity to make the gas pedal design similar to mine or for any other reason.

After running the program, you should adjust areas of the steering wheel and the gas pedal marker on the screen so that they are always detected and nothing unwanted isn't. When adjusted, you can start calibration.

Calibration process requires two things: calibrating the steering wheel and the gas pedal. The steering wheel must simply be rotated in any direction so that the algorithm can calculate the radius and center point of your wheel. When you can see on the screen that both parameters are calculated correctly, you press *Spacebar*, locking these params which will no longer be recalculated. Then you can proceed to gas pedal calibration. The program must know which height of the marker to consider minimum and which maximum, so to lock minimum value you press *1* and to lock maximum value you press *2*. After that the program will scale raw values in this boundaries.

After that, the program is ready to use.

# Notes

I tested it only on Windows 11 for Forza Horizon 4 on virtual controller DualShock4, with left stick horizontal state corresponding to turning and right trigger corresponding to gas.

As this is a computer vision -based program, it strickly relies on lighting conditions, so color ranges must be adjusted for your lighting AND color markers of your choice (I personally chose red because it is the brightest I have and best distinguished color in my environment)

This isn't any serious project or invention, this project doesn't claim to be revolutionary or whatever. Just a silly thing that I really enjoyed developing and using and I though it might amuse others as well, so don't take it serious.

ALMOST ALL THE CODE IS WRITTEN USING CHAT-GPT 4o, so don't blame me for bad code style or aweful architecture. I know it's bad, maybe I'll rewrite it someday, but it's working and I am satisfied with the result. The project might receive changes in future.
