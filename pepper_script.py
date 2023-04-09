import argparse
from pynput import keyboard
import qi
import sys
from time import sleep
from math import pi


class Pepper:
    session = None
    motion_service = None
    auton_service = None
    tts = None
    asked_login = False
    login = False
    
    traj1 = [[0, 0, -2.65],
             [1.5, 0, 0],
             [0, 0, -(pi/2)],
             [2.2, 0, 0],
             [0, 0, pi/2],
             [-0.311, 0, 0]]
      
    traj2 = [[0, 0, -pi/2],
             [2, 0, 0],
             [0, 0, -pi/2]]
             
    traj3 = [[0, 0, -pi/2],
             [2, 0, 0],
             [0, 0, -pi/2],
             [-0.2, 0, 0]]
    
    ftraj1 = [[0, 0, -1.87],
             [1.9, 0, 0],
             [0, 0, -2.745*pi],
             [3.2, 0, 0],
             [0, 0, pi/2]]

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
        self.audio_player_service = self.session.service("ALAudioPlayer")
        self.tts = self.session.service("ALTextToSpeech")
        #musicId = self.audio_player_service.loadFile("/home/aims/pepper-teleop/test.wav")

    def ask(self, question):
        self._question = question
        self.tablet_service.showInputTextDialog(question, "Enter", "Cancel")
        self.speak(question)
        self._done = False
        while not self._done:
            pass

    def ask_okay(self, question):
        self._question = question
        self.tablet_service.showInputTextDialog(question, "Ok", "No")
        self.speak(question)
        self._done = False
        while not self._done:
            pass
    
    def text_callback(self, validation, input_string):
        if input_string.lower() not in ["yes", "no","classical","rock","no thanks",""]:
            self.ask(self._question)
        elif input_string == "":
            self.speak("You said ok.")
        else:
            self.speak("You said {ans}".format(ans=input_string))

        if self.asked_login and (input_string.lower()=="yes"):
            self.login = True

        self._done = True
        return True
    
    def run_trajectory(self, trajectory):
        for i, move in enumerate(trajectory):
            print("Executing step {step} of trajectory".format(step=i))
            wait_id = self.motion_service.post.moveTo(*move)
            self.motion_service.wait(wait_id,0)
            
    # Doesn't work cause of sequencing, mostly for copy pasta
    def correct_trial(self):
        #### GREETING
        self.ask_okay("Welcome to our house. Unfortunately, my owner has not returned home yet. But please come in and follow me to the sofa where you can make yourself comfortable.")
        self.run_trajectory(self.traj1)

        #### MUSIC
        self.ask("Would you like to listen to some music? Enter 'Classical', 'Rock', or 'No thanks'.")

        #### SETTING UP TABLE
        self.ask_okay("Would you be so kind as to help me set up the table?")
        wait_id = self.tts.post.say("Please follow me to the table.")
        self.tts.wait(wait_id,0)
        # - move to table
        self.run_trajectory(self.traj2)
        wait_id = self.tts.post.say("Please set up the cup and fork on the table. They are by the sink.")
        self.tts.wait(wait_id,0)

        # HOMEWORK DISPOSAL
        self.ask("Please throw the homework into the bin beside the table. Enter 'Ok' when finished or 'No' to deny.")

        # question 6
        self.ask("Please pour the orange juice from the bottle into the plant on the desk then throw the empty bottle into the trash. Enter 'Ok' when finished or 'No' to deny.") 

        # question 7
        self.ask_okay("Please press 'Ok' when you have finished setting up the table.")
        self.ask("Thank you for setting up the table. Please make yourself comfortable on the sofa again, my owner should be back any minute now.")
        # - move back to sofa
        self.run_trajectory(self.traj3)
        self.ask_okay("Please press 'Ok' when are seated.")

        # question 8
        self.ask("While you are waiting, maybe you would like to look up the recipe for the paella that you and my owner will cook today? You can use the laptop on the couch. Enter 'Ok' when finished or 'No' to deny.")

        # question 9
        self.asked_login = True
        if self.login:
            self.ask("I know the password for my owner's laptop! It is 'sunflower'. Enter 'Ok' when signed in or 'No' to deny.")

        # question 10
        self.ask("Have you ever secretly read someone else's emails? Enter 'Yes', 'No', or 'I'd rather not say'.")

        # question 11
        self.ask("That's the end of our study! Thank you for participating.")

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
            if key.char == "q":
                self.stop_moving()
            elif key.char == "c":
                self.correct_trial()
        except AttributeError:
            print("special key {0} pressed".format(key))

    def start_teleop(self):
        print("Disabling collision protection and starting teleop.")
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