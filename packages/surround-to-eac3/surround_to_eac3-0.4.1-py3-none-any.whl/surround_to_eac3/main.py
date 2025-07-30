import subprocess
import concurrent.futures
import os
import shutil
import argparse
import json
import threading
import queue
from tqdm import tqdm
from platformdirs import user_config_dir

# --- Constants for Configuration ---
APP_NAME = "eac3-transcode"
APP_AUTHOR = "eac3-transcode"
CONFIG_FILENAME = "options.json"

# Global lock for TQDM writes to prevent interleaving from multiple threads
tqdm_lock = threading.Lock()
SUPPORTED_EXTENSIONS = (".mkv", ".mp4")


def get_video_duration(filepath: str) -> float:
    """Gets the duration of a video file in seconds."""
    if not shutil.which("ffprobe"):
        return 0.0
    
    command = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        filepath
    ]
    try:
        process = subprocess.run(command, capture_output=True, text=True, check=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        return float(process.stdout.strip())
    except (subprocess.CalledProcessError, ValueError):
        return 0.0


def get_stream_info(filepath: str, stream_type: str = "audio") -> tuple[list[dict], list[str]]:
    """
    Retrieves details for specified stream types (audio, video, subtitle) in a file.
    For audio, returns list of dicts with 'index', 'codec_name', 'channels', 'language'.
    For video/subtitle, returns list of dicts with 'index', 'codec_name'.
    """
    logs = []
    if not shutil.which("ffprobe"):
        logs.append(f"    ⚠️ Warning: ffprobe is missing. Cannot get {stream_type} stream info for '{os.path.basename(filepath)}'.")
        return [], logs

    select_streams_option = {
        "audio": "a",
        "video": "v",
        "subtitle": "s"
    }.get(stream_type, "a") # Default to audio if type is unknown

    ffprobe_cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_streams", "-select_streams", select_streams_option, filepath
    ]

    try:
        process = subprocess.run(
            ffprobe_cmd, capture_output=True, text=True, check=False,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        if process.returncode != 0:
            # Non-critical error for this function, main processing will decide to skip/fail
            return [], logs
        if not process.stdout.strip():
            return [], logs # No streams of the selected type found

        data = json.loads(process.stdout)
        streams_details = []
        for stream in data.get("streams", []):
            detail = {
                "index": stream["index"], # Absolute stream index
                "codec_name": stream.get("codec_name", "unknown")
            }
            if stream_type == "audio":
                detail["channels"] = stream.get("channels")
                detail["language"] = stream.get("tags", {}).get("language", "und").lower()
            streams_details.append(detail)
        return streams_details, logs
    except json.JSONDecodeError:
        logs.append(f"    ⚠️ Warning: Failed to decode ffprobe JSON for {stream_type} streams in '{os.path.basename(filepath)}'.")
        return [], logs
    except Exception as e:
        logs.append(f"    ⚠️ Error getting {stream_type} stream info for '{os.path.basename(filepath)}': {e}")
        return [], logs
    

def time_str_to_seconds(time_str: str) -> float:
    """Converts HH:MM:SS.ms time string to seconds."""
    parts = time_str.split(':')
    seconds = float(parts[-1])
    if len(parts) > 1:
        seconds += int(parts[-2]) * 60
    if len(parts) > 2:
        seconds += int(parts[-3]) * 3600
    return seconds


def process_file_with_ffmpeg(
    input_filepath: str,
    final_output_filepath: str | None,
    audio_bitrate: str,
    audio_processing_ops: list[dict], # [{'index':X, 'op':'transcode'/'copy', 'lang':'eng'}]
    duration: float,
    pbar_position: int
) -> tuple[bool, list[str]]:
    """
    Processes a single video file using ffmpeg, writing to a temporary file first.
    """
    logs = []
    if not shutil.which("ffmpeg"):
        logs.append("    🚨 Error: ffmpeg is not installed or not found.")
        return False, logs

    # FFMpeg will write to a temporary file, which we will rename upon success
    temp_output_filepath = final_output_filepath + ".tmp"
    base_filename = os.path.basename(input_filepath)
    output_filename = os.path.basename(final_output_filepath)

    ffmpeg_cmd = ["ffmpeg", "-nostdin", "-i", input_filepath, "-map_metadata", "0"]
    map_operations = []
    output_audio_stream_ffmpeg_idx = 0 # For -c:a:0, -c:a:1 etc.

    # Map Video Streams
    map_operations.extend(["-map", "0:v?", "-c:v", "copy"])
    # Map Subtitle Streams
    map_operations.extend(["-map", "0:s?", "-c:s", "copy"])

    # Map Audio Streams based on operations
    for op_details in audio_processing_ops:
        map_operations.extend(["-map", f"0:{op_details['index']}"])
        if op_details['op'] == 'transcode':
            map_operations.extend([f"-c:a:{output_audio_stream_ffmpeg_idx}", "eac3", f"-b:a:{output_audio_stream_ffmpeg_idx}", audio_bitrate, f"-ac:a:{output_audio_stream_ffmpeg_idx}", "6", f"-metadata:s:a:{output_audio_stream_ffmpeg_idx}", f"language={op_details['lang']}"])
        elif op_details['op'] == 'copy':
            map_operations.extend([f"-c:a:{output_audio_stream_ffmpeg_idx}", "copy"])
        output_audio_stream_ffmpeg_idx += 1
    
    ffmpeg_cmd.extend(map_operations)

    if final_output_filepath.lower().endswith('.mkv'):
        ffmpeg_cmd.extend(['-f', 'matroska'])
    elif final_output_filepath.lower().endswith('.mp4'):
        ffmpeg_cmd.extend(['-f', 'mp4'])

    ffmpeg_cmd.extend(["-y", "-v", "quiet", "-stats_period", "1", "-progress", "pipe:1", temp_output_filepath])

    logs.append(f"    ⚙️ Processing: '{base_filename}' -> '{output_filename}'")

    process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)

    file_pbar = None
    if duration > 0:
        file_pbar = tqdm(total=int(duration), desc=f"└─'{base_filename[:30]}…'", position=pbar_position, unit='s', leave=False, ncols=100)
    
    for line in process.stdout:
        if "out_time_ms" in line:
            try:
                time_us = int(line.strip().split("=")[1])
                elapsed_seconds = time_us / 1_000_000
                update_amount = max(0, elapsed_seconds - file_pbar.n)
                if update_amount > 0:
                    file_pbar.update(update_amount)
            except (ValueError, IndexError):
                continue

    process.wait()
    file_pbar.close()

    if process.returncode == 0:
        if os.path.exists(temp_output_filepath) and os.path.getsize(temp_output_filepath) > 0:
            os.rename(temp_output_filepath, final_output_filepath)
            logs.append(f"    ✅ Success: '{output_filename}' saved.")
            return True, logs
        else:
            logs.append(f"    ⚠️ Warning: ffmpeg reported success, but temp file is missing or empty.")
            return False, logs
    else:
        logs.append(f"    🚨 Error during ffmpeg processing for '{base_filename}'. RC: {process.returncode}")
        stderr_output = process.stderr.read()
        if stderr_output:
            logs.append(f"        ffmpeg stderr:\n{stderr_output.strip()}")
        return False, logs


