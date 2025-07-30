import asyncio
from pathlib import Path
from typing import Dict

from turbo_docs.constants import CODE_EXTENSIONS, IGNORE_FOLDERS, TURBO_DOCS_STR
from turbo_docs.llm import count_tokens, get_completion_stream


def get_files(max_lines: int = 1000) -> Dict[Path, str]:
    """
    Recursively list all files in the current directory

    - Skip files that contain folders starting with .
    - Skip files that have a suffix that is not in CODE_EXTENSIONS
    - Skip files that are not files (e.g. directories)
    - Skip files that are named README.md (this will contaminate our generation)
    - Skip files that have more than max_lines lines
    - Skip files that cannot be read as text

    :param max_lines: Maximum number of lines allowed in a file
    :return: Dictionary of Path to file content
    """
    files = {}
    for file in Path(".").glob("**/*"):
        if any(part.startswith(".") for part in file.parts):
            continue
        if file.suffix not in CODE_EXTENSIONS:
            continue
        if any(part in IGNORE_FOLDERS for part in file.parts):
            continue
        if not file.is_file():
            continue
        if file.name.lower() == "readme.md":
            continue

        try:
            with open(file, "rb") as f:
                if f.read().count(b"\n") > max_lines:
                    continue
            files[file] = file.read_text(encoding="utf-8")

        except (UnicodeDecodeError, OSError) as e:
            print(f"Skipping {file} because {e}")
            continue

    return files


def files_to_str(files: Dict[Path, str]) -> str:
    """
    Convert a dictionary of files to a string
    """
    filestr = ""
    for file, content in files.items():
        filestr += f"# {file.name}\n\n"
        filestr += content
        filestr += "\n\n"
    return filestr


async def generate_chain_of_thought(repo_str: str) -> str:
    """
    Generate a chain of thought for the repository string.
    """
    chain_of_thought = ""
    generator = await get_completion_stream(
        message=f"You are an intelligence software dev AI agent. Here is the repository you are working on:\n\n\n{repo_str}\n\n\nBefore we generate the readme, think out loud step by step how we could build an amazing one here (what goes into making an impactful readme and where is that information located in the codebase?)."
    )
    async for chunk in generator:
        print(chunk, end="", flush=True)
        chain_of_thought += chunk
    print()
    return chain_of_thought


async def generate_readme(repo_str: str, chain_of_thought: str) -> str:
    """
    Generate a README.md file from the repository string.
    """
    readme = ""
    generator = await get_completion_stream(
        message=f"Given the following chain of thought and code repository, generate a README.md file in markdown format (no triple backticks needed).\n\n\n# Chain of thought:\n{chain_of_thought}\n\n\n# Code repository:\n{repo_str}"
    )
    async for chunk in generator:
        print(chunk, end="", flush=True)
        readme += chunk
    print()
    return readme


async def generate() -> None:
    """
    Recursively list all files in the current directory skipping paths that contain folders starting with .
    Returns absolute paths for all files.
    """

    files = get_files()
    repo_str = files_to_str(files)
    num_tokens = count_tokens(repo_str)

    print(TURBO_DOCS_STR)
    print(f"Generating README.md (ingesting {num_tokens} tokens)...")
    print("=" * 50, " Generating chain of thought ", "=" * 50)
    chain_of_thought = await generate_chain_of_thought(repo_str)
    print("=" * 50, " Generating README.md ", "=" * 50)
    readme = await generate_readme(repo_str, chain_of_thought)
    print("=" * 50, " Saving README.md ", "=" * 50)
    with open("README.md", "w") as f:
        f.write(readme)


if __name__ == "__main__":
    asyncio.run(generate())
