#!/usr/bin/env python3

import click
import json
import logging
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from rich.live import Live
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.text import Text
import time

from .api import ToothFairyAPI
from .config import load_config, save_config, ToothFairyConfig

console = Console()


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


def validate_configuration(config: ToothFairyConfig) -> None:
    """Validate configuration and provide helpful error messages."""
    missing_fields = []

    if not config.api_key:
        missing_fields.append("API Key")
    if not config.workspace_id:
        missing_fields.append("Workspace ID")

    if missing_fields:
        missing_str = " and ".join(missing_fields)
        console.print(f"[red]Error: Missing required configuration: {missing_str}[/red]")
        console.print()
        console.print("[yellow]To fix this, run the configure command:[/yellow]")
        console.print(
            "[dim]tf configure --api-key YOUR_API_KEY --workspace-id YOUR_WORKSPACE_ID[/dim]"
        )
        console.print()
        console.print("[yellow]Or set environment variables:[/yellow]")
        if not config.api_key:
            console.print("[dim]export TF_API_KEY='your-api-key'[/dim]")
        if not config.workspace_id:
            console.print("[dim]export TF_WORKSPACE_ID='your-workspace-id'[/dim]")
        console.print()
        console.print("[yellow]Or create a config file at ~/.toothfairy/config.yml:[/yellow]")
        console.print("[dim]api_key: your-api-key[/dim]")
        console.print("[dim]workspace_id: your-workspace-id[/dim]")
        raise click.ClickException(f"Configuration incomplete: missing {missing_str}")


@click.group()
@click.option("--config", "-c", help="Path to configuration file")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.pass_context
def cli(ctx, config: Optional[str], verbose: bool):
    """ToothFairy AI CLI - Interact with ToothFairy AI agents via command line."""
    setup_logging(verbose)

    try:
        tf_config = load_config(config)
        ctx.ensure_object(dict)
        ctx.obj["config"] = tf_config
        ctx.obj["api"] = ToothFairyAPI(
            base_url=tf_config.base_url,
            ai_url=tf_config.ai_url,
            ai_stream_url=tf_config.ai_stream_url,
            api_key=tf_config.api_key,
            workspaceid=tf_config.workspace_id,
            verbose=verbose,
        )
    except Exception as e:
        console.print(f"[red]Configuration error: {e}[/red]")
        ctx.exit(1)


@cli.command()
@click.option("--base-url", default="https://api.toothfairyai.com", help="ToothFairy API base URL")
@click.option("--ai-url", default="https://ai.toothfairyai.com", help="ToothFairy AI URL")
@click.option(
    "--ai-stream-url", default="https://ais.toothfairyai.com", help="ToothFairy AI Streaming URL"
)
@click.option("--api-key", required=True, help="API key")
@click.option("--workspace-id", required=True, help="Workspace ID")
@click.option("--config-path", help="Path to save config file")
def configure(
    base_url: str,
    ai_url: str,
    ai_stream_url: str,
    api_key: str,
    workspace_id: str,
    config_path: Optional[str],
):
    """Configure ToothFairy CLI credentials and settings."""
    config = ToothFairyConfig(
        base_url=base_url,
        ai_url=ai_url,
        ai_stream_url=ai_stream_url,
        api_key=api_key,
        workspace_id=workspace_id,
    )

    try:
        save_config(config, config_path)
        console.print("[green]Configuration saved successfully![/green]")
        if not config_path:
            console.print(f"Config saved to: {config.get_config_path()}")
    except Exception as e:
        console.print(f"[red]Error saving configuration: {e}[/red]")


