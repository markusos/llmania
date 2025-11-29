import argparse
import multiprocessing
import os
import subprocess
import sys
from functools import partial
from typing import Dict, Literal

# Add project root to the Python path
sys.path.insert(0, ".")

# Define result types
ResultType = Literal["win", "loss", "timeout", "crash"]

LOG_DIR = "benchmark_logs"
CRASH_LOG_DIR = "crash_logs"
for d in [LOG_DIR, CRASH_LOG_DIR]:
    if not os.path.exists(d):
        os.makedirs(d)


def run_game_with_timeout(
    seed: int,
    timeout_seconds: int = 1,
    log_limit: int = 1000,
) -> tuple[ResultType, int]:
    """
    Runs the game in a separate process with a timeout.

    Args:
        seed: The seed for the random number generator.
        timeout_seconds: The timeout in seconds.
        log_limit: The maximum number of logs to save for losses and timeouts.

    Returns:
        A tuple containing the result of the game run and the seed.
    """
    command = [
        "uv",
        "run",
        "python",
        "src/main.py",
        "--ai",
        "--seed",
        str(seed),
        "--debug",
        "--verbose",
    ]
    try:
        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
        output = process.stdout
        error = process.stderr

        if error:
            if seed < log_limit:
                log_file = f"crash_seed_{seed}.log"
                with open(os.path.join(CRASH_LOG_DIR, log_file), "w") as f:
                    f.write("--- STDOUT ---\n")
                    f.write(output)
                    f.write("\n--- STDERR ---\n")
                    f.write(error)
            return "crash", seed

        if "You win!" in output:
            return "win", seed

        if "Game Over" in output:
            if seed < log_limit:
                with open(os.path.join(LOG_DIR, f"loss_seed_{seed}.log"), "w") as f:
                    f.write(output)
            return "loss", seed

        return "loss", seed
    except subprocess.TimeoutExpired as e:
        if seed < log_limit:
            if e.stdout:
                output = e.stdout.decode("utf-8", "ignore")
            else:
                output = "No output captured before timeout."

            log_file = f"timeout_seed_{seed}.log"
            with open(os.path.join(LOG_DIR, log_file), "w") as f:
                f.write(output)
        return "timeout", seed


def main():
    """
    Main function to run the benchmark.
    """
    parser = argparse.ArgumentParser(description="Run AI benchmark")
    parser.add_argument(
        "--seeds",
        type=int,
        default=1000,
        help="Number of seeds to run (default: 1000).",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=1,
        help="Timeout per game in seconds (default: 1).",
    )
    args = parser.parse_args()

    num_seeds = args.seeds
    timeout_seconds = args.timeout

    print(
        f"Running benchmark with Utility AI on {num_seeds} seeds "
        f"(timeout={timeout_seconds}s)..."
    )

    results: Dict[ResultType, int] = {"win": 0, "loss": 0, "timeout": 0, "crash": 0}
    timeout_seeds = []
    crash_seeds = []

    # Create a partial function with the timeout
    run_func = partial(run_game_with_timeout, timeout_seconds=timeout_seconds)

    with multiprocessing.Pool() as pool:
        run_results = pool.map(run_func, range(num_seeds))

    for result, seed in run_results:
        results[result] += 1
        if result == "timeout":
            timeout_seeds.append(seed)
        elif result == "crash":
            crash_seeds.append(seed)

    if timeout_seeds:
        with open("timeout_seeds.txt", "w") as f:
            for seed in timeout_seeds:
                f.write(f"{seed}\n")
        print(f"\nSaved {len(timeout_seeds)} timeout seeds to timeout_seeds.txt")

    if crash_seeds:
        with open("crash_seeds.txt", "w") as f:
            for seed in crash_seeds:
                f.write(f"{seed}\n")
        print(f"Saved {len(crash_seeds)} crash seeds to crash_seeds.txt")

    total_runs = sum(results.values())
    win_percentage = (results["win"] / total_runs) * 100 if total_runs > 0 else 0

    print("\n--- AI Benchmark Results (Utility AI) ---")
    print(f"Total runs: {total_runs}")
    print(f"Wins: {results['win']}")
    print(f"Losses: {results['loss']}")
    print(f"Timeouts: {results['timeout']}")
    print(f"Crashes: {results['crash']}")
    print(f"Win percentage: {win_percentage:.2f}%")


if __name__ == "__main__":
    main()
