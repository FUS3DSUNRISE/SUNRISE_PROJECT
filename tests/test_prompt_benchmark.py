import importlib.util
import sys
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(__file__).resolve().parents[1] / "app" / "services" / "prompt_benchmark.py"
SPEC = importlib.util.spec_from_file_location("prompt_benchmark", MODULE_PATH)
prompt_benchmark = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = prompt_benchmark
SPEC.loader.exec_module(prompt_benchmark)


BENCHMARK_CRITERIA = prompt_benchmark.BENCHMARK_CRITERIA
BenchmarkReport = prompt_benchmark.BenchmarkReport
build_desktop_benchmark_hta = prompt_benchmark.build_desktop_benchmark_hta
build_result = prompt_benchmark.build_result
build_sample_report = prompt_benchmark.build_sample_report
chart_data_from_report = prompt_benchmark.chart_data_from_report
create_score_state = prompt_benchmark.create_score_state
default_prompt_records = prompt_benchmark.default_prompt_records
iter_test_prompts = prompt_benchmark.iter_test_prompts
load_persisted_benchmark_data = prompt_benchmark.load_persisted_benchmark_data
print_console_report = prompt_benchmark.print_console_report
report_from_state = prompt_benchmark.report_from_state
rows_for_report = prompt_benchmark.rows_for_report
save_persisted_benchmark_data = prompt_benchmark.save_persisted_benchmark_data
detailed_rows_for_report = prompt_benchmark.detailed_rows_for_report
build_report_lines = prompt_benchmark.build_report_lines


class PromptBenchmarkTests(unittest.TestCase):
    def test_benchmark_library_contains_expected_difficulties(self):
        prompts = list(iter_test_prompts())

        self.assertEqual(len(prompts), 20)
        self.assertEqual(
            {prompt.difficulty for prompt in prompts},
            {"Simple", "Medium", "Difficult", "Ambiguous"},
        )

    def test_average_score_is_calculated_per_test(self):
        prompt = next(prompt for prompt in iter_test_prompts() if prompt.name == "wooden_chair")
        result = build_result(
            prompt,
            compliance=8,
            stability=9,
            geometry_quality=7,
            materials=8,
            blender_success=10,
            final_export=10,
        )

        self.assertEqual(result.average_score(), 8.67)

    def test_report_exposes_per_test_and_overall_averages(self):
        report = build_sample_report()

        self.assertEqual(set(BENCHMARK_CRITERIA), set(report.results[0].scores.as_dict().keys()))
        self.assertEqual(report.average_by_test()["wooden_pallet"], 6.0)
        self.assertEqual(report.average_by_difficulty()["Simple"], 8.42)
        self.assertEqual(report.overall_average(), 8.42)

    def test_chart_data_orders_difficulties_and_marks_simple_highest(self):
        report = build_sample_report()

        chart_data = chart_data_from_report(report)

        self.assertEqual([label for label, _ in chart_data], ["Simple", "Medium", "Difficult", "Ambiguous"])
        self.assertEqual(max(chart_data, key=lambda item: item[1])[0], "Simple")

    def test_rows_for_report_return_table_friendly_values(self):
        report = build_sample_report()

        rows = rows_for_report(report)

        self.assertEqual(rows[0]["difficulty"], "Simple")
        self.assertEqual(rows[0]["name"], "wooden_pallet")
        self.assertEqual(rows[0]["average"], "6.00")
        self.assertIn("compliance", rows[0])

    def test_detailed_rows_match_console_level_fields(self):
        report = build_sample_report()

        rows = detailed_rows_for_report(report)

        self.assertEqual(rows[0]["name"], "wooden_pallet")
        self.assertEqual(rows[0]["difficulty"], "Simple")
        self.assertIn("A standard wooden shipping pallet.", rows[0]["prompt"])
        self.assertEqual(rows[0]["average_score"], "6.00/10")
        self.assertEqual(rows[0]["compliance"], "4.00")

    def test_build_report_lines_matches_console_structure(self):
        report = build_sample_report()

        lines = build_report_lines(report)

        self.assertIn("wooden_pallet [Simple]", lines)
        self.assertIn("  Prompt: A standard wooden shipping pallet.", lines)
        self.assertIn("  Average Score: 6.00/10", lines)
        self.assertIn("  - compliance: 4.00", lines)
        self.assertIn("Notes: Poor result, certain parts are not attached to the base", lines)

    def test_state_round_trip_rebuilds_report(self):
        source_report = build_sample_report()

        state = create_score_state(source_report)
        rebuilt_report = report_from_state(state)

        self.assertEqual(rebuilt_report.average_by_test(), source_report.average_by_test())
        self.assertEqual(rebuilt_report.overall_average(), source_report.overall_average())

    def test_persisted_data_can_add_custom_prompt(self):
        store_path = Path("tests") / "prompt_benchmark_data_test.json"
        if store_path.exists():
            store_path.unlink()

        try:
            prompts = default_prompt_records() + [
                {
                    "name": "custom_robot",
                    "difficulty": "Difficult",
                    "prompt": "A compact household helper robot.",
                    "target_shape": "Robot",
                    "notes": "Custom benchmark prompt",
                }
            ]
            score_state = create_score_state()
            score_state["custom_robot"] = {
                "compliance": 8.0,
                "stability": 7.0,
                "geometry_quality": 8.0,
                "materials": 7.0,
                "blender_success": 9.0,
                "final_export": 9.0,
                "reviewer_notes": "Saved from desktop app",
            }

            save_persisted_benchmark_data(prompts, score_state, store_path=store_path)
            loaded = load_persisted_benchmark_data(store_path=store_path)

            self.assertTrue(any(prompt["name"] == "custom_robot" for prompt in loaded["prompts"]))
            self.assertEqual(loaded["score_state"]["custom_robot"]["blender_success"], 9.0)
        finally:
            if store_path.exists():
                store_path.unlink()

    def test_desktop_hta_contains_report_viewer_results(self):
        sample_report = build_sample_report()
        html = build_desktop_benchmark_hta(
            initial_prompts=default_prompt_records(),
            initial_state=create_score_state(sample_report),
        )

        self.assertIn("3D Prompt Benchmark Results", html)
        self.assertIn("<hta:application", html)
        self.assertIn("results-view", html)
        self.assertIn("wooden_pallet [Simple]", html)
        self.assertIn("Average Score", html)

    def test_invalid_score_raises_error(self):
        prompt = next(prompt for prompt in iter_test_prompts() if prompt.name == "wooden_pallet")

        with self.assertRaises(ValueError):
            build_result(
                prompt,
                compliance=11,
                stability=9,
                geometry_quality=9,
                materials=9,
                blender_success=10,
                final_export=10,
            )

    def test_console_report_prints_summary(self):
        report = build_sample_report()
        fake_stdout = StringIO()

        with patch("sys.stdout", fake_stdout):
            print_console_report(report)

        output = fake_stdout.getvalue()
        self.assertIn("3D Prompt Benchmark Report", output)
        self.assertIn("wooden_pallet [Simple]", output)
        self.assertIn("Average By Difficulty", output)
        self.assertIn("Overall Average: 8.42/10", output)

    def test_empty_report_prints_graceful_message(self):
        fake_stdout = StringIO()

        with patch("sys.stdout", fake_stdout):
            print_console_report(BenchmarkReport())

        self.assertIn("No benchmark results available.", fake_stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
