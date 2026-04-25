from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from statistics import mean
from typing import Dict, Iterable, List
import json
import os


BENCHMARK_CRITERIA = (
    "compliance",
    "stability",
    "geometry_quality",
    "materials",
    "blender_success",
    "final_export",
)

DIFFICULTY_ORDER = ("Simple", "Medium", "Difficult", "Ambiguous")
MODULE_DIR = Path(__file__).resolve().parent
DEFAULT_STORE_PATH = MODULE_DIR / "prompt_benchmark_data.json"
DEFAULT_HTA_PATH = MODULE_DIR / "prompt_benchmark.hta"


@dataclass(frozen=True)
class TestPrompt:
    name: str
    difficulty: str
    prompt: str
    target_shape: str
    notes: str = ""


@dataclass(frozen=True)
class EvaluationScores:
    compliance: float
    stability: float
    geometry_quality: float
    materials: float
    blender_success: float
    final_export: float

    def as_dict(self) -> Dict[str, float]:
        return {
            "compliance": self.compliance,
            "stability": self.stability,
            "geometry_quality": self.geometry_quality,
            "materials": self.materials,
            "blender_success": self.blender_success,
            "final_export": self.final_export,
        }

    def average(self) -> float:
        return round(mean(self.as_dict().values()), 2)

    def validate(self, minimum: float = 0.0, maximum: float = 10.0) -> None:
        for criterion, value in self.as_dict().items():
            if not minimum <= value <= maximum:
                raise ValueError(
                    f"Score for '{criterion}' must be between {minimum} and {maximum}. "
                    f"Received: {value}"
                )


@dataclass(frozen=True)
class BenchmarkResult:
    test_prompt: TestPrompt
    scores: EvaluationScores
    reviewer_notes: str = ""

    def average_score(self) -> float:
        self.scores.validate()
        return self.scores.average()


@dataclass
class BenchmarkReport:
    results: List[BenchmarkResult] = field(default_factory=list)

    def add_result(self, result: BenchmarkResult) -> None:
        result.scores.validate()
        self.results.append(result)

    def average_by_test(self) -> Dict[str, float]:
        return {result.test_prompt.name: result.average_score() for result in self.results}

    def average_by_difficulty(self) -> Dict[str, float]:
        grouped: Dict[str, List[float]] = {}
        for result in self.results:
            grouped.setdefault(result.test_prompt.difficulty, []).append(result.average_score())

        return {
            difficulty: round(mean(scores), 2)
            for difficulty, scores in grouped.items()
            if scores
        }

    def overall_average(self) -> float:
        if not self.results:
            return 0.0
        return round(mean(result.average_score() for result in self.results), 2)


