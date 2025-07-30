from click.testing import CliRunner
from node_hermes_core.cli import schema


def test_hello_world():
    runner = CliRunner()
    result = runner.invoke(schema, ["-o", "schema.json", "--config", "test/config_virtual.yaml"])
    print(result.output)
    assert result.exit_code == 0


test_hello_world()
