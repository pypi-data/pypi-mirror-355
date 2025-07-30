
import argparse
import os
import json
import requests
from pathlib import Path

VERSION = "0.0.3"

CONFIG_PATH = Path.home() / ".modelcli_models.json"

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

def resolve_model_name(name, data):
    return data["aliases"].get(name, name)

def get_model(name, data):
    resolved = resolve_model_name(name, data)
    return data["models"].get(resolved, None)

def create_prompt(command, args):
    if command == "summarize":
        return f"Summarize this text in 3 bullets:\n{args.text}"
    elif command == "translate":
        return f"Translate this text to {args.language}:\n{args.text}"
    elif command == "email":
        return f"Write an email in a {args.tone} tone saying:\n{args.text}"
    elif command == "custom":
        return args.prompt
    else:
        return args.text

def run_prompt(model_data, prompt):
    headers = {"Content-Type": "application/json"}
    if model_data["key"].lower() != "none" and model_data["key"].strip() != "":
        headers["Authorization"] = f"Bearer {model_data['key']}"
    data = {
        "model": model_data["model"],
        "messages": [{"role": "user", "content": prompt}]
    }
    r = requests.post(model_data["url"], headers=headers, json=data)
    r.raise_for_status()
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


DEFAULTS_PATH = Path.home() / ".modelcli_defaults.json"

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

def main():
    parser = argparse.ArgumentParser(description="Universal CLI for LLMs")
    parser.add_argument("--version", action="store_true", help="Show modelcli version")
    subparsers = parser.add_subparsers(dest="command")

    config = subparsers.add_parser("configure-model")
    config.add_argument("--name", required=True)
    config.add_argument("--url", required=True)
    config.add_argument("--key", required=True)
    config.add_argument("--model", required=True)

    setdef = subparsers.add_parser("set-default")
    setdef.add_argument("--name", required=True)

    alias = subparsers.add_parser("alias")
    alias.add_argument("--for", dest="for_model", required=True)
    alias.add_argument("--as", dest="alias_name", required=True)

    summarize = subparsers.add_parser("summarize")
    summarize.add_argument("text", type=str)
    summarize.add_argument("--model", type=str)

    translate = subparsers.add_parser("translate")
    translate.add_argument("text", type=str)
    translate.add_argument("--language", type=str, default="english")
    translate.add_argument("--model", type=str)

    email = subparsers.add_parser("email")
    email.add_argument("text", type=str)
    email.add_argument("--tone", type=str, default="neutral")
    email.add_argument("--model", type=str)

    custom = subparsers.add_parser("custom")
    custom.add_argument("prompt", type=str)
    custom.add_argument("--model", type=str)

    
    listcmd = subparsers.add_parser("list-models")
    removecmd = subparsers.add_parser("remove-model")
    removecmd.add_argument("--name", required=True)
    
    langcmd = subparsers.add_parser("set-language")
    langcmd.add_argument("--to", required=True)

    parser.add_argument("prompt", nargs="?", help="Prompt to send directly if no command is given")
    args = parser.parse_args()

    if args.version:
        print(f"modelcli version {VERSION}")
        return

    data = load_models()
    defaults = load_defaults()

    
    if args.command == "list-models":
        list_models(data)
        return

    if args.command == "remove-model":
        if args.name in data["models"]:
            del data["models"][args.name]
            if data["default"] == args.name:
                data["default"] = next(iter(data["models"]), None)
            data["aliases"] = {k: v for k, v in data["aliases"].items() if v != args.name}
            save_models(data)
            print(f"🗑️ Removed model '{args.name}'")
        else:
            print(f"❌ Model '{args.name}' not found.")
        return

    if args.command == "configure-model":
        if not args.name or not args.url or not args.model or args.key is None:
            print("❌ Missing required --name, --url, --model, or --key")
            return
        data["models"][args.name] = {
            "url": args.url,
            "key": args.key,
            "model": args.model
        }
        if data["default"] is None:
            data["default"] = args.name
        save_models(data)
        print(f"✅ Model '{args.name}' configured successfully.")
        return

        data["models"][args.name] = {
            "url": args.url,
            "key": args.key,
            "model": args.model
        }
        if data["default"] is None:
            data["default"] = args.name
        save_models(data)
        print(f"✅ Model '{args.name}' configured successfully.")
        return

    
    if args.command == "set-language":
        defaults["language"] = args.to
        save_defaults(defaults)
        print(f"🌐 Default translation language set to '{args.to}'")
        return

    if args.command == "set-default":
        if args.name in data["models"]:
            data["default"] = args.name
            save_models(data)
            print(f"✅ Default model set to '{args.name}'")
        else:
            print(f"❌ Model '{args.name}' not found.")
        return

    if args.command == "alias":
        if args.for_model in data["models"]:
            data["aliases"][args.alias_name] = args.for_model
            save_models(data)
            print(f"✅ Alias '{args.alias_name}' created for '{args.for_model}'")
        else:
            print(f"❌ Model '{args.for_model}' not found.")
        return

    
    if args.command in ["summarize", "translate", "email", "custom"] or args.prompt:
        model_name = getattr(args, 'model', None) or data.get("default")
        if not model_name:
            print("❌ No default model set and no --model provided.")
            return
        model_data = get_model(model_name, data)
        if not model_data:
            print(f"❌ Model '{model_name}' not found.")
            return

        if args.command == "summarize":
            prompt = f"Summarize this text in 3 bullets:\n{args.text}"
        elif args.command == "translate":
            prompt = f"Translate this text to {args.language if hasattr(args, 'language') else defaults.get('language', 'english')}:\n{args.text}"
        elif args.command == "email":
            prompt = f"Write an email in a {args.tone} tone saying:\n{args.text}"
        elif args.command == "custom":
            prompt = args.prompt
        elif args.prompt:
            prompt = args.prompt
        else:
            prompt = "Hi."

        response = run_prompt(model_data, prompt)
        print("\n🧠 Response:\n")
        print(response)
        return

        model_name = args.model or data.get("default")
        if not model_name:
            print("❌ No default model set and no --model provided.")
            return
        model_data = get_model(model_name, data)
        if not model_data:
            print(f"❌ Model '{model_name}' not found.")
            return
        prompt = create_prompt(args.command, args)
        response = run_prompt(model_data, prompt)
        print("\n🧠 Response:\n")
        print(response)
        return

    parser.print_help()

def run():
    main()