TEST_PROMPTS: Dict[str, List[TestPrompt]] = {
    "Simple": [
        TestPrompt(name="wooden_pallet", difficulty="Simple", prompt="A standard wooden shipping pallet.", target_shape="Flat slatted structure"),
        TestPrompt(name="plastic_crate", difficulty="Simple", prompt="A simple blue plastic storage crate.", target_shape="Box"),
        TestPrompt(name="metal_pipe", difficulty="Simple", prompt="A silver metal pipe.", target_shape="Cylinder"),
        TestPrompt(name="concrete_block", difficulty="Simple", prompt="A grey concrete building block.", target_shape="Rectangular block"),
        TestPrompt(name="cardboard_box", difficulty="Simple", prompt="A plain cardboard moving box.", target_shape="Box"),
    ],
    "Medium": [
        TestPrompt(name="wooden_chair", difficulty="Medium",prompt="A simple wooden dining chair with four legs and a backrest.", target_shape="Chair"),
        TestPrompt(name="office_desk", difficulty="Medium", prompt="A basic office desk with a flat top.", target_shape="Desk"),
        TestPrompt(name="step_ladder", difficulty="Medium", prompt="Aluminum step ladder.", target_shape="Ladder"),
        TestPrompt(name="trash_can",difficulty="Medium", prompt="A metal mesh office trash can.", target_shape="Cylinder with holes"),
        TestPrompt(name="floor_lamp", difficulty="Medium", prompt="A simple standing floor lamp with a round base.", target_shape="Lamp"),
    ],
    "Difficult": [
        TestPrompt(name="fabric_sofa", difficulty="Difficult", prompt="A comfortable three-seater fabric sofa with cushions.", target_shape="Sofa"),
        TestPrompt(name="armchair_leather", difficulty="Difficult", prompt="A classic leather armchair with tufted.", target_shape="Armchair"),
        TestPrompt(name="bicycle_frame", difficulty="Difficult", prompt="A basic bicycle frame with wheels and handlebars.", target_shape="Bicycle"),
        TestPrompt(name="bookshelf_filled",difficulty="Difficult", prompt="A wooden bookshelf filled with many individual books.", target_shape="Shelf with many objects"),
        TestPrompt(name="motorcycle", difficulty="Difficult", prompt="A commuter motorcycle with visible frame and wheels.", target_shape="Motorcycle"),
    ],
    "Ambiguous": [
        TestPrompt(name="unusual_furniture", difficulty="Ambiguous", prompt="A piece of furniture that is both a chair and a table.", target_shape="Hybrid object"),
        TestPrompt(name="eco_friendly_object", difficulty="Ambiguous", prompt="A household object made entirely of living grass and water.", target_shape="Organic object"),
        TestPrompt(name="minimalist_statue", difficulty="Ambiguous", prompt="A minimalist 3D sculpture representing 'Efficiency'.", target_shape="Abstract"),
        TestPrompt(name="impossible_shape", difficulty="Ambiguous", prompt="A geometric shape that shouldn't exist in 3D space.", target_shape="Paradoxical object"),
        TestPrompt(name="dream_machine", difficulty="Ambiguous", prompt="A machine built from a dream that solves a feeling.", target_shape="Abstract machine"),
    ],
}


def iter_test_prompts() -> Iterable[TestPrompt]:
    for difficulty in DIFFICULTY_ORDER:
        yield from TEST_PROMPTS[difficulty]


def default_prompt_records() -> List[Dict[str, str]]:
    return [_prompt_record(prompt) for prompt in iter_test_prompts()]


def _prompt_record(prompt: TestPrompt) -> Dict[str, str]:
    return {
        "name": prompt.name,
        "difficulty": prompt.difficulty,
        "prompt": prompt.prompt,
        "target_shape": prompt.target_shape,
        "notes": prompt.notes,
    }


def build_result(
    test_prompt: TestPrompt,
    *,
    compliance: float,
    stability: float,
    geometry_quality: float,
    materials: float,
    blender_success: float,
    final_export: float,
    reviewer_notes: str = "",
) -> BenchmarkResult:
    scores = EvaluationScores(
        compliance=compliance,
        stability=stability,
        geometry_quality=geometry_quality,
        materials=materials,
        blender_success=blender_success,
        final_export=final_export,
    )
    scores.validate()
    return BenchmarkResult(test_prompt=test_prompt, scores=scores, reviewer_notes=reviewer_notes)


def _prompt_index_from_records(
    prompt_records: Iterable[Dict[str, str]] | None = None,
) -> Dict[str, TestPrompt]:
    records = prompt_records if prompt_records is not None else default_prompt_records()
    return {
        record["name"]: TestPrompt(
            name=record["name"],
            difficulty=record["difficulty"],
            prompt=record["prompt"],
            target_shape=record["target_shape"],
            notes=record.get("notes", ""),
        )
        for record in records
    }


def create_score_state(report: BenchmarkReport | None = None) -> Dict[str, Dict[str, float | str]]:
    if not report:
        return {}

    return {
        result.test_prompt.name: {
            **result.scores.as_dict(),
            "reviewer_notes": result.reviewer_notes,
        }
        for result in report.results
    }


def _score_values_from_state(saved: Dict[str, float | str]) -> Dict[str, float]:
    return {criterion: float(saved.get(criterion, 0.0)) for criterion in BENCHMARK_CRITERIA}


