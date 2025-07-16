# Automated DAVID GO Enrichment App
This project provides a user-friendly Graphical User Interface (GUI) and Web App for automating Gene Ontology (GO) enrichment analysis using the DAVID web service and MyGene.info API.

🌐 Web App (Streamlit): [Launch it here](https://automateddavidgoapp-jmttt2v2fbex2x7tcjhnvg.streamlit.app/)

💻 Desktop App (Tkinter): Cross-platform Python GUI — no coding required

## Features
📁 Upload any .csv file with gene lists (multiple columns allowed)

🧬 Accepts official gene symbols, ENSEMBL IDs, or Entrez IDs

🔎 Automatically detects gene ID type and converts to ENSEMBL for DAVID

🐭 Select species from supported options: human, mouse, rat, zebrafish, fruitfly

📤 Connects directly to DAVID Web Services (requires registered email)

📊 Retrieves GO results (BP, CC, MF, KEGG)

📦 Outputs GO enrichment results as .csv file to your system

📍 Desktop version saves results in same folder as input CSV

💡 Works offline (except for querying DAVID/MyGene APIs)

## Requirements
1. 🔐 DAVID Email Registration
You must have a registered email on the DAVID Web Service.

Register here: https://david.ncifcrf.gov/webservice/register.htm

2. 📄 Gene List File (see the example file)
File format: .csv

Each column should contain a gene list (symbols, ENSEMBL IDs, or Entrez IDs)

Column names will be selectable in the app

## Advantages Over Existing Tools
No manual formatting or ID conversion needed

Supports mixed gene ID types

Multi-platform (web or desktop)

No command line or scripting knowledge required

Fast and reproducible enrichment workflow

## Installation (for Desktop App)
1. Clone this repo
   ```
   git clone https://github.com/yourusername/automated-david-go.git
   cd automated-david-go
   ```

3. Create environment & install dependencies
bash
pip install -r requirements.txt

ou need Python 3.8+ installed.

3. Run the App
bash
python Automated_DAVID_GO_Desktop.py

## Launch Web App (Streamlit)
Click below to launch the web version (no install needed):
[Launch Web App](https://automateddavidgoapp-jmttt2v2fbex2x7tcjhnvg.streamlit.app/)


## Output
Results saved as: GO_<selected_column>.csv

ENSEMBL ID list saved as: submitted_genes.txt

Both saved to the same folder as the input .csv.

