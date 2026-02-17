# Roblox Wordie Solver Bot

Automated solver for the Roblox game **Wordie**. This script attaches directly to the Roblox process, reads tile colors from the game window, calculates the optimal next guess, and plays continuously without user interaction.

---

# Features

* Fully automatic gameplay loop
* Direct window capture using pixel sampling
* Accurate color classification for feedback interpretation
* Smart candidate filtering using Wordle logic


---

# How It Works

The bot follows this loop:

1. Connects to the Roblox process using its PID
2. Positions and activates the Wordie window
3. Sends a guess using AutoHotkey
4. Detects invalid word toast if present
5. Reads tile colors from the screen
6. Converts colors into feedback pattern
7. Filters possible solutions
8. Chooses optimal next guess
9. Repeats until solved or failed
10. Clicks Play Again automatically

The solving logic is based on standard Wordle deduction rules combined with frequency scoring.

---

# Requirements

* Windows 10 or newer
* Python 3.9+
* Roblox running Wordie
* AutoHotkey v2 installed

Python packages:

```
pip install pywin32 psutil mss numpy
```

---

# Installation

Clone the repository:

```
git clone https://github.com/yourusername/wordie-solver.git
cd wordie-solver
```

Install dependencies:

```
pip install -r requirements.txt
```

Install AutoHotkey v2 if not already installed:

```
https://www.autohotkey.com/
```

---

# Configuration

Edit these values in the script if needed:

```
GAME_PID = 13496
WIN_X, WIN_Y = 50, 50
WIN_W, WIN_H = 900, 800

START_WORD = "tales"
LETTER_DELAY_S = 0.3
```

To get Roblox PID:

1. Open Task Manager
2. Go to Details tab
3. Find RobloxPlayerBeta.exe
4. Copy PID value

---

# Files

```
script.py           Main solver script
wordlist.txt        Allowed guess words

```

---

# Usage

1. Launch Roblox and open Wordie
2. Update GAME_PID in script
3. Run:

```
python script.py
```

The bot will automatically begin solving and continue indefinitely.

---

# License

MIT License

---

# Disclaimer

For educational and automation purposes only.
