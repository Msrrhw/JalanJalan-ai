
# JalanJalan.AI

JalanJalan.AI is a smart chatbot that generates a personalized, day-by-day travel itinerary complete with images, ratings, and accommodation suggestions.

## Setup

1.  **Create and activate a virtual environment:**
    ```bash
    # Create the environment
    python -m venv venv
    
    # Activate on Windows
    venv\Scripts\activate
    
    # Activate on macOS/Linux
    source venv/bin/activate
    ```

2.  **Install the required packages:**
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

This project requires two API keys to function correctly.

1.  **Get your Gemini API Key:**
    -   Go to [Google AI Studio](https://aistudio.google.com/).
    -   Click on "Get API key" and create a new API key.

2.  **Set up your `.env` file:**
    -   Open the `.env` file in the project directory.
    -   Replace the placeholder values with the API keys you obtained.
    ```
    GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
    ```

## How to Run

1.  **Make sure your virtual environment is activated.**

2.  **Run the application from your terminal:**
    ```bash
    python app.py
    ```

3.  **Open your web browser and go to `http://127.0.0.1:5000`**

4.  **Fill in your travel preferences and click "Create My Itinerary".**
