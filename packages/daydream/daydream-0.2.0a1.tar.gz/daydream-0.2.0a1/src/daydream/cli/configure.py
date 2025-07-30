import json
import shlex
import shutil
from pathlib import Path
from typing import Annotated, Any

import anyio
import rich
import typer
from fastmcp.cli.claude import get_claude_config_path

from daydream.cli._app import app
from daydream.cli.options import PROFILE_OPTION
from daydream.config.utils import DEFAULT_CONFIG, Config, get_config_path, load_config, save_config
from daydream.plugins.base import PluginManager
from daydream.utils import Choice, checkbox, confirm, iprint


def _resolve_default_claude_mcp_config_filename() -> Path | None:
    claude_config_dir = get_claude_config_path()
    if claude_config_dir is None:
        return None
    return claude_config_dir / "claude_desktop_config.json"


_default_claude_mcp_config_filename = _resolve_default_claude_mcp_config_filename()


def _resolve_default_uvx() -> Path:
    uv_path = shutil.which("uvx")
    if uv_path:
        return Path(uv_path).absolute()
    return Path("uvx")


_default_uvx_path = _resolve_default_uvx()


def _resolve_default_repo_path() -> Path:
    return Path.cwd().absolute()


_default_repo_path = _resolve_default_repo_path()


def _resolve_default_claude_app() -> Path:
    return Path("/Applications/Claude.app").resolve()


_default_claude_app = _resolve_default_claude_app()


@app.command()
def configure(
    profile: str = PROFILE_OPTION,
    uv_path: Annotated[
        Path,
        typer.Option(
            ...,
            "--uv-path",
            help="Path to the uv executable",
            show_default=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            writable=False,
            resolve_path=False,
            exists=True,
        ),
    ] = _default_uvx_path,
    mcp_command_prefix: Annotated[
        str | None,
        typer.Option(
            ...,
            "--mcp-command-prefix",
            help="Command prefix to use for the Daydream MCP Server (e.g., 'aws-vault exec your_aws_profile')",
        ),
    ] = None,
    mcp_command_directory: Annotated[
        Path | None,
        typer.Option(
            ...,
            "--mcp-command-dir",
            help="Path to the directory MCP server will be started",
            show_default=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            writable=False,
            resolve_path=False,
            exists=True,
        ),
    ] = _default_repo_path,
    claude_app: Annotated[
        Path | None,
        typer.Option(
            ...,
            "--claude-app",
            help="Path to the Claude Desktop app",
            show_default=True,
            file_okay=False,
            dir_okay=True,
            readable=True,
            writable=False,
            resolve_path=False,
            exists=False,
        ),
    ] = _default_claude_app,
    claude_config_file: Annotated[
        Path | None,
        typer.Option(
            ...,
            "--claude-config-filename",
            help="Path to the Claude Desktop MCP config json file",
            show_default=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            writable=True,
            resolve_path=False,
            exists=False,
        ),
    ] = _default_claude_mcp_config_filename,
) -> None:
    async def _recipe() -> None:
        _welcome_to_daydream()
        cfg = _initialize_daydream_config(profile)
        plugin_mgr = PluginManager(cfg)
        await _select_plugins_to_enable_disable(cfg)
        iprint("")
        await _configure_plugins(cfg, plugin_mgr)
        iprint("")
        await _validate_plugins(cfg, plugin_mgr)
        save_config(cfg, profile)
        await _suggest_building_graph()
        daydream_mcp_server_config = _generate_mcp_server_config(
            uv_path, mcp_command_prefix, mcp_command_directory
        )
        await _setup_clients_and_open(daydream_mcp_server_config, claude_app, claude_config_file)

    anyio.run(_recipe)


