import os
import shutil
import platform
import subprocess
import logging
import time


logger = logging.getLogger("services.blender_executor")


class BlenderExecutionError(Exception):
    def __init__(self, message, stderr="", returncode=None):
        super().__init__(message)
        self.stderr = stderr
        self.returncode = returncode


def get_blender_executable():
    env_blender = os.getenv("BLENDER_PATH")
    if env_blender and os.path.exists(env_blender):
        return env_blender

    path_blender = shutil.which("blender")
    if path_blender:
        return path_blender

    if platform.system() == "Windows":
        drives = ["C:\\", "D:\\"]
        folders = [
            r"Program Files\Blender Foundation",
            r"Program Files (x86)\Steam\steamapps\common\Blender",
        ]

        for drive in drives:
            for folder in folders:
                search_path = os.path.join(drive, folder)
                if os.path.exists(search_path):
                    for root, dirs, files in os.walk(search_path):
                        if "blender.exe" in files:
                            return os.path.join(root, "blender.exe")

    elif platform.system() == "Darwin":
        mac_path = "/Applications/Blender.app/Contents/MacOS/Blender"
        if os.path.exists(mac_path):
            return mac_path

    return None


def write_script(prompt_id: int, code: str) -> str:
    filename = f"temp_script_{prompt_id}.py"

    try:
        with open(filename, "w", encoding="utf-8") as file:
            file.write(code)

        logger.debug("Script written to %s (%d bytes)", filename, len(code))

    except OSError as exc:
        raise OSError(f"Could not write temp script '{filename}': {exc}") from exc

    return filename


def cleanup_file(path: str) -> None:
    try:
        if path and os.path.exists(path):
            os.remove(path)
            logger.debug("Cleaned up temp file: %s", path)

    except OSError as exc:
        logger.warning("Could not remove temp file '%s': %s", path, exc)


def run_blender_script(prompt_id: int, script_filename: str, output_path: str, timeout: int = 120):
    blender_path = get_blender_executable()

    if not blender_path:
        raise BlenderExecutionError(
            "Blender executable not found automatically. Please set BLENDER_PATH in your .env file."
        )

    logger.info(
        "Launching Blender | prompt_id=%s blender_path=%s script=%s timeout=%ss",
        prompt_id,
        blender_path,
        script_filename,
        timeout,
    )

    start_time = time.perf_counter()

    try:
        result = subprocess.run(
            [blender_path, "--background", "--python", script_filename],
            capture_output=True,
            text=True,
            timeout=timeout,
        )

    except subprocess.TimeoutExpired as exc:
        raise BlenderExecutionError(
            f"Blender process timed out after {timeout} seconds.",
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
        logger.error(
            "Blender stderr | prompt_id=%s stderr=%s",
            prompt_id,
            result.stderr[-3000:],
        )

        raise BlenderExecutionError(
            "Blender exited with non-zero return code.",
            stderr=result.stderr,
            returncode=result.returncode,
        )

    if result.stderr:
        logger.warning(
            "Blender stderr non-fatal | prompt_id=%s stderr=%s",
            prompt_id,
            result.stderr[-1000:],
        )

    if not os.path.exists(output_path):
        raise BlenderExecutionError(
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

    return {
        "output_path": output_path,
        "elapsed": elapsed,
        "size": glb_size,
    }