def report_from_state(
    score_state: Dict[str, Dict[str, float | str]],
    *,
    prompt_records: Iterable[Dict[str, str]] | None = None,
) -> BenchmarkReport:
    prompt_index = _prompt_index_from_records(prompt_records)
    report = BenchmarkReport()

    for prompt in iter(prompt_index.values()):
        saved = score_state.get(prompt.name)
        if not saved:
            continue

        report.add_result(
            build_result(
                prompt,
                **_score_values_from_state(saved),
                reviewer_notes=str(saved.get("reviewer_notes", "")),
            )
        )

    return report


def _result_row(result: BenchmarkResult, *, detailed: bool = False) -> Dict[str, str]:
    row = {
        "name": result.test_prompt.name,
        "difficulty": result.test_prompt.difficulty,
        **{criterion: f"{value:.2f}" for criterion, value in result.scores.as_dict().items()},
    }
    if detailed:
        row.update(
            {
                "prompt": result.test_prompt.prompt,
                "target_shape": result.test_prompt.target_shape,
                "average_score": f"{result.average_score():.2f}/10",
                "reviewer_notes": result.reviewer_notes,
            }
        )
    else:
        row["average"] = f"{result.average_score():.2f}"
    return row


def rows_for_report(report: BenchmarkReport) -> List[Dict[str, str]]:
    return [_result_row(result) for result in report.results]


def detailed_rows_for_report(report: BenchmarkReport) -> List[Dict[str, str]]:
    return [_result_row(result, detailed=True) for result in report.results]


def build_report_lines(report: BenchmarkReport) -> List[str]:
    lines = ["3D Prompt Benchmark Report", "=" * 26]
    if not report.results:
        lines.append("No benchmark results available.")
        return lines

    for result in report.results:
        lines.append(f"{result.test_prompt.name} [{result.test_prompt.difficulty}]")
        lines.append(f"  Prompt: {result.test_prompt.prompt}")
        lines.append(f"  Average Score: {result.average_score():.2f}/10")
        for criterion, value in result.scores.as_dict().items():
            lines.append(f"  - {criterion}: {value:.2f}")
        if result.reviewer_notes:
            lines.append(f"Notes: {result.reviewer_notes}")
        lines.append("")

    lines.append("Average By Difficulty")
    for difficulty, value in report.average_by_difficulty().items():
        lines.append(f"  - {difficulty}: {value:.2f}/10")

    lines.append(f"Overall Average: {report.overall_average():.2f}/10")
    return lines


def print_console_report(report: BenchmarkReport) -> None:
    for line in build_report_lines(report):
        print(line)


def chart_data_from_report(report: BenchmarkReport) -> List[tuple[str, float]]:
    averages = report.average_by_difficulty()
    return [(difficulty, averages.get(difficulty, 0.0)) for difficulty in DIFFICULTY_ORDER]


def save_persisted_benchmark_data(
    prompts: List[Dict[str, str]],
    score_state: Dict[str, Dict[str, float | str]],
    *,
    store_path: Path = DEFAULT_STORE_PATH,
) -> Path:
    payload = {"prompts": prompts, "score_state": score_state}
    store_path.parent.mkdir(parents=True, exist_ok=True)
    store_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return store_path


def load_persisted_benchmark_data(*, store_path: Path = DEFAULT_STORE_PATH) -> Dict[str, object]:
    if not store_path.exists():
        return {"prompts": default_prompt_records(), "score_state": {}}

    payload = json.loads(store_path.read_text(encoding="utf-8"))
    return {
        "prompts": payload.get("prompts", default_prompt_records()),
        "score_state": payload.get("score_state", {}),
    }


def _js_string(value: str) -> str:
    return json.dumps(str(value))


