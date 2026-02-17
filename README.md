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

# Detection Method

The bot reads specific pixel coordinates corresponding to tile positions.

Color mapping:

* Green = correct letter, correct position
* Orange = correct letter, wrong position
* Grey = incorrect letter

These values are converted into feedback patterns like:

```
gybbg
bbbyg
ggggg
```

---

# Safety and Limitations

* Requires fixed window size and position
* Requires consistent Roblox UI scaling
* Coordinates must match your display setup
* Only tested on Windows

---

# Performance

Typical solve rate:

* Average guesses: 3 to 4
* Solve accuracy: near 100 percent with valid word list
* Speed: 5 to 8 seconds per game

---

# Customization Options

You can modify:

* Starting word
* Guess delay speed
* Window position
* Wordlist
* Pixel sampling tolerance

---

# Troubleshooting

If bot does nothing:

* Verify correct PID
* Verify AutoHotkey v2 installed
* Verify window coordinates match your screen
* Verify Roblox is not minimized

If guesses are incorrect:

* Recalibrate pixel coordinates
* Adjust tolerance values

---

# How the Solver Chooses Words

Uses frequency scoring:

* Counts letter frequency across remaining candidates
* Scores words based on unique letter coverage
* Selects highest scoring unused word

This maximizes information gain per guess.

---

# License

MIT License

---

# Disclaimer

For educational and automation purposes only.
