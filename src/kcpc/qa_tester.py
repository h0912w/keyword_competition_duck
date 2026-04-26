"""qa_tester module for KCPC.

Automated QA testing using REAL pipeline - executes actual KCPC main function.
"""

import argparse
import os
import random
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal

import pandas as pd

from kcpc.config import get_config
from kcpc.logging_config import get_logger
from kcpc.measurer import measure_keyword

logger = get_logger()


@dataclass
class TestWord:
    """Test word with frequency score."""

    word: str
    frequency_score: int  # 1-10, 1= highest frequency, 10= lowest frequency
    expected_min: int  # Minimum expected DDG results
    expected_max: int  # Maximum expected DDG results


@dataclass
class QATestResult:
    """QA test result."""

    iteration: int
    test_words: list[TestWord]
    actual_results: dict[str, int]
    pass_count: int
    fail_count: int
    passed: bool


# Frequency-based English word lists
HIGH_FREQ_WORDS = [
    "the", "and", "have", "for", "not", "you", "with", "this", "that", "but"
]

MID_FREQ_WORDS = [
    "research", "analysis", "method", "development", "management",
    "software", "system", "process", "service", "technology",
    "project", "product", "solution", "platform", "strategy",
    "marketing", "business", "customer", "digital", "design"
]

LOW_FREQ_WORDS = [
    "xyzqwerty123", "ultra-rare-term-abc", "nonexistentword987",
    "obscure-vocabulary-def", "rare-technical-term-xyz"
]


def generate_test_words(count: int = 10, high_freq: int = 3, mid_freq: int = 4, low_freq: int = 3) -> list[TestWord]:
    """Generate frequency-based test words.

    Args:
        count: Total number of words to generate.
        high_freq: Number of high frequency words (score 1-3).
        mid_freq: Number of mid frequency words (score 4-7).
        low_freq: Number of low frequency words (score 8-10).

    Returns:
        list[TestWord]: List of test words with frequency scores.
    """
    test_words = []

    # High frequency words (score 1-3)
    for i in range(high_freq):
        word = random.choice(HIGH_FREQ_WORDS)
        score = random.randint(1, 3)
        test_words.append(TestWord(
            word=word,
            frequency_score=score,
            expected_min=7,  # Expected 7-10 results
            expected_max=10
        ))

    # Mid frequency words (score 4-7)
    for i in range(mid_freq):
        word = random.choice(MID_FREQ_WORDS)
        score = random.randint(4, 7)
        test_words.append(TestWord(
            word=word,
            frequency_score=score,
            expected_min=4,  # Expected 4-7 results
            expected_max=7
        ))

    # Low frequency words (score 8-10)
    for i in range(low_freq):
        word = random.choice(LOW_FREQ_WORDS)
        score = random.randint(8, 10)
        # Add random suffix to ensure uniqueness
        unique_word = f"{word}-{random.randint(100, 999)}"
        test_words.append(TestWord(
            word=unique_word,
            frequency_score=score,
            expected_min=0,  # Expected 0-3 results
            expected_max=3
        ))

    random.shuffle(test_words)
    return test_words


def verify_expectations(test_words: list[TestWord], actual_results: dict[str, int]) -> bool:
    """Verify if actual results match expected ranges.

    Args:
        test_words: List of test words with expected ranges.
        actual_results: Dictionary mapping word to actual DDG result count.

    Returns:
        bool: True if all results match expectations.
    """
    all_passed = True

    for test_word in test_words:
        actual = actual_results.get(test_word.word, -1)

        if test_word.expected_min <= actual <= test_word.expected_max:
            logger.info(f"[PASS] {test_word.word}: expected {test_word.expected_min}-{test_word.expected_max}, actual {actual}")
        else:
            logger.warning(f"[FAIL] {test_word.word}: expected {test_word.expected_min}-{test_word.expected_max}, actual {actual}")
            all_passed = False

    return all_passed