def _welcome_to_daydream() -> None:
    rich.print("""[red]
                ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣀⠤⠤⠒⠒⠒⠒⠒⠒⠤⢤⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀[red]
                ⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⠴⠚⠁⠀⠀⠀⠀⣀⣀⣀⡀⠀⠀⠀⠀⠙⠲⢄⠀⠀⠀⠀⠀⠀⠀⠀[orange]
                ⠀⠀⠀⠀⠀⠀⢀⡴⠊⠀⠀⢀⡠⠖⠒⠉⠉⠀⠀⠀⠈⠉⠑⠲⢤⡀⠀⠀⠑⣄⠀⠀⠀⠀⠀⠀[yellow]
                ⠀⠀⠀⠀⠀⣠⠋⠀⠀⣠⠴⠋⠀⠀⢀⡠⠤⠔⠒⠒⠦⠤⣀⠀⠀⠙⢦⡀⠀⠈⢣⠀⠀⠀⠀⠀[yellow]
                ⠀⠀⠀⠀⡰⠁⠀⠀⡼⠋⠀⠀⡠⠚⠁⠀⠀⠀⠀⠀⠀⠀⠈⠑⢄⠀⠀⠱⡄⠀⠀⢳⠀⠀⠀⠀[green]
                ⠀⠀⠀⢰⠁⠀⠀⡞⠀⠀⣠⠊⠀⠀⣠⠔⠊⠉⠉⠁⠒⠤⡀⠀⠈⢳⡀⠀⢳⡀⠀⠀⢧⠀⠀⠀[green]
                ⠀⠀⠀⡇⠀⠀⡸⠁⠀⡰⠁⠀⢀⡜⠁⠀⠀⠀⠀⠀⠀⠀⠈⢢⠀⠐⢧⠀⠀⢧⠀⠀⠘⡄⠀⠀[blue]
                ⠀⠀⢸⠁⠀⣠⡇⢀⣠⣇⡀⢀⠎⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣇⠀⣸⣄⣀⠘⣆⡀⠀⣇⠀⠀[blue]
                ⠀⠀⢸⣞⠉⠈⠙⡟⠀⠀⣻⠞⠳⣄⠀⠀⠀⠀⠀⠀⠀⠀⢠⡴⠛⢾⠁⠀⢘⡿⠁⠈⠹⣿⠀⠀[magenta]
                ⠀⣴⠟⠿⠀⠀⠀⠀⠀⠀⠀⠀⢠⠾⣄⠀⠀⠀⠀⠀⠀⢀⠼⣅⡀⠀⠀⠀⠀⠀⠀⠀⠘⠛⢦⠀[magenta]
                ⠸⣇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡀⣸⡇⠀⠀⠀⠀⠀⡏⠀⢁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⡇[bright_magenta]
                ⠀⠈⠹⠃⠀⠀⡄⠀⠀⠠⡀⠀⠙⣿⠉⠀⠀⠀⠀⠀⠀⠈⢹⠋⠀⠀⡤⠀⠀⢰⡄⠀⠀⢻⠉⠀[bright_magenta]
                ⠀⠀⠘⠦⠤⠼⠳⢄⣀⡰⠓⠂⠐⠋⠀⠀⠀⠀⠀⠀⠀⠀⠈⠓⠀⠚⠧⣀⣠⠞⠳⠤⠤⠟⠁⠀[default]

    ██████╗  █████╗ ██╗   ██╗██████╗ ██████╗ ███████╗ █████╗ ███╗   ███╗
    ██╔══██╗██╔══██╗╚██╗ ██╔╝██╔══██╗██╔══██╗██╔════╝██╔══██╗████╗ ████║
    ██║  ██║███████║ ╚████╔╝ ██║  ██║██████╔╝█████╗  ███████║██╔████╔██║
    ██║  ██║██╔══██║  ╚██╔╝  ██║  ██║██╔══██╗██╔══╝  ██╔══██║██║╚██╔╝██║
    ██████╔╝██║  ██║   ██║   ██████╔╝██║  ██║███████╗██║  ██║██║ ╚═╝ ██║
    ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚═════╝ ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝

> Welcome to Daydream!
>
> This interactive tool will walk through the configuration of your system.
> We'll setup Daydream plugins, configuration, and configure clients like Claude Desktop or Amazon Q to use the Daydream MCP server...
> """)


def _initialize_daydream_config(profile: str) -> Config:
    cfg_path = get_config_path(profile, create=True)
    if cfg_path.exists():
        return load_config(profile=profile)
    return PluginManager.default_config


async def _select_plugins_to_enable_disable(
    cfg: Config,
) -> None:
    iprint("Daydream uses plugins to access your infrastructure resources, like AWS or Aptible.")
    iprint("Each plugin may be enabled or disabled to match your desired knowledge graph")
    iprint(
        "Some plugins require configuration, for example the AWS plugin needs access to your AWS account"
    )
    iprint("")
    iprint("These are the plugins we recommend:")
    for plugin_name, plugin_cfg in DEFAULT_CONFIG.plugins.items():
        if plugin_cfg.enabled:
            iprint(f"• {plugin_name}")
    iprint("")
    if await confirm(
        "Would you like to change this?",
        default=False,
    ):
        await _enable_disable_plugins(cfg)


async def _enable_disable_plugins(cfg: Config) -> None:
    possible_plugins = list(cfg.plugins.keys())
    enabled_search = len(possible_plugins) > 10
    selected_plugins = await checkbox(
        "Which plugins would you like to enable for the Daydream MCP Server? Press enter to continue",
        choices=[Choice(p, checked=plugin_cfg.enabled) for p, plugin_cfg in cfg.plugins.items()],
        use_search_filter=enabled_search,
        use_jk_keys=not enabled_search,
    )
    for plugin_name, plugin_cfg in cfg.plugins.items():
        plugin_cfg.enabled = plugin_name in selected_plugins


