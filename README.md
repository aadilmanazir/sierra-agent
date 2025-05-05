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
- Promotions (e.g., "Can I have a discount code for being awesome?")

Type `exit`, `quit`, or `bye` to end the conversation.

### TODO: Running Evaluations

## Project Structure

```
sierra-agent/
├── api/                     # FastAPI application
│   ├── main.py              # API entry point
│   ├── routes/              # API endpoints
│   │   ├── products.py      # Product endpoints
│   │   └── orders.py        # Order endpoints 
│   └── models/              # Pydantic models
│       ├── products.py      # Product models
│       └── order.py         # Order models
├── agent/                   # Conversation agent
│   ├── conversation.py      # Core agent logic with SierraAgent class
│   ├── types.py             # Agent state definitions
│   ├── services/            # Service integrations
│   │   ├── products.py      # Product API services
│   │   └── orders.py        # Order API services
│   └── utils/               # Utility mixins and functions
│       ├── agent_utils.py   # General agent utilities and intent detection
│       ├── product_utils.py # Product-specific functionality
│       └── order_utils.py   # Order-specific functionality
├── data/                    # Data files
│   ├── ProductCatalog.json  # Product catalog data
│   └── CustomerOrders.json  # Customer order data
├── evals/                   # TODO
│   └── test_cases.py        # TODO
├── main.py                  # CLI entry point
├── pyproject.toml           # Poetry configuration
└── README.md                # Project documentation
```