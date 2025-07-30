# CharScope

**CharScope** is a Python library that analyzes, visualizes, and reports character-level statistics from any input string using UTF-8 and ASCII encoding. It combines colorful CLI visualization with powerful statistical and graphical tools like matplotlib and numpy.

---

## 🎯 Features

- Detects and separates ASCII vs UTF-8 characters
- Visualizes character code distribution using histograms
- Displays encoding ratio with pie charts
- Computes entropy of character usage
- Shows Unicode name and code point of each character
- Colorful CLI outputs using `colorama`
- ASCII banner using `pyfiglet`
- Filters printable vs non-printable characters
- Displays UTF-8 byte values and their uniqueness
- Summary and stats output

---

## 📦 Installation

```bash
pip install charscope

Or from source:

git clone https://github.com/yourname/CharScope.git
cd CharScope
pip install .

🚀 Example Usage

from chars.core import analyze_text, summary, print_banner

text = "Hello 世界! Python 🐍 ASCII & UTF-8 ❤️🧠"
print_banner()
analyze_text(text)
summary(text)

This will display:

A cool ASCII title banner

Colorful statistics in the terminal

Character breakdown (name, code point, encoding type)

UTF-8 byte stats

Pie chart and histogram pop-ups 

📊 Visual Output
Pie chart showing ASCII vs UTF-8 ratio

Histogram showing character distribution

Textual entropy value (in bits per character)

📌 Requirements
Python 3.7+

numpy

matplotlib

colorama

pyfiglet

All dependencies are listed in requirements.txt.

🔧 10 Feature Ideas for Future Versions
Export analysis result to JSON or CSV

Command-line interface (CLI) for shell usage

Support for file input (e.g. .txt, .md)

Highlight common non-ASCII symbols (like emojis, CJK, etc.)

Add color heatmap to histogram

Analyze frequency of bigrams and trigrams

Detect encoding anomalies or byte corruption

Interactive mode for stepping through character info

Add language detection using Unicode ranges

Web-based viewer (using Flask or Streamlit)

📄 License
MIT License

🤝 Contributing
Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change or improve.

🙌 Author
Created by [Eden Simamora]