async def _configure_plugins(cfg: Config, plugin_mgr: PluginManager) -> None:
    iprint("Now we will go through plugin specific configuration...")
    iprint("")
    for plugin_name, plugin_cfg in cfg.plugins.items():
        if not plugin_cfg.enabled:
            continue
        iprint(f"Configuring [bold]{plugin_name}[/bold] plugin settings...")
        plugin = plugin_mgr.get_plugin(plugin_name)
        plugin_settings = await plugin.interactive_configure(cfg)
        plugin_cfg.settings = plugin_settings
        iprint(f"✅ {plugin_name} plugin settings configured successfully!")
        iprint("")


async def _validate_plugins(cfg: Config, plugin_mgr: PluginManager) -> None:
    iprint(
        "And now we'll verify that these plugins have the appropriate configuration, and validate any authentication works as expected..."
    )
    iprint("")
    for plugin_name, plugin_cfg in cfg.plugins.items():
        if not plugin_cfg.enabled:
            continue
        iprint(f"Validating {plugin_name} plugin...")
        plugin = plugin_mgr.get_plugin(plugin_name)
        # FIXME: propagate failed validation... but don't cause the process to stop
        attempt_validation = True
        config_valid = False
        err: Exception | None = None
        while attempt_validation:
            try:
                await plugin.validate_plugin_config()
            except Exception as ex:
                iprint(f"{plugin_name} validation error: {ex!s}")
                attempt_validation = await confirm(f"Retry {plugin_name} validation?", default=True)
                err = ex
            else:
                config_valid = True
                attempt_validation = False
        if config_valid:
            iprint(f"✅ {plugin_name} has valid config and is working!")
        else:
            iprint(f"❌ {plugin_name} validation failed: {err!s}")


async def _suggest_building_graph() -> None:
    iprint("We recommend building the knowledge graph before proceeding.")
    iprint("Try running this command in another window:")
    iprint("")
    iprint("    uvx daydream build-graph")
    iprint("")
    while not await confirm("Ready to proceed?", default=True):
        pass
    iprint("")


def _generate_mcp_server_config(
    uv_path: Path, mcp_command_prefix: str | None, mcp_command_directory: Path | None
) -> dict[str, Any]:
    command, *args = [
        *shlex.split(mcp_command_prefix or ""),
        str(uv_path),
        "run",
        *(["--directory", str(mcp_command_directory)] if mcp_command_directory else []),
        "daydream",
        "start",
        "--disable-sse",
    ]
    env = {
        "HOME": str(Path.home()),
    }
    return {
        "command": shutil.which(command),
        "args": args,
        "env": env,
    }


async def _setup_clients_and_open(
    daydream_mcp_server_config: dict[str, Any],
    claude_app: Path | None,
    claude_config_file: Path | None,
) -> None:
    # claude code: ~/Library/Application Support/Claude/claude_desktop_config.json
    # amazon q: ~/.aws/amazonq/mcp.json
    # cursor: ~/.cursor/mcp.json
    # windsurf: ~/.codeium/windsurf/mcp_config.json
    if not await confirm(
        "Would you like to setup Claude Code to use the Daydream MCP server?",
        default=True,
    ):
        return
    if claude_app is None or not claude_app.exists():
        iprint(f"❌ Claude Desktop app not found at [bright_black]{claude_app}[/bright_black]")
        iprint(
            "Please let us know about this issue, and try again with the --claude-app <path> flag"
        )
        iprint("")
        return
    if claude_config_file is None:
        iprint(
            f"❌ Claude Desktop MCP configuration file not found at [bright_black]{claude_config_file}[/bright_black]"
        )
        iprint(
            "Please let us know about this issue, and try again with the --claude-config-filename <path> flag"
        )
        iprint("")
        return
    await _setup_claude_desktop_client(daydream_mcp_server_config, claude_app, claude_config_file)


async def _merge_daydream_mcp_config(
    daydream_mcp_server_config: dict[str, Any], config_file: Path
) -> dict[str, Any]:
    mcp_servers = {
        "mcpServers": {
            "daydream": daydream_mcp_server_config,
        }
    }
    if not config_file.exists():
        return mcp_servers
    if not (existing_mcp_servers := json.loads(config_file.read_text())):
        return mcp_servers
    if not (
        isinstance(existing_mcp_servers, dict)
        and all(isinstance(k, str) for k in existing_mcp_servers)
    ):
        return mcp_servers
    result = {**existing_mcp_servers, **{"daydream": daydream_mcp_server_config}}
    return result


async def _setup_claude_desktop_client(
    daydream_mcp_server_config: dict[str, Any], claude_app: Path, claude_config_file: Path
) -> None:
    mcp_servers = await _merge_daydream_mcp_config(daydream_mcp_server_config, claude_config_file)
    claude_config_file.write_text(json.dumps(mcp_servers, indent=2))
    iprint(
        f"✅ Updated Claude Desktop MCP config file at [bright_black]{claude_config_file.resolve()!s}[/bright_black]"
    )
    if await confirm("Would you like to open the Claude Desktop app now?", default=True):
        iprint(f"Opening [bright_black]{claude_app}[/bright_black]...")
        typer.launch(str(claude_app))
    iprint("")
