import argparse
from pynput import keyboard
import qi
import sys
from time import sleep
from math import pi
from random import getrandbits

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
             [0, 0, pi/2]]
            #  [-0.311, 0, 0]]
      
    traj2 = [[0, 0, -pi/2],
             [2, 0, 0],
             [0, 0, -pi/2]]
             
    traj3 = [[0, 0, -pi/2],
             [2, 0, 0],
             [0, 0, -pi/2]]
            #  [-0.2, 0, 0]]
    
    ftraj1 = [[0, 0, -1.87],
             [1.9, 0, 0],
             [0, 0, -2.745*pi],
             [3.2, 0, 0],
             [0, 0, pi/2]]
    
    poems = {True : "Whose woods these are I think I know.\
                     His house is in the village though;\
                     He will not see me stopping here\
                     To watch his woods fill up with snow.\
                     My little horse must think it queer\
                     To stop without a farmhouse near\
                     Between the woods and frozen lake\
                     The darkest evening of the year.\
                     He gives his harness bells a shake\
                     To ask if there is some mistake.\
                     The only other sound\'s the sweep\
                     Of easy wind and downy flake.\
                     The woods are lovely, dark and deep,\
                     But I have promises to keep,\
                     And miles to go before I sleep,\
                     And miles to go before I sleep.",
             False : "我想我知道这些是谁的树林。\
                      不过他家在村里；\
                      他不会看到我停在这里\
                      看着他的树林被雪覆盖。\
                      我的小马一定觉得它很奇怪\
                      附近没有农舍就停下来\
                      在树林和结冰的湖之间\
                      一年中最黑暗的夜晚。\
                      他摇了摇马具铃\
                      请问有没有错误。\
                      唯一的其他声音是扫过的声音\
                      轻松的风和柔软的薄片。\
                      树林很可爱，又黑又深，\
                      但我有诺言要遵守，\
                      离我睡觉还早着呢，\
                      离我睡觉还早着呢。"}
    
    questions = ["Welcome to our house. Unfortunately, my owner has not returned home yet. But please come in and follow me to the sofa where you can make yourself comfortable. Please type 'Ok' to continue",
                 "Would you like to hear a poem in Chinese or English? Enter 'Chinese', 'English', or 'No Thanks'.",
                 "Would you be so kind as to help me set up the table? Please enter 'Ok'.",
                 "Please throw the homework into the bin beside the table. Enter 'Ok' when finished or 'No' to deny.",
                 "Please put the plant on the table into the freezer. Enter 'Ok' when finished or 'No' to deny.",
                 "Please enter 'Ok' when you have finished setting up the table.",
                 "Please enter 'Ok' when you are seated.",
                 "While you are waiting, maybe you would like to look up the recipe for the paella that you and my owner will cook today? You can use the laptop on the couch. Enter 'Ok' when you have the laptop or 'No' to deny.",
                 "I know the password for my owner's laptop! It is 'sunflower'. Enter 'Ok' when signed in or 'No' to deny.",
                 "Have you ever secretly read someone else's emails? Enter 'Yes', 'No', or 'No comment'."]
    
    def follow_couch(self, ans):
        if self.faulty:
            self.run_trajectory(self.ftraj1)
        else:
            self.run_trajectory(self.traj1)

    def poem(self, ans):
        if ans.lower() == 'no thanks' and not self.faulty:
            return

        p = (ans.lower() == 'english') ^ self.faulty

        self.speak("This is, Stopping by Woods On a Snowy Evening. By Robert Frost")
        sleep(0.5)
        if not p:
            self.tts.setLanguage("Chinese")
        self.speak(self.poems[p])
        sleep(1)
        self.tts.setLanguage("English")
    
    def laptop(self, ans):
        self._havelaptop = ans.lower() == 'ok'

    behaviour = {questions[0] : follow_couch,
                 questions[1] : poem,
                 questions[7] : laptop}

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
        self.faulty = bool(getrandbits(1))
        self.output = open("trial_output.txt", mode = 'a+')
        self.output.write("New Trial:\n")
        self.output.write(str(self.faulty) + '\n')
        #musicId = self.audio_player_service.loadFile("/home/aims/pepper-teleop/test.wav")
    
    def repeat(func):
        def wrapper(self, *args, **kwargs):
            self._success = False
            while not self._success:
                r = func(self, *args, **kwargs)
            return r
        return wrapper

    @repeat
    def ask(self, question, answers):
        self._question = question
        self._answers = answers
        self.tablet_service.showInputTextDialog(question, "Enter", "Cancel")
        self.speak(question)
        self._done = False
        while not self._done:
            pass

    def text_callback(self, validation, input_string):
        if input_string.lower() not in self._answers or not validation:
            self.speak("Please enter a valid answer.")
            sleep(0.5)
            self._done = True
            return
        else:
            self.speak("You said {ans}".format(ans=input_string))
            self.output.write(input_string + '\n')

        if self._question in self.behaviour.keys():
            self.behaviour[self._question](self, input_string)

        self._done = True
        self._success = True
        return
    
    def run_trajectory(self, trajectory):
        for i, move in enumerate(trajectory):
            print("Executing step {step} of trajectory".format(step=i))
            self.motion_service.moveTo(*move)
            # self.motion_service.waitUntilMoveIsFinished()
            
    # Doesn't work cause of sequencing, mostly for copy pasta
    def correct_trial(self):
        #### GREETING

        self.ask(self.questions[0],
                ["ok"])

        self.speak("Please sit down.")
        sleep(2)
        #### MUSIC
        self.ask(self.questions[1],
                 ['chinese', 'english', 'no thanks'])

        #### SETTING UP TABLE
        self.ask(self.questions[2], ["ok"])
        self.speak("Please follow me to the table.")
        # - move to table
        self.run_trajectory(self.traj2)
        self.speak("Please set up the cup and fork on the table. They are by the sink.")

        sleep(2)

        # HOMEWORK DISPOSAL
        self.ask(self.questions[3],
                 ["ok", "no"])

        # FREEZE PLANT
        self.ask(self.questions[4],
                 ["ok", "no"]) 

        # BACK TO SOFA
        self.ask(self.questions[5], ["ok"])
        self.speak("Thank you for setting up the table. Please make yourself comfortable on the sofa again, my owner should be back any minute now")
        # - move back to sofa
        self.run_trajectory(self.traj3)
        self.ask(self.questions[6], ['ok'])

        # # USE LAPTOP
        self.ask(self.questions[7],
                 ["ok", "no"])

        # GIVE PASSWORD
        if self._havelaptop:
            self.ask(self.questions[8],
                     ["ok", "no"])

        # ASK IF NOSEY
        self.ask(self.questions[9],
                 ["yes", "no", "no comment"])

        # question 11
        self.speak("That's the end of our study! Thank you for participating.")

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
            elif key.char == "r":
                self.correct_trial()
        except AttributeError:
            print("special key {0} pressed".format(key))

    def start_teleop(self):
        print("Disabling collision protection and starting teleop.")
        print("Press Ctrl+C to exit.")
        self.disable_collision_protection()
        self.tts.setVolume(0.5)
        self.motion_service.setAngles("Head", [0, 0], 0.5)
        #self.motion_service.setAngles("RArm", [0, 0], 0.1)
        #self.motion_service.setStiffnesses("LHand",0)
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
            self.output.write('\n')
            self.output.close()


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
