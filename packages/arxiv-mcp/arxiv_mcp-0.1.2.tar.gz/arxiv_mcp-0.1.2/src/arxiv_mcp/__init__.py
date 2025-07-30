# server.py
import os
import re
import shutil
import tarfile
import tempfile
from typing import Optional

import requests
from markitdown import MarkItDown
from mcp.server.fastmcp import FastMCP

# Create an MCP server
mcp = FastMCP("ArxivMCP")


def _extract_arxiv_id(identifier: str) -> str:
    """
    Extracts the arXiv ID from a URL or a plain string.
    Handles formats like:
    - https://arxiv.org/abs/1706.03762
    - https://arxiv.org/pdf/1706.03762
    - 1706.03762
    - 1706.03762v1
    """
    # Regex to capture the arXiv ID (e.g., 2405.18386 or 2405.18386v1)
    match = re.search(r"(\d{4}\.\d{5}(?:v\d+)?|\w+\-?\d{4}\.\d{4}(?:v\d+)?)", identifier)
    if match:
        return match.group(1)
    return identifier  # Return original if no match, let calling function handle error


def _download_file(url: str, save_path: str) -> bool:
    """
    Downloads a file from a given URL to a specified path.
    Returns True on success, False on failure.
    """
    print(f"Attempting to download from: {url}")
    try:
        response = requests.get(url, stream=True, timeout=30)  # Added timeout
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)

        with open(save_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Successfully downloaded to {save_path}")
        return True
    except requests.exceptions.HTTPError as e:
        print(f"HTTP error downloading {url}: {e}. Status code: {e.response.status_code}")
    except requests.exceptions.ConnectionError as e:
        print(f"Connection error downloading {url}: {e}")
    except requests.exceptions.Timeout as e:
        print(f"Timeout error downloading {url}: {e}")
    except Exception as e:
        print(f"An unexpected error during download from {url}: {e}")
    return False


def _extract_tex_content(tar_gz_path: str, extract_dir: str) -> Optional[str]:
    """
    Extracts and concatenates content of .tex files from a tar.gz archive.
    Returns the concatenated content or None if no .tex files found or an error occurs.
    """
    paper_content = ""
    try:
        with tarfile.open(tar_gz_path, "r:gz") as tar:
            # Security: Prevent path traversal
            def is_within_directory(directory, path, follow_symlinks=True):
                abs_directory = os.path.abspath(directory)
                abs_path = os.path.abspath(path)
                if follow_symlinks:
                    return os.path.commonpath([abs_directory, abs_path]) == abs_directory
                else:
                    return abs_path.startswith(abs_directory)

            members = [
                m
                for m in tar.getmembers()
                if is_within_directory(extract_dir, os.path.join(extract_dir, m.name))
            ]
            tex_files = [m for m in members if m.name.endswith(".tex")]

            if not tex_files:
                print(f"No .tex files found in {os.path.basename(tar_gz_path)}.")
                return None

            for tex_file_info in tex_files:
                try:
                    # Extract only the .tex file
                    tar.extract(tex_file_info, path=extract_dir, filter="data")
                    extracted_path = os.path.join(extract_dir, tex_file_info.name)
                    if os.path.exists(extracted_path):
                        with open(extracted_path, "r", encoding="utf-8", errors="ignore") as f:
                            paper_content += f.read() + "\n\n"
                    else:
                        print(f"Warning: Extracted .tex file not found at {extracted_path}")
                except Exception as e:
                    print(f"Error extracting or reading {tex_file_info.name}: {e}")
            return paper_content.strip() if paper_content else None

    except tarfile.ReadError as e:
        print(
            f"Error reading tar.gz file {tar_gz_path}: {e}. It might not be a valid tar.gz or corrupted."
        )
    except Exception as e:
        print(f"An unexpected error during LaTeX extraction from {tar_gz_path}: {e}")
    return None


def _convert_pdf_to_markdown(pdf_path: str) -> Optional[str]:
    """
    Converts a PDF file to Markdown content using MarkItDown.
    Returns the Markdown content or None if conversion fails.
    """
    if not os.path.exists(pdf_path):
        print(f"PDF file not found at {pdf_path}.")
        return None

    print(f"Converting PDF {os.path.basename(pdf_path)} to Markdown...")
    try:
        md_converter = MarkItDown(enable_plugins=False)
        md_result = md_converter.convert(pdf_path)
        if md_result and md_result.text_content:
            return md_result.text_content.strip()
        else:
            print(
                f"MarkItDown conversion returned no text content for {os.path.basename(pdf_path)}."
            )
            return None
    except Exception as e:
        print(f"Error converting PDF {os.path.basename(pdf_path)} to Markdown: {e}")
        return None


@mcp.tool()
def fetch_arxiv_paper_content(arxiv_identifier: str) -> str:
    """
    Fetches the content of an arXiv paper.

    Args:
        arxiv_identifier: The arXiv paper ID, or a URL to the paper.
                          Examples: "1705.03762", "https://arxiv.org/abs/1705.03762v7", "https://arxiv.org/pdf/1705.03762"

    Returns:
        The content of the paper as a string (LaTeX or Markdown),
        or an error message if content cannot be fetched.
    """
    arxiv_id = _extract_arxiv_id(arxiv_identifier)
    if not arxiv_id:
        return f"Error: Could not extract arXiv ID from '{arxiv_identifier}'"

    temp_dir = None
    try:
        temp_dir = tempfile.mkdtemp()
        latex_content = None
        pdf_content = None

        # 1. Attempt to download and extract LaTeX source
        source_url = f"https://arxiv.org/src/{arxiv_id}"
        source_filename = os.path.join(temp_dir, f"{arxiv_id}.tar.gz")

        if _download_file(source_url, source_filename):
            latex_content = _extract_tex_content(source_filename, temp_dir)
            if latex_content:
                return latex_content
            else:
                print(f"Could not get valid LaTeX content for {arxiv_id}. Trying PDF.")
        else:
            print(f"Failed to download LaTeX source for {arxiv_id}. Trying PDF.")

        # 2. If LaTeX source fails, attempt to download PDF and convert
        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}"
        pdf_filename = os.path.join(temp_dir, f"{arxiv_id}.pdf")

        if _download_file(pdf_url, pdf_filename):
            pdf_content = _convert_pdf_to_markdown(pdf_filename)
            if pdf_content:
                return pdf_content
            else:
                return (
                    f"Error: Could not convert PDF for {arxiv_id} to Markdown or content is empty."
                )
        else:
            return f"Error: Failed to download PDF for {arxiv_id}."

    except Exception as e:
        return f"An unexpected error occurred: {e}"
    finally:
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            print(f"Cleaned up temporary directory: {temp_dir}")


def main() -> None:
    mcp.run(transport="stdio")
