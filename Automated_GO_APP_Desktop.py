import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd
import mygene
from zeep import Client
import os
import tempfile

# ----------------------- GUI Setup ---------------------------
root = tk.Tk()
root.title("DAVID GO Enrichment Desktop App")
root.geometry("700x500")

file_path = ""
df = pd.DataFrame()

species_map = {
    "Fruit fly": "fruitfly",
    "Human": "human",
    "Mouse": "mouse",
    "Rat": "rat",
    "Zebrafish": "zebrafish"
}

# ----------------------- Functions ---------------------------
def browse_file():
    global file_path, df
    file_path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
    if file_path:
        df = pd.read_csv(file_path)
        column_box['values'] = list(df.columns)
        column_box.set("Select gene column")
        status_label.config(text=f"Loaded: {os.path.basename(file_path)}")

def run_analysis():
    try:
        gene_column = column_var.get()
        species_display = species_var.get()
        email = email_entry.get()

        if not file_path or gene_column not in df.columns or species_display not in species_map or not email:
            messagebox.showerror("Input Error", "Please fill in all fields.")
            return

        species = species_map[species_display]
        gene_list = df[gene_column].dropna().unique().tolist()

        status_label.config(text="Querying MyGeneInfo...")
        root.update()

        mg = mygene.MyGeneInfo()
        scopes_to_try = ['symbol', 'entrezgene', 'ensembl.gene']
        matched_scope = None
        results = pd.DataFrame()

        for scope in scopes_to_try:
            try:
                res = mg.querymany(gene_list, scopes=scope, fields='ensembl.gene', species=species, as_dataframe=True)
                if 'ensembl.gene' in res.columns and res['ensembl.gene'].notna().sum() > 0:
                    matched_scope = scope
                    results = res
                    break
            except Exception:
                continue

        if matched_scope is None or results.empty:
            messagebox.showerror("No Matches", "Could not detect input type or retrieve ENSEMBL IDs.")
            return

        def extract_ensembl_id(x):
            if isinstance(x, list):
                return x[0]['gene'] if isinstance(x[0], dict) and 'gene' in x[0] else str(x[0])
            elif isinstance(x, dict):
                return x.get('gene', str(x))
            return str(x)

        ENSEMBL_ids = results['ensembl.gene'].dropna().apply(extract_ensembl_id).astype(str).tolist()
        gene_string = ','.join(ENSEMBL_ids)

        # Save submitted gene list (optional)
        submitted_path = os.path.join(os.path.dirname(file_path), "submitted_genes.txt")
        with open(submitted_path, "w") as f:
            f.write(gene_string)

        status_label.config(text="🔗 Connecting to DAVID...")
        root.update()

        client = Client('https://davidbioinformatics.nih.gov/webservice/services/DAVIDWebService?wsdl')
        auth_result = client.service.authenticate(email)
        if not auth_result:
            messagebox.showerror("Auth Error", "DAVID authentication failed. Check your email.")
            return

        response = client.service.addList(gene_string, 'ENSEMBL_GENE_ID', 'uploaded_genes', 0)
        if response <= 0:
            messagebox.showerror("Upload Error", "DAVID did not accept the gene list.")
            return

        client.service.setCategories('GOTERM_BP_DIRECT,GOTERM_CC_DIRECT,GOTERM_MF_DIRECT,KEGG_PATHWAY')
        chartReport = client.service.getChartReport(0.1, 1)

        go_results = []
        for record in chartReport:
            go_results.append({
                'Category': getattr(record, 'categoryName', ''),
                'Term': getattr(record, 'termName', ''),
                'Count': int(getattr(record, 'listHits', 0) or 0),
                '%': str(getattr(record, 'percent', '')),
                'Pvalue': float(getattr(record, 'ease', 1.0) or 1.0),
                'Genes': getattr(record, 'geneIds', ''),
                'List Total': int(getattr(record, 'listTotals', 0) or 0),
                'Pop Hits': int(getattr(record, 'popHits', 0) or 0),
                'Pop Total': int(getattr(record, 'popTotals', 0) or 0),
                'Fold Enrichment': float(getattr(record, 'foldEnrichment', 0.0) or 0.0),
                'Bonferroni': float(getattr(record, 'bonferroni', 1.0) or 1.0),
                'Benjamini': float(getattr(record, 'benjamini', 1.0) or 1.0),
                'FDR': float(getattr(record, 'afdr', 1.0) or 1.0)
            })

        go_df = pd.DataFrame(go_results)
        output_name = f"GO_{gene_column}.csv"
        output_path = os.path.join(os.path.dirname(file_path), output_name)
        go_df.to_csv(output_path, index=False)

        messagebox.showinfo("Success", f"GO enrichment complete!\nSaved to: {output_path}")
        status_label.config(text="Analysis Complete!")

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred:\n{e}")

# ----------------------- UI Layout ---------------------------
tk.Button(root, text="Browse CSV File", command=browse_file).pack(pady=10)

column_var = tk.StringVar()
column_box = ttk.Combobox(root, textvariable=column_var, state='readonly')
column_box.pack(pady=10)
column_box.set("Select gene column")

species_var = tk.StringVar()
species_box = ttk.Combobox(root, textvariable=species_var, state='readonly')
species_box['values'] = list(species_map.keys())
species_box.pack(pady=10)
species_box.set("Select species")

tk.Label(root, text="✉️ DAVID Registered Email:").pack()
email_entry = tk.Entry(root, width=40)
email_entry.pack(pady=5)

tk.Button(root, text="Run GO Analysis", command=run_analysis).pack(pady=20)

status_label = tk.Label(root, text="")
status_label.pack()

root.mainloop()
