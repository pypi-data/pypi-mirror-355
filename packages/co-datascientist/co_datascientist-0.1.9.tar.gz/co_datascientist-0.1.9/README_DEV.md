# CoDatascientist Dev Readme
the user-facing co-datascientist python library!

dependencies: calls `co-datascientist-backend`

## Running CLI

1. **run co-datascientist-backend**: follow co-datascientist-backend instructions on how to run, it will probably run on port 8001. make sure the CO_DATASCIENTIST_BACKEND_URL in settings (.env) is correct.
2. **run main.py with arguments**. to test the whole workflow, use the test file at `tests/test_scripts/xor_solver.py`. 
run this command (make sure you have torch installed otherwise it won't work (you can try running the script to see if you have the right libraries): 
```bash
uv run main.py run --script-path tests/test_scripts/xor_solver.py
```

#TODO: setupa comandad for testing always in dev mode ... on a dummy file with just the worse tokens etc ... 

uv run main.py --dev run --script-path /home/ozkilim/Co-DataScientist/XOR/xor_solver.py --python-path /home/ozkilim/POC/Pi-aColada/.venv/bin/python


uv run main.py run --script-path /home/ozkilim/Co-DataScientist/XOR/xor_solver.py --python-path /home/ozkilim/POC/Pi-aColada/.venv/bin/python

## 🔑 Adding Your OpenAI API Key (Development)

For development, you can manage your OpenAI API key through the CLI commands:

### Add/Update OpenAI Key
```bash
# This will prompt you to enter your OpenAI API key
uv run main.py --reset-openai-key --dev run --script-path tests/test_scripts/xor_solver.py
```

Or use the dedicated key management command:
```bash
# Manage your OpenAI key
uv run main.py openai-key
```

### Remove OpenAI Key
```bash
# Switch back to free tier
uv run main.py openai-key --remove
```

### Check Current Status
```bash
# See if you're using your OpenAI key or the free tier
uv run main.py status
```

**Benefits of adding your OpenAI key:**
- 🚀 **Unlimited usage** with your OpenAI account
- 💰 **Direct billing** to your OpenAI account  
- 🔒 **No usage limits** from TropiFlow's free tier
- 🛠️ **Better for development** - no rate limiting during testing

**Note**: Get your OpenAI API key from [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)

## Using the MCP

1. **configure cursor**: Follow the `README.md` instructions
2. **optional (but recommended) - enable autorun mode**: this way it doesn't ask for permission to run the tool each time. settings → features → enable auto-run 
3. **run the local mcp server**: 
```bash
uv run main.py mcp-server
```
it will ask you to enter your api key. generate a key following the readme in `co-datascientist-backend` repository.
4. **test it!**: open the test file at `tests/test_scripts/xor_solver.py` in cursor, and ask the model help from co-datascientist in improving the code.

*note:* when restarting the mcp-server, reload it from the cursor settings UI, otherwise it won't work
 
## Uploading to PyPi
following [this guide](https://packaging.python.org/en/latest/guides/distributing-packages-using-setuptools/) with uv, this is how to upload co-datascientist to pypi:
1. make sure you have a [PyPi](https://pypi.org/) account
2. generate release files: `uv build`
3. upload using twine (via uv to ensure latest version):
```bash
uv run twine upload dist/*
``` 
4. you will be prompted for a token, you can view it on your pypi account