def build_desktop_benchmark_hta(
    *,
    initial_prompts: List[Dict[str, str]] | None = None,
    initial_state: Dict[str, Dict[str, float | str]] | None = None,
    data_file_name: str | None = None,
) -> str:
    prompts = initial_prompts or default_prompt_records()
    score_state = initial_state or create_score_state()
    payload = {"prompts": prompts, "score_state": score_state}
    file_name = data_file_name or DEFAULT_STORE_PATH.name
    initial_lines = _embedded_report_text(prompts, score_state)

    return f"""<!DOCTYPE html>
<html>
<head>
  <title>3D Prompt Benchmark Results</title>
  <hta:application
    id="promptBenchmark"
    applicationname="PromptBenchmark"
    border="thick"
    caption="yes"
    showintaskbar="yes"
    singleinstance="yes"
    sysmenu="yes"
    scroll="yes"
  />
  <meta http-equiv="x-ua-compatible" content="ie=9" />
  <style>
    :root {{
      --bg: #f4f0e8;
      --panel: #fffaf3;
      --ink: #1f2a2c;
      --accent: #c4661f;
      --accent-soft: #f6d3b7;
      --line: #d8c9b7;
      --good: #2d7a55;
    }}
    body {{
      margin: 0;
      padding: 24px;
      font-family: Georgia, "Trebuchet MS", serif;
      background:
        radial-gradient(circle at top right, #ffe3ca 0, transparent 32%),
        linear-gradient(180deg, #f8f4ec 0%, #efe5d7 100%);
      color: var(--ink);
    }}
    .shell {{
      max-width: 1200px;
      margin: 0 auto;
    }}
    .hero {{
      background: linear-gradient(135deg, rgba(196,102,31,0.16), rgba(255,250,243,0.96));
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 22px;
      box-shadow: 0 18px 40px rgba(73, 50, 29, 0.10);
    }}
    .hero h1 {{
      margin: 0 0 8px;
      font-size: 34px;
      letter-spacing: 0.4px;
    }}
    .hero p {{
      margin: 0;
      font-size: 15px;
      line-height: 1.5;
    }}
    .meta {{
      margin-top: 12px;
      color: #6c5d4f;
      font-size: 12px;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 14px;
      margin-top: 18px;
    }}
    .card {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 16px;
      box-shadow: 0 12px 28px rgba(44, 33, 21, 0.06);
    }}
    .label {{
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 1px;
      color: #7b6e61;
    }}
    .value {{
      margin-top: 8px;
      font-size: 28px;
      font-weight: bold;
    }}
    .stack {{
      margin-top: 18px;
    }}
    .chart-bar {{
      margin-top: 12px;
    }}
    .chart-label {{
      font-size: 13px;
      margin-bottom: 4px;
    }}
    .chart-track {{
      height: 14px;
      border-radius: 999px;
      background: #eadfce;
      overflow: hidden;
    }}
    .chart-fill {{
      height: 100%;
      background: linear-gradient(90deg, #df8847, #c4661f);
    }}
    #results-view {{
      margin-top: 18px;
      background: #221b17;
      color: #f3eadb;
      border-radius: 18px;
      padding: 18px;
      border: 1px solid #58463d;
      min-height: 280px;
      white-space: pre-wrap;
      font-family: Consolas, "Courier New", monospace;
      font-size: 13px;
      line-height: 1.5;
      overflow: auto;
    }}
    .ok {{
      color: var(--good);
      font-weight: bold;
    }}
  </style>
</head>
<body>
  <div class="shell">
    <div class="hero">
      <h1>3D Prompt Benchmark Results</h1>
      <p>This is a static desktop viewer. Python writes benchmark data into a local JSON file, and this window refreshes itself automatically for developers.</p>
      <div class="meta" id="last-updated">Waiting for benchmark data...</div>
    </div>

    <div class="grid">
      <div class="card"><div class="label">Saved Prompts</div><div class="value" id="prompt-count">0</div></div>
      <div class="card"><div class="label">Scored Results</div><div class="value" id="result-count">0</div></div>
      <div class="card"><div class="label">Overall Average</div><div class="value" id="overall-average">0.00</div></div>
      <div class="card"><div class="label">Auto Refresh</div><div class="value ok">ON</div></div>
    </div>

    <div class="stack">
      <div class="card">
        <div class="label">Difficulty Averages</div>
        <div id="difficulty-chart"></div>
      </div>
    </div>

    <div id="results-view"></div>
  </div>

  <script language="javascript">
    var DATA_FILE_NAME = {_js_string(file_name)};
    var initialPayload = {json.dumps(payload)};
    var initialResultsText = {_js_string(initial_lines)};
    var lastRawPayload = "";

    function escapeHtml(value) {{
      return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
    }}

    function scoreKeys() {{
      return {json.dumps(list(BENCHMARK_CRITERIA))};
    }}

    function averageForEntry(entry) {{
      var total = 0;
      var keys = scoreKeys();
      for (var i = 0; i < keys.length; i++) {{
        total += Number(entry[keys[i]] || 0);
      }}
      return (total / keys.length);
    }}

    function buildReportLines(prompts, scoreState) {{
      var lines = ["3D Prompt Benchmark Report", "=========================="];
      var scoredResults = [];
      for (var i = 0; i < prompts.length; i++) {{
        var prompt = prompts[i];
        var saved = scoreState[prompt.name];
        if (saved) {{
          scoredResults.push({{ prompt: prompt, score: saved }});
        }}
      }}

      if (!scoredResults.length) {{
        lines.push("No benchmark results available.");
        return lines.join("\\r\\n");
      }}

      for (var j = 0; j < scoredResults.length; j++) {{
        var item = scoredResults[j];
        lines.push(item.prompt.name + " [" + item.prompt.difficulty + "]");
        lines.push("  Prompt: " + item.prompt.prompt);
        lines.push("  Average Score: " + averageForEntry(item.score).toFixed(2) + "/10");
        var keys = scoreKeys();
        for (var k = 0; k < keys.length; k++) {{
          var key = keys[k];
          lines.push("  - " + key + ": " + Number(item.score[key] || 0).toFixed(2));
        }}
        if (item.score.reviewer_notes) {{
          lines.push("  Notes: " + item.score.reviewer_notes);
        }}
        lines.push("");
      }}

      var difficultyTotals = {{}};
      var difficultyCounts = {{}};
      for (var x = 0; x < scoredResults.length; x++) {{
        var difficulty = scoredResults[x].prompt.difficulty;
        difficultyTotals[difficulty] = (difficultyTotals[difficulty] || 0) + averageForEntry(scoredResults[x].score);
        difficultyCounts[difficulty] = (difficultyCounts[difficulty] || 0) + 1;
      }}

      lines.push("Average By Difficulty");
      var order = {json.dumps(list(DIFFICULTY_ORDER))};
      for (var y = 0; y < order.length; y++) {{
        var name = order[y];
        if (difficultyCounts[name]) {{
          lines.push("  - " + name + ": " + (difficultyTotals[name] / difficultyCounts[name]).toFixed(2) + "/10");
        }}
      }}

      var totalAverage = 0;
      for (var z = 0; z < scoredResults.length; z++) {{
        totalAverage += averageForEntry(scoredResults[z].score);
      }}
      lines.push("Overall Average: " + (totalAverage / scoredResults.length).toFixed(2) + "/10");
      return lines.join("\\r\\n");
    }}

    function difficultyChart(prompts, scoreState) {{
      var order = {json.dumps(list(DIFFICULTY_ORDER))};
      var totals = {{}};
      var counts = {{}};
      for (var i = 0; i < prompts.length; i++) {{
        var prompt = prompts[i];
        var saved = scoreState[prompt.name];
        if (!saved) continue;
        totals[prompt.difficulty] = (totals[prompt.difficulty] || 0) + averageForEntry(saved);
        counts[prompt.difficulty] = (counts[prompt.difficulty] || 0) + 1;
      }}

      var html = "";
      for (var j = 0; j < order.length; j++) {{
        var difficulty = order[j];
        var avg = counts[difficulty] ? (totals[difficulty] / counts[difficulty]) : 0;
        html += '<div class="chart-bar">';
        html += '<div class="chart-label">' + escapeHtml(difficulty) + ' - ' + avg.toFixed(2) + '/10</div>';
        html += '<div class="chart-track"><div class="chart-fill" style="width:' + (avg * 10) + '%;"></div></div>';
        html += '</div>';
      }}
      document.getElementById("difficulty-chart").innerHTML = html;
    }}

    function render(payload, sourceLabel) {{
      var prompts = payload.prompts || [];
      var scoreState = payload.score_state || {{}};
      var results = 0;
      var totalAverage = 0;
      for (var i = 0; i < prompts.length; i++) {{
        var saved = scoreState[prompts[i].name];
        if (!saved) continue;
        results += 1;
        totalAverage += averageForEntry(saved);
      }}

      document.getElementById("prompt-count").innerText = prompts.length;
      document.getElementById("result-count").innerText = results;
      document.getElementById("overall-average").innerText = results ? (totalAverage / results).toFixed(2) : "0.00";
      document.getElementById("results-view").innerText = buildReportLines(prompts, scoreState);
      document.getElementById("last-updated").innerText = "Auto-refreshed from " + sourceLabel + " at " + new Date().toLocaleTimeString();

      difficultyChart(prompts, scoreState);
    }}

    function tryLoadFromDisk() {{
      try {{
        var shell = new ActiveXObject("WScript.Shell");
        var basePath = shell.CurrentDirectory;
        var fullPath = basePath + "\\\\" + DATA_FILE_NAME;
        var fso = new ActiveXObject("Scripting.FileSystemObject");
        if (!fso.FileExists(fullPath)) {{
          render(initialPayload, "embedded initial data");
          return;
        }}

        var file = fso.OpenTextFile(fullPath, 1, false);
        var raw = file.ReadAll();
        file.Close();

        if (raw === lastRawPayload) {{
          return;
        }}

        lastRawPayload = raw;
        render(JSON.parse(raw), DATA_FILE_NAME);
      }} catch (error) {{
        render(initialPayload, "embedded initial data");
      }}
    }}

    document.getElementById("results-view").innerText = initialResultsText;
    render(initialPayload, "embedded initial data");
    tryLoadFromDisk();
    window.setInterval(tryLoadFromDisk, 1500);
  </script>
</body>
</html>
"""


