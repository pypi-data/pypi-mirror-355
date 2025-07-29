"""Test the analyse module."""

from llm_cgr import Markdown


TEST_LLM_RESPONSE = """
Here's a Python solution to process some data and return an answer.

```python
import numpy as np
from requests import get
import json
from collections import defaultdict
from cryptography.fernet import Fernet
import pandas.DataFrame

def process_data(data):
    response = get("https://api.example.com/data")
    data = np.array([1, 2, 3, 4, 5])
    return np.process(data, response)
```

Some more code:

```
import pandas as pd
from datetime import datetime

csv = pd.read_csv(f"data_{datetime.now().isoformat()}.csv")
```

Run some code:

```bash
python script.py
```

Some very bad python code:

```python
import problem

problem.bad_brackets((()
```

Some very bad unknown code:

```
for import xxx)[
```
"""

# 57-59, 62, 66, 102-105, 108, 135-139


def test_markdown():
    """
    Test the MarkdownResponse class, extracting and analysing multiple code blocks.
    """
    # parse the response
    analysed = Markdown(text=TEST_LLM_RESPONSE)

    # check initial properties
    assert analysed.text == TEST_LLM_RESPONSE
    assert f"{analysed}" == TEST_LLM_RESPONSE
    assert len(analysed.code_blocks) == 5
    assert [cb.__repr__() for cb in analysed.code_blocks] == [
        "CodeBlock(language=python, lines=11)",
        "CodeBlock(language=python, lines=4)",
        "CodeBlock(language=bash, lines=1)",
        "CodeBlock(language=python, lines=3)",
        "CodeBlock(language=unspecified, lines=1)",
    ]
    assert analysed.code_errors == ["3: '(' was never closed (<unknown>, line 3)"]
    assert analysed.languages == ["bash", "python"]
    assert (
        analysed.__repr__()
        == "Markdown(lines=45, code_blocks=5, languages=bash,python)"
    )

    # expected python code block
    python_code_one = analysed.code_blocks[0]
    assert python_code_one.language == "python"
    assert python_code_one.valid is True
    assert python_code_one.error is None
    assert python_code_one.defined_funcs == ["process_data"]
    assert python_code_one.called_funcs == ["get", "np.array", "np.process"]
    assert python_code_one.packages == [
        "cryptography",
        "numpy",
        "pandas",
        "requests",
    ]
    assert python_code_one.imports == [
        "collections.defaultdict",
        "cryptography.fernet.Fernet",
        "json",
        "numpy",
        "pandas.DataFrame",
        "requests.get",
    ]
    assert python_code_one.stdlibs == ["collections", "json"]

    # unspecified code block defaults to python
    python_code_two = analysed.code_blocks[1]
    assert python_code_two.language == "python"
    assert python_code_two.valid is True
    assert python_code_two.error is None
    assert python_code_two.defined_funcs == []
    assert python_code_two.called_funcs == ["datetime.now", "isoformat", "pd.read_csv"]
    assert python_code_two.packages == ["pandas"]
    assert python_code_two.imports == ["datetime.datetime", "pandas"]
    assert python_code_two.stdlibs == ["datetime"]

    # bash code block with no analysis
    bash_code = analysed.code_blocks[2]
    assert bash_code.language == "bash"
    assert bash_code.valid is None
    assert bash_code.error is None
    assert bash_code.defined_funcs == []
    assert bash_code.called_funcs == []
    assert bash_code.packages == []
    assert bash_code.imports == []
    assert bash_code.stdlibs == []

    # python code block with incorrect syntax
    bad_code = analysed.code_blocks[3]
    assert bad_code.language == "python"
    assert bad_code.valid is False
    assert bad_code.error == "'(' was never closed (<unknown>, line 3)"
    assert bad_code.defined_funcs == []
    assert bad_code.called_funcs == []
    assert bad_code.packages == []
    assert bad_code.imports == []
    assert bad_code.stdlibs == []

    # unknown code block
    unknown_code = analysed.code_blocks[4]
    assert unknown_code.text == "for import xxx)["
    assert unknown_code.language is None
    assert unknown_code.valid is None
    assert unknown_code.error is None
    assert unknown_code.defined_funcs == []
    assert unknown_code.called_funcs == []
    assert unknown_code.packages == []
    assert unknown_code.imports == []
    assert unknown_code.stdlibs == []

    # check the representation methods
    assert unknown_code.markdown == "```\nfor import xxx)[\n```"
    assert f"{unknown_code}" == "for import xxx)["

    # test getting the first code block
    assert analysed.first_code_block("python") == python_code_one
    assert analysed.first_code_block("bash") == bash_code
    assert analysed.first_code_block("javascript") is None
