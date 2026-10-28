# Contributing

Thanks for helping improve NOVA.

## Workflow

1. Fork or clone the project.
2. Create a feature branch.
3. Keep changes focused and document them clearly.
4. Validate with the project tests before opening a pull request.
5. Include a short summary of the problem, fix, and verification steps.

## Local setup

- Create a virtual environment.
- Install dependencies from `requirements.txt`.
- Configure MySQL and set `SMART_INVENTORY_DB_PASSWORD`.
- Run the application from the project root with `python app.py`.

## Code guidelines

- Preserve the existing Tkinter design and database behavior.
- Do not modify live production data during development.
- Use MySQL-safe parameterized queries.
- Keep new files scoped to the project and document non-obvious changes.

## Testing

Run the project test suite from the repository root:

```bash
python -m unittest discover -s tests -v
```

## Pull requests

Open a pull request with:

- a short description of the change,
- the affected files,
- validation steps, and
- any known limitations.