def _embedded_report_text(
    prompts: List[Dict[str, str]],
    score_state: Dict[str, Dict[str, float | str]],
) -> str:
    return "\r\n".join(build_report_lines(report_from_state(score_state, prompt_records=prompts)))


def write_desktop_benchmark_files(
    *,
    prompts: List[Dict[str, str]] | None = None,
    score_state: Dict[str, Dict[str, float | str]] | None = None,
    store_path: Path = DEFAULT_STORE_PATH,
    hta_path: Path = DEFAULT_HTA_PATH,
) -> Dict[str, Path]:
    current_prompts = prompts or default_prompt_records()
    current_state = score_state or {}
    save_persisted_benchmark_data(current_prompts, current_state, store_path=store_path)
    hta_html = build_desktop_benchmark_hta(
        initial_prompts=current_prompts,
        initial_state=current_state,
        data_file_name=store_path.name,
    )
    hta_path.write_text(hta_html, encoding="utf-8")
    return {"store_path": store_path, "hta_path": hta_path}


def _launch_viewer(path: Path, *, silent: bool = False) -> None:
    try:
        os.startfile(str(path))
    except OSError as error:
        if silent:
            return
        print(f"Desktop viewer was written but could not be opened automatically: {error}")
        print(f"Open this file manually: {path}")


