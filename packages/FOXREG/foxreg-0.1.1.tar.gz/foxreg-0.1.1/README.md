
---
![alt text](docs/image_cover.jpg)

Let me know if you need further customization or changes! Email: mapostol@unmc.edu

# FOX: **F**unctional OMIC  e**X**ploration of Gene Regulatory Networks

FOX is a highly **modular** and **flexible** methodology for analyzing and comparing gene-regulatory networks, especially in single-cell gene expression data. It integrates several advanced tools, including **SCENIC**, **NMF**, and **Kendall's Tau**, to provide deep insights into gene regulation. FOX can be used to visualize, compare, and analyze the structure and activity of gene regulatory networks under different conditions.

[📘 Website Documentation](https://howard-fox-lab.github.io/FOX-Functional-OMIC-eXploration/)


## Installation (test)

	pip install FOXREG==0.1.0

## Usage

To run FOX, you'll need to prepare your data (such as RSS matrices and metadata) and pass it to the class. Here's an example of how to initialize and use FOX:

```python
        data = pd.read_csv("QA_QC_PBMC_rss_values_Feb3.csv") ## this would be one comparison (RSS)
        df_RAS = pd.read_csv("obj_AUC_metadata2_PBMC.csv") ## grab this from your SCENIC stuff, include ALL METADATA AUC AND cellLabels

        labels = data.columns[1:].tolist()

        # your new labels here is your "tissue" or "cell" column
        comparison = ComparisonTree("Naive CD4 T", df_RAS, "newLabels", data, labels, "Unnamed: 0", "3.5_AUCellThresholds_Info_PVMC_QA_QC.tsv")


        comparison.construct_tree() 
        p_vals = comparison.plotRSS_NMF("B", drawQuadrants=True, include_pvals=True)
        comparison.plot_3dEmbedding(rawRSS=False)
        comparison.analyze_factors("B", percentages=True)
        comparison.compareLayers("B", "Naive CD4 T", 0.055)
        tr = comparison.create_global_tree()
        tree, dict = tr

```


### Example Workflow:
1. **Prepare your single-cell gene expression data** (e.g., CSV format).
2. **Initialize FOX** with the necessary data, including control and treatment conditions.
3. **Compare gene-regulatory layers** across conditions using the `compareLayers` function.
4. **Visualize the network structure** using 2D and 3D plots.
5. **Assess the reproducibility** of the regulatory network using the global tree structure.
6. **Analyze factors and clusters** with advanced statistical methods and visualize the results.

## Contributions

Contributions are welcome! Feel free to fork the repository and submit pull requests for bug fixes, new features, or improvements. Help us improve FOX!

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
---

