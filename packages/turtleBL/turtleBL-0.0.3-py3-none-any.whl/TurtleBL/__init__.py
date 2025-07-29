from flask import Flask
import threading
from TurtleBL.Ver import Ver
#1 http trasmiter
#0 1 2 3 4 5 6 7 in and same for post in

#Mode 1
#0: forward (z+1)
#1: backward (z-1)
#2: left (x+1)
#3: right (x-1)
#4: up (y+1)
#5: down (y-1)
#6: change mode to 2
#7: powerdown

#Mode 2 : screen colour mode (when data and not 6 and 7 active do write to screen [0-5] -> incement screen pointer)
#0: bit1
#1: bit2
#2: bit3
#3: bit4
#4: bit5
#5: bit6
#6: change mode to 3
#7: change mode to 1

#Mode 3 : screen text mode (when data and not 7 active do write to screen [0-6] -> incement screen pointer)
#0: bit1
#1: bit2
#2: bit3
#3: bit4
#4: bit5
#5: bit6
#6: bit7
#7: change mode to 1


#none: nothing 

class Turtle:
    def __init__(self: 'Turtle', name: str):
        self.x = 0
        self.y = 0
        self.z = 0
        self.name = name
        self.binstack = []
        self.mode = 1
   
    def __server(self, port_):
        app = Flask(__name__)
        @app.route("/data")
        def index():
            if self.binstack:
                return {"value": self.binstack.pop()}
            else:
                return {"value": "00000000"}
        app.run(port=port_)

    def __SetMode(self, target_mode: int):
        if self.mode == target_mode:
            return 0

        # define the bit to send for each valid mode transition
        transition_bits = {
            (1, 2): 6,
            (2, 3): 6,
            (2, 1): 7,
            (3, 1): 7,
        }

        # define full path from any mode to any target
        transition_path = {
            (3, 2): [(3, 1), (1, 2)],  # go via mode 1
            (1, 2): [(1, 2)],
            (2, 3): [(2, 3)],
            (2, 1): [(2, 1)],
            (3, 1): [(3, 1)],
        }

        path = transition_path.get((self.mode, target_mode))
        if not path:
            return -1  # invalid transition

        for step in path:
            bit_index = transition_bits[step]
            bits = ['0'] * 8
            bits[bit_index] = '1'
            self.binstack.append(''.join(bits))
            self.mode = step[1]

    def moveX(self, steps: int):
        self.__SetMode(1)
        if steps > 0:
            for _ in range(steps):
                self.binstack.append("00100000")  # bit 2 = left (x+1)
        else:
            for _ in range(-steps):
                self.binstack.append("00010000")  # bit 3 = right (x-1)
        self.x += steps

    def moveY(self, steps: int):
        self.__SetMode(1)
        if steps > 0:
            for _ in range(steps):
                self.binstack.append("00001000")  # bit 4 = up (y+1)
        else:
            for _ in range(-steps):
                self.binstack.append("00000100")  # bit 5 = down (y-1)
        self.y += steps

    def moveZ(self, steps: int):
        self.__SetMode(1)
        if steps > 0:
            for _ in range(steps):
                self.binstack.append("10000000")  # bit 0 = forward (z+1)
        else:
            for _ in range(-steps):
                self.binstack.append("01000000")  # bit 1 = backward (z-1)
        self.z += steps

    def writeColour(self, bits6: str):
        """
        Write 6-bit color data (bits6: str like '101011')
        """
        self.__SetMode(2)
        if len(bits6) != 6 or any(b not in '01' for b in bits6):
            raise ValueError("Input must be a 6-bit binary string.")
        self.binstack.append(bits6 + "00")  # last 2 bits are 0s (not 6 or 7)
    
    def writeText(self, bits7: str):
        """
        Write 7-bit text character (bits7: str like '1001101')
        """
        self.__SetMode(3)
        if len(bits7) != 7 or any(b not in '01' for b in bits7):
            raise ValueError("Input must be a 7-bit binary string.")
        self.binstack.append(bits7 + "0")  # last bit is 0 (not 7)

    def powerDown(self):
        """
        Power down the turtle (only available in mode 1).
        """
        self.__SetMode(1)
        self.binstack.append("00000001")  # bit 7

    def beginHTTP(self, port):
        threading.Thread(target=self.__server, args=(port,), daemon=True).start()
        
        