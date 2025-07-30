# DAESIM_preprocess
Harvesting environmental forcing data for running the Dynamic Agro-Ecosystem Simulator (DAESIM)


# Setup locally
1. Download and install Miniconda from https://www.anaconda.com/download/success
2. Add the miniconda filepath to your ~/.zhrc, e.g. export PATH="/opt/miniconda3/bin:$PATH" 
3. brew install gdal
4. git clone https://github.com/ChristopherBradley/DAESIM_preprocess.git
5. cd DAESIM_preprocess
6. conda env create -f environment.yml
7. conda activate DAESIM_preprocess
8. pytest

# Uploading to pip
1. 