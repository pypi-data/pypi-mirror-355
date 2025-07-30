
import argparse
import os
import json
import requests
from pathlib import Path

VERSION = "0.0.6a"

CONFIG_PATH = Path.home() / ".modelcli_models.json"
DEFAULTS_PATH = Path.home() / ".modelcli_defaults.json"

def load_models():
    try:
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH, "r") as f:
                data = json.load(f)
                if isinstance(data, dict) and "models" in data and "default" in data and "aliases" in data:
                    return data
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

def resolve_model_name(name, data):
    return data["aliases"].get(name, name)

def get_model(name, data):
    resolved = resolve_model_name(name, data)
    return data["models"].get(resolved, None)

def run_prompt(model_data, prompt):
    headers = {"Content-Type": "application/json"}
    if model_data["key"].lower() != "none" and model_data["key"].strip() != "":
        headers["Authorization"] = f"Bearer {model_data['key']}"
    data = {
        "model": model_data["model"],
        "messages": [{"role": "user", "content": prompt}]
    }
    r = requests.post(model_data["url"], headers=headers, json=data)
    try:
        r.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print(f"❌ Error {r.status_code}: {r.text}")
        raise SystemExit
    response = r.json()
    if 'choices' in response:
        return response['choices'][0]['message']['content']
    elif 'message' in response:
        return response['message'].get('content', '[⚠️ No content]')
    else:
        return f"[⚠️ Unexpected response format]\n{response}"

def list_models(data):
    if not data["models"]:
        print("📭 No models configured.")
        return
    print("📚 Registered models:")
    for name, info in data["models"].items():
        default = " (default)" if data["default"] == name else ""
        aliases = [k for k, v in data["aliases"].items() if v == name]
        print(f" • {name}{default}")
        print(f"   ↪ URL: {info['url']}")
        print(f"   ↪ Model: {info['model']}")
        print(f"   ↪ Key: {'[set]' if info['key'] not in ['none', ''] else '[none]'}")
        if aliases:
            print(f"   ↪ Aliases: {', '.join(aliases)}")

def main():
    parser = argparse.ArgumentParser(description="Universal CLI for LLMs (ChatGPT, Mistral, LM Studio, OpenRouter, etc.)")
    parser.add_argument("--version", action="version", version=f"modelcli {VERSION}")
    parser.add_argument("--model", help="Override default model by name or alias")
    parser.add_argument("command", nargs="?", help="Command to run (summarize, translate, email, custom or prompt text)")
    parser.add_argument("text", nargs=argparse.REMAINDER, help="Text or prompt")

    args = parser.parse_args()
    data = load_models()
    defaults = load_defaults()

    if args.command == "configure-model":
        name = input("Model name: ")
        url = input("Model URL: ")
        key = input("API key (or 'none'): ")
        model = input("Model ID (e.g. gpt-4, mistral): ")
        data["models"][name] = {"url": url, "key": key, "model": model}
        if data["default"] is None:
            data["default"] = name
        save_models(data)
        print(f"✅ Model '{name}' configured successfully.")
        return

    if args.command == "set-default":
        name = input("Model name to set as default: ")
        if name in data["models"]:
            data["default"] = name
            save_models(data)
            print(f"✅ Default model set to '{name}'")
        else:
            print(f"❌ Model '{name}' not found.")
        return

    if args.command == "set-language":
        lang = input("Target language: ")
        defaults["language"] = lang
        save_defaults(defaults)
        print(f"🌐 Language set to '{lang}'")
        return

    if args.command == "alias":
        orig = input("Original model name: ")
        alias = input("Alias name: ")
        if orig in data["models"]:
            data["aliases"][alias] = orig
            save_models(data)
            print(f"✅ Alias '{alias}' created for '{orig}'")
        else:
            print(f"❌ Model '{orig}' not found.")
        return

    if args.command == "list-models":
        list_models(data)
        return

    if args.command == "remove-model":
        name = input("Model name to remove: ")
        if name in data["models"]:
            del data["models"][name]
            if data["default"] == name:
                data["default"] = next(iter(data["models"]), None)
            data["aliases"] = {k: v for k, v in data["aliases"].items() if v != name}
            save_models(data)
            print(f"🗑️ Removed model '{name}'")
        else:
            print(f"❌ Model '{name}' not found.")
        return

    # Determine the model to use
    model_name = args.model or data.get("default")
    if not model_name:
        print("❌ No model specified or configured.")
        return
    model_data = get_model(model_name, data)
    if not model_data:
        print(f"❌ Model '{model_name}' not found.")
        return

    joined_text = " ".join(args.text).strip()
    if not joined_text:
        print("❗ No input provided.")
        return

    # Detect command and build prompt
    command = args.command.lower() if args.command else ""
    if command == "summarize":
        prompt = f"Summarize this text in 3 bullet points in {defaults['language']}:\n{joined_text}"
    elif command == "translate":
        prompt = f"Translate this text to {defaults['language']}:\n{joined_text}"
    elif command == "email":
        prompt = f"Write an email in a neutral tone in {defaults['language']}:\n{joined_text}"
    elif command == "custom":
        prompt = f"In {defaults['language']}, {joined_text}"
    else:
        prompt = f"In {defaults['language']}, {args.command} {joined_text}".strip()

    response = run_prompt(model_data, prompt)
    print("
🧠 Response:
")
    print(response)

def run():
    main()
