# GPTProfessor

An LLM-powered study application that reads your course notes and provides assistance with Q&A, chat, and quizzing. Built with Langchain and Streamlit.

## Installation

Get an OpenAI API token:
```
https://openai.com/blog/openai-api
```
Clone the repository: 
```
https://github.com/Plebtato/GPTProfessor.git
```
Install the dependencies. It is recommended to use a virtual environment:
```
pip install -r requirements.txt
```
Run the app with Streamlit:
```
streamlit run GPTProfessor/app.py
```
Once the application is running, you can access it through the link provided by Streamlit. You can add your token manually in your sidebar or through your environment variables (preferred!).

## Features

**Document Sync:** Upload your course materials and textbooks. These will be saved into collections for easy management and can be automatically updated when your files change. Currently supports PDF, Word, CSV, and plain text documents. Google Drive and code comprehension features are on the way!

**Q&A:** Ask questions and get answers related to your course materials with high accuracy.

**Chat:** Engage in a chat discussions with ChatGPT integrated with accurate knowledge from your courses.

**Quiz:** Test your knowledge with exam questions and solutions generated from your notes and textbooks. 

**Model Selection:** There are options to run OpenAI's DaVinci, GPT-3.5, and GPT-4 models with custom prompts tuned for each.


This project integrates Langchain's Document QA and chat pipelines, as shown below.

![image](https://github.com/Plebtato/GPTProfessor/assets/19521127/eea0a4fc-73d1-4883-8cbe-64ff631342cd)
![image](https://github.com/Plebtato/GPTProfessor/assets/19521127/f5c4c437-2ce3-47ac-b051-d9fca4b1a260)
[Diagrams sourced from Langchain](https://python.langchain.com/docs/get_started/introduction)

## Interface
<img width="1280" alt="image" src="https://github.com/Plebtato/GPTProfessor/assets/19521127/53d38173-3b09-439e-a06b-899cc92881c4">