@cli.command()
@click.argument("message")
@click.option("--agent-id", required=True, help="Agent ID to send message to")
@click.option("--phone-number", help="Phone number for SMS channel")
@click.option("--customer-id", help="Customer ID")
@click.option("--provider-id", help="SMS provider ID")
@click.option("--customer-info", help="Customer info as JSON string")
@click.option(
    "--output", "-o", type=click.Choice(["json", "text"]), default="text", help="Output format"
)
@click.option("--verbose", "-v", is_flag=True, help="Show detailed response information")
@click.pass_context
def send(
    ctx,
    message: str,
    agent_id: str,
    phone_number: Optional[str],
    customer_id: Optional[str],
    provider_id: Optional[str],
    customer_info: Optional[str],
    output: str,
    verbose: bool,
):
    """Send a message to a ToothFairy AI agent."""
    config: ToothFairyConfig = ctx.obj["config"]
    validate_configuration(config)

    api: ToothFairyAPI = ctx.obj["api"]

    # Parse customer info if provided
    parsed_customer_info = {}
    if customer_info:
        try:
            parsed_customer_info = json.loads(customer_info)
        except json.JSONDecodeError:
            console.print("[red]Invalid JSON in customer-info[/red]")
            ctx.exit(1)

    try:
        with console.status("Sending message to agent..."):
            response = api.send_message_to_agent(
                message=message,
                agent_id=agent_id,
                phone_number=phone_number,
                customer_id=customer_id,
                provider_id=provider_id,
                customer_info=parsed_customer_info,
            )

        if output == "json":
            console.print(json.dumps(response, indent=2))
        else:
            agent_resp = response["agent_response"]

            if verbose:
                # Verbose mode: show all details
                console.print(Panel(f"[bold green]Message sent successfully![/bold green]"))

                table = Table(title="Response Details")
                table.add_column("Field", style="cyan")
                table.add_column("Value", style="white")

                table.add_row("Chat ID", response["chat_id"])
                table.add_row("Message ID", response["message_id"])

                console.print(table)

                # Show full agent response
                console.print(
                    Panel(
                        Syntax(json.dumps(agent_resp, indent=2), "json"),
                        title="[bold blue]Agent Response (Full)[/bold blue]",
                        border_style="blue",
                    )
                )
            else:
                # Default mode: show only the clean agent text
                if "contents" in agent_resp and "content" in agent_resp["contents"]:
                    # Extract clean content from the response
                    clean_content = agent_resp["contents"]["content"].strip()
                    console.print(clean_content)
                elif "text" in agent_resp:
                    console.print(agent_resp["text"])
                else:
                    # Fallback to JSON if no recognizable text format
                    console.print(
                        "[yellow]No text response found. Use --verbose for full details.[/yellow]"
                    )

    except Exception as e:
        console.print(f"[red]Error sending message: {e}[/red]")
        ctx.exit(1)


