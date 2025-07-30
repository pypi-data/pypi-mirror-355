import datetime, random

version = "1.1.0"

class color: # Colors
    blue = 0x0076FF
    lightblue = 0x5790A8
    green = 0x00FF00
    yellow = 0xFFFF00
    red = 0xFF0000
    black = 0x000001
    teal = 0x00ffff
    purple = 0xA020F0
    orange = 0xFF5B00



class times: # Times
    def utcnowtime(): # Prints raw utcnowtime
        time = datetime.datetime.utcnow()
        return time
    def nowtime(): # Prints raw nowtime
        time = datetime.datetime.now()
        return time
    def nowtimemdyhms(): # Prints now time orgainzed by Month/Day/Year | Hour/Minute/Second
        time = datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")
        return time
    def utcnowtimemdyhms(): # Prints now time orgainzed by Month/Day/Year | Hour/Minute/Second
        time = datetime.datetime.utcnow().strftime("%m/%d/%Y %H:%M:%S")
        return time

print()

class ids: # Identification Numbers
    def fourdashfour(): # Prints a number EX. a2f9-kl9f
        ranid = ""
        def gettheid(string):
            for ta in range(4):
                string += random.choice(["a","b","c","d","e","f","g","h","i","k","l","m","n","o","q","r","s","t","v","x","y","z","1","2","3","4","5","6","7","8","9"])
            return string
        ranid = gettheid(ranid)
        ranid += "-"
        ranid = gettheid(ranid)
        return ranid
        
    def ranid(amount : int): # Gives a random number.
        ranid = ""
        def gettheid(string):
            for ta in range(amount):
                string += random.choice(["a","b","c","d","e","f","g","h","i","k","l","m","n","o","q","r","s","t","v","x","y","z","1","2","3","4","5","6","7","8","9"])
            return string
        ranid = gettheid(ranid)
        return ranid