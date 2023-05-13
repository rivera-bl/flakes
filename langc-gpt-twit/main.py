import fnmatch
import shutil
import os
import git
import re
from langchain.vectorstores import FAISS
from langchain.embeddings.openai import OpenAIEmbeddings
# Model and chain
from langchain.chat_models import ChatOpenAI
# Text splitters
from langchain.text_splitter import CharacterTextSplitter
from langchain.document_loaders import TextLoader
# The LangChain component we'll use to get the documents
from langchain.chains import RetrievalQA

openai_api_key = os.environ["OPENAI_API_KEY"]
# TODO fetch remote repositories
# TODO include the dir tree layout as text as part of the documents
location = input(
    "Enter the location of the files (local path or git repository): ")

# Check if input is a local path
if os.path.isdir(location):
    root_dir = location
    # continue with the rest of the code

# Check if input is a git repository
elif re.match(r"^(^https:\/\/.*\.git$|^git@.*:.*\.git$)", location):
    # Clone the git repository to a temporary directory
    tmp_dir = "/tmp/langc-gpt-repo"
    git.Repo.clone_from(location, tmp_dir)
    root_dir = tmp_dir

# Invalid input
else:
    print("Invalid input.")

# root_dir = '/home/wim/code/personal/flakes'
exclude = [
    "**/.git*",
    "**/.venv*",
    "**/.direnv"
]
# query = "Explain the langc-gpt-twit code. Use examples and show the command to run it locally with nix and python. Use markdown syntax. The code that you will provide is meant to be used as a README.md for a github repository."

llm = ChatOpenAI(model='gpt-3.5-turbo', openai_api_key=openai_api_key)

# -----------------
# Vectorstore dance
# -----------------
embeddings = OpenAIEmbeddings(
    disallowed_special=(), openai_api_key=openai_api_key)

docs = []

# Go through each folder
for dirpath, dirnames, filenames in os.walk(root_dir):

    # Go through each file
    for file in filenames:
        dir = os.path.join(dirpath, file)
        if any(fnmatch.fnmatch(dir, pattern) for pattern in exclude):
            continue
        try:
            # Load up the file as a doc and split
            loader = TextLoader(dir, encoding='utf-8')
            docs.extend(loader.load_and_split())
        except Exception as e:
            pass

print(f"{len(docs)} documents found.")
print("Embedding documents...")

# Embed and store them in a docstore. This will make an API call to OpenAI
docsearch = FAISS.from_documents(docs, embeddings)

print("Ready to search.")
# Get our retriever ready
qa = RetrievalQA.from_chain_type(
    llm=llm, chain_type="stuff", retriever=docsearch.as_retriever())

if 'query' not in locals() or not query:
    query = input("Enter your query: ")

print("Running query...")

output = qa.run(query)
print("\n" + output)

if 'tmp_dir' in locals():
    shutil.rmtree(tmp_dir)
