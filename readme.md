# 🔍 SEO Content Gap Analyser

The SEO Content Gap Analyser is a Python-based Streamlit web application that helps SEOs and content marketers identify missing content opportunities on a webpage. 

By combining live intent data from the **AlsoAsked API** with the analytical power of a **local AI model (Gemma4)** via Ollama, this tool automatically scrapes a target URL and evaluates exactly which user questions are currently answered and which are missing.

## ✨ Features
* **Live Question Extraction:** Pulls "People Also Ask" questions natively using the AlsoAsked API.
* **Automated Content Scraping:** Scrapes the target URL while bypassing basic bot-protection using custom headers.
* **Local AI Processing:** Uses Ollama and the `gemma4:e4b` model to analyse text locally, saving API costs.
* **Smart Deduplication:** Automatically flattens and deduplicates complex question trees.
* **One-Click Export:** Download a cleanly formatted CSV containing `Answered` and `Unanswered` questions for easy content briefs.

**Created by [Atkinson Smith Digital](https://atkinsonsmithdigital.com)**
---

## 🛠️ Prerequisites

Before you run this application, you must have the following installed on your machine:

1. **Python 3.8+**
2. **[Ollama](https://ollama.com/)** (Running locally)
3. An active **AlsoAsked API Key**

---

## 🚀 Installation & Setup

**1. Clone the repository**
Download or clone this repository to your local machine.

**2. Install Python Dependencies**
Open your terminal in the project folder and run:
```bash
pip install streamlit requests beautifulsoup4 pandas watchdog