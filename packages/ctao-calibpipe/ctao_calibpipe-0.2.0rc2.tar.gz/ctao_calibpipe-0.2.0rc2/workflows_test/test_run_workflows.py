import subprocess
from enum import Enum, auto
from pathlib import Path

import pytest


class WorkflowGroup(Enum):
    ATMOSPHERE = auto()
    # Add other groups as needed


def run_cwl(workflow, config=None):
    command = ["cwltool", workflow]
    if config is not None:
        command.append(config)
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        return result.stderr
    except subprocess.CalledProcessError as e:
        return e.stderr


@pytest.mark.integration()
@pytest.mark.parametrize(
    ("group", "id"),
    [
        pytest.param(
            WorkflowGroup.ATMOSPHERE,
            "2",
            marks=pytest.mark.verifies_usecase("UC-120-1.2"),
        ),
        pytest.param(
            WorkflowGroup.ATMOSPHERE,
            "3",
            marks=pytest.mark.verifies_usecase("UC-120-1.3"),
        ),
        pytest.param(
            WorkflowGroup.ATMOSPHERE,
            "7",
            marks=pytest.mark.verifies_usecase("UC-120-1.7"),
        ),
    ],
)
def test_run_cwl(group, id):
    path_to_workflows = Path(__file__).parent / "../workflows"
    path_to_workflows_cfgs = Path(__file__).parent / "../workflows_cfgs"

    # Use glob to find the file matching the new naming convention
    workflow_pattern = f"uc-120-{group.value}.{id}*.cwl"
    config_pattern = f"uc-120-{group.value}.{id}*.cfg"

    try:
        workflow_file = next(
            (path_to_workflows / group.name.lower()).glob(workflow_pattern)
        )
        config_file = next(
            (path_to_workflows_cfgs / group.name.lower()).glob(config_pattern)
        )
    except StopIteration:
        pytest.fail(
            f"No matching workflow or config file found for pattern {workflow_pattern}"
        )

    output = run_cwl(workflow_file, config_file)
    assert (
        "Final process status is success" in output
        or "Final process status is temporaryFail" in output
    )
    if "Final process status is temporaryFail" in output:
        assert "exited with status: 100" in output
