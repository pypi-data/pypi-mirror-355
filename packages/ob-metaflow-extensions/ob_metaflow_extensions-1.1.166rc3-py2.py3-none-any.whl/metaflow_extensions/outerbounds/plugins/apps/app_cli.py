from metaflow._vendor import click

OUTERBOUNDS_APP_CLI_AVAILABLE = True
try:
    import outerbounds.apps.app_cli as ob_apps_cli
except ImportError:
    OUTERBOUNDS_APP_CLI_AVAILABLE = False


if not OUTERBOUNDS_APP_CLI_AVAILABLE:

    @click.group()
    def _cli():
        pass

    @_cli.group(help="Dummy Group to append to CLI for Safety")
    def app():
        pass

    @app.command(help="Dummy Command to append to CLI for Safety")
    def cannot_deploy():
        raise Exception("Outerbounds App CLI not available")

    cli = _cli
else:
    cli = ob_apps_cli.cli