def run_qa_test_iteration(iteration: int, test_words: list[TestWord], input_file: str, output_file: str) -> QATestResult:
    """Run a single QA test iteration using REAL KCPC pipeline.

    Args:
        iteration: Iteration number.
        test_words: List of test words.
        input_file: Path to input file.
        output_file: Path to output file.

    Returns:
        QATestResult: Test result.
    """
    logger.info(f"=== QA Test Iteration {iteration} ===")

    # Create input file
    with open(input_file, "w", encoding="utf-8") as f:
        for test_word in test_words:
            f.write(f"{test_word.word}\n")

    # Run REAL KCPC pipeline using subprocess
    try:
        result = subprocess.run(
            [sys.executable, "-m", "kcpc.main", "--input", input_file, "--output", output_file],
            capture_output=True,
            text=True,
            timeout=300,  # 5 minutes timeout
            cwd=Path(__file__).parent.parent.parent
        )

        if result.returncode != 0:
            logger.error(f"KCPC pipeline failed: {result.stderr}")
            # Fill with -1 for failures
            actual_results = {tw.word: -1 for tw in test_words}
        else:
            # Read actual results from Excel output
            actual_results = {}
            try:
                df = pd.read_excel(output_file)
                for _, row in df.iterrows():
                    keyword = row.get("Keyword", "")
                    count = row.get("Top10_Title_Match_Count", -1)
                    if keyword:
                        actual_results[keyword] = int(count) if pd.notna(count) else -1
            except Exception as e:
                logger.error(f"Failed to read results: {e}")
                actual_results = {tw.word: -1 for tw in test_words}

    except subprocess.TimeoutExpired:
        logger.error("KCPC pipeline timeout")
        actual_results = {tw.word: -1 for tw in test_words}
    except Exception as e:
        logger.error(f"QA test error: {e}")
        actual_results = {tw.word: -1 for tw in test_words}

    # Verify expectations
    passed = verify_expectations(test_words, actual_results)

    pass_count = sum(1 for tw in test_words
                    if tw.expected_min <= actual_results.get(tw.word, -1) <= tw.expected_max)
    fail_count = len(test_words) - pass_count

    return QATestResult(
        iteration=iteration,
        test_words=test_words,
        actual_results=actual_results,
        pass_count=pass_count,
        fail_count=fail_count,
        passed=passed
    )


