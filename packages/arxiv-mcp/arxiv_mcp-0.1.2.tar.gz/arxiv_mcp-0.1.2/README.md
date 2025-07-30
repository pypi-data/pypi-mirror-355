<!--
 * @Author: Zerui Han <hanzr.nju@outlook.com>
 * @Date: 2025-06-12 17:13:25
 * @Description: 
 * @FilePath: /arxiv-mcp/README.md
 * @LastEditTime: 2025-06-12 20:03:30
-->
# ArXiv Paper Fetcher
A simple MCP server to fetch the content of ArXiv papers. It prioritizes downloading LaTeX source, falling back to PDF conversion if the source is unavailable.

# Features
- Flexible Input: Accepts ArXiv IDs (e.g., 1706.03762) or full ArXiv URLs (e.g., https://arxiv.org/abs/1706.03762, or https://arxiv.org/pdf/1706.03762).
- LaTeX Source Priority: Attempts to download and extract .tex files from the paper's source archive first.
- PDF Fallback: If LaTeX source is not available or extraction fails, it downloads the PDF and converts it to Markdown using [Markitdown](https://github.com/microsoft/markitdown).