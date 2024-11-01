```
         _ __      __
   _____(_) /_____/ /___ _      ______
  / ___/ / __/ __  / __ \ | /| / / __ \
 (__  ) / /_/ /_/ / /_/ / |/ |/ / / / /
/____/_/\__/\__,_/\____/|__/|__/_/ /_/
```

A tool to help you generate your standup notes from Linear.app!

## Installation

### Local Development Setup

1. Install `uv` if you haven't already:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Clone the repository:
```bash
git clone https://github.com/kevinjqiu/sitdown.git
cd sitdown
```

3. Create and activate a virtual environment:
```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

4. Install dependencies:
```bash
uv pip install -e .
```

## Usage

1. First, get your Linear API key from [Linear Settings > API](https://linear.app/settings/api)

2. Set your API key in .env file:
```bash
LINEAR_API_KEY="lin_api_xxxxxxxxxxxx"
OPENAI_API_KEY="sk_xxxxxxxxxxxxxxxxxxxxxxxx"
```

3. Run the tool:
```bash
sitdown

# Or to get issues from the last N days
sitdown --days 7
```

## Development

To run linting:
```bash
ruff check .
```

## License

MIT