@cli.command()
@click.argument("message")
@click.option("--agent-id", required=True, help="Agent ID to send message to")
@click.option("--phone-number", help="Phone number for SMS channel")
@click.option("--customer-id", help="Customer ID")
@click.option("--provider-id", help="SMS provider ID")
@click.option("--customer-info", help="Customer info as JSON string")
@click.option(
    "--output", "-o", type=click.Choice(["json", "text"]), default="text", help="Output format"
)
@click.option("--verbose", "-v", is_flag=True, help="Show detailed streaming information")
@click.option("--show-progress", is_flag=True, help="Show agent processing status updates")
@click.pass_context
def send_stream(
    ctx,
    message: str,
    agent_id: str,
    phone_number: Optional[str],
    customer_id: Optional[str],
    provider_id: Optional[str],
    customer_info: Optional[str],
    output: str,
    verbose: bool,
    show_progress: bool,
):
    """Send a message to a ToothFairy AI agent with real-time streaming response.

    This command shows the agent's response as it's being generated in real-time,
    providing live updates on the agent's processing status and streaming text output.

    STREAMING BEHAVIOR EXPLAINED:

    🔄 STATUS UPDATES: The agent goes through several processing phases:

    • 'connected': Connection established with streaming server
    • 'init': Agent initialization started
    • 'initial_setup_completed': Basic setup and context loading finished
    • 'tools_processing_completed': Any required tools/functions processed
    • 'replying': Agent begins generating the actual response (text starts streaming)
    • 'updating_memory': Agent updates conversation memory
    • 'memory_updated': Memory update completed
    • 'complete': Stream finished successfully

    📝 TEXT STREAMING: Once the agent reaches 'replying' status, you'll see the response
    text being built progressively, word by word, just like ChatGPT or similar AI assistants.

    💡 TIP: Use --show-progress to see detailed status updates, or --verbose for full debug info.
    """
    config: ToothFairyConfig = ctx.obj["config"]
    validate_configuration(config)

    api: ToothFairyAPI = ctx.obj["api"]

    # Parse customer info if provided
    parsed_customer_info = {}
    if customer_info:
        try:
            parsed_customer_info = json.loads(customer_info)
        except json.JSONDecodeError:
            console.print("[red]Invalid JSON in customer-info[/red]")
            ctx.exit(1)

    # Initialize variables for streaming
    current_text = ""
    final_response = None
    processing_status = None
    connection_established = False
    last_update_time = 0

    def map_state_with_label(state: str) -> str:
        """Map agent processing state to user-friendly label with emojis."""
        status_map = {
            "data_processing_completed": "📊 **Retrieving data**",
            "tools_processing_completed": "🛠️ **Choosing tools**", 
            "replying": "🧚 **Responding**",
            "main_generation_completed": "✨ **Generation completed**",
            "memory_updated": "💾 Memory updated",
            "updating_memory": "💾 Updating memory...",
            "init": "🚀 Initializing...",
            "initial_setup_completed": "✅ Setup completed",
            "image_analysis_in_progress": "🖼️ Analyzing image...",
            "video_analysis_in_progress": "🎥 Analyzing video...",
            "audio_analysis_in_progress": "🎵 Analyzing audio...",
            "image_generation_in_progress": "🎨 Generating image...",
            "video_generation_in_progress": "🎬 Generating video...",
            "3D_model_generation_in_progress": "🏗️ Creating 3D model...",
            "code_generation_in_progress": "💻 Generating code...",
            "code_execution_in_progress": "⚡ Executing code...",
            "internet_search_in_progress": "🔍 Searching internet...",
            "planning_in_progress": "🗺️ Planning response...",
            "handed_off_to_human": "👤 Handed off to human",
            "completed": "🎉 Completed",
        }
        return status_map.get(state, f"📊 {state}")

    try:
        console.print(f"[cyan]Streaming message to agent {agent_id}...[/cyan]")
        console.print(f"[dim]Message: {message}[/dim]")
        console.print()

        if output == "json":
            # JSON mode: collect all events and output at the end
            all_events = []

            for event_type, event_data in api.send_message_to_agent_stream(
                message=message,
                agent_id=agent_id,
                phone_number=phone_number,
                customer_id=customer_id,
                provider_id=provider_id,
                customer_info=parsed_customer_info,
            ):
                all_events.append({"event_type": event_type, "event_data": event_data})

                if event_type == "error":
                    console.print(
                        f"[red]Streaming error: {event_data.get('message', 'Unknown error')}[/red]"
                    )
                    break

            console.print(json.dumps(all_events, indent=2))

        else:
            # Text mode: show live streaming
            response_panel = None

            with Live(console=console, refresh_per_second=4) as live:

                for event_type, event_data in api.send_message_to_agent_stream(
                    message=message,
                    agent_id=agent_id,
                    phone_number=phone_number,
                    customer_id=customer_id,
                    provider_id=provider_id,
                    customer_info=parsed_customer_info,
                ):

                    if verbose:
                        # Verbose mode: show all event details
                        console.print(
                            f"[dim]Event: {event_type} | Data: {json.dumps(event_data, indent=2)}[/dim]"
                        )

                    # Handle connection status events
                    if event_data.get("status") == "connected":
                        connection_established = True
                        if show_progress:
                            live.update(
                                Panel(
                                    "🔗 [green]Connected to streaming server[/green]",
                                    title="Status",
                                )
                            )
                        continue

                    if event_data.get("status") == "complete":
                        if show_progress:
                            live.update(
                                Panel(
                                    "🎉 [green]Stream completed successfully![/green]",
                                    title="Status",
                                )
                            )
                        break

                    # Handle message events
                    if event_data.get("type") == "message":
                        metadata = {}
                        agent_status = None

                        # Parse metadata if available
                        if event_data.get("metadata"):
                            try:
                                metadata = json.loads(event_data["metadata"])
                                agent_status = metadata.get("agent_processing_status")
                            except json.JSONDecodeError:
                                # Metadata parsing failed, continue without it
                                pass

                        # Handle status changes
                        if agent_status and agent_status != processing_status:
                            processing_status = agent_status
                            if show_progress:
                                status_msg = map_state_with_label(processing_status)
                                live.update(
                                    Panel(f"[yellow]{status_msg}[/yellow]", title="Agent Status")
                                )

                        # Handle progressive text streaming with enhanced logic
                        if event_data.get("text") and agent_status == "replying":
                            new_text = event_data["text"].strip()
                            current_time = time.time() * 1000  # Convert to milliseconds

                            # Only update if text is different, longer, and enough time has passed
                            if (new_text != current_text and 
                                len(new_text) > len(current_text) and 
                                current_time - last_update_time > 50):
                                
                                current_text = new_text
                                last_update_time = current_time

                                # Create live-updating response panel
                                response_text = Text(current_text)
                                response_panel = Panel(
                                    response_text,
                                    title="[bold green]🧚 Agent Response (Live)[/bold green]",
                                    border_style="green",
                                )
                                live.update(response_panel)

                        # Handle fulfilled status (final response)
                        if event_data.get("status") == "fulfilled":
                            final_response = event_data
                            if current_text:
                                # Update with final formatted response - just change emoji
                                final_text = Text(current_text)
                                final_panel = Panel(
                                    final_text,
                                    title="[bold blue]🪄 Final Response[/bold blue]",
                                    border_style="blue",
                                )
                                live.update(final_panel)

                        # Handle additional metadata events (images, files, callback metadata)
                        if event_data.get("images") is not None or event_data.get("files") is not None:
                            # These are attachment events - could show notification if needed
                            if verbose:
                                console.print("[dim]📎 Attachments processed[/dim]")

                        if event_data.get("callbackMetadata"):
                            # Function execution metadata
                            if verbose:
                                console.print("[dim]⚙️ Function execution metadata received[/dim]")

                    # Handle errors
                    if event_type == "error":
                        error_msg = event_data.get("message", "Unknown streaming error")
                        live.update(Panel(f"[red]❌ Error: {error_msg}[/red]", title="Error"))
                        console.print(f"[red]Streaming error: {error_msg}[/red]")
                        ctx.exit(1)

            # After streaming is complete
            console.print()

            if verbose and final_response:
                # Show final response metadata in verbose mode
                console.print(Panel("📊 [bold cyan]Final Response Metadata[/bold cyan]"))
                metadata_table = Table()
                metadata_table.add_column("Field", style="cyan")
                metadata_table.add_column("Value", style="white")

                if "metadata_parsed" in final_response:
                    metadata = final_response["metadata_parsed"]
                    for key, value in metadata.items():
                        if key != "agent_processing_status":  # Already shown during streaming
                            metadata_table.add_row(str(key), str(value))
                    console.print(metadata_table)

            if not current_text:
                console.print("[yellow]No text response received from agent.[/yellow]")

    except KeyboardInterrupt:
        console.print("\n[yellow]Streaming interrupted by user[/yellow]")
        ctx.exit(0)
    except Exception as e:
        console.print(f"[red]Error during streaming: {e}[/red]")
        ctx.exit(1)


