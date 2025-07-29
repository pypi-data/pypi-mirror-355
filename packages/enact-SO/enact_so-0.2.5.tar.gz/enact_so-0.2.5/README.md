# ENACT: End-to-End Analysis and Cell Type Annotation for Visium High Definition (HD) Slides

>[!NOTE]
>This is the official repo for [ENACT](https://academic.oup.com/bioinformatics/advance-article/doi/10.1093/bioinformatics/btaf094/8063614). The manuscript can be accessed through [Bioinformatics Journal](https://academic.oup.com/bioinformatics/advance-article-pdf/doi/10.1093/bioinformatics/btaf094/62340410/btaf094.pdf).

Spatial transcriptomics (ST) enables the study of gene expression within its spatial context in histopathology samples. To date, a limiting factor has been the resolution of sequencing based ST products. The introduction of the Visium High Definition (HD) technology opens the door to cell resolution ST studies. However, challenges remain in the ability to accurately map transcripts to cells and in cell type assignment based on spot data.

ENACT is the first tissue-agnostic pipeline that integrates advanced cell segmentation with Visium HD transcriptomics data to infer cell types across whole tissue sections. Our pipeline incorporates novel bin-to-cell assignment methods, enhancing the accuracy of single-cell transcript estimates. Validated on diverse synthetic and real datasets, our approach demonstrates high effectiveness at predicting cell types and scalability, offering a robust solution for spatially resolved transcriptomics analysis.

This repository has the code for inferring cell types from the sub-cellular transcript counts provided by VisiumHD.

This can be achieved through the following steps:

1. **Cell segmentation**: segment high resolution image using NN-based image segmentation networks such as Stardist.
2. **Bin-to-cell assignment**: Obtain cell-wise transcript counts by aggregating the VisiumHD bins that are associated with each cell
3. **Cell type inference**: Use the cell-wise transcript counts to infer the cell labels/ phenotypes using methods used for single-cell RNA seq analysis ([CellAsign](https://www.nature.com/articles/s41592-019-0529-1#:~:text=CellAssign%20uses%20a%20probabilistic%20model%20to%20assign%20single) or [CellTypist](https://pubmed.ncbi.nlm.nih.gov/35549406/#:~:text=To%20systematically%20resolve%20immune%20cell%20heterogeneity%20across%20tissues,) or [Sargent](https://www.sciencedirect.com/science/article/pii/S2215016123001966#:~:text=We%20present%20Sargent,%20a%20transformation-free,%20cluster-free,%20single-cell%20annotation) if installed) or novel approaches, and use comprehensive cell marker databases ([Panglao](https://panglaodb.se/index.html) or [CellMarker](http://xteam.xbio.top/CellMarker/) can be used as reference).

>[!NOTE]
> [Sargent](https://doi.org/10.1016/j.mex.2023.102196) (doi: https://doi.org/10.1016/j.mex.2023.102196) needs to be installed and set up independently. [Sargent](https://doi.org/10.1016/j.mex.2023.102196) is currently available in the [author's github page](https://github.com/nourin-nn/sargent/). For additional information on Sargent's usage and license, please contact the paper's corresponding authors (nima.nouri@sanofi.com) or check their GitHub page.
>
> We provide the results obtained by Sargent in [ENACT's Zenodo page](https://doi.org/10.5281/zenodo.15211043) under the following folders:
>- ENACT_supporting_files/public_data/human_colorectal/paper_results/chunks/naive/sargent_results/
>- ENACT_supporting_files/public_data/human_colorectal/paper_results/chunks/weighted_by_area/sargent_results/
>- ENACT_supporting_files/public_data/human_colorectal/paper_results/chunks/weighted_by_transcript/sargent_results/
>- ENACT_supporting_files/public_data/human_colorectal/paper_results/chunks/weighted_by_cluster/sargent_results/

<!-- 
<div style="text-align: center;">
  <img src="figs/pipelineflow.png" alt="ENACT"/>
</div> -->
![plot](figs/pipelineflow.png)

## Index of Instructions:
1. Installation
   - [System Requirements](#system-requirements)
   - [Install ENACT from Source](#install-enact-from-source)
   - [Install ENACT with Pip](#install-enact-with-pip)
2. Inputs and Outputs
   - [Input Files for ENACT](#input-files-for-enact)
   - [Defining ENACT Configurations](#defining-enact-configurations)
   - [Output Files for ENACT](#output-files-for-enact)
3. Running ENACT
   - [Basic Example: Running ENACT from Notebook](#basic-example-running-enact-from-notebook)
   - [Basic Example: Running ENACT from Terminal](#basic-example-running-enact-from-terminal)
   - [Running Instructions](#running-instructions)
4. Visualizing Outputs
   - [Working with ENACT Output](#working-with-enact-output)
   - [Visualizing Results on TissUUmaps](#visualizing-results-on-tissuumaps)
5. Reproducing Paper Results
   - [Reproducing Paper Results](#reproducing-paper-results)
   - [Creating Synthetic VisiumHD Datasets](#creating-synthetic-visiumhd-datasets)
6. [Citing ENACT](#citing-enact)

## System Requirements
ENACT was tested with the following specifications:
* Hardware Requirements: 32 CPU, 64GB RAM, 100 GB (harddisk and memory requirements may vary depending on whole slide image size; if the weight of the wsi is small the memory requirements can be significantly decreased)

* Software: Python 3.10, (Optional) GPU (CUDA 11)

## Install ENACT from Source 
### Step 1: Clone ENACT repository
```
git clone https://github.com/Sanofi-Public/enact-pipeline.git
cd enact-pipeline
```
### Step 2: Setup Python environment
Start by defining the location and the name of the Conda environment in the `Makefile`:
```
ENV_DIR := /home/oneai/envs/   <---- Conda environment location
PY_ENV_NAME := enact_py_env    <---- Conda environment name
```
Next, run the following Make command to create a Conda environment with all of ENACT's dependencies
```
make setup_py_env
```

## Install ENACT with Pip
ENACT can be installed from [Pypi](https://pypi.org/project/enact-SO/) using:
```
pip install enact-SO
```

## Input Files for ENACT
ENACT requires only three files, which can be obtained from SpaceRanger’s outputs for each experiment:

1. **Whole resolution tissue image**. This will be segmented to obtain the cell boundaries that will be used to aggregate the transcript counts.
2. **tissue_positions.parquet**. This is the file that specifies the *2um* Visium HD bin locations relative to the full resolution image.
3. **filtered_feature_bc_matrix.h5**. This is the .h5 file with the *2um* Visium HD bin counts.

## Defining ENACT Configurations
ENACT users can choose to specify the configurations via one of two ways:

1. Passing them within the class constructor:
```
  from enact.pipeline import ENACT

  so_hd = ENACT(
      cache_dir="/home/oneai/test_cache",
      wsi_path="Visium_HD_Human_Colon_Cancer_tissue_image.btf",
      visiumhd_h5_path="binned_outputs/square_002um/filtered_feature_bc_matrix.h5",
      tissue_positions_path="binned_outputs/square_002um/spatial/tissue_positions.parquet",
      )
```
<details>
  <summary><strong>Full list of ENACT parameters (click to expand)</strong></summary>

  ## Parameters

  - **cache_dir (str)**:  
    Directory to cache ENACT results. This must be specified by the user.

  - **wsi_path (str)**:  
    Path to the Whole Slide Image (WSI) file. This must be provided by the user.

  - **visiumhd_h5_path (str)**:  
    Path to the Visium HD h5 file containing spatial transcriptomics data. This 
    must be provided by the user.

  - **tissue_positions_path (str)**:  
    Path to the tissue positions file that contains spatial locations of barcodes. 
    This must be provided by the user.

  - **analysis_name (str)**:  
    Name of the analysis, used for output directories and results.  
    *Default*: `"enact_demo"`.

  - **seg_method (str)**:  
    Cell segmentation method.  
    *Default*: `"stardist"`.  
    *Options*: `["stardist"]`.

  - **patch_size (int)**:  
    Size of patches (in pixels) to process the image. Use a smaller patch size to 
    reduce memory requirements.  
    *Default*: `4000`.

  - **use_hvg (bool)**:  
    Whether to use highly variable genes (HVG) during the analysis.  
    *Default*: `True`.  
    *Options*: `[True]`.

  - **n_hvg (int)**:  
    Number of highly variable genes to use if `use_hvg` is `True`.  
    *Default*: `1000`.

  - **n_clusters (int)**:  
    Number of clusters. Used only if `bin_to_cell_method` is `"weighted_by_cluster"`.  
    *Default*: `4`.

  - **bin_representation (str)**:  
    Representation type for VisiumHD bins.  
    *Default*: `"polygon"`.  
    *Options*: `["polygon"]`.

  - **bin_to_cell_method (str)**:  
    Method to assign bins to cells.  
    *Default*: `"weighted_by_cluster"`.  
    *Options*: `["naive", "weighted_by_area", "weighted_by_gene", "weighted_by_cluster"]`.

  - **cell_annotation_method (str)**:  
    Method for annotating cell types.  
    *Default*: `"celltypist"`.  
    *Options*: `["celltypist", "sargent" (if installed), "cellassign"]`.

  - **cell_typist_model (str)**:  
    Path to the pre-trained CellTypist model for cell type annotation. Only used if 
    `cell_annotation_method` is `"celltypist"`.  
    Refer to [CellTypist Models](https://www.celltypist.org/models) for a list of 
    available models.  
    *Default*: `""` (empty string).

  - **run_synthetic (bool)**:  
    Whether to run synthetic data generation for testing purposes.  
    *Default*: `False`.

  - **segmentation (bool)**:  
    Flag to run the image segmentation step.  
    *Default*: `True`.

  - **bin_to_geodataframes (bool)**:  
    Flag to convert the bins to GeoDataFrames.  
    *Default*: `True`.

  - **bin_to_cell_assignment (bool)**:  
    Flag to run bin-to-cell assignment.  
    *Default*: `True`.

  - **cell_type_annotation (bool)**:  
    Flag to run cell type annotation.  
    *Default*: `True`.

  - **cell_markers (dict)**:  
    A dictionary of cell markers used for annotation. Only used if `cell_annotation_method` 
    is one of `["sargent", "cellassign"]`.

  - **chunks_to_run (list)**:  
    Specific chunks of data to run the analysis on, typically for debugging.  
    *Default*: `[]` (runs all chunks).

  - **configs_dict (dict)**:  
    Dictionary containing ENACT configuration parameters. If provided, the values 
    in `configs_dict` will override any corresponding parameters passed directly 
    to the class constructor. This is useful for running ENACT with a predefined 
    configuration for convenience and consistency.  
    *Default*: `{}` (uses the parameters specified in the class constructor).

</details>

2. Specifying configurations in a `yaml` file: (sample file located under `config/configs.yaml`):
```yaml
    analysis_name: <analysis-name>                              <---- custom name for analysis. Will create a folder with that name to store the results
    run_synthetic: False                                        <---- True if you want to run bin to cell assignment on synthetic dataset, False otherwise
    cache_dir: <path-to-store-enact-outputs>                    <---- path to store pipeline outputs
    paths:
        wsi_path: <path-to-whole-slide-image>                   <---- path to whole slide image
        visiumhd_h5_path: <path-to-counts-file>                 <---- location of the 2um x 2um gene by bin file (filtered_feature_bc_matrix.h5) from 10X Genomics 
        tissue_positions_path: <path-to-tissue-positions>       <---- location of the tissue of the tissue_positions.parquet file from 10X genomicsgenomics
    steps:
        segmentation: True                                      <---- True if you want to run segmentation
        bin_to_geodataframes: True                              <---- True to convert bin to geodataframes
        bin_to_cell_assignment: True                            <---- True to bin-to-cell assignment
        cell_type_annotation: True                              <---- True to run cell type annotation
    params:
      bin_to_cell_method: "weighted_by_cluster"                 <---- bin-to-cell assignment method. Pick one of ["naive", "weighted_by_area", "weighted_by_gene", "weighted_by_cluster"]
      cell_annotation_method: "celltypist"                      <---- cell annotation method. Pick one of ["cellassign", "celltypist"]
      cell_typist_model: "Human_Colorectal_Cancer.pkl"          <---- CellTypist model weights to use. Update based on organ of interest if cell_annotation_method is set to "celltypist"
      seg_method: "stardist"                                    <---- cell segmentation method. Stardist is the only option for now
      image_type: "he"                                          <---- image type. Options are ["he", "if"] (for H&E image or IF image, respectively.) 
      nucleus_expansion: True                                   <---- flag to enable nuclei expansion to get cell boundaries. Default is True.
      expand_by_nbins: 2                                        <---- number of bins to expand the nuclei by to get cell boundaries. Default is 2 bins.
      patch_size: 4000                                          <---- defines the patch size. The whole resolution image will be broken into patches of this size. Reduce if you run into memory issues
      use_hvg: True                                             <---- True only run analysis on top n highly variable genes. Setting it to False runs ENACT on all genes in the counts file
      n_hvg: 1000                                               <---- number of highly variable genes to use. Default is 1000.
      destripe_norm: False                                      <---- flag to enable destripe normalization (Bin2cell normalization). Recommend enable only for CellTypist. Disable for Sargent.
      n_clusters: 4                                             <---- number of cell clusters to use for the "weighted_by_cluster" method. Default is 4.
      n_pcs: 250                                                <---- number of principal components before clustering for Weighted-by-Cluster. Default is 250.
  stardist:
      block_size: 4096                                          <---- the size of image blocks the model processes at a time
      prob_thresh: 0.005                                        <---- value between 0 and 1, higher values lead to fewer segmented objects, but will likely avoid false positives
      overlap_thresh: 0.001                                     <---- value between 0 and 1, higher values allow segmented objects to overlap substantially
      min_overlap: 128                                          <---- overlap between blocks, should it be larger than the size of a cell
      context: 128                                              <---- context pixels around the blocks to be included during prediction
      n_tiles: (4,4,1)                                          <---- the input image is broken up into (overlapping) tiles that are processed independently and re-assembled. This parameter denotes a tuple of the number of tiles for every image axis
      stardist_modelname: "2D_versatile_he"                     <---- Specify one of the available Stardist models. 2D_versatile_fluo (for IF images) or 2D_versatile_he (for H&E images)
      channel_to_segment: 2                                     <---- Only applicable for IF images. This is the image channel to segment (usually the DAPI channel)
  cell_markers:                                                 <---- cell-gene markers to use for cell annotation. Only applicable if params/cell_annotation_method is "cellassign" or "sargent". No need to specify for "CellTypist"
      Epithelial: ["CDH1","EPCAM","CLDN1","CD2"]
      Enterocytes: ["CD55", "ELF3", "PLIN2", "GSTM3", "KLF5", "CBR1", "APOA1", "CA1", "PDHA1", "EHF"]
      Goblet cells: ["MANF", "KRT7", "AQP3", "AGR2", "BACE2", "TFF3", "PHGR1", "MUC4", "MUC13", "GUCA2A"]
```

## Output Files for ENACT
ENACT outputs all its results under the `cache` directory which gets automatically created at run time:
```
.
└── cache/
    └── <anaylsis_name> /
        ├── chunks/					# ENACT results at a chunck level
        │   ├── bins_gdf/
        │   │   └── patch_<patch_id>.csv
        │   ├── cells_gdf/
        │   │   └── patch_<patch_id>.csv
        │   └── <bin_to_cell_method>/
        │       ├── bin_to_cell_assign/
        │       │   └── patch_<patch_id>.csv
        │       ├── cell_ix_lookup/
        │       │   └── patch_<patch_id>.csv
        │       └── <cell_annotation_method>_results/
        │           ├── cells_adata.csv
        │           └── merged_results.csv
        ├── tmap/					# Directory storing files to visualize results on TissUUmaps
        │   ├── <run_name>_adata.h5
        │   ├── <run_name>_tmap.tmap
        │   ├── cells_layer.png
        │   └── wsi.tif
        └── cells_df.csv				# cells dataframe, each row is a cell with its coordinates
```
ENACT breaks down the whole resolution image into "chunks" (or patches) of size `patch_size`. Results are provided per-chunk under the `chunks` directory.
* `bins_gdf`:Folder containing GeoPandas dataframes representing the 2um Visium HD bins within a given patch
* `cells_gdf`: Folder containing GeoPandas dataframes representing cells segmented in the tissue
* `<bin_to_cell_method>/bin_to_cell_assign`: Folder contains dataframes with the transcripts assigned to each cells
* `<bin_to_cell_method>/cell_ix_lookup`: Folder contains dataframes defining the indices and coordinates of the cells
* `<bin_to_cell_method>/<cell_annotation_method>_results/cells_adata.csv`: Anndata object containing the results from ENACT (cell coordinates, cell types, transcript counts)
* <`bin_to_cell_method>/<cell_annotation_method>_results/merged_results.csv`: Dataframe (.csv) containing the results from ENACT (cell coordinates, cell types)

## Basic Example: Running ENACT from Notebook
The **[demo notebook](ENACT_demo.ipynb)** provides a step-by-step guide on how to install and run ENACT on VisiumHD public data using notebook. The **[output processing demo notebook](ENACT_outputs_demo.ipynb)** provides a comprehensive, step-by-step guide on how the user can use the generated data for further downstream analysis (see [Working with ENACT Output](#working-with-enact-output) for additional details)

## Basic Example: Running ENACT from Terminal
This section provides a guide for running ENACT on the [Human Colorectal Cancer sample](https://www.10xgenomics.com/datasets/visium-hd-cytassist-gene-expression-libraries-of-human-crc) provided on 10X Genomics' website.
### Step 1: Install ENACT from Source 
Refer to [Install ENACT from Source](#install-enact-from-source)

### Step 2: Download the necessary files from the 10X Genomics website:

1.  Whole slide image: full resolution tissue image
```
curl -O https://cf.10xgenomics.com/samples/spatial-exp/3.0.0/Visium_HD_Human_Colon_Cancer/Visium_HD_Human_Colon_Cancer_tissue_image.btf
```

2. Visium HD output file. The transcript counts are provided in a .tar.gz file that needs to be extracted:
```
curl -O https://cf.10xgenomics.com/samples/spatial-exp/3.0.0/Visium_HD_Human_Colon_Cancer/Visium_HD_Human_Colon_Cancer_binned_outputs.tar.gz
tar -xvzf Visium_HD_Human_Colon_Cancer_binned_outputs.tar.gz
```
Locate the following two files from the extracted outputs file.
```
.
└── binned_outputs/
    └── square_002um/
        ├── filtered_feature_bc_matrix.h5   <---- Transcript counts file (2um resolution)
        └── spatial/
            └── tissue_positions.parquet    <---- Bin locations relative to the full resolution image
```

### Step 3: Update input file locations and parameters under `config/configs.yaml`

Refer to [Running Instructions](#running-instructions) for a full list of ENACT parameters to change.

Below is a sample configuration file to use to run ENACT on the Human Colorectal cancer sample:

```yaml
analysis_name: "colon-demo"
run_synthetic: False # True if you want to run bin to cell assignment on synthetic dataset, False otherwise.
cache_dir: "cache/ENACT_outputs"                                                                          # Change according to your desired output location
paths:  
  wsi_path: "<path_to_data>/Visium_HD_Human_Colon_Cancer_tissue_image.btf"                                # whole slide image path
  visiumhd_h5_path: "<path_to_data>/binned_outputs/square_002um/filtered_feature_bc_matrix.h5"            # location of the 2um x 2um gene by bin file (filtered_feature_bc_matrix.h5) from 10X Genomics.   
  tissue_positions_path: "<path_to_data>/binned_outputs/square_002um/spatial/tissue_positions.parquet"    # location of the tissue of the tissue_positions.parquet file from 10X genomics
steps:
  segmentation: True # True if you want to run segmentation
  bin_to_geodataframes: True # True to convert bin to geodataframes
  bin_to_cell_assignment: True # True to assign cells to bins
  cell_type_annotation: True # True to run cell type annotation
params:
  seg_method: "stardist" # Stardist is the only option for now
  image_type: "if" # Image type: Options: ["he", "if"] (for H&E image or IF image, respectively.) 
  nucleus_expansion: True # Flag to enable nuclei expansion to get cell boundaries
  expand_by_nbins: 2 # Number of bins to expand the nuclei by to get cell boundaries
  patch_size: 4000 # Defines the patch size. The whole resolution image will be broken into patches of this size
  bin_representation: "polygon"  # or point TODO: Remove support for anything else
  bin_to_cell_method: "weighted_by_cluster" # or naive
  cell_annotation_method: "celltypist"
  cell_typist_model: "Human_Colorectal_Cancer.pkl"
  use_hvg: True # Only run analysis on highly variable genes + cell markers specified
  n_hvg: 1000 # Number of highly variable genes to use
  n_clusters: 4 # Number of clusters for Weighted-by-Cluster
  n_pcs: 250 # Number of principal components before clustering for Weighted-by-Cluster
  chunks_to_run: []
stardist:
  block_size: 4096 # the size of image blocks the model processes at a time
  prob_thresh: 0.005 # value between 0 and 1, higher values lead to fewer segmented objects, but will likely avoid false positives
  overlap_thresh: 0.001 # value between 0 and 1, higher values allow segmented objects to overlap substantially
  min_overlap: 128 # overlap between blocks, should it be larger than the size of a cell
  context: 128 # context pixels around the blocks to be included during prediction
  n_tiles: (4,4,1) #the input image is broken up into (overlapping) tiles that are processed independently and re-assembled. This parameter denotes a tuple of the number of tiles for every image axis
  stardist_modelname: "2D_versatile_fluo" # Specify one of the available Stardist models: 2D_versatile_fluo (for IF images) or 2D_versatile_he (for H&E images)
  channel_to_segment: 2 # Only applicable for IF images. This is the image channel to segment (usually the DAPI channel)
cell_markers: # Only needed if cell_annotation_method is one of "Sargent" or "CellAssign"
  # Human Colon
  Epithelial: ["CDH1","EPCAM","CLDN1","CD2"]
  Enterocytes: ["CD55", "ELF3", "PLIN2", "GSTM3", "KLF5", "CBR1", "APOA1", "CA1", "PDHA1", "EHF"]
  Goblet cells: ["MANF", "KRT7", "AQP3", "AGR2", "BACE2", "TFF3", "PHGR1", "MUC4", "MUC13", "GUCA2A"]
  Enteroendocrine cells: ["NUCB2", "FABP5", "CPE", "ALCAM", "GCG", "SST", "CHGB", "IAPP", "CHGA", "ENPP2"]
  Crypt cells: ["HOPX", "SLC12A2", "MSI1", "SMOC2", "OLFM4", "ASCL2", "PROM1", "BMI1", "EPHB2", "LRIG1"]
  Endothelial: ["PECAM1","CD34","KDR","CDH5","PROM1","PDPN","TEK","FLT1","VCAM1","PTPRC","VWF","ENG","MCAM","ICAM1","FLT4"]     
  Fibroblast: ["COL1A1","COL3A1","COL5A2","PDGFRA","ACTA2","TCF21","FN"]
  Smooth muscle cell: ["BGN","MYL9","MYLK","FHL2","ITGA1","ACTA2","EHD2","OGN","SNCG","FABP4"]
  B cells: ["CD74", "HMGA1", "CD52", "PTPRC", "HLA-DRA", "CD24", "CXCR4", "SPCS3", "LTB", "IGKC"]
  T cells: ["JUNB", "S100A4", "CD52", "PFN1P1", "CD81", "EEF1B2P3", "CXCR4", "CREM", "IL32", "TGIF1"]
  NK cells: ["S100A4", "IL32", "CXCR4", "FHL2", "IL2RG", "CD69", "CD7", "NKG7", "CD2", "HOPX"]

```

## Running Instructions
This section provides a guide on running ENACT on your own data
### Step 1: Install ENACT from Source 
Refer to [Install ENACT from Source](#install-enact-from-source)

### Step 2: Define the Location of ENACT's Required Files
Define the locations of ENACT's required files in the `config/configs.yaml` file. Refer to [Input Files for ENACT](#input-files-for-enact)
```yaml
    analysis_name: <analysis-name>                              <---- custom name for analysis. Will create a folder with that name to store the results
    cache_dir: <path-to-store-enact-outputs>                    <---- path to store pipeline outputs
    paths:
        wsi_path: <path-to-whole-slide-image>                   <---- path to whole slide image
        visiumhd_h5_path: <path-to-counts-file>                 <---- location of the 2um x 2um gene by bin file (filtered_feature_bc_matrix.h5) from 10X Genomics. 
        tissue_positions_path: <path-to-tissue-positions>       <---- location of the tissue of the tissue_positions.parquet file from 10X genomics
```

### Step 3: Define ENACT configurations
Define the following core parameters in the `config/configs.yaml` file:
```yaml
    params:
      bin_to_cell_method: "weighted_by_cluster"                 <---- bin-to-cell assignment method. Pick one of ["naive", "weighted_by_area", "weighted_by_gene", "weighted_by_cluster"]
      cell_annotation_method: "celltypist"                      <---- cell annotation method. Pick one of ["cellassign", "celltypist", "sargent" (if installed)]
      cell_typist_model: "Human_Colorectal_Cancer.pkl"          <---- CellTypist model weights to use. Update based on organ of interest if using cell_annotation_method is set to
```
Refer to [Defining ENACT Configurations](#defining-enact-configurations) for a full list of parameters to configure. If using CellTypist, set `cell_typist_model` to one of the following models based on the organ and species under study: [CellTypist models](https://www.celltypist.org/models#:~:text=CellTypist%20was%20first%20developed%20as%20a%20platform%20for). 

### Step 4: Define Cell Gene Markers
>[!NOTE]
>Only applies if cell_annotation_method is "cellassign" or "sargent". Skip this step if using CellTypist

Define the cell gene markers in `config/configs.yaml` file. Those can be expert annotated or obtained from open-source databases such as [Panglao](https://panglaodb.se/index.html) or [CellMarker](http://xteam.xbio.top/CellMarker/). Example cell markers for human colorectal cancer samples:
```yaml
  cell_markers:
    Epithelial: ["CDH1","EPCAM","CLDN1","CD2"]
    Enterocytes: ["CD55", "ELF3", "PLIN2", "GSTM3", "KLF5", "CBR1", "APOA1", "CA1", "PDHA1", "EHF"]
    Goblet cells: ["MANF", "KRT7", "AQP3", "AGR2", "BACE2", "TFF3", "PHGR1", "MUC4", "MUC13", "GUCA2A"]
    Enteroendocrine cells: ["NUCB2", "FABP5", "CPE", "ALCAM", "GCG", "SST", "CHGB", "IAPP", "CHGA", "ENPP2"]
    Crypt cells: ["HOPX", "SLC12A2", "MSI1", "SMOC2", "OLFM4", "ASCL2", "PROM1", "BMI1", "EPHB2", "LRIG1"]
    Endothelial: ["PECAM1","CD34","KDR","CDH5","PROM1","PDPN","TEK","FLT1","VCAM1","PTPRC","VWF","ENG","MCAM","ICAM1","FLT4"]     
    Fibroblast: ["COL1A1","COL3A1","COL5A2","PDGFRA","ACTA2","TCF21","FN"]
    Smooth muscle cell: ["BGN","MYL9","MYLK","FHL2","ITGA1","ACTA2","EHD2","OGN","SNCG","FABP4"]
    B cells: ["CD74", "HMGA1", "CD52", "PTPRC", "HLA-DRA", "CD24", "CXCR4", "SPCS3", "LTB", "IGKC"]
    T cells: ["JUNB", "S100A4", "CD52", "PFN1P1", "CD81", "EEF1B2P3", "CXCR4", "CREM", "IL32", "TGIF1"]
    NK cells: ["S100A4", "IL32", "CXCR4", "FHL2", "IL2RG", "CD69", "CD7", "NKG7", "CD2", "HOPX"]
```
### Step 5: Run ENACT
```
make run_enact
```

## Working with ENACT Output

The **[output demo notebook](ENACT_outputs_demo.ipynb)** provides a comprehensive, step-by-step guide on how to access and analyze output data from ENACT. The notebook covers the following topics:

- **Loading the AnnData object in Python**  
  Learn how to load the main data structure for single-cell analysis.

- **Extracting cell types and their spatial coordinates**  
  Access information about cell types and their positions in the tissue.

- **Determining the number of shared and unique bins per cell**  
  Explore metrics that characterize the bin and cell relationships.

- **Accessing and visualizing the number of transcripts per cell**  
  Visualize and analyze transcriptional activity across cells.

- **Identifying the top-n expressed genes in the sample**  
  Retrieve the most highly expressed genes in your dataset.

- **Generating interactive plots**  
  Visualize cell boundaries and cell types within the tissue using interactive visualizations.

- **Performing downstream analysis**  
  Run a sample analysis, such as neighborhood enrichment analysis, using external packages like **Squidpy**.

This notebook serves as a helpful resource for navigating and analyzing ENACT output data effectively.


## Visualizing Results on TissUUmaps
To view results on [TissUUmaps](https://tissuumaps.github.io), begin by installing TissUUmaps by following the instructions at:
https://tissuumaps.github.io/TissUUmaps-docs/docs/intro/installation.html#. 
            
Once installed, follow the instructions at: https://tissuumaps.github.io/TissUUmaps-docs/docs/starting/projects.html#loading-projects
            
For convenience, ENACT creates a TissUUmaps project file (.tmap extension) located at under the `<cache_dir>/tmap/` folder.
<!-- 
<div style="text-align: center;">
  <img src="figs/tissuumaps.png" alt="tissuumaps"/>
</div> -->
![plot](figs/tissuumaps.png)

## Reproducing Paper Results
This section provides a guide on how to reproduce the ENACT paper results on the [10X Genomics Human Colorectal Cancer VisumHD sample](https://www.10xgenomics.com/datasets/visium-hd-cytassist-gene-expression-libraries-of-human-crc). 
Here, ENACT is run on various combinations of bin-to-cell assignment methods and cell annotation algorithms.

### Step 1: Install ENACT from Source 
Refer to [Install ENACT from Source](#install-enact-from-source)

### Step 2: Run ENACT on combinations of bin-to-cell assignment methods and cell annotation algorithms
3. Run the following command which will download all the supplementary file from [ENACT's Zenodo page](https://doi.org/10.5281/zenodo.15211043) and programmatically run ENACT with various combinations of bin-to-cell assignment methods and cell annotation algorithms:
```
make reproduce_results
```

## Creating Synthetic VisiumHD Datasets

1. To create synthetic VisiumHD dataset from Xenium or seqFISH+ data, run and follow the instructions of the notebooks in [src/synthetic_data](src/synthetic_data).

2. To run the ENACT pipeline with the synthetic data, set the following parameters in the `config/configs.yaml` file: 

```yaml
run_synthetic: True                                        <---- True if you want to run bin to cell assignment on synthetic dataset, False otherwise.
```
    
3. Run ENACT:
```
make run_enact
```

 ## Citing ENACT
 If you use this repository or its tools in your research, please cite the following:
 ```
  @article{10.1093/bioinformatics/btaf094,
  author = {Kamel, Mena and Song, Yiwen and Solbas, Ana and Villordo, Sergio and Sarangi, Amrut and Senin, Pavel and Sunaal, Mathew and Ayestas, Luis Cano and Levin, Clement and Wang, Seqianand Classe, Marion and Bar-Joseph, Ziv and Pla Planas, Albert},
  title = {ENACT: End-to-end Analysis of Visium High Definition (HD) Data},
  journal = {Bioinformatics},
  pages = {btaf094},
  year = {2025},
  month = {03},
  abstract = {Spatial transcriptomics (ST) enables the study of gene expression within its spatial context in histopathology samples. To date, a limiting factor has been the resolution of sequencing based ST products. The introduction of the Visium High Definition (HD) technology opens the door to cell resolution ST studies. However, challenges remain in the ability to accurately map transcripts to cells and in assigning cell types based on the transcript data.We developed ENACT, a self-contained pipeline that integrates advanced cell segmentation with Visium HD transcriptomics data to infer cell types across whole tissue sections. Our pipeline incorporates novel bin-to-cell assignment methods, enhancing the accuracy of single-cell transcript estimates. Validated on diverse synthetic and real datasets, our approach is both scalableto samples with hundreds of thousands of cells and effective, offering a robust solution for spatially resolved transcriptomics analysis.ENACT source code is available at https://github.com/Sanofi-Public/enact-pipeline. Experimental data is available at https://doi.org/10.5281/zenodo.15211043.Supplementary data are available at Bioinformatics online.},
  issn = {1367-4811},
  doi = {10.1093/bioinformatics/btaf094},
  url = {https://doi.org/10.1093/bioinformatics/btaf094},
  eprint = {https://academic.oup.com/bioinformatics/advance-article-pdf/doi/10.1093/bioinformatics/btaf094/62340410/btaf094.pdf},
  }
 ```
