import argparse
from pynput import keyboard
import qi
import sys
from time import sleep


class Pepper:
    session = None
    motion_service = None
    auton_service = None
    tts = None

    def __init__(self, ip, port):
        self.session = qi.Session()
        try:
            print("Connecting to Pepper at {ip}:{port}".format(ip=ip, port=port))
            self.session.connect("tcp://{ip}:{port}".format(ip=ip, port=str(port)))
            print("Connected!")
        except RuntimeError:
            print("Unable to connect to Pepper.")
            sys.exit(1)
        self.motion_service = self.session.service("ALMotion")
        self.tablet_service = self.session.service("ALTabletService")
        self.auton_service = self.session.service("ALAutonomousMoves")
        self.tts = self.session.service("ALTextToSpeech")

    def ask(self, question):
        self._question = question
        self.tablet_service.showInputTextDialog(question, "Ok", "Cancel")
    
    def text_callback(self, validation, input_string):
    	if input_string.lower() not in ["yes", "no"]:
            self.ask(self._question)
    	else:
            self.speak("You said {ans}".format(ans=input_string))
    	return True

    def move_forward(self, speed):
        print("Moving")
        self.motion_service.moveToward(speed, 0, 0)

    def turn_around(self, speed):
        print("Turning")
        self.motion_service.moveToward(0, 0, speed)
    
    def run_trajectory(self, trajectory):
        for i, move in enumerate(trajectory):
            print("Executing step {step} of trajectory".format(step=i))
            self.motion_service.moveTo(*move)

    def stop_moving(self):
        print("Stopping")
        self.motion_service.stopMove()

    def disable_collision_protection(self):
        print("Disabling collision protection")
        self.motion_service.setExternalCollisionProtectionEnabled("All", False)

    def sleep(self, duration):
        sleep(duration)
        self.stop_moving()

    def speak(self, text):
        self.tts.say(text)

    def enable_collision_protection(self):
        print("Enabling collision protection")
        self.auton_service.setBackgroundStrategy("backToNeutral")
        self.motion_service.setExternalCollisionProtectionEnabled("All", True)

    def on_keypress(self, key):
        try:
            print("alphanumeric key {0} pressed".format(key.char))
            if key.char == "w":
                self.move_forward(0.5)
                # self.sleep(3)
            elif key.char == "s":
                self.move_forward(-0.5)
                # self.sleep(3)
            elif key.char == "a":
                self.turn_around(1)
                # self.sleep(1.3)
            elif key.char == "d":
                self.turn_around(-1)
                # self.sleep(1.3)
            elif key.char == "q":
                self.stop_moving()
            elif key.char == "r":
                self.run_trajectory([
                 [0, 0, -2.44],
                 [1.6, 0, -0.235],
                 [0.062, -0.031, -1.556],
                 [2.2, 0, 0.192],
                 [0.049, -0.134, 1.716],
                 [-0.311, 0.063, 0.155]
                ])
            elif key.char == "p":
                print(robot.motion_service.getRobotPosition(False))
            elif key.char == "1":
                self.speak("Hey, welcome to AI makerspace!")
            elif key.char == "2":
                self.speak("Hey thank you, it was nice to meet you")
            elif key.char == "3":
            	 self.ask("Are you a robot?")
            	 self.speak("Are you a robot?")
        except AttributeError:
            print("special key {0} pressed".format(key))

    def start_teleop(self):
        print("Disabling collision protection and starting teleop.")
        print(
            "W: forward, S: backward, A: turn left, D: turn right, 1: say hi, 2: say bye"
        )
        print("Press Ctrl+C to exit.")
        self.disable_collision_protection()
        signalId = self.tablet_service.onInputText.connect(self.text_callback)
        listener = keyboard.Listener(on_press=self.on_keypress)
        listener.start()
        try:
            while True:
                pass
        except KeyboardInterrupt:
            listener.stop()
            self.enable_collision_protection()
            self.tablet_service.onInputText.disconnect(signalId)
            self.stop_moving()
            pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="teleop.py",
        description="Teleoperation script for Pepper Robot.",
    )
    parser.add_argument("--ip", type=str, required=True, help="Pepper's IP address")
    parser.add_argument(
        "-p", "--port", type=int, default=9559, help="Pepper's port number"
    )

    args = parser.parse_args()
    robot = Pepper(args.ip, args.port)
    robot.start_teleop()
