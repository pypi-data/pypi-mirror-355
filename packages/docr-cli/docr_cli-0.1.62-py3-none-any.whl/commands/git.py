"""Git repository management commands."""
import subprocess
from pathlib import Path
from typing import Dict
from rich import print as rprint
from rich.prompt import Confirm
from rich.progress import Progress

from utils import ConsoleUtils


# Repository URLs for cloning
REPOSITORY_URLS = {
    "aisolutions-docreview-serverless": "https://bitbucket.umd.edu/scm/aisolutions/aisolutions-docreview-serverless.git",
    "aisolutions-costsmodule-serverless": "https://bitbucket.umd.edu/scm/aisolutions/aisolutions-costsmodule-serverless.git",
    "aisolutions-jobsmodule-serverless": "https://bitbucket.umd.edu/scm/aisolutions/aisolutions-jobsmodule-serverless.git",
    "aisolutions-workspaces-serverless": "https://bitbucket.umd.edu/scm/aisolutions/aisolutions-workspaces-serverless.git",
    "oidc-oidcauthorizer-serverless": "https://bitbucket.umd.edu/scm/oidc/oidc-oidcauthorizer-serverless.git",
    "oidc-oidcmanager-serverless": "https://bitbucket.umd.edu/scm/oidc/oidc-oidcmanager-serverless.git",
    "oidc-oidcwebcomponent": "https://bitbucket.umd.edu/scm/oidc/oidc-oidcwebcomponent.git",
    "aisolutions-docreview-cli": "https://bitbucket.umd.edu/scm/aiteam/aisolutions-docreview-cli.git"
}


def git_clone():
    """Clone missing repositories required for the Doc Review system."""
    console_utils = ConsoleUtils()
    
    # Always use current directory for git clone
    project_root = Path.cwd()
    
    rprint(f"\n[bold]Doc Review Repository Manager[/bold]")
    rprint(f"\n[yellow]This command will clone all required repositories to:[/yellow]")
    rprint(f"[cyan]{project_root}[/cyan]")
    
    # Show what will be cloned
    rprint(f"\n[bold]The following repositories will be cloned:[/bold]")
    for repo_name in REPOSITORY_URLS.keys():
        rprint(f"  • {repo_name}")
    
    if not Confirm.ask(f"\nProceed with cloning {len(REPOSITORY_URLS)} repositories to this directory?"):
        rprint("[yellow]Clone operation cancelled.[/yellow]")
        return
    
    # Check which repos already exist
    existing_repos = []
    missing_repos = []
    
    for repo_name in REPOSITORY_URLS.keys():
        repo_path = project_root / repo_name
        if repo_path.exists():
            if (repo_path / '.git').exists():
                existing_repos.append(repo_name)
            else:
                rprint(f"[red]Warning: {repo_name} exists but is not a git repository![/red]")
                missing_repos.append(repo_name)
        else:
            missing_repos.append(repo_name)
    
    if existing_repos:
        rprint(f"\n[green]Found {len(existing_repos)} existing repositories:[/green]")
        for repo in existing_repos:
            rprint(f"  ✓ {repo}")
    
    if not missing_repos:
        rprint("\n[green]All repositories already cloned![/green]")
        return
    
    rprint(f"\n[yellow]Need to clone {len(missing_repos)} repositories:[/yellow]")
    for repo in missing_repos:
        rprint(f"  • {repo}")
    
    # Clone missing repositories
    rprint(f"\n[bold]Cloning repositories...[/bold]")
    
    success_count = 0
    failed_repos = []
    
    with Progress() as progress:
        task = progress.add_task("[cyan]Cloning repositories...", total=len(missing_repos))
        
        for repo_name in missing_repos:
            repo_url = REPOSITORY_URLS[repo_name]
            repo_path = project_root / repo_name
            
            progress.update(task, description=f"[cyan]Cloning {repo_name}...")
            
            try:
                # Run git clone
                result = subprocess.run(
                    ['git', 'clone', repo_url, str(repo_path)],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    success_count += 1
                    console_utils.print_success(f"Cloned {repo_name}")
                else:
                    failed_repos.append((repo_name, result.stderr))
                    console_utils.print_error(f"Failed to clone {repo_name}: {result.stderr}")
            
            except Exception as e:
                failed_repos.append((repo_name, str(e)))
                console_utils.print_error(f"Error cloning {repo_name}: {e}")
            
            progress.advance(task)
    
    # Summary
    rprint(f"\n[bold]Clone Summary:[/bold]")
    rprint(f"  • Successfully cloned: [green]{success_count}[/green]")
    rprint(f"  • Failed: [red]{len(failed_repos)}[/red]")
    rprint(f"  • Already existed: [cyan]{len(existing_repos)}[/cyan]")
    
    if failed_repos:
        rprint(f"\n[red]Failed to clone the following repositories:[/red]")
        for repo, error in failed_repos:
            rprint(f"  • {repo}: {error}")
        rprint(f"\n[yellow]You may need to manually clone these repositories or check your network/permissions.[/yellow]")
    else:
        rprint(f"\n[green]All repositories cloned successfully![/green]")
    
    rprint(f"\n[dim]All repositories cloned to: {project_root}[/dim]")