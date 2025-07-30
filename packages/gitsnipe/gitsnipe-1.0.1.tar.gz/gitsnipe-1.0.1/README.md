# GitSnipe

A powerful and flexible CLI tool to scan websites for exposed `.git/config` files, extract credentialed repository URLs, and clone repositories using Git or git-dumper. Designed for security researchers, penetration testers, and DevOps professionals.

---

## 🚀 Features

- **Comprehensive Scanning:**  
    Detect exposed `.git/config` files using advanced path and header bypass techniques.
- **Credential Extraction:**  
    Identify and extract embedded credentials (tokens, usernames, passwords) from repository URLs.
- **Repository Cloning:**  
    Clone repositories using standard Git or [git-dumper](https://github.com/arthaud/git-dumper) for maximum compatibility.
- **Automated Analysis:**  
    Analyze repository metadata, commit history, branches, tags, and structure.
- **Multi-format Input:**  
    Accepts TXT, CSV, and JSON files with domain/URL lists (with or without ports).
- **Detailed Reporting:**  
    Generates JSON and Markdown reports with scan and clone details.
- **Safe Credential Handling:**  
    Redacts sensitive tokens in saved reports and prompts before using high-privilege credentials.
- **Batch Processing:**  
    Scan and clone from single URLs or large input files.
- **Rich CLI Output:**  
    Uses [Rich](https://github.com/Textualize/rich) for beautiful, informative terminal output.

---

## 📦 Installation

```bash
pip install gitsnipe
```

Or install from source:

```bash
git clone https://github.com/ishanoshada/GitSnipe
cd GitSnipe
pip install -e .
```

### Requirements

- Python 3.7+
- [git-dumper](https://github.com/arthaud/git-dumper) (`pip install git-dumper`)
- Git client installed and available in PATH

---

## 🛠️ Usage

### Basic Scan

```bash
gitsnipe https://example.com
```

### Batch Scan

```bash
gitsnipe -i domain_ports.txt
```

### Advanced Options

```bash
gitsnipe [URL] [-i INPUT_FILE] [-o OUTPUT_DIR] [-f] [--clone]
```

#### Arguments

- `url`: Website URL to scan (e.g., `https://example.com`)
- `-i, --input-file`: File containing URLs/domains to scan (`.txt`, `.csv`, `.json`)
- `-o, --output-dir`: Directory for scan results and cloned repositories
- `-f, --force`: Overwrite existing clone directories
- `--clone`: Skip scanning and attempt direct cloning (useful if you already know the repo is exposed)

#### Examples

```bash
# Scan a single URL
gitsnipe https://example.com

# Scan multiple URLs from a file
gitsnipe -i domain_ports.txt -o output_dir

# Force overwrite existing directories during clone
gitsnipe https://example.com -f --clone

# Save results to a custom output directory
gitsnipe https://example.com -o /path/to/output
```

---

## 📂 Output Structure

```
output_dir/
├── scan_results/
│   └── scan_result_YYYYMMDD_HHMMSS.json
└── cloned_repos/
        └── repository_name/
                ├── .git/
                ├── .clone_info.json
                └── CLONE_INFO.md
```

- **scan_results/**: JSON files with detailed scan summaries.
- **cloned_repos/**: Each cloned repository with metadata and Markdown report.

---

## 🔒 Security Notes

- Credentials are redacted in saved reports.
- Prompts for confirmation before using high-privilege tokens.
- Designed for responsible security testing—**do not use on systems you do not own or have explicit permission to test**.

---

## 🧩 Features in Detail

### Git Config Detection

- Multiple path and header bypass strategies for WAF/IDS evasion.
- Advanced response and redirect analysis.
- Supports explicit port numbers and non-standard domains.

### Credential Analysis

- Detects and classifies tokens (GitHub, GitLab, Bitbucket, etc.).
- Assesses privilege level and security scope.
- Securely handles and redacts sensitive information.

### Repository Analysis

- Extracts repository metadata (branches, tags, commit history).
- Calculates repository size and structure.
- Reports on untracked/dirty files.

### Documentation & Reporting

- Generates Markdown and JSON reports for each clone.
- Summarizes scan results for batch operations.
- Easy integration with other tools and workflows.

---

## ⚠️ Error Handling

- Robust exception management and clear error messages.
- Handles network errors, permission issues, and malformed input gracefully.
- Continues batch scans even if some targets fail.

---

## 📜 License

MIT License

---

## 🤝 Contributing

Contributions are welcome! Please read the contribution guidelines before submitting pull requests or issues.

---

## 💬 Support

For issues, feature requests, or questions, please use the [GitHub issue tracker](https://github.com/ishanoshada/GitSnipe/issues).

---

## ⭐ Acknowledgements

- [git-dumper](https://github.com/arthaud/git-dumper)
- [Rich](https://github.com/Textualize/rich)
- [GitPython](https://github.com/gitpython-developers/GitPython)

---

**Disclaimer:**  
This tool is for educational and authorized security testing purposes only. Always obtain proper permission before scanning or cloning repositories from third-party systems.

