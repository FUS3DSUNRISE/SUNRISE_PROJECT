import os
import subprocess
import logging
import traceback
import time
import shutil       
import platform
from dotenv import load_dotenv
from worker import celery
from app.extensions import db
from app.models.prompt import PromptRequest, PromptStatus
from langchain_openai import ChatOpenAI
from app.services.prompt_service import Parameters, PromptService, build_llm_prompt
import config

load_dotenv()


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("tasks.process_prompt")


def get_blender_executable():
    # 1. Check in .env file
    env_blender = os.getenv("BLENDER_PATH")
    if env_blender and os.path.exists(env_blender):
        return env_blender
        
    # 2. Check system environment variables (PATH)
    path_blender = shutil.which("blender")
    if path_blender:
        return path_blender
        
    # 3. Check standard Windows and Steam installation paths
    if platform.system() == "Windows":
        drives = ["C:\\", "D:\\"]
        folders = [
            r"Program Files\Blender Foundation",
            r"Program Files (x86)\Steam\steamapps\common\Blender"
        ]
        for drive in drives:
            for folder in folders:
                search_path = os.path.join(drive, folder)
                if os.path.exists(search_path):
                    for root, dirs, files in os.walk(search_path):
                        if "blender.exe" in files:
                            return os.path.join(root, "blender.exe")
                            
    # 4. Check standard macOS path
    elif platform.system() == "Darwin":
        mac_path = "/Applications/Blender.app/Contents/MacOS/Blender"
        if os.path.exists(mac_path):
            return mac_path
            
    return None


class ConfigurationError(Exception):
    """Missing or invalid environment / config values."""


class LLMError(Exception):
    """Failure during LLM invocation."""


class BlenderError(Exception):
    def __init__(self, message, stderr="", returncode=None):
        super().__init__(message)
        self.stderr = stderr
        self.returncode = returncode


def _resolve_config(attr: str, fallback: str) -> str:
    return (
        getattr(config, attr, None)
        or getattr(getattr(config, "Config", object()), attr, None)
        or fallback
    )

def load_system_prompt() -> str:
    prompt_path = _resolve_config(
        "LLM_SYSTEM_PROMPT_PATH",
        "app/prompts/system_prompt.txt"
    )

    if not os.path.exists(prompt_path):
        raise ConfigurationError(f"System prompt file not found: {prompt_path}")

    with open(prompt_path, "r", encoding="utf-8") as file:
        return file.read().strip()


def _write_script(prompt_id: int, code: str) -> str:
    filename = f"temp_script_{prompt_id}.py"
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(code)
        logger.debug("Script written to %s (%d bytes)", filename, len(code))
    except OSError as exc:
        raise OSError(f"Could not write temp script '{filename}': {exc}") from exc
    return filename


def _cleanup(path: str) -> None:
    try:
        if path and os.path.exists(path):
            os.remove(path)
            logger.debug("Cleaned up temp file: %s", path)
    except OSError as exc:
        logger.warning("Could not remove temp file '%s': %s", path, exc)


def _fail_prompt(prompt: PromptRequest, message: str) -> None:
    prompt.status = PromptStatus.FAILED
    prompt.error_message = message[:2000]  # guard against oversized DB writes
    db.session.commit()


def _strip_code_fences(content: str) -> str:
    return content.replace("```python", "").replace("```", "").strip()


def _prepare_generated_code(code: str, output_path: str) -> str:
    export_line = f"bpy.ops.export_scene.gltf(filepath='{output_path}', export_format='GLB')"
    legacy_export_line = "bpy.ops.export_scene.gltf(filepath='static/models/result.glb', export_format='GLB')"

    code = code.strip()
    if legacy_export_line in code:
        return code.replace(legacy_export_line, export_line)
    if export_line in code:
        return code
    return f"{code}\n\n{export_line}"


def _build_generation_prompt(prompt: PromptRequest, parameters: dict) -> str:
    final_user_prompt = PromptService.create_final_prompt(
        user_query=prompt.prompt_text,
        parameters=parameters,
    )

    if not parameters:
        return final_user_prompt

    try:
        validated_params = Parameters(**parameters)
    except Exception as exc:
        logger.warning("Parameter validation failed in task for prompt_id=%s: %s", prompt.id, exc)
        return final_user_prompt

    return build_llm_prompt(final_user_prompt, validated_params)

