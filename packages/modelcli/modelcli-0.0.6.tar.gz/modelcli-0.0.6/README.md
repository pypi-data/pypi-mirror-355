
# modelcli

`modelcli` is a universal command-line interface to interact with any LLM provider or local model.

## Installation

```bash
pip install modelcli
```

## Commands

### Add a model
```bash
modelcli configure-model --name mymodel --url http://localhost:11434/v1/chat/completions --key none --model llama3
```

### Use predefined commands
```bash
modelcli summarize "This is a long article..." --model mymodel
modelcli translate "Hola mundo" --language english --model mymodel
modelcli email "Meeting canceled" --tone formal --model mymodel
```

### Run a custom prompt
```bash
modelcli custom "List 3 interesting facts about Saturn" --model mymodel
```
