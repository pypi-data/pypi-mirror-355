import batchfactory as bf
from batchfactory.op import *
import itertools as itt

def lines(text):
    return [line.strip() for line in text.split('\n') if line.strip()]

def split_text(text, max_length=8192)->list[str]:
    groups = [""]
    for line in lines(text):
        if groups[-1] == "" or (len(groups[-1]) + len(line) + 1 <= max_length):
            groups[-1] += (line + "\n")
        else:
            groups.append(line + "\n")
    return groups

def label_line_numbers(text,offset=1):
    return "\n".join(f"{i+offset}: {line}" for i, line in enumerate(lines(text)))

def split_text_by_line_labels(text, line_labels, offset=1):
    groups = [""]
    for i, line in enumerate(lines(text)):
        if i+offset in line_labels and groups[-1] != "":
            groups.append("")
        groups[-1] += line + "\n\n"
    return groups

def flatten_list(lst):
    return list(itt.chain.from_iterable(lst))

def print_labeled_lines(text, line_labels, offset=1):
    flagged_lines = [line for i, line in enumerate(lines(text)) if i + offset in line_labels]
    for i, line in enumerate(flagged_lines):
        print(f"{i + offset}: {line.strip()}")

def text_to_integer_list(text):
    try:
        return [int(i) for i in text.split()]
    except ValueError:
        return []

LABEL_SEG_PROMPT = """
Please label the following text by identifying different Scenes.

A Scene is a unit of story with a clear beginning, middle, and end, structured around conflict or change. It often contains multiple beats and actions.

A Scene should be approximately 400–800 words long. Try to divide a chapter into multiple scenes.

I will provide you with a text in which each line is labeled with a number.

Your task is to output the line numbers that indicate the start of each scene, including chapter boundaries.

Note that the given text may begin in the middle of a scene, so the first line might not mark the start of a new scene.

Please output only the line numbers, separated by spaces, with no additional text or formatting.

The text is as follows:

```
{text}
```

Please provide the line numbers marking the start of each scene in the text above, separated by spaces, with no additional text or formatting.  
Your Output:
"""

project = bf.ProjectFolder("text_segmentation", 1, 0, 5)
broker  = bf.brokers.LLMBroker(project["cache/llm_broker.jsonl"])
model = "gpt-4o-mini@openai" # for demo only, need a better model for this task

def AskLLM(prompt, output_key, identifier):
    g = GenerateLLMRequest(prompt, model=model)
    g |= CallLLM(project[f"cache/llm_call_{identifier}.jsonl"], broker, failure_behavior="retry")
    g |= ExtractResponseText(output_key=output_key)
    g |= MapField(remove_cot, output_key)
    g |= CleanupLLMData()
    return g

g = ReadTxtFolder(project["in/books"])

# START_EXAMPLE_EXPORT
g |= MapField(lambda x: split_text(label_line_numbers(x)), "text", "text_segments")
spawn_chain = AskLLM(LABEL_SEG_PROMPT, "labels", 1)
spawn_chain |= MapField(text_to_integer_list, "labels")
g | ListParallel(spawn_chain, "text_segments", "text", "labels", "labels")
g |= MapField(flatten_list, "labels")
g |= MapField(split_text_by_line_labels, ["text", "labels"], "text_segments")
g |= ExplodeList(["filename","text_segments"],["filename","text"])
# END_EXAMPLE_EXPORT

g |= MapField(lambda filename, list_idx: [filename, f"Chapter {list_idx+1}"], ["filename", "list_idx"], "headings")
g |= WriteMarkdownEntries(project["out/chapterized"],filename_key="filename")


def download_if_missing(url, path, binary=False, headers=None):
    import os, requests
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        mode = "wb" if binary else "w"
        with open(path, mode, encoding=None if binary else "utf-8") as f:
            f.write(response.content if binary else response.text)
    mode = "rb" if binary else "r"
    with open(path, mode, encoding=None if binary else "utf-8") as f:
        return f.read()

def download_alice(path="./data/examples/alice.txt"):
    url = "https://www.gutenberg.org/files/11/11-0.txt"
    return download_if_missing(url, path, binary=False)


download_alice(project["in/books/Alice in Wonderland.txt"])
g.execute(dispatch_brokers=True)