@cli.command()
@click.option(
    "--output", "-o", type=click.Choice(["json", "text"]), default="text", help="Output format"
)
@click.pass_context
def chats(ctx, output: str):
    """List all chats in the workspace."""
    config: ToothFairyConfig = ctx.obj["config"]
    validate_configuration(config)

    api: ToothFairyAPI = ctx.obj["api"]

    try:
        with console.status("Fetching chats..."):
            chats_data = api.get_all_chats()

        if output == "json":
            console.print(json.dumps(chats_data, indent=2))
        else:
            if not chats_data:
                console.print("[yellow]No chats found[/yellow]")
                return

            table = Table(title="Workspace Chats")
            table.add_column("Chat ID", style="cyan")
            table.add_column("Name", style="white")
            table.add_column("Customer ID", style="green")
            table.add_column("Created", style="dim")

            # Handle different response formats
            chat_list = chats_data if isinstance(chats_data, list) else chats_data.get("items", [])

            for chat in chat_list:
                table.add_row(
                    chat.get("id", "N/A"),
                    chat.get("name", "N/A"),
                    chat.get("customerId", "N/A"),
                    chat.get("createdAt", "N/A"),
                )

            console.print(table)

    except Exception as e:
        console.print(f"[red]Error fetching chats: {e}[/red]")
        ctx.exit(1)


