# convert midi to score

import os
def midi2score(midi_file_path: str):
    return _midi2score(midi_file_path)


def _midi2score(midi_file_path: str, output_file_path = None):
    import requests

    # Prepare the endpoint URL
    url = "http://localhost:8080/invocations"

    if output_file_path is None:
        music_xml_filename = os.path.basename(midi_file_path).replace(".mid", ".musicxml")
        output_file_path = os.path.join(os.getcwd(), "results", music_xml_filename)

    # Create empty JSON body
    data = {}

    # Send the MIDI file
    with open(midi_file_path, 'rb') as f:
        files = {'file': f}
        response = requests.post(url, files=files, json=data)

    # write the response (musicxml) to the output file path
    with open(output_file_path, 'w') as f:
        f.write(response.text)

    return output_file_path
