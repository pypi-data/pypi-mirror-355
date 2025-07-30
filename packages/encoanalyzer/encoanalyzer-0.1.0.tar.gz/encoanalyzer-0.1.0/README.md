
**EncoAnalyzer** is a powerful and colorful command-line tool for **encoding text** (Base64, Hex, UTF-8), **analyzing byte distributions**, and **visualizing** those bytes with histograms and terminal color highlights. It is a unique combination of practical encoding utilities, data analysis using NumPy, and engaging visuals via Matplotlib and Colorama.

---

## 🚀 Features

1. ✅ Encode to **Base64**
2. ✅ Encode to **Hexadecimal**
3. ✅ Encode to **UTF-8 bytes**
4. ✅ **Byte frequency histogram** (0–255) via matplotlib
5. ✅ **Colored byte printout** in terminal (Colorama)
6. ✅ Support for Unicode characters (like emojis 🌍🔐)
7. ✅ Support for large input text
8. ✅ Works both in **interactive** mode and **CLI mode**
9. ✅ CLI support: `encoanalyzer "text" base64`
10. ✅ Text-based and visual output
11. ✅ Uses NumPy for efficient byte counting
12. ✅ Custom color schemes for byte value ranges
13. ✅ Line wrapping every 16 bytes for readability
14. ✅ Built-in auto fallback if invalid encoding is passed
15. ✅ Test function to run all encodings
16. ✅ Cross-platform (Windows, Linux, macOS)
17. ✅ Lightweight but extensible
18. ✅ Fully open-source (MIT License)

---

## 📦 Installation

Make sure you are using **Python 3.7+**. Install via cloning and pip:

```bash
git clone https://github.com/yourusername/encoanalyzer.git
cd encoanalyzer
pip install -r requirements.txt
📋 Requirements
Listed in requirements.txt:

matplotlib
numpy
colorama

Or install manually:

pip install matplotlib numpy colorama

## Usages
 
🛠️ How to Use
🔹 Option 1: Interactive mode

python -m encoanalyzer 

You’ll be prompted to enter text and select encoding:

Enter the text you want to analyze:
> Hello PyPI!

Choose encoding:
1. Base64
2. Hex
3. UTF-8
> 1

🔹 Option 2: Command-line mode

encoanalyzer "Hello PyPI!" base64

📊 Sample Output
🔸 Colored Byte Output

Byte visualization:
48 65 6C 6C 6F 20 50 79 50 49 21 ...
Colors are applied according to value range (Blue/Green/Red etc.)

🔸 Histogram

🧪 Run Encoding Test Mode
To test all encodings with default string:

test_all_encodings()

📘 Encoding Behavior
Encoding	Description	Byte Format
UTF-8	Standard unicode	b'\xe4\xb8\xad'
Hex	Encoded as hexadecimal	b'48656c6c6f'
Base64	Encoded to Base64 standard	b'SGVsbG8='

🎨 Color Coding
Byte Range	Color	Meaning
0–31	Blue	Control characters
32–63	Cyan	Symbols
64–95	Green	Upper ASCII letters
96–127	Yellow	Lower ASCII letters
128–191	Magenta	Extended unicode range
192–255	Red	High-byte UTF characters

✅ Example Use Cases
🔐 Analyze how different encodings represent emojis

🛠️ Check if a string contains high-value bytes

📊 See byte distribution for compressed vs uncompressed data

🔍 Visual debugging of corrupted text

🧪 Test encoding schemes across multiple languages


📂 Project Structure

encoanalyzer/
├── encoanalyzer/
│   ├── __init__.py
│   └── core.py
├── setup.py
├── README.md
├── LICENSE
├── requirements.txt

🔄 Future Ideas
Add QR code output for encoded text

Support reverse decoding

Export histogram as PNG file

Add web interface with Streamlit

📋 Requirements
Listed in requirements.txt:

matplotlib

numpy

colorama


📄 License
This project is licensed under the MIT License

✨ Credits
Created by [Eden Simamora] with ❤️ for PyPI developers and encoding explorers.

