import multiprocessing
import subprocess
import sys
from typing import Dict, Literal

# Add project root to the Python path
sys.path.insert(0, ".")

# Define result types
ResultType = Literal["win", "loss", "timeout"]


def run_game_with_timeout(seed: int, timeout_seconds: int = 1) -> ResultType:
    """
    Runs the game in a separate process with a timeout.

    Args:
        seed: The seed for the random number generator.
        timeout_seconds: The timeout in seconds.

    Returns:
        The result of the game run (win, loss, or timeout).
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
        if "You win!" in output:
            return "win"
        elif "Game Over" in output:
            return "loss"
        else:
            # If neither win nor loss is detected, it could be an unexpected state
            # or the game finished without a clear win/loss message.
            # We'll treat this as a loss for benchmarking purposes.
            return "loss"
    except subprocess.TimeoutExpired:
        return "timeout"


def main():
    """
    Main function to run the benchmark.
    """
    num_seeds = 1000
    results: Dict[ResultType, int] = {"win": 0, "loss": 0, "timeout": 0}

    with multiprocessing.Pool() as pool:
        # Use a map to apply the run_game_with_timeout function to each seed
        # and collect the results.
        run_results = pool.map(run_game_with_timeout, range(num_seeds))

    # Count the occurrences of each result type
    for result in run_results:
        results[result] += 1

    # Calculate and print the results
    total_runs = sum(results.values())
    win_percentage = (results["win"] / total_runs) * 100 if total_runs > 0 else 0

    print("\n--- AI Benchmark Results ---")
    print(f"Total runs: {total_runs}")
    print(f"Wins: {results['win']}")
    print(f"Losses: {results['loss']}")
    print(f"Timeouts: {results['timeout']}")
    print(f"Win percentage: {win_percentage:.2f}%")


if __name__ == "__main__":
    main()
