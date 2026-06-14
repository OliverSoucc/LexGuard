import argparse
import json
import sys
from pathlib import Path

import mlflow

from src.agents.graph import lexguard_app
from src.config import (
    BASELINE_EVAL_SET_PATH,
    MLFLOW_TRACKING_URI,
    EXPERIMENT_EVALUATION,
    EVAL_PASS_THRESHOLD,
)

mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
mlflow.set_experiment(EXPERIMENT_EVALUATION)



def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run LexGuard evaluation suite.")
    parser.add_argument(
        "--eval-set",
        type=Path,
        default=BASELINE_EVAL_SET_PATH,
        help="Path to evaluation JSON file.",
    )
    parser.add_argument(
        "--run-name",
        type=str,
        default=None,
        help="Optional MLflow run name. If omitted, a name is derived from the eval file name.",
    )
    return parser.parse_args()


def load_eval_data(eval_set_path: Path) -> list[dict]:
    if not eval_set_path.exists():
        print(f"❌ Error: Could not find eval set at {eval_set_path}")
        sys.exit(1)

    with open(eval_set_path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_evaluation(eval_set_path: Path, run_name: str | None = None) -> int:
    print("\n" + "=" * 60)
    print("🧪 Starting LexGuard Automated Evaluation")
    print(f"📂 Eval set: {eval_set_path}")
    print("=" * 60 + "\n")

    eval_data = load_eval_data(eval_set_path)
    passed_tests = 0
    total_tests = len(eval_data)

    if total_tests == 0:
        print("❌ Eval set is empty.")
        return 1

    resolved_run_name = run_name or f"eval::{eval_set_path.stem}"

    with mlflow.start_run(run_name=resolved_run_name):
        mlflow.log_param("eval_set_path", str(eval_set_path))
        mlflow.log_param("eval_set_name", eval_set_path.name)
        mlflow.log_param("eval_set_size", total_tests)
        mlflow.log_param("pass_threshold", EVAL_PASS_THRESHOLD)

        for idx, test in enumerate(eval_data, 1):
            print(f"Running Test {idx}/{total_tests}: {test['id']} ...")

            initial_state = {
                "question": test["question"],
                "context": "",
                "draft_answer": "",
                "critique": "",
                "status": "",
                "retry_count": 0,
                "is_safe": True,
            }

            final_state = lexguard_app.invoke(initial_state)
            test_passed = True

            expected_is_safe = test["expected_is_safe"]
            actual_is_safe = final_state["is_safe"]

            if actual_is_safe != expected_is_safe:
                print(f"  ❌ FAILED: Expected is_safe={expected_is_safe}, got {actual_is_safe}")
                test_passed = False
            else:
                print(f"  ✅ Guardrail acted correctly (is_safe={actual_is_safe})")

            draft_answer = final_state["draft_answer"]
            expected_substring = test["expected_substring"]

            if expected_substring not in draft_answer:
                print(f"  ❌ FAILED: Missing required substring: '{expected_substring}'")
                test_passed = False
            else:
                print("  ✅ Output contains required substring.")

            if test_passed:
                print("  ✅ TEST PASSED")
                passed_tests += 1

            print("-" * 40)

            running_accuracy = passed_tests / idx
            mlflow.log_metric("running_accuracy", running_accuracy, step=idx)
            mlflow.log_metric("passed_tests", passed_tests, step=idx)
            mlflow.log_metric("total_tests", total_tests, step=idx)

    accuracy = passed_tests / total_tests

    print("\n" + "=" * 60)
    print(f"🏆 EVALUATION COMPLETE: {passed_tests}/{total_tests} Passed ({accuracy * 100:.1f}%)")
    print("=" * 60 + "\n")

    if accuracy < EVAL_PASS_THRESHOLD:
        print(
            f"❌ PIPELINE BLOCKED: Accuracy {accuracy * 100:.1f}% "
            f"is below the {(EVAL_PASS_THRESHOLD * 100):.1f}% baseline."
        )
        return 1
    return 0


if __name__ == "__main__":
    args = parse_args()
    sys.exit(run_evaluation(args.eval_set, args.run_name))