@cli.command()
@click.argument("chat_id")
@click.option(
    "--output", "-o", type=click.Choice(["json", "text"]), default="text", help="Output format"
)
@click.pass_context
def chat(ctx, chat_id: str, output: str):
    """Get details of a specific chat."""
    config: ToothFairyConfig = ctx.obj["config"]
    validate_configuration(config)

    api: ToothFairyAPI = ctx.obj["api"]

    try:
        with console.status(f"Fetching chat {chat_id}..."):
            chat_data = api.get_chat(chat_id)

        if output == "json":
            console.print(json.dumps(chat_data, indent=2))
        else:
            console.print(Panel(f"[bold green]Chat Details[/bold green]"))

            table = Table()
            table.add_column("Field", style="cyan")
            table.add_column("Value", style="white")

            for key, value in chat_data.items():
                if isinstance(value, (dict, list)):
                    value = json.dumps(value, indent=2)
                table.add_row(str(key), str(value))

            console.print(table)

    except Exception as e:
        console.print(f"[red]Error fetching chat: {e}[/red]")
        ctx.exit(1)


@cli.command()
@click.argument("query")
@click.option(
    "--top-k",
    "-k",
    default=10,
    type=click.IntRange(1, 50),
    help="Number of documents to retrieve (1-50)",
)
@click.option(
    "--status", type=click.Choice(["published", "suspended"]), help="Filter by document status"
)
@click.option("--document-id", help="Search within specific document ID")
@click.option("--topics", help="Comma-separated topic IDs to filter by")
@click.option(
    "--output", "-o", type=click.Choice(["json", "text"]), default="text", help="Output format"
)
@click.option("--verbose", "-v", is_flag=True, help="Show detailed search information")
@click.pass_context
def search(
    ctx,
    query: str,
    top_k: int,
    status: Optional[str],
    document_id: Optional[str],
    topics: Optional[str],
    output: str,
    verbose: bool,
):
    """Search for documents in the knowledge hub."""
    config: ToothFairyConfig = ctx.obj["config"]
    validate_configuration(config)

    api: ToothFairyAPI = ctx.obj["api"]

    # Build metadata filters
    metadata = {}
    if status:
        metadata["status"] = status
    if document_id:
        metadata["documentId"] = document_id
    if topics:
        topic_list = [topic.strip() for topic in topics.split(",") if topic.strip()]
        if topic_list:
            metadata["topic"] = topic_list

    try:
        with console.status("Searching knowledge hub..."):
            results = api.search_documents(
                text=query, top_k=top_k, metadata=metadata if metadata else None
            )

        if output == "json":
            console.print(json.dumps(results, indent=2))
        else:
            # Handle different response formats - results might be array or dict
            documents = results if isinstance(results, list) else results.get("results", [])

            if not documents:
                console.print("[yellow]No documents found for your query[/yellow]")
                return

            console.print(Panel(f"[bold green]Found {len(documents)} document(s)[/bold green]"))

            for i, doc in enumerate(documents, 1):
                score = doc.get("cosinesim", 0)
                doc_id = doc.get("doc_id", doc.get("chunk_id", "N/A"))

                # Extract text content directly from document
                text_content = doc.get("raw_text", "No content available")
                doc_status = doc.get("status", "unknown")
                doc_topics = doc.get("topics", [])
                doc_title = doc.get("title", "Untitled")

                # Create header
                header = f"[bold cyan]Document {i}[/bold cyan] (Score: {score:.3f})"

                if verbose:
                    # Verbose mode: show all details
                    table = Table(title=f"Document {i} Details")
                    table.add_column("Field", style="cyan")
                    table.add_column("Value", style="white")

                    table.add_row("Document ID", doc_id)
                    table.add_row("Relevance Score", f"{score:.4f}")
                    table.add_row("Status", doc_status)
                    table.add_row("Topics", ", ".join(doc_topics) if doc_topics else "None")
                    table.add_row(
                        "Content Preview",
                        text_content[:200] + "..." if len(text_content) > 200 else text_content,
                    )

                    console.print(table)
                else:
                    # Default mode: show clean content
                    console.print(
                        Panel(
                            text_content[:500] + "..." if len(text_content) > 500 else text_content,
                            title=header,
                            border_style="blue",
                        )
                    )

                if i < len(documents):  # Add separator except for last item
                    console.print()

    except Exception as e:
        console.print(f"[red]Error searching documents: {e}[/red]")
        ctx.exit(1)


