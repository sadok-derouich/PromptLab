# PromptLab
# 🧪 PromptLab

**PromptLab** is a lightweight web-based tool for crafting, testing, versioning, and evaluating prompts across different Large Language Models (LLMs). Designed for prompt engineers, LLM enthusiasts, researchers, and tinkerers, it provides a structured playground to streamline your experimentation workflow.

---

## ✨ Why PromptLab?

Prompt engineering is as much science as it is art. Whether you're iterating on system prompts, testing user inputs, or benchmarking different models and APIs — PromptLab keeps everything organized and testable in one place.

---

## 📌 Features

- 🔧 **Prompt Versioning:** Create, edit, and track both system and user prompts across versions.
- 💬 **Prompt Runner:** Test prompts live against OpenAI or DeepSeek APIs with temperature control.
- 📝 **Output Evaluation:** Rank and comment on generated responses for later analysis.
- 📈 **CSV Export:** Download all outputs in CSV format for external analysis or reporting.
- 🗃 **PostgreSQL-Backed:** Easily deploy with any PostgreSQL database (local or cloud like Supabase).
- 🔍 **Frontend Tabs:** Intuitive UI for Admin, Runner, and Outputs.
- 🧩 **Configurable Providers:** Switch between LLM APIs on the fly.
- ⚡ **Fast & Lightweight:** No frameworks, no frontend build step — just Flask and vanilla JS.

---

## 🧰 Prerequisites

- Python 3.8+
- PostgreSQL instance (local or Supabase)
- API keys:
  - [OpenAI](https://platform.openai.com/)
  - [DeepSeek](https://platform.deepseek.com/)
- Browser (modern Chrome/Firefox recommended)

---

## 📦 Installation

```bash
git clone https://github.com/yourusername/promptlab.git
cd promptlab
```

> _Make sure your PostgreSQL database is running and accessible._

### 1. Install Dependencies

```bash
pip install flask flask-cors psycopg2 openai
```

### 2. Set Up `config.json`

Create a file named `config.json` in the root folder:

```json
{
  "OPENAI_API_KEY": "your-openai-api-key",
  "DEEPSEEK_API_KEY": "your-deepseek-api-key",
  "DB_HOST": "localhost",
  "DB_PORT": Port,
  "DB_NAME": "your_database",
  "DB_USER": "your_user",
  "DB_PASS": "your_password"
}
```

### 3. Create the Tables

Run the schema using psql or any PostgreSQL GUI:

```bash
psql -h <host> -U <user> -d <database> -f table.sql
```

### 4. Run the App

```bash
python app.py
```

Visit: [http://localhost:5001]

---

## 🗂 Interface Overview

| Tab            | Purpose                                         |
|----------------|--------------------------------------------------|
| **Prompt Runner** | Select prompts, run them, save outputs          |
| **Prompt Admin**  | Create/edit system and user prompts with versioning |
| **Outputs**       | View all saved responses, export CSV, delete entries |

---

## 🧪 Supported Models

| Provider  | Supported Models |
|-----------|------------------|
| OpenAI    | `gpt-3.5-turbo`, `gpt-4`, `gpt-4o`, `gpt-4o-mini`, `gpt-4-turbo`, `gpt-4-vision-preview` |
| DeepSeek  | `deepseek-chat`, `deepseek-reasoner` |

---

## 📁 File Structure

```bash
📦 promptlab/
├── app.py               # Flask backend and routes
├── config.json          # Local config (excluded from repo)
├── table.sql            # Database schema
├── index.html           # Tabbed interface
├── prompt-admin.html    # Admin panel for prompt CRUD
├── prompt-runner.html   # Live testing interface
├── outputs.html         # View & export prompt responses
```

---

## 🧱 Built With

- 🐍 **Python + Flask**
- 🐘 **PostgreSQL**
- 🔑 **OpenAI & DeepSeek APIs**
- 🧾 **Vanilla JS + HTML/CSS**

---

## 📈 Sample Workflow

1. Navigate to **Prompt Admin** and create your system/user prompts.
2. Switch to **Prompt Runner**, select prompts, choose a model and temperature.
3. Run the prompt and observe the JSON output.
4. Evaluate the output using the ranking and comment.
5. Go to **Outputs** to browse, delete, or export your saved entries.

---

## 🧪 Future Ideas

- 🌐 Add Anthropic, Mistral or Ollama support
- 📊 Data visualizations for output quality tracking
- 🧪 A/B testing mode for prompt variants
- 🔐 Authentication for multi-user use
- 🐳 Docker container for fast deployment

---

## 📤 Contributing

Contributions, bug reports, and ideas are very welcome!  
Please open an [issue](https://github.com/sadok-derouich/promptlab/issues) or submit a PR.

---

## 📜 License

MIT — feel free to use, modify, and share.

---

## 👤 Author

Crafted by a gynecologist who loves LLMs and clean code.  
Enjoy and prompt responsibly. ✨

---

## 🔗 Resources

- [OpenAI API Docs](https://platform.openai.com/docs)
- [DeepSeek API](https://platform.deepseek.com/)
- [Supabase (PostgreSQL Cloud)](https://supabase.com/)