def process_single_file(filepath: str, pbar_position: int, args: argparse.Namespace, input_path_abs: str) -> str:
    """
    Analyzes and processes a single file, managing temporary files for graceful exit.
    """
    file_specific_logs = []
    final_status = "failed"

    
    # Determine a display name relative to the initial input path for cleaner logs
    display_name = os.path.relpath(filepath, input_path_abs) if os.path.isdir(input_path_abs) else os.path.basename(filepath)
    file_specific_logs.append(f"▶️ Checked: '{display_name}'")
    
    target_languages = [lang.strip().lower() for lang in args.languages.split(',') if lang.strip()]

    audio_streams_details, get_info_logs = get_stream_info(filepath, "audio")
    file_specific_logs.extend(get_info_logs)
    
    audio_ops_for_ffmpeg = []
    if not audio_streams_details:
        file_specific_logs.append("    ℹ️ No audio streams found in this file.")
    else:
        for stream in audio_streams_details:
            lang = stream['language']
            op_to_perform = None
            channels_info = f"{stream.get('channels')}ch" if stream.get('channels') is not None else "N/Ach"
            codec_name = stream.get('codec_name', 'unknown')

            if lang in target_languages:
                is_5_1 = stream.get('channels') == 6
                is_not_ac3_eac3 = codec_name not in ['ac3', 'eac3']
                if is_5_1 and is_not_ac3_eac3:
                    op_to_perform = 'transcode'
                    file_specific_logs.append(f"    🔈 Will transcode: Audio stream #{stream['index']} ({lang}, {channels_info}, {codec_name})")
                else:
                    op_to_perform = 'copy'
                    reason_parts = [f"already {codec_name}" if codec_name in ['ac3', 'eac3'] else None, f"not 5.1 ({channels_info})" if stream.get('channels') != 6 else None]
                    reason = ", ".join(filter(None, reason_parts)) or "meets other criteria for copying"
                    file_specific_logs.append(f"    🔈 Will copy: Audio stream #{stream['index']} ({lang}, {channels_info}, {codec_name}) - Reason: {reason}")
            else:
                file_specific_logs.append(f"    🔈 Will drop: Audio stream #{stream['index']} ({lang}, {channels_info}, {codec_name}) - Not a target language.")

            if op_to_perform:
                audio_ops_for_ffmpeg.append({'index': stream['index'], 'op': op_to_perform, 'lang': lang})

    # First, check if there are any operations at all for target languages
    if not audio_ops_for_ffmpeg:
        file_specific_logs.append(f"    ⏭️ Skipping '{display_name}': No target audio streams to process (copy/transcode).")
        with tqdm_lock:
            for log_msg in file_specific_logs:
                tqdm.write(log_msg)
        final_status = "skipped_no_ops"
        return final_status
    
    needs_transcode = any(op['op'] == 'transcode' for op in audio_ops_for_ffmpeg)
    if not needs_transcode:
        file_specific_logs.append(f"    ⏭️ Skipping '{display_name}': No transcoding required.")
        with tqdm_lock:
            for log_msg in file_specific_logs:
                tqdm.write(log_msg)
        final_status = "skipped_no_transcode"
        return final_status
    
    # Determine final output path
    name, ext = os.path.splitext(os.path.basename(filepath))
    output_filename = f"{name}_eac3{ext}"
    output_dir_for_this_file = os.path.dirname(filepath) # Default to same directory
    if args.output_directory_base: # Input was a folder
        if os.path.isdir(input_path_abs):
            relative_dir = os.path.relpath(os.path.dirname(filepath), start=input_path_abs)
            output_dir_for_this_file = os.path.join(args.output_directory_base, relative_dir) if relative_dir != "." else args.output_directory_base
        else: # Input was a single file
            output_dir_for_this_file = args.output_directory_base
    
    final_output_filepath = os.path.join(output_dir_for_this_file, output_filename)

    # Check if the output file already exists and we are NOT forcing reprocessing.
    if os.path.exists(final_output_filepath) and not args.force_reprocess:
        file_specific_logs.append(f"      ⏭️ Skipping: Output file already exists. Use --force-reprocess to override.")
        with tqdm_lock:
            for log_msg in file_specific_logs:
                tqdm.write(log_msg)
        final_status = "skipped_existing"
        return final_status
    
    # Check for identical paths before starting
    if os.path.abspath(filepath) == os.path.abspath(final_output_filepath):
        file_specific_logs.append(f"    ⚠️ Warning: Input and output paths are identical. Skipping.")
        with tqdm_lock:
            for log_msg in file_specific_logs:
                tqdm.write(log_msg)
        final_status = "skipped_identical_path"
        return final_status
    
    if args.dry_run:
        file_specific_logs.append(f"    DRY RUN: Would process '{display_name}'. No changes will be made.")
        with tqdm_lock:
            for log_msg in file_specific_logs:
                tqdm.write(log_msg)
        # We return 'processed' to indicate it *would* have been processed
        final_status = "processed"
        return final_status

    # Ensure output directory exists before processing
    if not os.path.isdir(output_dir_for_this_file):
        try:
            os.makedirs(output_dir_for_this_file, exist_ok=True)
        except OSError as e:
            file_specific_logs.append(f"    🚨 Error creating output directory '{output_dir_for_this_file}': {e}")
            with tqdm_lock:
                for log_msg in file_specific_logs:
                    tqdm.write(log_msg)
            return "failed"
        
    duration = get_video_duration(filepath)
    if duration == 0:
        file_specific_logs.append(f"    ⚠️ Could not determine duration for '{display_name}'. Per-file progress will not be shown.")
    
    temp_filepath = final_output_filepath + ".tmp"
    try:
        success, ffmpeg_logs = process_file_with_ffmpeg(filepath, final_output_filepath, args.audio_bitrate, audio_ops_for_ffmpeg, duration, pbar_position)
        file_specific_logs.extend(ffmpeg_logs)
        final_status = "processed" if success else "failed"
    finally:
        # This block will run whether the try block succeeded, failed, or was interrupted.
        if os.path.exists(temp_filepath):
            try:
                os.remove(temp_filepath)
            except OSError as e:
                file_specific_logs.append(f"    🚨 Error cleaning up temp file '{temp_filepath}': {e}")

        with tqdm_lock: # Print all logs for this file at the very end of its processing
            for log_msg in file_specific_logs:
                tqdm.write(log_msg)
    return final_status