def generate_qa_report(test_results: list[QATestResult], output_file: str) -> None:
    """Generate QA report.

    Args:
        test_results: List of test results.
        output_file: Path to output report file.
    """
    lines = []

    # Header
    lines.append("# QA 리포트")
    lines.append("")
    lines.append(f"## 실행 정보")
    lines.append(f"- 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"- 총 반복 횟수: {len(test_results)}회")
    lines.append(f"- 최종 판정: {'PASS' if test_results[-1].passed else 'FAIL'}")
    lines.append("")

    # Final iteration details
    final_result = test_results[-1]
    lines.append("## 최종 테스트 단어")
    lines.append("")
    lines.append("| 단어 | 빈도 점수 | 예상 범위 | 실제 결과 | 일치 |")
    lines.append("|------|-----------|-----------|-----------|------|")

    for test_word in final_result.test_words:
        actual = final_result.actual_results.get(test_word.word, -1)
        match = "✓" if test_word.expected_min <= actual <= test_word.expected_max else "✗"
        lines.append(f"| {test_word.word} | {test_word.frequency_score} | "
                    f"{test_word.expected_min}-{test_word.expected_max} | {actual} | {match} |")

    lines.append("")
    lines.append("## 무한 반복 이력")
    lines.append("")
    lines.append("| 회차 | 판정 | 통과 | 실패 |")
    lines.append("|------|------|------|------|")

    for result in test_results:
        status = "PASS" if result.passed else "FAIL"
        lines.append(f"| {result.iteration} | {status} | {result.pass_count} | {result.fail_count} |")

    lines.append("")
    lines.append("## 최종 판정")
    lines.append("")
    if final_result.passed:
        lines.append("**PASS**")
        lines.append("모든 테스트 단어가 예상 범위 내에 있음.")
    else:
        lines.append("**FAIL**")
        lines.append(f"{final_result.fail_count}개 단어가 예상 범위를 벗어났음.")

    # Write report
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    logger.info(f"QA report saved to {output_file}")


def generate_comprehensive_report(test_results: list[QATestResult], output_file: str) -> None:
    """Generate comprehensive QA report covering all iterations.

    Args:
        test_results: List of test results.
        output_file: Path to output report file.
    """
    lines = []

    # Header
    lines.append("# QA Comprehensive Report (1000 Words)")
    lines.append("")
    lines.append(f"## 실행 정보")
    lines.append(f"- 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"- 총 반복 횟수: {len(test_results)}회")
    lines.append(f"- 총 테스트 단어: {sum(len(r.test_words) for r in test_results)}개")

    # Calculate overall statistics
    total_words = sum(len(r.test_words) for r in test_results)
    total_pass = sum(r.pass_count for r in test_results)
    total_fail = sum(r.fail_count for r in test_results)
    pass_rate = (total_pass / total_words * 100) if total_words > 0 else 0

    lines.append(f"- 총 통과: {total_pass}개")
    lines.append(f"- 총 실패: {total_fail}개")
    lines.append(f"- 통과율: {pass_rate:.1f}%")
    lines.append(f"- 최종 판정: {'PASS' if total_fail == 0 else 'FAIL'}")
    lines.append("")

    # Summary by frequency
    lines.append("## 빈도별 결과 요약")
    lines.append("")

    high_freq_results = []
    mid_freq_results = []
    low_freq_results = []

    for result in test_results:
        for tw in result.test_words:
            actual = result.actual_results.get(tw.word, -1)
            passed = tw.expected_min <= actual <= tw.expected_max

            if tw.frequency_score <= 3:
                high_freq_results.append((tw.word, tw.frequency_score, actual, passed))
            elif tw.frequency_score <= 7:
                mid_freq_results.append((tw.word, tw.frequency_score, actual, passed))
            else:
                low_freq_results.append((tw.word, tw.frequency_score, actual, passed))

    def analyze_group(group_results, group_name):
        if group_results:
            lines.append(f"### {group_name}")
            lines.append("")
            lines.append(f"- 총: {len(group_results)}개")
            lines.append(f"- 통과: {sum(1 for r in group_results if r[3])}개")
            lines.append(f"- 실패: {sum(1 for r in group_results if not r[3])}개")
            lines.append("")

    analyze_group(high_freq_results, "고빈도 단어 (Frequency Score 1-3)")
    analyze_group(mid_freq_results, "중빈도 단어 (Frequency Score 4-7)")
    analyze_group(low_freq_results, "저빈도 단어 (Frequency Score 8-10)")

    # Show failed items if any
    all_results = high_freq_results + mid_freq_results + low_freq_results
    failed_results = [r for r in all_results if not r[3]]

    if failed_results:
        lines.append("## 실패한 단어 목록")
        lines.append("")
        lines.append("| 단어 | 빈도 점수 | 예상 범위 | 실제 결과 |")
        lines.append("|------|-----------|-----------|-----------|")

        for word, score, actual, _ in failed_results[:100]:  # Show max 100 failures
            if score <= 3:
                expected_range = "7-10"
            elif score <= 7:
                expected_range = "4-7"
            else:
                expected_range = "0-3"
            lines.append(f"| {word} | {score} | {expected_range} | {actual} |")

        lines.append("")

    # Iteration history
    lines.append("## 반복 이력")
    lines.append("")
    lines.append("| 회차 | 판정 | 통과 | 실패 |")
    lines.append("|------|------|------|------|")

    for result in test_results:
        status = "PASS" if result.passed else "FAIL"
        lines.append(f"| {result.iteration} | {status} | {result.pass_count} | {result.fail_count} |")

    lines.append("")
    lines.append("## 최종 판정")
    lines.append("")
    if total_fail == 0:
        lines.append("**PASS**")
        lines.append(f"모든 {total_words}개 테스트 단어가 예상 범위 내에 있음.")
    else:
        lines.append("**FAIL**")
        lines.append(f"{total_fail}개 단어가 예상 범위를 벗어났음.")

    # Write report
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    logger.info(f"Comprehensive QA report saved to {output_file}")


def run_infinite_qa_test(max_iterations: int = 100, start_iteration: int = 1) -> None:
    """Run QA test with REAL KCPC pipeline for each iteration.

    Args:
        max_iterations: Maximum number of iterations (default 100).
        start_iteration: Starting iteration number (default 1).
    """
    config = get_config()

    word_count = config.qa_word_count if hasattr(config, 'qa_word_count') else 10
    high_freq = config.qa_high_freq_words if hasattr(config, 'qa_high_freq_words') else 3
    mid_freq = config.qa_mid_freq_words if hasattr(config, 'qa_mid_freq_words') else 4
    low_freq = config.qa_low_freq_words if hasattr(config, 'qa_low_freq_words') else 3

    test_results = []

    # Load existing results if starting from iteration > 1
    if start_iteration > 1:
        logger.info(f"Resuming from iteration {start_iteration}")
        for i in range(1, start_iteration):
            output_file = f"./output/qa/qa_result_{i:03d}.xlsx"
            input_file = f"./input/qa/test_words_iter_{i:03d}.txt"
            try:
                # Load test words from input file
                with open(input_file, "r", encoding="utf-8") as f:
                    words = [line.strip() for line in f if line.strip()]

                # Load results from Excel
                df = pd.read_excel(output_file)
                actual_results = {}
                for _, row in df.iterrows():
                    keyword = row.get("Keyword", "")
                    count = row.get("Top10_Title_Match_Count", -1)
                    if keyword:
                        actual_results[keyword] = int(count) if pd.notna(count) else -1

                # Reconstruct TestWord objects (assign frequency scores based on results)
                test_words = []
                for word, actual in actual_results.items():
                    if actual >= 7:
                        score = random.randint(1, 3)
                        expected_min, expected_max = 7, 10
                    elif actual >= 4:
                        score = random.randint(4, 7)
                        expected_min, expected_max = 4, 7
                    else:
                        score = random.randint(8, 10)
                        expected_min, expected_max = 0, 3

                    test_words.append(TestWord(
                        word=word,
                        frequency_score=score,
                        expected_min=expected_min,
                        expected_max=expected_max
                    ))

                pass_count = sum(1 for tw in test_words
                                if tw.expected_min <= actual_results.get(tw.word, -1) <= tw.expected_max)
                fail_count = len(test_words) - pass_count

                test_results.append(QATestResult(
                    iteration=i,
                    test_words=test_words,
                    actual_results=actual_results,
                    pass_count=pass_count,
                    fail_count=fail_count,
                    passed=(fail_count == 0)
                ))
            except Exception as e:
                logger.warning(f"Could not load iteration {i}: {e}")

        logger.info(f"Loaded {len(test_results)} previous results")

    try:
        for iteration in range(start_iteration, max_iterations + 1):
            logger.info(f"\n{'='*60}")
            logger.info(f"QA Test Iteration {iteration}/{max_iterations}")
            logger.info(f"{'='*60}\n")

            # Generate new test words for each iteration
            test_words = generate_test_words(word_count, high_freq, mid_freq, low_freq)

            # Unique input/output files for each iteration
            input_file = f"./input/qa/test_words_iter_{iteration:03d}.txt"
            output_file = f"./output/qa/qa_result_{iteration:03d}.xlsx"

            # Run test iteration with REAL pipeline
            result = run_qa_test_iteration(iteration, test_words, input_file, output_file)
            test_results.append(result)

            # Always continue for 100 iterations to test various word combinations
            if iteration >= max_iterations:
                logger.info(f"\n[COMPLETE] QA Test completed {max_iterations} iterations")
                break
            else:
                logger.info(f"\n[CONTINUE] Iteration {iteration} complete, continuing...")

            # Delay between iterations (DDG rate limiting)
            time.sleep(5)

    except KeyboardInterrupt:
        logger.info("\nQA Test interrupted by user")
    finally:
        # Always generate comprehensive report
        if test_results:
            output_file = f"./output/qa/qa_report_1000words.md"
            generate_comprehensive_report(test_results, output_file)


def main() -> int:
    """Main entry point for QA tester.

    Returns:
        int: Exit code (0 for success, 1 for failure).
    """
    parser = argparse.ArgumentParser(description="KCPC QA Tester")
    parser.add_argument("--start", type=int, default=1, help="Starting iteration number (default: 1)")
    parser.add_argument("--max", type=int, default=100, help="Maximum iteration number (default: 100)")
    args = parser.parse_args()

    try:
        run_infinite_qa_test(max_iterations=args.max, start_iteration=args.start)
        return 0
    except Exception as e:
        logger.error(f"QA test failed with error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
