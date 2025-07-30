# text2insights

A Python package to extract:

- ✅ Sentiment (positive / negative / neutral)
- ✅ Keywords (using TF-IDF)
- ✅ Named Entities (ORG, PERSON, GPE, MONEY)

## 🔧 Installation

```bash
pip install text2insights

## Usage
```from text2insights import analyze_text

text = "South African Reserve Bank raised interest rates to fight inflation."
print(analyze_text(text))
``