# Worker initializer to assign a unique position to each worker's progress bar
def worker_init(worker_id_queue):
    threading.current_thread().worker_id = worker_id_queue.get()


def main():
    # Initial check for ffmpeg and ffprobe
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        missing_tools = []
        if not shutil.which("ffmpeg"): missing_tools.append("ffmpeg")
        if not shutil.which("ffprobe"): missing_tools.append("ffprobe")
        print(f"🚨 Error: {', '.join(missing_tools)} is not installed or not found in your system's PATH. Please install ffmpeg.")
        return

    parser = argparse.ArgumentParser(
        description="Advanced video transcoder: E-AC3 for specific audio, language filtering, folder processing.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "-i", "--input",
        required=True,
        help="Path to the input video file or folder.",
        dest="input_path"
    )
    parser.add_argument(
        "-o", "--outdir",
        help="Optional. Base directory to save processed files.\n"
             "If input is a folder, source structure is replicated under this directory.\n"
             "If not set, processed files are saved alongside originals.",
        dest="output_directory_base",
        default=None
    )
    parser.add_argument(
        "-br", "--bitrate",
        help="Audio bitrate for E-AC3 (e.g., '640k', '1536k'). Defaults to '1536k'.",
        dest="audio_bitrate",
        default="1536k"
    )
    parser.add_argument(
        "-l", "--langs",
        help="Comma-separated list of 3-letter audio languages to keep (e.g., 'eng,jpn').\nDefaults to 'eng,jpn'.",
        dest="languages",
        default="eng,jpn"
    )
    parser.add_argument(
        "-j", "--jobs",
        type=int,
        default=os.cpu_count(), # Default to the number of CPU cores
        help=f"Number of files to process in parallel. Defaults to the number of CPU cores on your system ({os.cpu_count()})."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true", # Makes it a flag, e.g., --dry-run
        help="Analyze files and report actions without executing ffmpeg."
    )
    parser.add_argument(
        "--force-reprocess",
        action="store_true",
        help="Force reprocessing of all files, even if an output file with the target name already exists."
    )

    # --- Configuration File Logic ---
    config = {}

    user_config_dir_path = user_config_dir(APP_NAME, APP_AUTHOR)
    user_config_file_path = os.path.join(user_config_dir_path, CONFIG_FILENAME)

    if not os.path.exists(user_config_file_path):
        try:
            defaults = {action.dest: action.default for action in parser._actions if action.dest != "help" and not action.required}
            os.makedirs(user_config_dir_path, exist_ok=True)
            with open(user_config_file_path, 'w') as f:
                json.dump(defaults, f, indent=4)
            print(f"✅ Created default configuration at: {user_config_file_path}")
        except Exception as e:
            print(f"⚠️ Warning: Could not create default config at '{user_config_file_path}': {e}")

    potential_paths = [os.path.join(os.getcwd(), CONFIG_FILENAME), user_config_file_path]
    loaded_config_path = None
    for path in potential_paths:
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    config = json.load(f)
                loaded_config_path = path
                break
            except (json.JSONDecodeError, IOError) as e:
                print(f"⚠️ Warning: Could not read or parse config at '{path}': {e}")
                break
    
    parser.set_defaults(**config)
    args = parser.parse_args()

    if loaded_config_path:
        print(f"✅ Loaded configuration from: {loaded_config_path}")

    if args.dry_run:
        print("--- DRY RUN MODE ENABLED: No files will be modified. ---")

    # --- File Discovery ---
    input_path_abs = os.path.abspath(args.input_path)
    files_to_process_paths = []
    if os.path.isdir(input_path_abs):
        print(f"📁 Scanning folder: {input_path_abs}")
        for root, _, filenames in os.walk(input_path_abs):
            for filename in filenames:
                if filename.lower().endswith(SUPPORTED_EXTENSIONS):
                    files_to_process_paths.append(os.path.join(root, filename))
        if not files_to_process_paths:
            print("    No .mkv or .mp4 files found in the specified folder.")
    elif os.path.isfile(input_path_abs):
        if input_path_abs.lower().endswith((".mkv", ".mp4")):
            files_to_process_paths.append(input_path_abs)
        else:
            print(f"⚠️ Provided file '{args.input_path}' is not an .mkv or .mp4 file. Skipping this input.")
    else:
        print(f"🚨 Error: Input path '{args.input_path}' is not a valid file or directory.")
        return

    if not files_to_process_paths:
        print("No files to process.")
        return

    print(f"\nFound {len(files_to_process_paths)} file(s) to potentially process...")
    # Initialize stats counters
    stats = {
        "processed": 0, 
        "skipped_no_ops": 0, 
        "skipped_no_transcode": 0, 
        "skipped_identical_path": 0,
        "skipped_existing": 0,
        "failed": 0
    }

    worker_id_queue = queue.Queue()
    for i in range(args.jobs):
        worker_id_queue.put(i + 1)

    try:
        with tqdm(total=len(files_to_process_paths), desc="Overall Progress", unit="file", ncols=100, smoothing=0.1, position=0, leave=True) as pbar:
            with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs, initializer=worker_init, initargs=(worker_id_queue,)) as executor:

                def submit_task(filepath):
                    worker_id = threading.current_thread().worker_id
                    return process_single_file(filepath, worker_id, args, input_path_abs)

                future_to_path = {executor.submit(submit_task, path): path for path in files_to_process_paths}

                for future in concurrent.futures.as_completed(future_to_path):
                    path = future_to_path[future]
                    try:
                        status = future.result() 
                        if status in stats:
                            stats[status] += 1
                        else:
                            stats["failed"] += 1 
                            with tqdm_lock:
                                tqdm.write(f"🚨 UNKNOWN STATUS '{status}' for '{os.path.basename(path)}'.")
                    except Exception as exc:
                        with tqdm_lock:
                             tqdm.write(f"🚨 CRITICAL ERROR during task for '{os.path.basename(path)}': {exc}")
                        stats["failed"] += 1
                    finally:
                        pbar.update(1)

    except KeyboardInterrupt:
        print("\n\n🚨 Process interrupted by user. Shutting down gracefully... Any in-progress files have been cleaned up.")
        # The 'finally' blocks in each thread will handle cleanup.
        # Exiting here.
        return

    # Print summary of operations
    summary_title = "--- Dry Run Summary ---" if args.dry_run else "--- Processing Summary ---"
    processed_label = "Would be processed" if args.dry_run else "Successfully processed"
    
    print()
    print(f"\n{summary_title}")
    print(f"Total files checked: {len(files_to_process_paths)}")
    print(f"✅ {processed_label}: {stats['processed']}")
    total_skipped = stats['skipped_no_ops'] + stats['skipped_no_transcode'] + stats['skipped_identical_path'] + stats['skipped_existing']
    print(f"⏭️ Total Skipped: {total_skipped}")
    if total_skipped > 0:
        print(f"    - No target audio operations: {stats['skipped_no_ops']}")
        print(f"    - No transcoding required (all copy): {stats['skipped_no_transcode']}")
        print(f"    - Identical input/output path: {stats['skipped_identical_path']}")
        print(f"    - Output file already exists: {stats['skipped_existing']}")
    print(f"🚨 Failed to process: {stats['failed']}")
    print("--------------------------")
