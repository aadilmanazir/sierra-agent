# Sierra Agent

A customer service agent and API for Sierra Outfitters, a fictional outdoor gear company.

## Features

- FastAPI backend for accessing product and order data
- Conversational agent powered by OpenAI
- Terminal-based interface for interacting with the agent
- Comprehensive evaluation framework for testing agent performance

## Setup

### Prerequisites

- Python 3.9+
- Poetry (for dependency management)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/sierra-agent.git
cd sierra-agent
```

2. Install dependencies with Poetry:
```bash
poetry install
```

3. Create a `.env` file in the project root with your OpenAI API key:
```
OPEN_AI_API_KEY=your_openai_api_key_here
```

4. Verify your environment:
```bash
poetry run python main.py env-check
```

## Usage

### Running the API Server

Start the FastAPI server with:

```bash
poetry run python main.py api
```

This will start the server at http://localhost:8000. You can access the API documentation at http://localhost:8000/docs.

### Using the Chat Interface

Start a conversation with the Sierra Agent:

```bash
poetry run python main.py chat
```

You can ask about:
- Products (e.g., "What backpacks do you sell?")
- Order status (e.g., "What's the status of order #W001?")
- Order tracking (e.g., "Track order TRK123456789")

Type `exit`, `quit`, or `bye` to end the conversation.

### Running Evaluations

Run the evaluation framework to test the agent's performance:

```bash
poetry run python main.py evaluate
```

This will run a series of test cases and generate a report in `evaluation_results.json`.

## Project Structure

```
sierra-agent/
├── api/                     # FastAPI application
│   ├── main.py              # API entry point
│   ├── routes/              # API endpoints
│   └── models/              # Pydantic models
├── agent/                   # Conversation agent
│   ├── conversation.py      # Core agent logic
│   ├── intents/             # Intent handlers
│   └── utils.py             # Utility functions
├── data/                    # Data files
│   ├── ProductCatalog.json  # Product catalog data
│   └── CustomerOrders.json  # Customer order data
├── evals/                   # Evaluation framework
│   ├── metrics.py           # Evaluation metrics
│   └── test_cases.py        # Test cases
├── main.py                  # CLI entry point
├── pyproject.toml           # Poetry configuration
└── README.md                # Project documentation
```

## Development

To add new features or fix bugs:

1. Add new data to `data/` if needed
2. Add models to `api/models/` 
3. Add routes to `api/routes/`
4. Add intent handlers to `agent/intents/`
5. Update the agent logic in `agent/conversation.py`
6. Add test cases to `evals/test_cases.py`