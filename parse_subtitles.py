import json
import os

def parse_subtitles():
    input_file = 'subtitles.json'
    output_file = 'subtitles_es.txt'

    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.")
        return

    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        with open(output_file, 'w', encoding='utf-8') as f:
            for item in data:
                if 'text' in item:
                    f.write(item['text'] + '\n')
        
        print(f"Successfully parsed {input_file} and saved to {output_file}")

    except json.JSONDecodeError:
        print(f"Error: Failed to decode JSON from {input_file}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    parse_subtitles()
