import pytest
import yaml
from pathlib import Path
from ksub.parsers.dsl import parse_script
from ksub.kubernetes.job import generate_job_specs

def test_entrypoint_parsing():
    """Test that entrypoint is correctly parsed from the script"""
    # Parse the example script
    script_path = Path("tests/examples/simple_entrypoint.sh")
    job_blocks = parse_script(script_path)
    
    # Check that we have at least one job block
    assert len(job_blocks) > 0, "No job blocks parsed from script"
    
    # Check the parsed entrypoint and commands
    for job_block in job_blocks:
        assert hasattr(job_block, 'entrypoint'), "Job block should have an entrypoint attribute"
        assert hasattr(job_block, 'commands'), "Job block should have a commands attribute"

def test_entrypoint_in_job_spec():
    """Test that entrypoint is correctly included in the job spec"""
    # Parse the example script
    script_path = Path("tests/examples/simple_entrypoint.sh")
    job_blocks = parse_script(script_path)
    
    # Generate job specs
    job_specs = generate_job_specs(job_blocks)
    
    # Check that we have specs for each job block
    assert len(job_specs) == len(job_blocks), "Number of job specs should match number of job blocks"
    
    # Check the generated job specs
    for name, spec in job_specs.items():
        # Convert YAML to dict
        job_dict = yaml.safe_load(spec)
        
        # Get container spec
        container = job_dict["spec"]["template"]["spec"]["containers"][0]
        
        # Check command and args
        if any(job_block.entrypoint for job_block in job_blocks if job_block.name == name):
            assert "command" in container, "Container should have command when entrypoint is specified"
        
        if any(job_block.commands for job_block in job_blocks if job_block.name == name):
            assert "args" in container, "Container should have args when commands are specified"