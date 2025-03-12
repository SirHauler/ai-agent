# convert audio to midi

import subprocess
import os
def audio2midi(audio_file_path: str, output_file_path = None):
    if output_file_path is None:
        # basename of the audio file
        print("Audio file path:", audio_file_path)
        print("Current working directory:", os.getcwd())
        if audio_file_path.endswith(".wav"):
            midi_filename = os.path.basename(audio_file_path).replace(".wav", ".mid")
        else:
            midi_filename = os.path.basename(audio_file_path).replace(".mp3", ".mid")
        output_file_path = os.path.join(os.getcwd(), "results", midi_filename)

    run_transkun(audio_file_path, output_file_path, use_gpu=True)

    return output_file_path

def run_transkun(input_path: str, output_path: str, use_gpu: bool = False):
    """
    Runs the transkun command-line tool with the given input and output file paths.

    :param input_path: Path to the input MP3 file.
    :param output_path: Path to the output MIDI file.
    :param use_gpu: Whether to enable GPU acceleration (default: False).
    """
    try:
        command = ["transkun", input_path, output_path]
        
        if use_gpu:
            command.append("--device")
            command.append("cuda")

        result = subprocess.run(command, check=True, capture_output=True, text=True)
        
        print("Transkun Output:", result.stdout)
        print("Transkun Error (if any):", result.stderr)
        print(f"Conversion successful: {input_path} -> {output_path}")

    except subprocess.CalledProcessError as e:
        print(f"Error running transkun: {e.stderr}")




