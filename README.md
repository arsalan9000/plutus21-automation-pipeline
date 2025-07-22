# AI-Powered Opportunity Pipeline for Plutus21

This project is a fully automated, end-to-end pipeline designed to capture, analyze, prioritize, and act on new partnership or investment opportunities. It was built as a demonstration of the core skills required for the Automation Engineer role at Plutus21 Partners.

## ✨ Live Demo

You can test the system live yourself!

1.  **[➡️ Fill out the Google Form here](https://forms.gle/i5uyRYXsaLKi1gUn9)** to submit a new opportunity.
2.  If you describe a "B2B SaaS company in Pakistan," you will trigger a high-priority alert in my test Slack channel.
3.  The results are processed and displayed in near real-time on the public results sheet. **[➡️ View the Results Sheet here](https://docs.google.com/spreadsheets/d/18kzW-tW6ClGD1-oS2px6kYfjOE57BmCLo31aabfRn6c/edit?usp=sharing)**

## 🚀 Key Features

*   **End-to-End Automation:** A zero-touch workflow from data submission to team notification and visual dashboarding.
*   **AI-Powered Analysis:** Leverages Google's Gemini AI to perform NLP tasks, including summarization and strategic alignment scoring based on a defined investment thesis.
*   **Multi-Platform Integration:** Seamlessly connects Google Forms, Google Sheets, a SQL database, and Slack using Python and various APIs.
*   **Automated Visual Dashboards:** Uses Google Apps Script for conditional formatting, automatically color-coding new leads by priority in the spreadsheet.
*   **Scalable Architecture:** Built with a clean, modular structure that can be easily adapted for different portfolio companies or business needs.

## ⚙️ Architecture

The automation follows this data flow:

`Google Form` -> `Google Sheet` -> `Python Script`
1.  **Fetch:** Scans the Sheet for unprocessed rows.
2.  **Analyze:** Sends description to Google Gemini AI for analysis & scoring.
3.  **Store:** Logs the opportunity and AI analysis in a SQLite database.
4.  **Alert:** If the score is high, sends a detailed notification to Slack.
5.  **Update:** Writes the status and AI results back to the Google Sheet.
6.  **Visualize:** A Google Apps Script trigger (`onEdit`) automatically color-codes the new row based on its priority score.

## 🛠️ Tech Stack

-   **Backend & Orchestration:** Python
-   **Data & Input:** Google Forms, Google Sheets
-   **Database:** SQLite
-   **AI/NLP:** Google Gemini API
-   **Notifications:** Slack API (Incoming Webhooks)
-   **Dashboarding:** Google Apps Script


## 🔧 How to Run Locally

1.  Clone the repository:
    ```bash
    git clone https://github.com/YourUsername/plutus21-automation-pipeline.git
    cd plutus21-automation-pipeline
    ```
2.  Create a virtual environment and install dependencies:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```
3.  Create a `.env` file and populate it with your own API keys (see `.env.example` if provided).
4.  Set up your own Google Cloud Service Account, Google Sheet, and Slack Webhook.
5.  Run the database setup script once:
    ```bash
    python setup_database.py
    ```
6.  Execute the main pipeline:
    ```bash
    python main.py
    ```
