#!/bin/bash
#SBATCH --job-name=lexguard_ingest
#SBATCH --partition=dgpu
#SBATCH --account=researchers
#SBATCH --gres=gpu:1
#SBATCH --time=00:20:00
#SBATCH --output=ingestion_results.log

module purge
module load Python/3.12.3
module load CUDA/12.1.1

cd "$SLURM_SUBMIT_DIR" || exit 1

source .venv/bin/activate

uv sync

python infrastructure/check_env.py

echo "🚀 Starting Ingestion..."
uv run python src/ingestion/embed.py
