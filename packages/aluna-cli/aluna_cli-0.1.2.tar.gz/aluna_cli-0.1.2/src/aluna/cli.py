"""Aluna CLI main entry point"""

import asyncio
import sys
from pathlib import Path
from typing import List, Optional

import click
import httpx
from rich.console import Console
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TaskID,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

console = Console()

DEFAULT_API_URL = "https://manaflow-ai--aluna-search-backend-0-serve.modal.run"


async def download_file(
    client: httpx.AsyncClient,
    filename: str,
    output_dir: Path,
    progress: Progress,
    task_id: TaskID,
    cart_id: Optional[str] = None,
    chunk_size: int = 10 * 1024 * 1024,  # 10MB chunks
) -> bool:
    """Download a single file with progress tracking"""
    output_path = output_dir / filename
    
    try:
        if cart_id:
            # Download from cart
            url = f"{client.base_url}/download/file/{cart_id}/{filename}"
        else:
            # Legacy mode - direct filename download (not implemented in backend)
            console.print(f"[red]Direct download not supported. Please use --cart option.[/red]")
            return False
        
        # Make a HEAD request to get file size
        try:
            head_response = await client.head(url, follow_redirects=True)
            head_response.raise_for_status()
            total_size = int(head_response.headers.get("content-length", 0))
            progress.update(task_id, total=total_size)
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                console.print(f"[red]File not found or cart expired: {filename}[/red]")
            else:
                console.print(f"[red]Error checking file: {e}[/red]")
            return False
        
        # Download with streaming
        downloaded = 0
        async with client.stream("GET", url) as response:
            response.raise_for_status()
            
            with open(output_path, "wb") as f:
                async for chunk in response.aiter_bytes(chunk_size):
                    f.write(chunk)
                    downloaded += len(chunk)
                    progress.update(task_id, completed=downloaded)
        
        console.print(f"[green]✓ Downloaded {filename}[/green]")
        return True
        
    except httpx.HTTPStatusError as e:
        console.print(f"[red]HTTP error downloading {filename}: {e}[/red]")
        return False
    except Exception as e:
        console.print(f"[red]Error downloading {filename}: {e}[/red]")
        return False


async def download_files_from_cart(
    cart_id: str,
    output_dir: Path,
    parallel: int = 3,
    chunk_size: int = 10,
    api_url: str = DEFAULT_API_URL,
) -> None:
    """Download files from a cart"""
    
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    
    async with httpx.AsyncClient(
        base_url=api_url,
        timeout=httpx.Timeout(30.0, read=None),
        limits=httpx.Limits(max_connections=parallel)
    ) as client:
        # First, get cart information
        console.print(f"[bold]Fetching cart information...[/bold]")
        try:
            cart_response = await client.get(f"/cart/{cart_id}")
            cart_response.raise_for_status()
            cart_data = cart_response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                console.print("[red]Cart not found or expired. Please create a new cart.[/red]")
            else:
                console.print(f"[red]Error fetching cart: {e}[/red]")
            return
        
        items = cart_data["items"]
        console.print(f"[bold]Found {len(items)} files in cart[/bold]")
        console.print(f"Total size: {cart_data['total_size_gb']:.2f} GB\n")
        
        # Set up progress tracking
        progress = Progress(
            TextColumn("[bold blue]{task.fields[filename]}", justify="right"),
            BarColumn(bar_width=None),
            "[progress.percentage]{task.percentage:>3.1f}%",
            "•",
            DownloadColumn(),
            "•",
            TransferSpeedColumn(),
            "•",
            TimeRemainingColumn(),
        )
        
        with progress:
            tasks = []
            for item in items:
                filename = item["filename"]
                task_id = progress.add_task(
                    f"Downloading {filename}",
                    filename=filename,
                    total=None
                )
                task = download_file(
                    client,
                    filename,
                    output_dir,
                    progress,
                    task_id,
                    cart_id,
                    chunk_size * 1024 * 1024
                )
                tasks.append(task)
            
            # Run downloads with limited concurrency
            semaphore = asyncio.Semaphore(parallel)
            
            async def bounded_download(task):
                async with semaphore:
                    return await task
            
            results = await asyncio.gather(
                *[bounded_download(task) for task in tasks],
                return_exceptions=True
            )
            
            # Summary
            successful = sum(1 for r in results if r is True)
            console.print(f"\n[bold]Downloaded {successful}/{len(items)} files[/bold]")


