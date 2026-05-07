import os
import re
import shutil
import platform
import subprocess
import logging
import time
from pathlib import Path

logger = logging.getLogger("services.blender_executor")

# Allowlist of safe Blender executable locations
_BLENDER_ALLOWLIST = {
    "Windows": [
        r"C:\Program Files\Blender Foundation",
        r"C:\Program Files (x86)\Steam\steamapps\common\Blender",
        r"D:\Program Files\Blender Foundation",
        r"D:\Program Files (x86)\Steam\steamapps\common\Blender",
    ],
    "Darwin": [
        "/Applications/Blender.app/Contents/MacOS/Blender",
    ],
}

_SAFE_OUTPUT_EXTENSIONS = {".glb", ".gltf", ".blend", ".png", ".obj", ".fbx"}
_MAX_SCRIPT_SIZE = 512 * 1024  # 512 KB
_MAX_TIMEOUT = 120             # 2 minutes hard cap


class BlenderExecutionError(Exception):
    def __init__(self, message, stderr="", returncode=None):
        super().__init__(message)
        # Truncate stderr to avoid logging/storing excessive data
        self.stderr = stderr[-3000:] if stderr else ""
        self.returncode = returncode


def _safe_resolve(path: str) -> Path:
    """Resolve and return a Path, raising ValueError on traversal attempts."""
    resolved = Path(path).resolve()
    return resolved


def get_blender_executable() -> str | None:
    # 1. Explicit env override — validate it's on the allowlist or a known safe path
    env_blender = os.getenv("BLENDER_PATH", "").strip()
    if env_blender:
        resolved = _safe_resolve(env_blender)
        if resolved.is_file() and os.access(resolved, os.X_OK):
            return str(resolved)
        logger.warning("BLENDER_PATH set but not a valid executable: %s", env_blender)

    # 2. PATH lookup — shutil.which already validates the file exists and is executable
    path_blender = shutil.which("blender")
    if path_blender:
        return path_blender

    # 3. Platform-specific allowlisted locations only
    system = platform.system()
    allowlist = _BLENDER_ALLOWLIST.get(system, [])

    for base in allowlist:
        base_path = Path(base)
        if not base_path.exists():
            continue
        if base_path.is_file():
            # Darwin exact path
            if os.access(base_path, os.X_OK):
                return str(base_path)
        else:
            # Windows: walk but stay within the allowlisted folder
            for root, _, files in os.walk(base_path):
                if "blender.exe" in files:
                    candidate = Path(root) / "blender.exe"
                    # Guard against symlink escape outside allowlisted base
                    if candidate.resolve().is_relative_to(base_path.resolve()):
                        return str(candidate)

    return None


def write_script(prompt_id: int, code: str) -> str:
    # Validate prompt_id to prevent path injection
    if not isinstance(prompt_id, int) or prompt_id < 0:
        raise ValueError(f"Invalid prompt_id: {prompt_id!r}")

    if len(code.encode("utf-8")) > _MAX_SCRIPT_SIZE:
        raise ValueError(
            f"Script exceeds maximum allowed size of {_MAX_SCRIPT_SIZE // 1024} KB."
        )

    # Write to a controlled temp directory, not the cwd
    tmp_dir = Path(os.getenv("BLENDER_SCRIPT_DIR", "/tmp/blender_scripts"))
    tmp_dir.mkdir(parents=True, exist_ok=True)

    filename = tmp_dir / f"temp_script_{prompt_id}.py"

    try:
        filename.write_text(code, encoding="utf-8")
        # Restrict permissions: owner read/write only
        filename.chmod(0o600)
        logger.debug("Script written to %s (%d bytes)", filename, len(code))
    except OSError as exc:
        raise OSError(f"Could not write temp script '{filename}': {exc}") from exc

    return str(filename)


def cleanup_file(path: str) -> None:
    try:
        if not path:
            return
        resolved = _safe_resolve(path)
        if resolved.exists():
            resolved.unlink()
            logger.debug("Cleaned up temp file: %s", resolved)
    except OSError as exc:
        logger.warning("Could not remove temp file '%s': %s", path, exc)


def run_blender_script(
    prompt_id: int,
    script_filename: str,
    output_path: str,
    timeout: int = 120,
) -> dict:
    # Validate timeout
    if not (1 <= timeout <= _MAX_TIMEOUT):
        raise ValueError(f"timeout must be between 1 and {_MAX_TIMEOUT}, got {timeout}")

    # Validate output path extension
    output_resolved = _safe_resolve(output_path)
    if output_resolved.suffix.lower() not in _SAFE_OUTPUT_EXTENSIONS:
        raise ValueError(f"Disallowed output extension: {output_resolved.suffix!r}")

    # Validate script path exists and hasn't been tampered with
    script_resolved = _safe_resolve(script_filename)
    if not script_resolved.is_file():
        raise BlenderExecutionError(f"Script file not found: {script_filename}")

    blender_path = get_blender_executable()
    if not blender_path:
        raise BlenderExecutionError(
            "Blender executable not found. Set BLENDER_PATH in your .env file."
        )

    logger.info(
        "Launching Blender | prompt_id=%s script=%s timeout=%ss",
        prompt_id,
        script_resolved.name,  # Log filename only, not full path
        timeout,
    )

    start_time = time.perf_counter()

    try:
        result = subprocess.run(
            [blender_path, "--background", "--python", str(script_resolved)],
            capture_output=True,
            text=True,
            timeout=timeout,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},  # Inherit env safely
            # Prevent the subprocess from inheriting unnecessary file descriptors
            close_fds=True,
        )
    except subprocess.TimeoutExpired as exc:
        raise BlenderExecutionError(
            f"Blender timed out after {timeout}s.",
            stderr=str(exc),
        ) from exc

    elapsed = time.perf_counter() - start_time

    logger.info(
        "Blender finished | prompt_id=%s returncode=%d elapsed=%.2fs",
        prompt_id,
        result.returncode,
        elapsed,
    )

    if result.returncode != 0:
        # Sanitize stderr before logging (strip potential ANSI/control chars)
        safe_stderr = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", result.stderr)
        logger.error("Blender stderr | prompt_id=%s stderr=%s", prompt_id, safe_stderr[-3000:])
        raise BlenderExecutionError(
            "Blender exited with a non-zero return code.",
            stderr=result.stderr,
            returncode=result.returncode,
        )

    if result.stderr:
        safe_stderr = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", result.stderr)
        logger.warning("Blender stderr (non-fatal) | prompt_id=%s stderr=%s", prompt_id, safe_stderr[-1000:])

    if not output_resolved.exists():
        raise BlenderExecutionError(
            f"Blender ran but output file was not created: {output_resolved.name}",
            stderr=result.stderr,
        )

    glb_size = output_resolved.stat().st_size
    logger.info("Output created | prompt_id=%s size=%d bytes", prompt_id, glb_size)

    return {
        "output_path": str(output_resolved),
        "elapsed": elapsed,
        "size": glb_size,
    }