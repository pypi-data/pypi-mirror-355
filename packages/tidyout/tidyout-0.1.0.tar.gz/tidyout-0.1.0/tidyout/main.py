#!/usr/bin/env python3

import sys
import ast
import json
import re
import argparse

def extract_key_value_blocks(raw_text):
    """
    Extract top-level key=value blocks from LLM-like output
    (e.g., content='...', response_metadata={...}, etc.)
    Works even when they're on the same line.
    """
    result = {}
    pattern = re.compile(r"(\w+)=((?:.|\n)*?)(?=\s+\w+=|\s*$)")
    for key, val in re.findall(pattern, raw_text):
        val = val.strip()
        try:
            parsed = ast.literal_eval(val)
            if isinstance(parsed, str):
                parsed = parsed.encode('utf-8').decode('unicode_escape')
        except Exception:
            parsed = val
        result[key] = parsed
    return result

def parse_colon_separated_content(content):
    """Convert 'key: value' lines into a dictionary"""
    result = {}
    for line in content.splitlines():
        if ':' in line:
            key, val = line.split(':', 1)
            result[key.strip()] = val.strip()
    return result

def main():
    parser = argparse.ArgumentParser(description="Convert LLM-style or OpenAI outputs to clean JSON")
    parser.add_argument("input_file", help="Input file")
    parser.add_argument("--inplace", action="store_true", help="Overwrite the input file")
    parser.add_argument("--out", type=str, help="Write to a different file")
    parser.add_argument("--openai", action="store_true", help="Parse OpenAI API call output")
    parser.add_argument("--split-content", action="store_true", help="Split content field by colon-separated lines")
    args = parser.parse_args()

    try:
        with open(args.input_file, "r", encoding="utf-8") as f:
            raw_text = f.read()

        output_dict = extract_key_value_blocks(raw_text)

        if args.split_content and "content" in output_dict and isinstance(output_dict["content"], str):
            output_dict["content"] = parse_colon_separated_content(output_dict["content"])

        json_output = json.dumps(output_dict, indent=2, ensure_ascii=False)

        if args.inplace:
            with open(args.input_file, "w", encoding="utf-8") as f:
                f.write(json_output + "\n")
            print(f"✅ Cleaned and saved in-place to {args.input_file}")
        elif args.out:
            with open(args.out, "w", encoding="utf-8") as f:
                f.write(json_output + "\n")
            print(f"✅ Saved cleaned JSON to {args.out}")
        else:
            print(json_output)

    except Exception as e:
        print("❌ Failed to parse:", e)
        sys.exit(1)

if __name__ == "__main__":
    main()
