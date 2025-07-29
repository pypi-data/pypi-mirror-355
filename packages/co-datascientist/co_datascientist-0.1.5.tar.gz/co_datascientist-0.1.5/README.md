# CoDatascientist

<div align="center">

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

<div align="center">
  <img src="figures/logo2.png" alt="PiñaColada Logo" width="500"/>
</div>

An agentic framework for recursive model improvement.

</div>

## 🚀 Quickstart
Install `co-datascientist`:

```bash
pip install co-datascientist
```

To use from command line, run:
```bash
co-datascientist run --script-path myscript.py
```

For development with a local backend, use the `--dev` flag:
```bash
co-datascientist --dev run --script-path myscript.py
```

To use from cursor or other AI clients, run the MCP server:
```bash
co-datascientist mcp-server
```

For development mode:
```bash
co-datascientist --dev mcp-server
```

And add the MCP configuration to the AI client. For example in cursor go to:
`file -> preferences -> cursor settings -> MCP -> Add new global MCP server`,
and add the co-datascientist mcp server config in the json, should look like this:
```json
{
  "mcpServers": {
    "CoDatascientist": {
        "url": "http://localhost:8001/sse"
    }
  }
}
```

## 💰 Cost Tracking
Track your LLM usage costs automatically:

```bash
# View summary costs
co-datascientist costs

# View detailed breakdown
co-datascientist costs --detailed
```

The system automatically tracks:
- **Total costs** across all workflows
- **Token usage** (input/output tokens)
- **Per-workflow costs** and breakdown
- **Model-specific costs** using LiteLLM's built-in pricing

All costs are calculated in real-time using LiteLLM's `completion_cost()` function with up-to-date pricing for all supported models (OpenAI, Anthropic, DeepSeek, etc.).

## 🧠 How does it work?
AI agents are advanced enough to hypothetize ideas, write the code, and evaluate results. 

While they're not yet advanced enough to do all of this independently, they are good enough to give a *worthy attempt* at each step.

CoDatascientist coordinates AI agents and automates the workflow of
Idea generation → implementation → testing.

The cycle is done iteratively, selecting the best candidates using the agent's own logic - this is why the metric for success has to be simple, which is the case with ML tasks: it's easy to boil the success to a single number or a vector.

## 🛠️ Features

### Idea Generation
- 📚 Arxiv paper reader
- 💡 Idea generator
- 🔍 Idea critic
- 📊 Time series tool APIs
- 📖 RAG with ML-trading books

### Implementation
- 🛠️ AIDER integration
- 🔄 Automatic improvement system
- 📈 Metric comparison

### Cost Management
- 💰 Real-time cost tracking per user
- 📊 Token usage monitoring
- 🔍 Workflow-level cost breakdown
- 📈 Model-specific cost analysis

### 📊 Benchmarking
Coming soon!

## Any questions? Contact us!
we're happy to help, discuss and debug.

contact us at `ozsamkilim@gmail.com`

---
<div align="center">
Made with ❤️ by the CoDatascientist team
</div>