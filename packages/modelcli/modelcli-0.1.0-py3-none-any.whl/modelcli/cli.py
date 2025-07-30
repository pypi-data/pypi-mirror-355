
import argparse
import json
import requests
from pathlib import Path

VERSION = "0.1.0"

CONFIG_PATH = Path.home() / ".modelcli_models.json"
DEFAULTS_PATH = Path.home() / ".modelcli_defaults.json"

def load_models():
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"models": {}, "default": None, "aliases": {}}

def save_models(data):
    with open(CONFIG_PATH, "w") as f:
        json.dump(data, f, indent=2)

def load_defaults():
    if DEFAULTS_PATH.exists():
        try:
            with open(DEFAULTS_PATH, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"language": "english"}

def save_defaults(data):
    with open(DEFAULTS_PATH, "w") as f:
        json.dump(data, f, indent=2)

def run_prompt(model_data, prompt):
    headers = {"Content-Type": "application/json"}
    if model_data["key"].lower() != "none":
        headers["Authorization"] = f"Bearer {model_data['key']}"
    payload = {
        "model": model_data["model"],
        "messages": [{"role": "user", "content": prompt}]
    }
    r = requests.post(model_data["url"], headers=headers, json=payload)
    try:
        r.raise_for_status()
    except Exception:
        print(f"HTTP {r.status_code}: {r.text}")
        return
    response = r.json()
    return response.get("choices", [{}])[0].get("message", {}).get("content", "[No content]")

def main():
    parser = argparse.ArgumentParser(description="Universal CLI for LLMs")
    parser.add_argument("--version", action="version", version=f"modelcli {VERSION}")
    parser.add_argument("--model", help="Override model name")
    parser.add_argument("command", nargs="?", help="Command or free prompt")
    parser.add_argument("text", nargs=argparse.REMAINDER, help="Text for the model")

    args = parser.parse_args()
    models = load_models()
    defaults = load_defaults()

    if args.command == "configure-model":
        name = input("Model name: ")
        url = input("URL: ")
        key = input("API key (or 'none'): ")
        model = input("Model ID: ")
        models["models"][name] = {"url": url, "key": key, "model": model}
        if not models["default"]:
            models["default"] = name
        save_models(models)
        print(f"Model '{name}' saved.")
        return

    if args.command == "list-models":
        for name, m in models["models"].items():
            print(f"- {name}: {m['model']} at {m['url']}")
        return

    if args.command == "set-default":
        name = input("Model to set as default: ")
        if name in models["models"]:
            models["default"] = name
            save_models(models)
            print(f"Default model set to '{name}'")
        else:
            print(f"Model '{name}' not found.")
        return

    if args.command == "set-language":
        lang = input("Language: ")
        defaults["language"] = lang
        save_defaults(defaults)
        print(f"Language set to '{lang}'")
        return

    # Handle prompt
    model_name = args.model or models.get("default")
    if not model_name or model_name not in models["models"]:
        print("No model configured or selected.")
        return

    prompt = " ".join(args.text) if args.text else args.command
    if not prompt:
        print("No prompt provided.")
        return

    language = defaults.get("language", "english")
    full_prompt = f"In {language}, {prompt}"
    response = run_prompt(models["models"][model_name], full_prompt)
    print("
Response:
")
    print(response)

def run():
    main()
