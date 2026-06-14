import sys
import torch

dependencies = [
    "chromadb",
    "torch",
    "langchain_chroma",
    "langchain_huggingface",
    "langchain_text_splitters",
    "mlflow"
]

print("🔍 [HPC] Validating AI Environment...")

for dep in dependencies:
    try:
        if dep == "langchain_chroma":
            import langchain_chroma
        elif dep == "langchain_huggingface":
            import langchain_huggingface
        else:
            __import__(dep)
        print(f"✅ {dep:25} is ready.")
    except ImportError as e:
        print(f"❌ ERROR: {dep} is MISSING. (Hint: run 'uv sync' on the HPC)")
        sys.exit(1)

print("\n⚙️  Checking Hardware Acceleration...")
if torch.cuda.is_available():
    gpu_name = torch.cuda.get_device_name(0)
    print(f"✅ CUDA is available!")
    print(f"🚀 Found GPU: {gpu_name}")

    vram = torch.cuda.get_device_properties(0).total_memory / 1e9
    print(f"💾 VRAM: {vram:.2f} GB")
else:
    print("⚠️  CUDA NOT FOUND. The script will run on CPU (Slow).")
    print("👉 Hint: Did you run this inside a Slurm GPU job?")