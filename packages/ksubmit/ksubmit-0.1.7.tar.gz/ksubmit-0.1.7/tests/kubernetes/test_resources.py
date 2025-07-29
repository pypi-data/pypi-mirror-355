import pytest
import yaml
from pathlib import Path
from ksubmit.parsers.dsl import parse_script
from ksubmit.kubernetes.job import generate_job_specs

def test_resource_parsing():
    """Test that resources are correctly parsed from the script"""
    # Parse the example script
    script_path = Path("tests/examples/simple_cpu.sh")
    job_blocks = parse_script(script_path)
    
    # Check that we have at least one job block
    assert len(job_blocks) > 0, "No job blocks parsed from script"
    
    # Check the parsed resources
    for job_block in job_blocks:
        assert job_block.name, "Job block should have a name"
        assert job_block.image, "Job block should have an image"
        assert job_block.resources, "Job block should have resources"

def test_job_spec_generation():
    """Test that job specs are correctly generated"""
    # Parse the example script
    script_path = Path("tests/examples/simple_cpu.sh")
    job_blocks = parse_script(script_path)
    
    # Generate job specs
    job_specs = generate_job_specs(job_blocks)
    
    # Check that we have specs for each job block
    assert len(job_specs) == len(job_blocks), "Number of job specs should match number of job blocks"
    
    # Check the generated job specs
    for name, spec in job_specs.items():
        # Convert YAML to dict
        job_dict = yaml.safe_load(spec)
        
        # Check basic structure
        assert "apiVersion" in job_dict, "Job spec should have apiVersion"
        assert "kind" in job_dict, "Job spec should have kind"
        assert "metadata" in job_dict, "Job spec should have metadata"
        assert "spec" in job_dict, "Job spec should have spec"
        
        # Check activeDeadlineSeconds
        assert "activeDeadlineSeconds" in job_dict["spec"], "Job spec should have activeDeadlineSeconds"
        
        # Check resources
        container = job_dict["spec"]["template"]["spec"]["containers"][0]
        assert "resources" in container, "Container should have resources"
        
        # Check memory units
        resources = container["resources"]
        if "requests" in resources and "memory" in resources["requests"]:
            memory = resources["requests"]["memory"]
            assert isinstance(memory, str), "Memory should be a string"
            assert memory.endswith("Mi") or memory.endswith("Gi"), "Memory should have units"
        
        # Check restart policy
        assert "restartPolicy" in job_dict["spec"]["template"]["spec"], "Job spec should have restartPolicy"
        
        # Check labels
        assert "labels" in job_dict["metadata"], "Job spec should have labels"