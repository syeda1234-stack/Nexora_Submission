# Nexora AI – Cross-Border & Student Finance Assistant

Nexora AI is a project developed by our team for the **2026 FinTechathon – International Track, Topic C**.

The idea behind Nexora is to make financial planning a little easier for international students. Studying in another country comes with different financial challenges, such as managing tuition fees, daily expenses, currency exchange, and international transfers.

We wanted to bring some of these tasks together in one place and explore how AI agents can help students make better-informed financial decisions.

## What Can Nexora Do?

Some of the main features we have worked on include:

- **Student Budget Planning:** Calculate expenses, income, and remaining balances.
- **Tuition Planning:** Estimate funding gaps and plan for upcoming educational expenses.
- **Currency Exchange:** Check reference exchange rates and estimate transfer amounts.
- **Transfer Estimation:** Compare estimated transfer costs using fees and exchange rates.
- **AI Financial Assistant:** Ask questions and receive financial planning suggestions.
- **Scholarship Discovery:** Find links to scholarship and university opportunities.
- **Transfer Simulation:** Prepare and review a transfer before explicitly confirming a simulated transaction.
- **Agent Activity:** Inspect how the agent plans requests and uses its available tools.

## How the AI Agent Works

One of the things we wanted to explore was making Nexora more than a basic chatbot.

The agent follows a tool-based workflow. It identifies the user's request, selects an appropriate tool, processes the result, and generates a response.

We used LangChain and LangGraph to implement the agent workflow, including tool calling and a self-review step.

The project also supports different execution modes:

- **Gemini:** Model-backed responses using the Gemini API.
- **Ollama Cloud:** An alternative model provider.
- **Demo Mode:** A local rule-based fallback that allows the application to demonstrate its main workflows without an AI API key.

This approach helps us demonstrate the project even when an external AI provider is unavailable.

## Technologies Used

| Area | Technologies |
|---|---|
| Backend | Python, FastAPI |
| Frontend | HTML, CSS, JavaScript |
| AI Agent | LangChain, LangGraph |
| AI Providers | Gemini, Ollama Cloud |
| Database | SQLite |
| API Communication | Requests, HTTPX |
| Testing | Pytest, FastAPI TestClient |

## Project Structure

```text
Nexora_Submission/
│
├── app.py
├── requirements.txt
├── README.md
├── render.yaml
│
├── nexora_agent/
│   ├── lc.py
│   ├── graph.py
│   ├── tools.py
│   ├── runtime.py
│   └── demo.py
│
├── static/
│   ├── style.css
│   ├── script.js
│   └── chat.js
│
├── templates/
│   └── index.html
│
├── tests/
│   ├── test_app.py
│   └── test_agent.py
│
├── TECHNICAL_DOCUMENTATION.md
└── SECURITY_SELF_ASSESSMENT.md
```

## Getting Started

To run Nexora locally, you need Python 3 and pip installed.

**1. Clone the repository**

```bash
git clone https://github.com/syeda1234-stack/Nexora_Submission.git
```

**2. Open the project directory**

```bash
cd Nexora_Submission
```

**3. Create a virtual environment**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

**4. Install the dependencies**

```bash
pip install -r requirements.txt
```

**5. Start the application**

```bash
uvicorn app:app --host 127.0.0.1 --port 8000
```

Open the following address in your browser:

http://127.0.0.1:8000

API documentation is also available at:

http://127.0.0.1:8000/docs

## AI Provider Configuration

Nexora can run in demo mode without an external AI API key.

For Gemini, configure your API key as a server-side environment variable:

```bash
export GEMINI_API_KEY='YOUR_API_KEY'
```

For Ollama Cloud, configure the required environment variables:

```bash
export NEXORA_AI_PROVIDER=ollama
export OLLAMA_API_KEY='YOUR_API_KEY'
export OLLAMA_MODEL='gpt-oss:120b'
```

Never upload actual API keys or private credentials to GitHub.

## Testing

We use Pytest and FastAPI TestClient for testing the application.

Run the tests using:

```bash
python -m pytest tests/test_app.py -q
```

The tests cover application health, input validation, budgeting calculations, transfer estimates, chat behaviour, and simulated transaction confirmation.

**Note:** A previous development test run reported 15 passed and 1 failed. The remaining failure needs to be investigated and retested before claiming that the entire test suite passes.

## Limitations and Security

Nexora is currently an educational prototype, not a production financial application.

Some important limitations include:

- It does not connect to real bank accounts.
- It does not execute actual money transfers.
- Exchange rates are reference values, not guaranteed remittance provider quotes.
- Scholarship and university discovery results are search links, not verified opportunities.
- AI-generated responses may contain errors.
- Production authentication, rate limiting, and independent security audits have not been implemented.
- Some interface modules are demonstrations rather than live integrations.

All transfer operations are simulations and are labelled `SIMULATED_NOT_SENT`.

Please use synthetic information when testing the application.

For more details, see:
- [Technical Documentation](TECHNICAL_DOCUMENTATION.md)
- [Security Self-Assessment](SECURITY_SELF_ASSESSMENT.md)

## Team Information

**Project Name:** Nexora AI

**Competition:** 2026 Shenzhen International FinTech Competition (FinTechathon)

**Track:** International Track

**Topic:** Topic C – Cross-Border & Student Finance Assistant

**Team Name:** Hermes Hodios

**Team Members:** [Add registered team member names]

## A Note About the Project

Building Nexora has been a learning experience for our team. Through this project, we explored AI agent workflows, backend development, financial calculations, API integration, and the importance of security when working with financial applications.

There is still room for improvement, and we hope to continue developing the project further.

Thanks for checking out Nexora AI!
