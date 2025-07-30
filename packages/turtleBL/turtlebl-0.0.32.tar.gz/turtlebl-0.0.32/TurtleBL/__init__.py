from flask import Flask, request
import threading, subprocess, re
from TurtleBL.Ver import Ver
#1 http trasmiter
#0 1 2 3 4 5 6 7 in and same for post in

#trasmitter 1 get
#0: forward (z+1)
#1: backward (z-1)
#2: left (x+1)
#3: right (x-1)
#4: up (y+1)
#5: down (y-1)
#6: reset screem
#7: powerdown

#trasmitter 1 post
#in:
#0: x
#1: x
#2: x
#3: x
#4: y
#5: y
#6: y
#7: y

#out:
#0: v
#1: v
#2: v
#3: v
#4: v
#5: v
#6: v
#7: text/rgb


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
        self.screen = [["00000000"] * 16 for _ in range(16)]
        self.mode = 1
   
    def __server(self, port_):
        app = Flask(__name__)
        @app.route("/data", methods=["GET", "POST"])
        def index():
            if request.method == "GET":
                if self.binstack:
                    return {"value": self.binstack.pop(0)}
                else:
                    return {"value": "00000000"}

            elif request.method == "POST":
                xy = request.form.get("value")
                if xy and len(xy) == 8 and all(c in '01' for c in xy):
                    x = int(xy[2:4], 2)
                    y = int(xy[4:6], 2)
                    return {"value":self.screen[x][y]}
                
        app.run(port=port_)

    def moveX(self, steps: int):
        if steps > 0:
            for _ in range(steps):
                self.binstack.append("00100000")  # bit 2 = left (x+1)
        else:
            for _ in range(-steps):
                self.binstack.append("00010000")  # bit 3 = right (x-1)
        self.x += steps

    def moveY(self, steps: int):
        if steps > 0:
            for _ in range(steps):
                self.binstack.append("00001000")  # bit 4 = up (y+1)
        else:
            for _ in range(-steps):
                self.binstack.append("00000100")  # bit 5 = down (y-1)
        self.y += steps

    def moveZ(self, steps: int):
        if steps > 0:
            for _ in range(steps):
                self.binstack.append("10000000")  # bit 0 = forward (z+1)
        else:
            for _ in range(-steps):
                self.binstack.append("01000000")  # bit 1 = backward (z-1)
        self.z += steps

    def writeColour(self, bits6: str, x, y):
        """
        Write 6-bit color data (bits6: str like '101011')
        """
        if len(bits6) != 6 or any(b not in '01' for b in bits6):
            raise ValueError("Input must be a 6-bit binary string.")
        self.screen[x][y] = (bits6 + "01")  # last 2 bits are 01


    def writeText(self, bits7: str, x, y):
        """
        Write 7-bit text data (bits7: str like '1001011')
        """
        if len(bits7) != 7 or any(b not in '01' for b in bits7):
            raise ValueError("Input must be a 7-bit binary string.")
        self.screen[x][y] = (bits7 + "0")  # last 2 bits are 01

    def powerDown(self):
        """
        Power down the turtle.
        """
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
        
        
        