async def download_files(
    filenames: List[str],
    output_dir: Path,
    parallel: int = 3,
    chunk_size: int = 10,
    api_url: str = DEFAULT_API_URL,
) -> None:
    """Download multiple files with parallel downloads"""
    
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Set up progress tracking
    progress = Progress(
        TextColumn("[bold blue]{task.fields[filename]}", justify="right"),
        BarColumn(bar_width=None),
        "[progress.percentage]{task.percentage:>3.1f}%",
        "•",
        DownloadColumn(),
        "•",
        TransferSpeedColumn(),
        "•",
        TimeRemainingColumn(),
    )
    
    async with httpx.AsyncClient(
        base_url=api_url,
        timeout=httpx.Timeout(30.0, read=None),
        limits=httpx.Limits(max_connections=parallel)
    ) as client:
        with progress:
            tasks = []
            for filename in filenames:
                task_id = progress.add_task(
                    f"Downloading {filename}",
                    filename=filename,
                    total=None
                )
                task = download_file(
                    client,
                    filename,
                    output_dir,
                    progress,
                    task_id,
                    chunk_size * 1024 * 1024
                )
                tasks.append(task)
            
            # Run downloads with limited concurrency
            semaphore = asyncio.Semaphore(parallel)
            
            async def bounded_download(task):
                async with semaphore:
                    return await task
            
            results = await asyncio.gather(
                *[bounded_download(task) for task in tasks],
                return_exceptions=True
            )
            
            # Summary
            successful = sum(1 for r in results if r is True)
            console.print(f"\n[bold]Downloaded {successful}/{len(filenames)} files[/bold]")


@click.group()
def cli():
    """Aluna CLI - Download pathology slides with ease"""
    pass


@cli.command()
@click.argument("filenames", nargs=-1, required=False)
@click.option(
    "--cart", "-c",
    type=str,
    help="Cart ID to download files from"
)
@click.option(
    "--output-dir", "-o",
    type=click.Path(file_okay=False, path_type=Path),
    default=Path.cwd(),
    help="Directory to save downloaded files"
)
@click.option(
    "--parallel", "-p",
    type=int,
    default=3,
    help="Number of parallel downloads"
)
@click.option(
    "--chunk-size",
    type=int,
    default=10,
    help="Download chunk size in MB"
)
@click.option(
    "--api-url",
    type=str,
    default=DEFAULT_API_URL,
    help="API URL for downloads"
)
def download(
    filenames: tuple,
    cart: Optional[str],
    output_dir: Path,
    parallel: int,
    chunk_size: int,
    api_url: str
):
    """Download SVS files by cart ID or filenames"""
    if cart:
        # Cart-based download
        console.print(f"[bold]Downloading files from cart {cart} to {output_dir}[/bold]\n")
        asyncio.run(download_files_from_cart(
            cart,
            output_dir,
            parallel,
            chunk_size,
            api_url
        ))
    elif filenames:
        # Legacy filename-based download
        console.print("[yellow]Note: Direct filename download is deprecated. Please use cart-based downloads.[/yellow]")
        console.print("[yellow]Visit the Aluna web interface to create a cart and get a cart ID.[/yellow]")
        sys.exit(1)
    else:
        console.print("[red]Please specify either --cart ID or filenames[/red]")
        console.print("\nExamples:")
        console.print("  uvx aluna download --cart ABC123XYZ")
        console.print("  aluna download --cart ABC123XYZ -o ./downloads")
        sys.exit(1)


def main():
    """Main entry point"""
    cli()


if __name__ == "__main__":
    main()