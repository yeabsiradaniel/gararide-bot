"""Entry point for Hugging Face Spaces.

Spaces with the Gradio SDK simply run `python app.py` on the free CPU and
expect something to listen on port 7860 — the bot's built-in web server
(the mini app) satisfies that, so no Docker needed.
"""
import os

os.environ.setdefault("PORT", "7860")

from bot import main

if __name__ == "__main__":
    main()
