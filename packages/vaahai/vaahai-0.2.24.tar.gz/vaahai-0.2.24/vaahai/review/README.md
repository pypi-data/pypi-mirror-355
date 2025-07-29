# VaahAI Review Module

This module provides components for code review functionality in the VaahAI system.

## Review Steps Registry

The Review Steps Registry is a central component that manages and organizes code review steps. It allows for registration, discovery, and execution of various code review checks.

### Key Components

- **ReviewStep**: Base class for all review steps
- **ReviewStepRegistry**: Central registry for managing review steps
- **ReviewStepCategory**: Enum defining categories for review steps
- **ReviewStepSeverity**: Enum defining severity levels for review steps

### Directory Structure

```
vaahai/review/
├── __init__.py                # Package exports
├── steps/                     # Review steps package
│   ├── __init__.py            # Package exports
│   ├── base.py                # Base classes and interfaces
│   ├── registry.py            # Registry implementation
│   └── built_in/              # Built-in review steps
│       ├── __init__.py        # Package exports
│       └── style.py           # Style-related review steps
```

## Usage

### Registering a Review Step

```python
from vaahai.review.steps import ReviewStepRegistry, ReviewStep, ReviewStepCategory, ReviewStepSeverity

@ReviewStepRegistry.register("my_custom_step")
class MyCustomStep(ReviewStep):
    def __init__(
        self,
        id="my_custom_step",
        name="My Custom Step",
        description="A custom review step",
        category=ReviewStepCategory.GENERAL,
        severity=ReviewStepSeverity.MEDIUM,
        **kwargs
    ):
        super().__init__(
            id=id,
            name=name,
            description=description,
            category=category,
            severity=severity,
            **kwargs
        )
    
    def execute(self, context):
        # Implement your review logic here
        return {
            "status": "success",
            "message": "Review completed",
            "issues": []
        }
```

### Finding Review Steps

```python
# Get all registered steps
all_steps = ReviewStepRegistry.get_all_steps()

# Get a specific step by ID
step_class = ReviewStepRegistry.get_step("line_length")

# Filter steps by category
style_steps = ReviewStepRegistry.filter_steps(category=ReviewStepCategory.STYLE)

# Filter steps by severity
critical_steps = ReviewStepRegistry.filter_steps(severity=ReviewStepSeverity.CRITICAL)

# Filter steps by tags
formatting_steps = ReviewStepRegistry.filter_steps(tags="formatting")
```

### Executing Review Steps

```python
# Create a step instance
line_length_step = ReviewStepRegistry.create_step_instance("line_length", max_length=100)

# Execute the step
context = {
    "file_path": "example.py",
    "content": "def example():\n    pass\n"
}
result = line_length_step.execute(context)

# Process the results
if result["status"] == "success":
    print(f"Found {len(result['issues'])} issues")
    for issue in result["issues"]:
        print(f"Line {issue['line']}: {issue['message']}")
```

## Built-in Review Steps

The module includes several built-in review steps:

### Style Checks

- **LineLength**: Checks if any lines exceed a maximum length
- **IndentationConsistency**: Checks if indentation is consistent throughout the code

## Extending with Custom Steps

You can create custom review steps by:

1. Subclassing `ReviewStep`
2. Implementing the `execute` method
3. Registering the step with `@ReviewStepRegistry.register()`

See the example script at `examples/review_steps_example.py` for a complete demonstration.
