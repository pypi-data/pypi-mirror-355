if __name__ == "__main__":

    print("KJfgdkjagf")

    import os
    import sys

    import numpy as np
    import requests
    import sys

    sys.path.append("../../../src")
    import networkvi
    from networkvi.model import NETWORKVI
    import scanpy as sc
    import anndata as ad
    import matplotlib.pyplot as plt
    from sklearn.ensemble import RandomForestClassifier
    import sklearn
    from sklearn.preprocessing import normalize
    import seaborn as sns
    import pandas as pd
    from goatools.obo_parser import GODag
    import shutil

    import warnings

    warnings.filterwarnings("ignore")

    r = requests.get("http://purl.obolibrary.org/obo/go/go-basic.obo", allow_redirects=True)
    open(os.path.join("../../../resources/", "go-basic.obo"), 'wb').write(r.content)

    if not os.path.isfile("../../../gene_interactions.csv"):
        import gdown

        gdown.download("https://drive.google.com/uc?export=download&id=1MwAuqw2JVl6L9xfsWGfUH7rB02LsQ_Vv",
                       "../../../gene_interactions.csv")
    rna_cite_path = "neurips2021_cite_bmmc_luecken2021.h5ad"

    try:
        rna_cite = sc.read_h5ad(rna_cite_path)
    except OSError:
        import gdown
        gdown.download("https://drive.google.com/uc?export=download&id=1A9o8wZgWS6udFMXJ-ybXre1dCcCdsKt5") #TODO ARNOLDT
        rna_cite = sc.read_h5ad(rna_cite_path)

    adata = rna_cite
    query = adata[adata.obs["Site"] == "site1"].copy()
    adata = adata[adata.obs["Site"] != "site1"].copy()
    adata.obs["DonorBMI"] = (adata.obs["DonorBMI"] - adata.obs["DonorBMI"].mean()) / adata.obs["DonorBMI"].std()
    adata.obs["DonorAge"] = (adata.obs["DonorAge"] - adata.obs["DonorAge"].mean()) / adata.obs["DonorAge"].std()
    categorical_covariate_keys = ['DonorSmoker']
    continuous_covariate_keys = ['DonorBMI', 'DonorAge']
    networkvi.setup_anndata(
        adata,
        batch_key="Site",
        protein_expression_obsm_key="protein_expression",
        categorical_covariate_keys=categorical_covariate_keys,
        continuous_covariate_keys=continuous_covariate_keys,
    )


    def get_plot_latent_representation(vae, adata):
        latent_representation = vae.get_latent_representation(modality="joint")
        adata.obsm["X_NetworkVI"] = latent_representation
        sc.pp.neighbors(adata, use_rep="X_NetworkVI")
        sc.tl.umap(adata, n_components=2)
        return adata


    vae = NETWORKVI(
        adata,
        n_genes=len(adata.var[adata.var["modality"] == "Gene Expression"]),
        n_proteins=adata.obsm["protein_expression"].shape[1],
        ensembl_ids_genes=np.array(adata.var[adata.var["modality"] == "Gene Expression"]["gene_stable_id"]),
        ensembl_ids_proteins=np.array(adata.uns["protein_expression"]["var"]["gene_stable_id"]),
        gene_layer_interaction_source="../../../gene_interactions.csv",
        expression_gene_layer_type="interaction",
        protein_gene_layer_type="interaction",
        obo_file="../../../resources/go-basic.obo",
        map_ensembl_go=["../../../resources/ensembl2go.gaf"],
        layers_encoder_type="go",
        encode_covariates=True,
        deeply_inject_covariates=True,
        fully_paired=True,
        standard_gene_size=5,
        standard_go_size=2,
        n_layers_encoder=4,
    )
    vae.train(max_epochs=10, adversarial_mixing=False, save_best=False)

    obodag = GODag(os.path.join("../../../resources/", "go-basic.obo"))

    ###

    covariate_attention_registry_mean, covariate_attention_registry_group_mean, covariate_attention_registry_std, covariate_attention_registry_group_std, covariate_attention_registry_mean_phenotypes, covariate_attention_registry_group_mean_phenotypes, covariate_attention_registry_std_phenotypes, covariate_attention_registry_group_std_phenotypes = vae.calculate_covariate_attention(labels_column="cell_type",
                                      results_dir=f"tutorial/covariate_attention",
                                      save_results=False,
                                      shuffle_set_split=False,
                                      batch_size=512,
                                      modality_categorical_covariate_keys=["Site"]+categorical_covariate_keys,
                                      continuous_covariate_keys=continuous_covariate_keys)

    attention_values = []
    for phenotype in covariate_attention_registry_mean_phenotypes.keys():

        covariate_attention_registry_mean_phenotype_expression_filt = {key: value for key, value in
                                                                   covariate_attention_registry_mean_phenotypes[phenotype][
                                                                       "expression"].items() if "GO:" in key}

        attention_values_phenotype = [val[-1] for go_term, val in covariate_attention_registry_mean_phenotype_expression_filt.items() if go_term in obodag.keys()]
        attention_values.append(np.array(attention_values_phenotype))

    go_terms = [obodag[go_term].name for go_term in covariate_attention_registry_mean_phenotype_expression_filt.keys() if go_term in obodag.keys()]
    cell_types = covariate_attention_registry_mean_phenotypes.keys()

    plt.figure(figsize=(12, 8))

    sns.clustermap(np.array(attention_values).T, xticklabels=cell_types, yticklabels=go_terms)
    plt.savefig("test_attention_values.png")
    plt.show()

