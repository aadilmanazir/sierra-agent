import os
import asyncio
import dotenv
import typer
import uvicorn
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich import print as rprint

from api.main import app as api_app
from agent import SierraAgent

# Load environment variables
dotenv.load_dotenv()

# Create Typer app
app = typer.Typer(help="Sierra Outfitters Agent")
console = Console()

@app.command()
def api(port: int = 8000, host: str = "127.0.0.1"):
    """
    Run the FastAPI backend server
    """
    rprint("[bold green]Starting Sierra Outfitters API server...[/bold green]")
    uvicorn.run(api_app, host=host, port=port)

@app.command()
def chat():
    """
    Start an interactive chat session with the Sierra Agent
    """
    rprint(Panel.fit(
        "[bold blue]Sierra Outfitters Customer Service Agent[/bold blue]",
        title="Sierra Agent",
        border_style="blue"
    ))
    
    async def chat_loop():
        agent = SierraAgent()
        
        # Get and display welcome message (agent starts in WELCOME state)
        with console.status("[bold yellow]Initializing...[/bold yellow]", spinner="dots"):
            welcome_message = await agent.process_message("")
        
        rprint(f"\n[bold blue]Sierra Agent[/bold blue]: {welcome_message}")
        
        while True:
            user_input = Prompt.ask("\n[bold cyan]You[/bold cyan]")
            
            if user_input.lower() in ["exit", "quit", "bye"]:
                rprint("[bold green]Thank you for chatting with Sierra Agent. Goodbye![/bold green]")
                break
            
            with console.status("[bold yellow]Thinking...[/bold yellow]", spinner="dots"):
                response = await agent.process_message(user_input)
            
            rprint(f"\n[bold blue]Sierra Agent[/bold blue]: {response}")
    
    # Run the chat loop
    asyncio.run(chat_loop())

@app.command()
def env_check():
    """
    Check if the environment is properly set up
    """
    # Check OpenAI API key
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        rprint("[bold red]ERROR: OPENAI_API_KEY not found in .env file[/bold red]")
        rprint("Please add your OpenAI API key to a .env file as OPENAI_API_KEY=your_key_here")
        return False
    
    # Check data files
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    product_catalog = os.path.join(data_dir, "ProductCatalog.json")
    customer_orders = os.path.join(data_dir, "CustomerOrders.json")
    
    if not os.path.exists(product_catalog):
        rprint(f"[bold red]ERROR: ProductCatalog.json not found in {data_dir}[/bold red]")
        return False
    
    if not os.path.exists(customer_orders):
        rprint(f"[bold red]ERROR: CustomerOrders.json not found in {data_dir}[/bold red]")
        return False
    
    rprint("[bold green]Environment check passed! Your system is ready to run Sierra Agent.[/bold green]")
    return True

if __name__ == "__main__":
    app()
