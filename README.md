# GPTProfessor

An LLM-powered study application that reads your course notes and provides assistance with Q&A, chat, and quizzing.

## Installation

Get an OpenAI API token:
```
https://openai.com/blog/openai-api
```
Clone the repository: 
```
https://github.com/Plebtato/GPTProfessor.git
```
Install the dependencies (venv recommended):
```
pip install -r requirements.txt
```
Run the app with Streamlit:
```
streamlit run GPTProfessor/app.py
```
Once the application is running, you can access it through the link provided by Streamlit. 

## Features

Document Sync: Upload your course materials and textbooks. These will be saved and can be automatically updated when your files change. Currently supports PDF, Word, CSV, and plain text documents. Google Drive and code comprehension features are on the way!

Q&A: Use this tab to ask questions and get answers related to your course materials with high accuracy.

Chat: Engage in a chat discussions with ChatGPT integrated with accurate knowledge from your courses.

Quiz: Test your knowledge with exam questions and solutions generated from your notes and textbooks. 