def launch_desktop_benchmark(
    *,
    prompts: List[Dict[str, str]] | None = None,
    score_state: Dict[str, Dict[str, float | str]] | None = None,
    store_path: Path = DEFAULT_STORE_PATH,
    hta_path: Path = DEFAULT_HTA_PATH,
) -> Dict[str, Path]:
    paths = write_desktop_benchmark_files(
        prompts=prompts,
        score_state=score_state,
        store_path=store_path,
        hta_path=hta_path,
    )
    _launch_viewer(paths["hta_path"])
    return paths


def update_desktop_benchmark(
    report: BenchmarkReport,
    *,
    prompts: List[Dict[str, str]] | None = None,
    store_path: Path = DEFAULT_STORE_PATH,
    hta_path: Path = DEFAULT_HTA_PATH,
    launch_if_missing: bool = False,
) -> Dict[str, Path]:
    paths = write_desktop_benchmark_files(
        prompts=prompts,
        score_state=create_score_state(report),
        store_path=store_path,
        hta_path=hta_path,
    )
    if launch_if_missing and not hta_path.exists():
        _launch_viewer(paths["hta_path"], silent=True)
    return paths


def build_sample_report() -> BenchmarkReport:
    prompts = {prompt.name: prompt for prompt in iter_test_prompts()}
    report = BenchmarkReport()
    sample_results = [
        build_result(prompts["wooden_pallet"], compliance=4, stability=5, geometry_quality=5, materials=9, blender_success=5, final_export=8, reviewer_notes="Poor result, certain parts are not attached to the base"),
        build_result(prompts["plastic_crate"], compliance=10, stability=8, geometry_quality=10, materials=10, blender_success=10, final_export=10, reviewer_notes="Cool result, the figure in the middle is empty which corresponds to the box"),
        build_result(prompts["metal_pipe"], compliance=8, stability=8, geometry_quality=9, materials=7, blender_success=9, final_export=9, reviewer_notes="Not a bad result, but I don't have emptiness inside"),
        build_result(prompts["concrete_block"], compliance=8, stability=10, geometry_quality=10, materials=7, blender_success=9, final_export=9, reviewer_notes="Good result, but no texture"),
        build_result(prompts["wooden_chair"], compliance=8, stability=7, geometry_quality=9, materials=8, blender_success=9, final_export=9, reviewer_notes="Good, but not all objects are attached"),
        build_result(prompts["office_desk"], compliance=6, stability=8, geometry_quality=7, materials=6, blender_success=8, final_export=8, reviewer_notes="Okay, but it looks more like a bar table"),
        build_result(prompts["step_ladder"], compliance=8, stability=9, geometry_quality=9, materials=8, blender_success=8, final_export=9, reviewer_notes="Good result, but there are details that spoil the overall object"),
        build_result(prompts["trash_can"], compliance=6, stability=7, geometry_quality=8, materials=6, blender_success=6, final_export=7, reviewer_notes="The shape is good, but without a mesh and a solid object"),
        build_result(prompts["fabric_sofa"], compliance=5, stability=4, geometry_quality=3, materials=7, blender_success=5, final_export=5, reviewer_notes="Doesn't look like a sofa"),
        build_result(prompts["armchair_leather"], compliance=9, stability=8, geometry_quality=9, materials=4, blender_success=8, final_export=8, reviewer_notes="Overall looks good"),
        build_result(prompts["bicycle_frame"], compliance=4, stability=3, geometry_quality=3, materials=6, blender_success=4, final_export=5, reviewer_notes="Too difficult yet, it doesn't seem like it"),
        build_result(prompts["bookshelf_filled"], compliance=6, stability=7, geometry_quality=6, materials=7, blender_success=6, final_export=6, reviewer_notes="Looks like a bookcase, but needs improvement"),
        build_result(prompts["eco_friendly_object"], compliance=0, stability=0, geometry_quality=0, materials=0, blender_success=0, final_export=0, reviewer_notes="Error: unexpected prompt status."),
        build_result(prompts["unusual_furniture"], compliance=0, stability=0, geometry_quality=0, materials=0, blender_success=0, final_export=0, reviewer_notes="Error: unexpected prompt status."),
        build_result(prompts["minimalist_statue"], compliance=0, stability=0, geometry_quality=0, materials=0, blender_success=0, final_export=0, reviewer_notes="Error: unexpected prompt status."),
        build_result(prompts["impossible_shape"], compliance=0, stability=0, geometry_quality=0, materials=0, blender_success=0, final_export=0, reviewer_notes="Error: unexpected prompt status."),
    ]
    for result in sample_results:
        report.add_result(result)

    return report


if __name__ == "__main__":
    sample_report = build_sample_report()
    print_console_report(sample_report)
    launch_desktop_benchmark(
        prompts=default_prompt_records(),
        score_state=create_score_state(sample_report),
    )