@celery.task(
    bind=True,
    max_retries=2,
    default_retry_delay=10,
)

def process_prompt_task(self, prompt_id: int, parameters=None, fast_track_id=None):
    from app import create_app

    app = create_app()

    with app.app_context():
        script_filename = None
        prompt = PromptRequest.query.get(prompt_id)

        if not prompt:
            logger.error("Prompt ID %s not found in database - aborting.", prompt_id)
            return
        
        

        if parameters is None:
            parameters = prompt.parameters or {}

        logger.info(
            "Prompt loaded | prompt_id=%s user_id=%s status=%s has_parameters=%s fast_track=%s",
            prompt_id,
            prompt.user_id,
            prompt.status.value,
            bool(parameters),
            bool(fast_track_id),
        )

        logger.info(
            "Task started | prompt_id=%s status=%s fast_track_id=%s",
            prompt_id,
            prompt.status,
            fast_track_id,
        )

        try:
            prompt.status = PromptStatus.PROCESSING
            db.session.commit()

            base_url = _resolve_config("LLM_BASE_URL", "https://api.groq.com/openai/v1")
            model_name = _resolve_config("LLM_MODEL", "llama-3.3-70b-versatile")
            api_key = _resolve_config("LLM_API_KEY", "")
            temperature = float(_resolve_config("LLM_TEMPERATURE", "0.2"))

            if not api_key:
                raise ConfigurationError("LLM_API_KEY is empty - set it in .env or config.")

            logger.info(
                "LLM config | base_url=%s model=%s temperature=%s system_prompt_path=%s prompt_id=%s",
                base_url,
                model_name,
                temperature,
                _resolve_config("LLM_SYSTEM_PROMPT_PATH", "app/prompts/system_prompt.txt"),
                prompt_id,
            )

            llm = ChatOpenAI(
                base_url=base_url,
                api_key=api_key,
                model=model_name,
                temperature=temperature,
            )

            if fast_track_id:

                source = PromptRequest.query.get(fast_track_id)
                if not source or not source.generated_code:
                    raise LLMError("Source for fast-track not found or has no code.")

                logger.info("Fast-track mode: revising existing code from ID=%s", fast_track_id)

                generation_prompt = _build_generation_prompt(prompt, parameters)

                modification_command = prompt.modification_command or ""

                human_prompt = (
                    "Revise the existing Blender Python script below.\n"
                    "You must update the model based on BOTH the updated parameters AND the modification command.\n\n"
                    "If there is any conflict, the parameters must be strictly respected.\n\n"

                    f"MODIFICATION COMMAND:\n{modification_command}\n\n"

                    f"UPDATED REQUEST (parameters):\n{generation_prompt}\n\n"

                    "EXISTING SCRIPT:\n"
                    f"{source.generated_code}"
            )
                
            else:
                human_prompt = _build_generation_prompt(prompt, parameters)

            logger.info("LLM input prepared | prompt_id=%s", prompt_id)
            logger.info(
                "Generation mode | prompt_id=%s mode=%s parameters=%s",
                prompt_id,
                "modification" if fast_track_id else "creation",
                parameters,
            )
            
            logger.info(
                "LLM human prompt preview | prompt_id=%s preview=%s",
                prompt_id,
                human_prompt[:500],
            )

            

            t0 = time.perf_counter()
            try:

                system_msg = load_system_prompt()

                logger.info(
                    "LLM system prompt loaded | prompt_id=%s length=%d",
                    prompt_id,
                    len(system_msg),
                )
                
                response = llm.invoke([
                    ("system", system_msg),
                    ("human", human_prompt),
                ])

            except Exception as exc:
                raise LLMError(f"LLM call failed: {exc}") from exc

            elapsed_llm = time.perf_counter() - t0
            logger.info(
                "LLM response received | prompt_id=%s elapsed=%.2fs tokens~%d",
                prompt_id,
                elapsed_llm,
                len(response.content) // 4,
            )

            logger.info(
                "LLM output preview | prompt_id=%s preview=%s",
                prompt_id,
                response.content[:500],
            )

            generated_code = _strip_code_fences(response.content)
            logger.info(
                "Generated code validation | prompt_id=%s contains_import_bpy=%s code_length=%d",
                prompt_id,
                "import bpy" in generated_code,
                len(generated_code),
            )
            
            if "import bpy" not in generated_code:
                raise LLMError("Generated code does not contain 'import bpy' - likely malformed.")
            

            output_filename = f"prompt_{prompt_id}.glb"
            output_path = f"static/models/{output_filename}"
            generated_code = _prepare_generated_code(generated_code, output_path)

            logger.debug("Generated code preview (first 300 chars):\n%s", generated_code[:300])

            prompt.generated_code = generated_code
            prompt.error_message = None
            db.session.commit()

            script_filename = _write_script(prompt_id, generated_code)

            logger.info(
                "Temporary script ready | prompt_id=%s output_path=%s",
                prompt_id,
                output_path,
            )

            blender_path = get_blender_executable()
            if not blender_path:
                raise ConfigurationError(
                    "Blender executable not found automatically! Please set BLENDER_PATH in your .env file."
                )

            logger.info(
                "Launching Blender | prompt_id=%s blender_path=%s script=%s timeout=%ss",
                prompt_id,
                blender_path,
                script_filename,
                120,
            )
            t1 = time.perf_counter()

            result = subprocess.run(
                [blender_path, "--background", "--python", script_filename],
                capture_output=True,
                text=True,
                timeout=120,
            )

            elapsed_blender = time.perf_counter() - t1
            logger.info(
                "Blender finished | prompt_id=%s returncode=%d elapsed=%.2fs",
                prompt_id,
                result.returncode,
                elapsed_blender,
            )

            if result.returncode != 0:
                logger.error(
                    "Blender stderr (prompt_id=%s):\n%s",
                    prompt_id,
                    result.stderr[-3000:],
                )
                raise BlenderError(
                    "Blender exited with non-zero return code.",
                    stderr=result.stderr,
                    returncode=result.returncode,
                )

            if result.stderr:
                logger.warning(
                    "Blender stderr (non-fatal, prompt_id=%s):\n%s",
                    prompt_id,
                    result.stderr[-1000:],
                )

            if not os.path.exists(output_path):
                raise BlenderError(
                    f"Blender ran successfully but output file was not created: {output_path}",
                    stderr=result.stderr,
                )

            glb_size = os.path.getsize(output_path)
            logger.info(
                "GLB created | prompt_id=%s path=%s size=%d bytes",
                prompt_id,
                output_path,
                glb_size,
            )

            prompt.status = PromptStatus.COMPLETED
            prompt.result_path = f"/static/models/{output_filename}"
            db.session.commit()
            logger.info("Task completed | prompt_id=%s result_path=%s", prompt_id, prompt.result_path)

        except ConfigurationError as exc:
            logger.critical("Configuration error | prompt_id=%s: %s", prompt_id, exc)
            _fail_prompt(prompt, str(exc))

        except LLMError as exc:
            logger.error("LLM error | prompt_id=%s: %s", prompt_id, exc)
            _fail_prompt(prompt, str(exc))
            try:
                raise self.retry(exc=exc)
            except self.MaxRetriesExceededError:
                logger.error("Max retries exceeded for LLM | prompt_id=%s", prompt_id)

        except BlenderError as exc:
            logger.error(
                "Blender error | prompt_id=%s returncode=%s: %s\nstderr tail:\n%s",
                prompt_id,
                exc.returncode,
                exc,
                exc.stderr[-2000:],
            )
            _fail_prompt(prompt, str(exc))

        except subprocess.TimeoutExpired:
            msg = "Blender process timed out after 120 seconds."
            logger.error("%s | prompt_id=%s", msg, prompt_id)
            _fail_prompt(prompt, msg)

        except Exception as exc:
            tb = traceback.format_exc()
            logger.error("Unexpected error | prompt_id=%s:\n%s", prompt_id, tb)
            _fail_prompt(prompt, f"Unexpected error: {exc}")
            try:
                raise self.retry(exc=exc)
            except self.MaxRetriesExceededError:
                logger.error("Max retries exceeded | prompt_id=%s", prompt_id)

        finally:
            _cleanup(script_filename)
