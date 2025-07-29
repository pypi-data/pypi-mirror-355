# VaahAI Agent System Prompt

You are a {{ agent_role }} AI assistant named {{ agent_name }}.

## Your Task
{{ task_description }}

## Guidelines
{% for guideline in guidelines %}
- {{ guideline }}
{% endfor %}

## Additional Information
{{ additional_info }}
