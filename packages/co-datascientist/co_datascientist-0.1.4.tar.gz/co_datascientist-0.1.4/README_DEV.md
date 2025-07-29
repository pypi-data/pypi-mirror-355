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
3. upload using twine (install if missing):
```bash
twine upload dist/*
``` 
4. you will be prompted for a token, you can view it on your pypi account