@cli.command()
@click.pass_context
def config_show(ctx):
    """Show current configuration."""
    config: ToothFairyConfig = ctx.obj["config"]

    table = Table(title="Current Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("Base URL", config.base_url)
    table.add_row("AI URL", config.ai_url)
    table.add_row("API Key", f"{'*' * 20}...{config.api_key[-4:]}" if config.api_key else "Not set")
    table.add_row("Workspace ID", config.workspace_id)

    console.print(table)


@cli.command()
def help_guide():
    """Show detailed help and usage examples."""
    console.print(
        Panel(
            "[bold cyan]ToothFairy AI CLI - Complete Usage Guide[/bold cyan]", border_style="cyan"
        )
    )

    console.print("\n[bold green]🚀 Getting Started[/bold green]")
    console.print("1. First, configure your credentials:")
    console.print("   [dim]tf configure --api-key YOUR_KEY --workspace-id YOUR_WORKSPACE[/dim]")

    console.print("\n2. Send a message to an agent:")
    console.print('   [dim]tf send "Hello, I need help" --agent-id YOUR_AGENT_ID[/dim]')

    console.print("\n3. Search the knowledge hub:")
    console.print('   [dim]tf search "AI configuration help"[/dim]')

    console.print("\n4. Explore your workspace:")
    console.print("   [dim]tf chats                    # List all conversations[/dim]")
    console.print("   [dim]tf config-show              # View current settings[/dim]")

    console.print("\n[bold blue]💬 Agent Communication Examples[/bold blue]")

    agent_examples = [
        ("Simple message", 'tf send "What are your hours?" --agent-id "info-agent"'),
        (
            "With customer info",
            'tf send "Schedule appointment" --agent-id "scheduler" --customer-info \'{"name": "John"}\'',
        ),
        ("Verbose output", 'tf send "Hello" --agent-id "agent-123" --verbose'),
        ("JSON for scripting", 'tf send "Help" --agent-id "agent-123" --output json'),
    ]

    agent_table = Table(show_header=True, header_style="bold blue")
    agent_table.add_column("Use Case", style="cyan", width=18)
    agent_table.add_column("Command", style="white")

    for use_case, command in agent_examples:
        agent_table.add_row(use_case, command)

    console.print(agent_table)

    console.print("\n[bold magenta]🔍 Knowledge Hub Search Examples[/bold magenta]")

    search_examples = [
        ("Basic search", 'tf search "AI agent configuration"'),
        ("Filter by status", 'tf search "machine learning" --status published'),
        ("Limit results", 'tf search "troubleshooting" --top-k 3'),
        ("Topic filtering", 'tf search "automation" --topics "topic_123,topic_456"'),
        ("Specific document", 'tf search "settings" --document-id "doc_550..."'),
        ("Verbose details", 'tf search "deployment" --verbose'),
        ("JSON output", 'tf search "API docs" --output json'),
    ]

    search_table = Table(show_header=True, header_style="bold magenta")
    search_table.add_column("Use Case", style="cyan", width=18)
    search_table.add_column("Command", style="white")

    for use_case, command in search_examples:
        search_table.add_row(use_case, command)

    console.print(search_table)

    console.print("\n[bold green]📋 Workspace Management Examples[/bold green]")

    mgmt_examples = [
        ("List all chats", "tf chats"),
        ("View chat details", "tf chat CHAT_ID"),
        ("Show config", "tf config-show"),
        ("Detailed help", "tf help-guide"),
    ]

    mgmt_table = Table(show_header=True, header_style="bold green")
    mgmt_table.add_column("Use Case", style="cyan", width=18)
    mgmt_table.add_column("Command", style="white")

    for use_case, command in mgmt_examples:
        mgmt_table.add_row(use_case, command)

    console.print(mgmt_table)

    console.print("\n[bold yellow]🔧 Configuration Options[/bold yellow]")
    config_table = Table(show_header=True, header_style="bold yellow")
    config_table.add_column("Method", style="cyan", width=15)
    config_table.add_column("Description", style="white")
    config_table.add_column("Example", style="dim")

    config_options = [
        ("Environment", "Set environment variables", "export TF_API_KEY=your_key"),
        (
            "Config file",
            "Use ~/.toothfairy/config.yml",
            "api_key: your_key\\nworkspace_id: your_workspace",
        ),
        ("CLI arguments", "Pass config file path", "tf --config /path/to/config.yml send ..."),
    ]

    for method, desc, example in config_options:
        config_table.add_row(method, desc, example)

    console.print(config_table)

    console.print("\n[bold red]⚠️  Common Issues & Solutions[/bold red]")
    issues_table = Table(show_header=True, header_style="bold red")
    issues_table.add_column("Issue", style="red", width=25)
    issues_table.add_column("Solution", style="white")

    issues = [
        (
            "Configuration incomplete",
            "Run: tf configure --api-key YOUR_KEY --workspace-id YOUR_WORKSPACE",
        ),
        ("No text response found", "Use --verbose flag to see full response details"),
        ("Agent not responding", "Check agent-id is correct and agent is active"),
        ("Network errors", "Verify API endpoints are accessible and credentials are valid"),
    ]

    for issue, solution in issues:
        issues_table.add_row(issue, solution)

    console.print(issues_table)

    console.print("\n[bold cyan]🔍 Search Filtering Guide[/bold cyan]")
    console.print("Knowledge Hub search supports powerful filtering options:")
    console.print("• [cyan]--status[/cyan]: Filter documents by 'published' or 'suspended' status")
    console.print("• [cyan]--topics[/cyan]: Use topic IDs from ToothFairyAI (comma-separated)")
    console.print("• [cyan]--document-id[/cyan]: Search within a specific document")
    console.print("• [cyan]--top-k[/cyan]: Control number of results (1-50)")
    console.print("• [cyan]--verbose[/cyan]: Show relevance scores and metadata")

    console.print("\n[bold magenta]📖 More Help[/bold magenta]")
    console.print("• Use [cyan]tf COMMAND --help[/cyan] for command-specific help")
    console.print("• Use [cyan]--verbose[/cyan] flag to see detailed request/response information")
    console.print("• Use [cyan]--output json[/cyan] for machine-readable output")
    console.print(
        "• Configuration is loaded from: environment variables → ~/.toothfairy/config.yml → CLI args"
    )

    console.print("\n[bold green]✨ Pro Tips[/bold green]")
    tips = [
        "💾 Save time: Configure once with 'tf configure', then just use 'tf send' and 'tf search'",
        "🔍 Debug issues: Use '--verbose' to see full API responses and troubleshoot",
        "📝 Scripting: Use '--output json' and tools like 'jq' to parse responses",
        "⚡ Quick tests: Only --agent-id is required for send, only query for search",
        "🎯 Better search: Use --status, --topics, and --document-id for targeted results",
        "🔧 Multiple environments: Use different config files with '--config' flag",
    ]

    for tip in tips:
        console.print(f"  {tip}")

    console.print(
        f"\n[dim]ToothFairy CLI v{__import__('toothfairy_cli').__version__} - For more help, visit the documentation[/dim]"
    )


def main():
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
