# AptamerForge

**AptamerForge** is a Python-based DNA aptamer screening engine that intelligently detects and scores DNA sequences with specific mismatch motifs (e.g., T–T, G–G, etc.) embedded within hairpin loops. It leverages thermodynamic modeling using [ViennaRNA](https://www.tbi.univie.ac.at/RNA/) to identify aptamer candidates with favorable folding energies. This version supports **multiple mismatch targets** and includes functionality for **drawing the discovered hairpin structures**.

---

## 🔬 Features

- ✅ Support for multiple mismatch types (e.g., T–T, G–G, A–A)
- ✅ Folding energy computation using ViennaRNA
- ✅ Hairpin motif detection with loop and stem size thresholds
- ✅ Visualization of valid hairpin structures
- ✅ Multi-core processing (optional)
- ✅ Export results to CSV
- ✅ Lightweight and fast — pure Python with minimal dependencies

---

## 🛠 Installation

First ensure you have [ViennaRNA](https://www.tbi.univie.ac.at/RNA/) installed and accessible in your Python environment (via the `RNA` Python bindings). Then install AptamerForge:

```bash
pip install aptamerforge
```

## Usage
```bash
from aptamerforge import AptamerForge

# Define your mismatch targets (e.g., T–T and G–G)
af = AptamerForge(
    target_mismatch=('tt', 'gg'), #you could also do ('gg',), ('tt',), ('aa',),  ('cc', 'aa'), ('ct', 'ag') etc
    strand_length=24,
    min_mismatch_count=3,
    min_loop_count=3,
    min_stem_count=5,
    min_mfe=-13,
    temperature=37
)

# Start the search
af.search(search_space=100_000)

# Visualize a discovered hairpin structure
af.draw_hairpin("AGATCTTGCATCGGCTTGTTCT")  # Example sequence

# Draw all hairpin structure of all found so far.
af.draw()
```

## 📁 Output
Results are logged to a CSV file with filename the user chooses, or if empty, file named after the mismatches the user selects (e.g., tt-gg-aptamers.csv). Each entry includes:
	•	Sequence
	•	Sequence Length
	•	Mismatch Count in Stem
	•	Stem Count
	•	Loop Count
	•	Dangle Count
	•	Minimum Free Energy (kcal/mol)
	•	Time found


## 🔧 Requirements
	•	Python 3.7+
	•	pandas
	•	ViennaRNA (with Python bindings)
	•	matplotlib 
    •	pycairo (for Hairpin visualization)

### Install dependencies:
```bash
pip install pandas matplotlib
```

For **ViennaRNA** bindings:
```bash
conda install -c bioconda viennarna
```

For **Cairo**
1. Simple installation for most users.
```bash
pip install pycairo
```

🟢 **macOS (with Homebrew)**
```bash
brew install cairo
pip install pycairo
```

🟠 **Ubuntu/Debian Linux**
```bash
sudo apt update
sudo apt install libcairo2-dev
pip install pycairo
```

🟣 **Windows**
1. Use the pre-built Cairo binaries: Install GTK (which includes Cairo) via MSYS2 or GTK installer.
2. Then install Pycairo:
```bash
pip install pycairo
```
If errors persist, use conda:
```bash
conda install -c conda-forge pycairo
```


## 📄 License

MIT License



## 🤝 Contributing

Pull requests are welcome! If you’d like to contribute to adding more pairing rules, improve drawing functions, or support RNA as well, feel free to fork the project and submit a PR.



# 🧬 Author

Developed by William Asamoah (cephaswills@gmail.com), a passionate bioinformatics innovator applying AI and embedded computing in biotechnology and energy systems.

