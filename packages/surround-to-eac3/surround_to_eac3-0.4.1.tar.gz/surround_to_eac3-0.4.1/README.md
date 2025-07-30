# Surround to E-AC3 Transcoder (eac3-transcode)

[![PyPI version](https://img.shields.io/pypi/v/surround-to-eac3.svg)](https://pypi.org/project/surround-to-eac3/)
[![PyPI pyversions](https://img.shields.io/pypi/pyversions/surround-to-eac3.svg)](https://pypi.org/project/surround-to-eac3/)

**A** command-line utility to intelligently find and convert 5.1 surround sound audio tracks in your video files (`.mkv`, `.mp4`) to **the E-AC3 (Dolby Digital Plus) format, while preserving other streams.**

This tool is perfect for users who want to standardize their media library's audio, ensuring compatibility and high quality for 5.1 channel audio tracks while allowing you to filter by language.

## Overview

`eac3-transcode` automates the often tedious process of inspecting video files, identifying specific audio tracks, and re-encoding them. It's designed to be smart about which tracks to process:

* **Scans Individual Files or Entire Directories:** 

  * Process a single video or batch-process an entire folder (including subfolders).

* **High-Performance Parrallel Processing:**

  * Processes multiple files simultaneously to dramatically speed up batch jobs, automatically using the optimal number of CPU cores.

* **User-Friendly Configuration:**
  * Automatically creates a default `options.json` file on the first run for easy customization. Command-line options always override the config file.

* **Interactive Progress Bar:**

  * A clean `tqdm` progress bar shows you the overall progress, ETA, and processing speed.

* **Safe Dry Run Mode:**

  * Run the script with a `--dry-run` flag to see a report of exactly what changes would be made without modifying any files.

* **Targets Specific Languages:** 

  * By default, it processes English (`eng`) and Japanese (`jpn`) audio streams, but this is **fully customizable** via a command-line argument.

* **Intelligent Transcoding:**

  * Converts 5.1 channel audio streams (that aren't already `ac3` or `eac3`) in your target languages to `eac3`.

* **Smart Copying:**

  * Copies target language audio streams that are already in `ac3` or `eac3` format.

  * Copies target language audio streams that are not 5.1 channels (e.g., stereo).

* **Stream Preservation:**

  * Video streams are always copied without re-encoding (lossless).

  * Subtitle streams are always copied without re-encoding.

* **Efficient Processing:**

  * Audio streams not in your target languages are dropped to save space and processing time.

  * Files are skipped entirely if no audio streams in the target languages meet the criteria for transcoding, preventing empty or unnecessary output files.

* **Efficient Processing:**

  * The script automatically skips processing a file if an output file with the target name already exists. This allows you to safely re-run the script on the same directory to only process new files. Use the `--force-reprocess` flag to override this behavior.

* **Flexible Output:** 

  * Save processed files alongside originals or in a specified output directory, maintaining the source folder structure if applicable.

## Prerequisites

Before you can use `eac3-transcode`, you **must** have **FFmpeg** installed on your system and accessible in your system's PATH. FFmpeg is used for both analyzing (ffprobe) and processing (ffmpeg) the video files.

* **Windows:** Download from [ffmpeg.org](https://ffmpeg.org/download.html#build-windows) and add the `bin` directory to your system's PATH.

* **macOS:** Install via Homebrew: `brew install ffmpeg`

* **Linux:** Install using your distribution's package manager (e.g., `sudo apt update && sudo apt install ffmpeg` for Debian/Ubuntu).

You can verify your FFmpeg installation by opening a terminal or command prompt and typing `ffmpeg -version` and `ffprobe -version`.

## Installation

Install `eac3-transcode` directly from PyPI using pip:

`pip install surround-to-eac3`  
It's recommended to install it in a virtual environment.

## Usage

The primary command is `eac3-transcode`.

### Basic Examples:

1. **See what the script would do without changing any files (Dry Run):**

`eac3-transcode --input "/path/to/your/video_folder/" --dry-run  `  
__*This is the safest way to start, to confirm the script's logic matches your expectations.*__

2. **Process** all videos in a folder (using defaults or your config file):**

`eac3-transcode --input "/path/to/your/video_folder/"`  
__*This will use all available CPU cores for maximum speed.*__

3. **Process videos and save them to a specific output directory:**

`eac3-transcode --input "/path/to/your/video_folder/" --outdir "/path/to/your/processed_videos/"`  

*If `/path/to/your/video_folder/` contains subfolders, the structure will be replicated under `/path/to/your/processed_videos/`.*

4. **Process with custom options (different languages, bitrate, and limited to 4 parallel jobs):**

`eac3-transcode --input "video.mkv" --langs "eng,spa" --bitrate "640k" --jobs 4`

5. **Force the script to re-process all files, even those that already exist:**

`eac3-transcode --input "/path/to/your/video_folder/" --force-reprocess`

## Configuration

For convenience, the script supports a `options.json` file to set your preferred defaults.

### How it Works

1. **Automatic Creation:** The **first time** you run the script, it will automatically create a default `options.json` file in your user's configuration directory. It will print a message showing you where the file was created.

2. **Search Order:** When you run the command,  it looks for a `options.json` file in this order:

    * **1. Current Directory:** A `options.json` in the folder you are running the command from (for project-specific settings).

    * **2. User Config Directory:** The global config file it created on the first run.

3. **Overrides:** Any option you provide on the command line (e.g., `--bitrate 640k`) will always take precedence over the setting in the config file for that specific run.

### Config File Location

The global config file is located in the standard directory for your operating system:

* Windows: `C:\Users\<YourUser>\AppData\Roaming\eac3-transcode\options.json`

* macOS: `/Users/<YourUser>/Library/Application Support/eac3-transcode/options.json`

* Linux: `/home/<YourUser>/.config/eac3-transcode/options.json`

**Example `options.json`**  
You can edit this JSON file ot change your default settings.  
```
{
    "output_directory_base": null,
    "audio_bitrate": "640k",
    "languages": "eng,jpn",
    "jobs": 8,
    "dry_run": false,
    "force_reprocess": false
}
```

## Command-Line Options

**Usage:**

`eac3-transcode [-h] -i INPUT_PATH [-o OUTPUT_DIRECTORY_BASE] [-br AUDIO_BITRATE] [-l LANGUAGES] [-j JOBS] [--dry-run] [--force-reprocess]`  
An advanced video transcoder that processes files to use E-AC3 for specific audio tracks, filters by language, and can process entire folders.

**Options:**

* `-h, --help`  
    Show this help message and exit.

* `-i INPUT_PATH, --input INPUT_PATH`  
    **(Required)** Path to the input video file or folder.

* `-o OUTPUT_DIRECTORY_BASE, --outdir OUTPUT_DIRECTORY_BASE`  
    **(Optional)** Base directory to save processed files. If the input is a folder, the original source structure is replicated under this directory. If this option is not set, processed files will be saved alongside the original files.

* `-br AUDIO_BITRATE, --bitrate AUDIO_BITRATE`  
    **(Optional)** Sets the audio bitrate for the E-AC3 stream (e.g., '640k', '1536k'). Defaults to '1536k'.

* `-l LANGUAGES, --langs LANGUAGES`  
    **(Optional)** Comma-separated list of 3-letter audio languages to keep (e.g., 'eng,spa,fre'). Defaults to 'eng,jpn'.

* `-j JOBS, --jobs JOBS`  
    **(Optional)** Number of files to process in parallel. Defaults to the number of CPU cores on your system.

* `--dry-run`  
    **(Optional)** Analyze files and report actions without executing ffmpeg. No files will be modified.

* `--force-reprocess`  
    **(Optional)** Force reprocessing of all files, even if an output file with the target name already exists.


## How It Works

1. **File Discovery:** The script scans the input path for `.mkv` and `.mp4` files.

2. **Pre-flight Checks:**

    * **Existence Check:** The script first determines the final output filename. If that file already exists and `--force-reprocess` is NOT used, the script skips the file and moves to the next one.

3. **Stream Analysis (using `ffprobe`):** For each file:

   * It extracts information about all audio streams: codec, channels, and language tags.

4. **Decision Logic:**

   * **Language Filter:** Only audio streams matching the languages provided with the `-l LANGUAGES, --langs LANGUAGES` option are considered for keeping. **This defaults to `eng,jpn`**. Others are marked to be dropped.

   * **Transcode Criteria:** A target language stream is transcoded to E-AC3 if it has 6 audio channels (5.1) and its current codec is not `ac3` or `eac3`.

   * **Copy Criteria:** A target language stream is copied directly if it's already `ac3`/`eac3` or it does not have 6 channels.

   * **File Skipping:** If no audio streams are marked for 'transcode', the entire file is skipped.

5. **Processing (using `ffmpeg`):**

   * If not in `--dry-run` mode, a new FFmpeg command is constructed. This processing is done in parallel for multiple files, with a progress bar updating you on the status of the batch.

   * Video (`-c:v copy`) and subtitle (`-c:s copy`) streams are mapped and copied directly.

   * Selected audio streams are mapped and either transcoded to `eac3` with the specified bitrate (and forced to 6 channels) or copied (`-c:a copy`).

   * Language metadata is set for transcoded audio streams.

   * The output file is named by appending `_eac3` to the original filename (before the extension).

## Troubleshooting

* **`ffmpeg` or `ffprobe` not found:**

  * Ensure FFmpeg is installed correctly and its `bin` directory is in your system's PATH environment variable. See the [Prerequisites](#prerequisites) section.

* **High CPU/Disk Usage:**

  * The script defaults to using all your CPU cores for maximum speed. If your system becomes unresponsive during processing, you can limit the number of parallel jobs with the `--jobs` flag (e.g., `--jobs 2`).

* **No files processed / "Skipping 'filename': No audio streams in the desired languages... meet criteria..."**:

  * This is expected if files don't meet the criteria. Check the log message:

    * **"Output file already exists.":** This is the default behavior. The script will not re-process a file if the output (`filename_eac3.mkv`) is already present. Use `--force-reprocess` if you want to overwrite it.

    * **"No audio streams... meet criteria":** This means no audio tracks in the target languages require transcoding to E-AC3. This reflects the default languages (`eng,jpn`) or the ones you specified with `--langs`.

* **Permission Errors:**

  * Ensure you have write permissions for the output directory and read permissions for the input files/directory.

* **Unexpected FFmpeg errors:**

  * The script prints FFmpeg's stderr output on failure, which can provide clues. Ensure your video files are not corrupted.

## Contributing

Contributions, issues, and feature requests are welcome! Feel free to check [issues page](https://gitea.jono-rams.work/jono/ffmpeg-audio-transcoder/issues).

## License

This project is licensed under the MIT License - see the [LICENSE](https://gitea.jono-rams.work/jono/ffmpeg-audio-transcoder/src/branch/main/LICENSE) file for details.

## Acknowledgements

* This tool relies heavily on the fantastic [FFmpeg](https://ffmpeg.org/) project.
* The progress bar is powered by [tqdm](https://github.com/tqdm/tqdm).
