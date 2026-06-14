package main

import (
	"context"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"dagger.io/dagger"
)

const (
	appDir           = "/app"
	vaultMountDir    = "/tmp/vault"
	vectorstoreDir   = "/app/data/vectorstore"
	quickEvalPath    = "data/test/quick_eval_set.json"
	baselineEvalPath = "data/test/baseline_eval_set.json"
	defaultMode      = "quick"
)

func main() {
	ctx := context.Background()

	client, err := dagger.Connect(ctx, dagger.WithLogOutput(os.Stderr))
	if err != nil {
		panic(err)
	}
	defer client.Close()

	mode := defaultMode
	if len(os.Args) > 1 {
		mode = os.Args[1]
	}

	togetherAPIKey := os.Getenv("TOGETHER_API_KEY")
	if togetherAPIKey == "" {
		fmt.Println("❌ TOGETHER_API_KEY is not set.")
		os.Exit(1)
	}

	// 🛡️ MLflow Network Bridge Configuration
	mlflowURI := os.Getenv("MLFLOW_TRACKING_URI")
	if mlflowURI == "" {
		mlflowURI = "http://host.docker.internal:5000"
	} else if strings.Contains(mlflowURI, "localhost") || strings.Contains(mlflowURI, "127.0.0.1") {
		mlflowURI = strings.ReplaceAll(mlflowURI, "localhost", "host.docker.internal")
		mlflowURI = strings.ReplaceAll(mlflowURI, "127.0.0.1", "host.docker.internal")
		fmt.Printf("🔄 [Network Bridge] Patched local MLflow URI tracking endpoint to: %s\n", mlflowURI)
	}

	// --- SOURCE ---
	src := client.Host().Directory(".", dagger.HostDirectoryOpts{
		Exclude: []string{
			".git",
			".venv",
			".pytest_cache",
			"__pycache__",
			"mlruns",
			"mlartifacts",
			"mlflow.db",
		},
	})

	homeDir, err := os.UserHomeDir()
	if err != nil {
		panic(err)
	}

	vaultPath := filepath.Join(homeDir, "lexguard_dvc_vault")
	vault := client.Host().Directory(vaultPath)

	secret := client.SetSecret("together_api_key", togetherAPIKey)

	base := src.DockerBuild().
		WithMountedDirectory(appDir, src).
		WithMountedDirectory(vaultMountDir, vault).
		WithWorkdir(appDir).
		WithEnvVariable("PYTHONPATH", appDir).
		WithEnvVariable("MLFLOW_TRACKING_URI", mlflowURI).
		WithSecretVariable("TOGETHER_API_KEY", secret)

	// --- ROUTING ---
	switch mode {
	case "quick":
		fmt.Println("🚀 Running QUICK pipeline...")
		err = runPipeline(ctx, base, quickEvalPath, "quick_eval")

	case "baseline":
		fmt.Println("🚀 Running BASELINE pipeline...")
		err = runPipeline(ctx, base, baselineEvalPath, "baseline_eval")

	default:
		fmt.Printf("❌ Unknown mode: %s\n", mode)
		os.Exit(1)
	}

	if err != nil {
		fmt.Printf("❌ Pipeline failed: %v\n", err)
		os.Exit(1)
	}

	fmt.Println("🎉 Pipeline PASSED")
}

func runPipeline(ctx context.Context, base *dagger.Container, evalSet string, runName string) error {
	// 🛡️ Sequentially run Pytest, then execute the MLflow Evaluation Script
	container := ensureVectorstore(base).
		WithExec([]string{
			"sh", "-lc",
			"PYTHONPATH=/app uv run pytest tests/ -v",
		}).
		WithExec([]string{
			"sh", "-lc",
			fmt.Sprintf(
				"PYTHONPATH=/app uv run python src/evaluation/evaluate.py --eval-set %s --run-name %s",
				evalSet,
				runName,
			),
		})

	out, err := container.Stdout(ctx)
	if err != nil {
		return err
	}

	fmt.Println(out)
	return nil
}

func ensureVectorstore(base *dagger.Container) *dagger.Container {
	// 🛡️ Dynamic DVC Vault Loader
	cmd := `
if [ -d "` + vectorstoreDir + `" ] && [ "$(ls -A ` + vectorstoreDir + ` 2>/dev/null)" ]; then
  echo "✅ Vectorstore exists. Skipping DVC pull."
else
  echo "📦 Vectorstore missing. Pulling..."
  uv run dvc remote add -d -f my_local_vault ` + vaultMountDir + `
  uv run dvc pull
fi
`
	return base.WithExec([]string{"sh", "-lc", cmd})
}