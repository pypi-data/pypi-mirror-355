
# 🤖 gemini_helper

**Use Gemini API with OpenAI Agent SDK easily!**  
This package allows students and developers to use free Gemini models (like `gemini-2.0-flash`) with the powerful [OpenAI Agent SDK](https://github.com/openai/openai-agents).

---

## 🚀 Installation

Using [uv](https://github.com/astral-sh/uv) (recommended):

```bash
uv add gemini_helper
```

Or via pip:

```bash
pip install gemini_helper
```

---

## ⚙️ Environment Setup

Create a `.env` file in your project root and add your Gemini API key:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

> 📌 You can get your key from [Google AI Studio](https://makersuite.google.com/app/apikey)

---

## 💡 How to Use

### ✅ Default (uses `gemini-2.0-flash`)

```python
from gemini_helper.core import get_gemini_model

model = get_gemini_model()
```

### ⚡ Custom model (like `gemini-1.0-pro`)

```python
model = get_gemini_model("gemini-1.0-pro")
```

You can now use this `model` inside your OpenAI Agent setup.

---

## 📦 Features

- 🔐 Secure API key handling via `.env`
- 🔄 Compatible with OpenAI Agent SDK
- 💸 No need for OpenAI's paid API – fully free using Gemini
- ⚙️ Optional model switching (e.g. `gemini-1.0-pro`, `gemini-2.0-pro`)
- 🧩 Easy to integrate into agent-based workflows

---

## 🛠 Dependencies

This package depends on:

- `openai-agent-sdk`
- `python-dotenv`

These are automatically installed with the package.

---

## 🧑‍💻 Author

Made with ❤️ by **Huriya Syed**  
Empowering students to build free agents using Gemini + OpenAI SDK.

---

## 📬 Contact / Support

Feel free to open an issue or connect with me on [LinkedIn](https://www.linkedin.com/in/huriya-syed-598371281/)  
Or email me at: **huriyasyed462@gmail.com**
