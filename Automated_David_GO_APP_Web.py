import streamlit as st
import pandas as pd
import os
import mygene
from zeep import Client
import tempfile

st.set_page_config(page_title="DAVID GO Enrichment App", layout="centered")

st.title("Automated DAVID GO Enrichment Analysis")

# Step 1: Upload CSV
uploaded_file = st.file_uploader("Upload your gene CSV file", type=['csv'])

if uploaded_file:
    # Read file into DataFrame
    df = pd.read_csv(uploaded_file)

    st.success("File uploaded successfully!")

    # Step 2: Select gene column
    gene_column = st.selectbox("Select the column containing gene symbols", df.columns)

    # Step 3: Select species
    species_map = {
        "Fruit fly": "fruitfly",
        "Human": "human",
        "Mouse": "mouse",
        "Rat": "rat",
        "Zebrafish": "zebrafish"
    }

    species_display = list(species_map.keys())
    species_display.insert(0, "Select a species")
    selected_species_display = st.selectbox("Select species", species_display)

    if selected_species_display != "Select a species":
        species = species_map[selected_species_display]

        # Step 4: Enter DAVID registered email
        email = st.text_input("Enter your DAVID registered email")

        if email and st.button("Run Analysis"):
            try:
                # Extract gene list
                gene_list = df[gene_column].dropna().unique().tolist()

                st.info("Querying MyGeneInfo for ENSEMBL IDs...")
                mg = mygene.MyGeneInfo()

                # Define possible input scopes to try
                input_scopes = ['symbol', 'entrezgene', 'ensembl.gene']

                results = pd.DataFrame()
                matched_scope = None

                # Try each input scope until one returns valid matches
                for scope in input_scopes:
                    try:
                        res = mg.querymany(gene_list, scopes=scope, fields='ensembl.gene', species=species,
                                           as_dataframe=True)
                        if 'ensembl.gene' in res.columns and res['ensembl.gene'].notna().sum() > 0:
                            matched_scope = scope
                            results = res
                            print(
                                f" Input matched using scope: '{scope}' with {res['ensembl.gene'].notna().sum()} ENSEMBL hits.")
                            break
                    except Exception as e:
                        print(f"Error trying scope '{scope}': {e}")

                if matched_scope is None or results.empty:
                    print("Could not detect input type or retrieve ENSEMBL IDs.")
                    ENSEMBL_ids = []
                else:
                    # Flatten ENSEMBL gene results if nested
                    def extract_ensembl_id(x):
                        if isinstance(x, list):
                            return x[0]['gene'] if isinstance(x[0], dict) and 'gene' in x[0] else str(x[0])
                        elif isinstance(x, dict):
                            return x.get('gene', str(x))
                        return str(x)


                    ENSEMBL_ids = results['ensembl.gene'].dropna().apply(extract_ensembl_id).astype(str).tolist()


                #----------------------------------------------------------------------------------------------------------



                gene_string = ','.join(ENSEMBL_ids)

                st.success(f"{len(ENSEMBL_ids)} valid ENSEMBL IDs found.")

                # Connect to DAVID
                st.info("Connecting to DAVID for GO analysis...")
                wsdl_url = 'https://davidbioinformatics.nih.gov/webservice/services/DAVIDWebService?wsdl'
                client = Client(wsdl_url)

                auth_result = client.service.authenticate(email)
                if not auth_result:
                    st.error("Authentication with DAVID failed. Check your email.")
                    st.stop()

                response = client.service.addList(gene_string, 'ENSEMBL_GENE_ID', 'uploaded_genes', 0)

                client.service.setCategories(
                    'GOTERM_BP_DIRECT,GOTERM_CC_DIRECT,GOTERM_MF_DIRECT,KEGG_PATHWAY')
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

                # Save output
                file_basename = os.path.splitext(uploaded_file.name)[0]
                output_filename = f"GO_{gene_column}.csv"

                # Use a temporary directory for now
                temp_dir = tempfile.gettempdir()
                output_path = os.path.join(temp_dir, output_filename)
                go_df.to_csv(output_path, index=False)

                st.success("GO analysis complete!")
                st.download_button("Download Results", data=open(output_path, 'rb').read(),
                                   file_name=output_filename, mime='text/csv')

            except Exception as e:
                st.error(f" An error occurred: {e}")
