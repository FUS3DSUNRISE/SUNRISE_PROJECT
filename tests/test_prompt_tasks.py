import unittest
import uuid
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import config
from app import create_app
from app.extensions import db
from app.models.prompt import PromptRequest, PromptStatus
from app.models.user import User


class PromptTaskTests(unittest.TestCase):
    def setUp(self):
        self.db_path = Path("tests") / f"test_prompt_tasks_{uuid.uuid4().hex}.db"
        if self.db_path.exists():
            self.db_path.unlink()

        config.Config.SQLALCHEMY_DATABASE_URI = f"sqlite:///{self.db_path.resolve().as_posix()}"
        config.Config.LLM_API_KEY = "test-key"

        self.app = create_app()
        self.app.config["TESTING"] = True
        from app.tasks.prompt_tasks import process_prompt_task
        self.process_prompt_task = process_prompt_task

        self.app_context = self.app.app_context()
        self.app_context.push()
        db.drop_all()
        db.create_all()

        self.user = User(username="tester", email="tester@example.com", password_hash="hash")
        db.session.add(self.user)
        db.session.commit()

        Path("static/models").mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        db.session.remove()
        try:
            db.drop_all()
        finally:
            db.engine.dispose()
            self.app_context.pop()
            if self.db_path.exists():
                try:
                    self.db_path.unlink()
                except PermissionError:
                    pass

    def _create_prompt(self, *, text="wooden stool", parameters=None, status=PromptStatus.QUEUED, generated_code=None):
        prompt = PromptRequest(
            prompt_text=text,
            parameters=parameters,
            generated_code=generated_code,
            category="Furniture",
            status=status,
            user_id=self.user.id,
        )
        db.session.add(prompt)
        db.session.commit()
        return prompt

    def _mock_blender_run(self, prompt_id):
        output_path = Path("static/models") / f"prompt_{prompt_id}.glb"
        output_path.write_bytes(b"glb")
        return SimpleNamespace(returncode=0, stderr="")

    def test_process_prompt_task_uses_parameterized_prompt_and_persists_generated_code(self):
        parameters = {
            "size": {"width": 1.0, "height": 1.2, "depth": 0.8},
            "geometry": {"complexity": 7, "smoothness": 32},
            "material": {"material_type": "Wood", "roughness": 0.4, "metallic": 0.1},
        }
        prompt = self._create_prompt(parameters=parameters)

        response = SimpleNamespace(
            content="import bpy\nbpy.ops.export_scene.gltf(filepath='static/models/result.glb', export_format='GLB')"
        )

        with patch("app.tasks.prompt_tasks.ChatOpenAI") as llm_cls, \
            patch("app.tasks.prompt_tasks.get_blender_executable", return_value="blender"), \
            patch("app.tasks.prompt_tasks.subprocess.run", side_effect=lambda *args, **kwargs: self._mock_blender_run(prompt.id)):
            llm_cls.return_value.invoke.return_value = response

            self.process_prompt_task.run(prompt_id=prompt.id, parameters=parameters)

        db.session.remove()
        saved = db.session.get(PromptRequest, prompt.id)
        human_prompt = llm_cls.return_value.invoke.call_args.args[0][1][1]

        self.assertIn("STRICT PARAMETERS", human_prompt)
        self.assertIn("width=1.0m", human_prompt)
        self.assertIn("Material: type=Wood", human_prompt)
        self.assertEqual(saved.status, PromptStatus.COMPLETED)
        self.assertIn("prompt_{}".format(prompt.id), saved.result_path)
        self.assertIn(f"static/models/prompt_{prompt.id}.glb", saved.generated_code)

    def test_fast_track_revises_saved_code_instead_of_reusing_raw_string_replacement(self):
        source = self._create_prompt(
            parameters={
                "size": {"width": 1.0, "height": 1.0, "depth": 1.0},
                "geometry": {"complexity": 3, "smoothness": 16},
                "material": {"material_type": "Wood", "roughness": 0.7, "metallic": 0.0},
            },
            status=PromptStatus.COMPLETED,
            generated_code="import bpy\nprint('old script')",
        )
        revised = self._create_prompt(
            text=source.prompt_text,
            parameters={
                "size": {"width": 2.0, "height": 1.5, "depth": 0.9},
                "geometry": {"complexity": 6, "smoothness": 24},
                "material": {"material_type": "Metal", "roughness": 0.2, "metallic": 0.9},
            },
        )

        response = SimpleNamespace(content="import bpy\nprint('revised script')")

        with patch("app.tasks.prompt_tasks.ChatOpenAI") as llm_cls, \
            patch("app.tasks.prompt_tasks.get_blender_executable", return_value="blender"), \
            patch("app.tasks.prompt_tasks.subprocess.run", side_effect=lambda *args, **kwargs: self._mock_blender_run(revised.id)):
            llm_cls.return_value.invoke.return_value = response

            self.process_prompt_task.run(
                prompt_id=revised.id,
                parameters=revised.parameters,
                fast_track_id=source.id,
            )

        db.session.remove()
        saved = db.session.get(PromptRequest, revised.id)
        human_prompt = llm_cls.return_value.invoke.call_args.args[0][1][1]

        self.assertIn("EXISTING SCRIPT:", human_prompt)
        self.assertIn("old script", human_prompt)
        self.assertIn("STRICT PARAMETERS", human_prompt)
        self.assertIn("width=2.0m", human_prompt)
        self.assertIn("revised script", saved.generated_code)
        self.assertEqual(saved.status, PromptStatus.COMPLETED)

    def test_legacy_hardcoded_blender_path_is_removed(self):
        task_source = Path("app/tasks/prompt_tasks.py").read_text(encoding="utf-8")
        self.assertNotIn("blender-launcher.exe", task_source)


if __name__ == "__main__":
    unittest.main()
