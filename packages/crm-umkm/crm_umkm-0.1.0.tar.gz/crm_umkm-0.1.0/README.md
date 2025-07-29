# UMKM CRM (MCP Server)

A lightweight [MCP server](https://github.com/multiprompt/mcp) for managing **small business (UMKM)** customer relationships, product sales, and order tracking using SQLite.

This server is designed for **micro and small enterprises (UMKM)** — from warung kopi to online shops — that need simple CRM capabilities, including product tracking, customer records, WhatsApp promotions, and more.

---

## ✨ Features

* 💾 Record customer orders and interactions
* 📦 Manage product inventory and sales
* 🔔 Notify when stock is low
* 📈 View top-selling products and loyal customers
* 📄 Export weekly activity to CSV
* 📲 Send WhatsApp promotions (via external API)

---

## 📦 Installation

Install from PyPI:

```bash
pip install crm-umkm
```

---

## 🚀 Usage

You can run the server using:

```bash
uvx crm-umkm
```

Or configure it in a client like [Cursor](https://cursor.so) or any MCP-compatible app:

```jsonc
{
  "mcpServers": {
    "crm-umkm": {
      "command": "uvx",
      "args": ["crm-umkm"],
      "env": {
        "DB_PATH": "/absolute/path/to/crm.db",
        "WHATSAPP_API_URL": "https://your-api.com/send",
        "WHATSAPP_API_TOKEN": "your-api-token"
      }
    }
  }
}
```

---

## 📁 Environment Variables

| Variable             | Description                                     | Default                         |
| -------------------- | ----------------------------------------------- | ------------------------------- |
| `DB_PATH`            | Path to SQLite database file                    | `crm_umkm.db`                   |
| `WHATSAPP_API_URL`   | Base URL for sending WhatsApp messages          | `https://api.whatsapp.com/send` |
| `WHATSAPP_API_TOKEN` | Token to authenticate with WhatsApp API service | *(empty)*                       |

The database will be initialized automatically on first run.

---

## 🧠 Prompt Behavior

This MCP server is specifically scoped for **UMKM CRM tasks**. The underlying LLM is guided to:

✅ Use these tools when:

* The user wants to record orders, view product stats, monitor stock, or export activity reports
* Managing small business customers and interactions
* Sending promotions via WhatsApp

🚫 Avoid using for:

* Enterprise-level CRM needs
* Marketing campaign automation at scale
* Large-scale ERP workflows

---

## 📂 Project Structure

```
crm-umkm/
└── src/
    └── crm_umkm/
        ├── __init__.py
        ├── server.py
        └── test.py
```

---

## 📝 License

ABRMS License
