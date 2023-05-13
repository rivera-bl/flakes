---

# LangC

 Python script that uses LangChain and OpenAI's GPT-3 to answer a question based on a set of documents. It's a powerful tool that can help you quickly find answers to complex questions.

## Overview

The `langc` code is a Python script that uses LangChain and OpenAI's GPT-3 to answer a question based on a set of documents. The script prompts the user to enter a question, and then uses LangChain and GPT-3 to find the best answer based on the set of documents and display the answer.

## Installation

In order to run the code locally, you will need to have Nix and Python 3 installed. Here are the steps to install and run the code:

1. Clone the repository to your local machine.
2. Navigate to the directory where the `default.nix` file is located.
3. Run the following command to enter a Nix shell:

   ```
   nix-shell
   ```

   This will install all dependencies specified in the `default.nix` file.

4. Once the shell is loaded, run the following command to activate the virtual environment:

   ```
   source .venv-langc/bin/activate
   ```

5. With the virtual environment activated, you can run the script with the following command:

   ```
   python main.py
   ```

   This will prompt you to enter a question. Once you've entered the question, the script will use LangChain and GPT-3 to find the best answer based on the set of documents and display the answer.

That's it! You should now be able to use LangC to answer questions based on a set of documents.