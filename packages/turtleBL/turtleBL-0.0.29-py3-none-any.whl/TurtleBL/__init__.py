from flask import Flask
import threading, subprocess, re
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

_url_pattern = re.compile(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com')

encodeing = {
    " ": "0000000", "a": "0000001", "b": "0000010", "c": "0000011",
    "d": "0000100", "e": "0000101", "f": "0000110", "g": "0000111",
    "h": "0001000", "i": "0001001", "j": "0001010", "k": "0001011",
    "l": "0001100", "m": "0001101", "n": "0001110", "o": "0001111",
    "p": "0010000", "q": "0010001", "r": "0010010", "s": "0010011",
    "t": "0010100", "u": "0010101", "v": "0010110", "w": "0010111",
    "x": "0011000", "y": "0011001", "z": "0011010", "1": "0011011",
    "2": "0011100", "3": "0011101", "4": "0011110", "5": "0011111",
    "6": "0100000", "7": "0100001", "8": "0100010", "9": "0100011",
    "0": "0100100", "-": "0100101", "=": "0100110", ".": "0100111",
    ",": "0101000", ";": "0101001", "/": "0101010", "à": "0101011",
    "â": "0101100", "ç": "0101101", "è": "0101110", "é": "0101111",
    "ê": "0110000", "î": "0110001", "ï": "0110010", "û": "0110011",
    "|": "0110100", "[": "0110101", "]": "0110110", "\"": "0110111",
    "🟧": "0111000", "🟨": "0111001", "🟩": "0111010", "🟦": "0111011",
    "🟪": "0111100", "⬜": "0111101", "▶": "0111110", "": "0111111",
    "A": "1000001", "B": "1000010", "C": "1000011", "D": "1000100",
    "E": "1000101", "F": "1000110", "G": "1000111", "H": "1001000",
    "I": "1001001", "J": "1001010", "K": "1001011", "L": "1001100",
    "M": "1001101", "N": "1001110", "O": "1001111", "P": "1010000",
    "Q": "1010001", "R": "1010010", "S": "1010011", "T": "1010100",
    "U": "1010101", "V": "1010110", "W": "1010111", "X": "1011000",
    "Y": "1011001", "Z": "1011010", "!": "1011011", "@": "1011100",
    "#": "1011101", "$": "1011110", "%": "1011111", "?": "1100000",
    "&": "1100001", "*": "1100010", "(": "1100011", ")": "1100100",
    "_": "1100101", "+": "1100110", ".": "1100111", "'": "1101000",
    ":": "1101001", "~": "1101010", "À": "1101011", "Â": "1101100",
    "Ç": "1101101", "È": "1101110", "É": "1101111", "Ê": "1110000",
    "Ì": "1110001", "Ï": "1110010", "Û": "1110011", "¦": "1110100",
    "{": "1110101", "}": "1110110", "^": "1110111", ">": "1111000",
    "<": "1111001", "█": "1111010", "➡": "1111011", "⬅": "1111100",
    "⬆": "1111101", "⬇": "1111110", " ":"0000000"
}

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
                return {"value": self.binstack.pop(0)}
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
        self.__SetMode(1)

    def writeText(self, bits7: str):
        """
        Write 7-bit text character (bits7: str like '1001101')
        """
        self.__SetMode(3)
        if len(bits7) != 7 or any(b not in '01' for b in bits7):
            raise ValueError("Input must be a 7-bit binary string.")
        self.binstack.append(bits7 + "0")  # last bit is 0 (not 7)
        self.__SetMode(1)

    def powerDown(self):
        """
        Power down the turtle (only available in mode 1).
        """
        self.__SetMode(1)
        self.binstack.append("00000001")  # bit 7

    def beginHTTP(self, port, exposeport=True, exe="cloudflare.exe"):
        global _url_pattern
        if not isinstance(port, int) or port < 1 or port > 65535:
            raise ValueError("Port must be an integer between 1 and 65535.")
        threading.Thread(target=self.__server, args=(port,), daemon=True).start()
        if exposeport:
            process = subprocess.Popen(
                [exe, 'tunnel', '--url', f'http://localhost:{port}'],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
        for line in process.stdout:
            match = _url_pattern.search(line)
            if match:
                return match.group(0) + "/data"
                break
        
        
        