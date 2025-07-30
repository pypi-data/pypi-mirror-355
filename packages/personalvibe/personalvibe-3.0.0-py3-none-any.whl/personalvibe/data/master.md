# {{ project_name }} development prompt

You are tasked with {{ task_summary }} related to the {{ project_name }} project.

You will be given the following information:

* User instructions
* Task instructions
* Project context

## User instruction

User instructions act as overrides on all remaining instruction material.
As opposed to a pre-prepared task instruction, user instructions are more
tactical and relevant to the current state of {{ project_name }} project,
and the specific needs to drive the development forward in the most optimal way.

<user_instructions>
{{ user_instructions }}
</user_instructions>

## Task instructions

Task instructions include a specific methodology for handling the remaining material
in order to achieve completion of a pre-prepared, commonly used task.
Task instructions also specify output requirements.

<task_instructions>
{{ task_instructions }}
</task_instructions>

## Project context

Project context can include a variety of documentation, code, tests, logs, and scripts.

<project_context>
{{ project_context }}
</project_context>
