#!/bin/bash
exec > >(tee -a pipeline.log) 2>&1

# Use the root .ml-venv environment
ENV_PYTHON="../.ml-venv/bin/python"

echo "Starting data processing..."
$ENV_PYTHON src/1_data_processing.py

echo "Starting embedding..."
$ENV_PYTHON src/2_embedding.py

echo "Starting PCA..."
$ENV_PYTHON src/4_pca.py

echo "Starting full clustering..."
$ENV_PYTHON src/6b_clustering_full.py

echo "Pipeline finished successfully!"
