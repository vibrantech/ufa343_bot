# ufa343_bot — AI Translator Telegram Bot

An advanced, asynchronous Telegram AI translation bot powered by **Google Gemini AI** and built with the `python-telegram-bot` framework. This application automatically detects user source languages and handles high-fidelity linguistic translation workflows seamlessly.

---

## 🚀 Features
* **AI-Driven Detection:** Automatically determines the input language.
* **Smart Translation Default:** Converts any standard incoming text message into clear, natural English by default.
* **Custom Target Formats:** Adapts instantly when a user requests a specific target language (e.g., *"Translate this to Spanish: ..."*).
* **Robust Cloud Pipeline:** Optimized to run 24/7 as a background process on cloud environments like Render.

---

## 🏗️ Project Architecture Layout

```text
ufa343_bot/
│
├── bot.py           # Main bot application logic & Gemini client handling
├── requirements.txt # Production software dependencies
└── README.md        # Documentation and deployment configuration
