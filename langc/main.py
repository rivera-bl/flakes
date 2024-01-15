from langchain.chains import RetrievalQA
from langchain.document_loaders import TextLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.chat_models import ChatOpenAI
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS
import git
import shutil
import re
import os
import fnmatch

# TODO include the filenames in a document
# TODO 
openai_api_key = os.environ["OPENAI_API_KEY"]
exclude = [
    "**/.git*",
    "**/.venv*",
    "**/.direnv",
    "**/__pycache__"
]


def get_location():
    location = input(
        "Enter the location of the files (local path or git repository): ")
    if os.path.isdir(location):
        return location
    elif re.match(r"^(^https:\/\/.*\.git$|^ssh://git@.*:.*\.git$)", location):
        tmp_dir = "/tmp/langc-gpt-repo"
        git.Repo.clone_from(location, tmp_dir)
        return tmp_dir
    else:
        print("Invalid input.")
        return None


def get_documents(root_dir):
    docs = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for file in filenames:
            dir = os.path.join(dirpath, file)
            if any(fnmatch.fnmatch(dir, pattern) for pattern in exclude):
                continue
            try:
                loader = TextLoader(dir, encoding='utf-8')
                docs.extend(loader.load_and_split())
            except Exception as e:
                pass
    return docs


def embed_documents(docs):
    embeddings = OpenAIEmbeddings(
        disallowed_special=(), openai_api_key=openai_api_key)
    docsearch = FAISS.from_documents(docs, embeddings)
    return docsearch


def run_query(query, qa):
    output = qa.run(query)
    print("\n" + output + "\n")


def main():
    root_dir = get_location()
    if not root_dir:
        return
    docs = get_documents(root_dir)
    print(f"{len(docs)} documents found.")
    print("Embedding documents...")
    docsearch = embed_documents(docs)
    print("Ready to search.")
    llm = ChatOpenAI(model='gpt-3.5-turbo', openai_api_key=openai_api_key)
    qa = RetrievalQA.from_chain_type(
        llm=llm, chain_type="stuff", retriever=docsearch.as_retriever())
    while True:
        query = input("Enter your query (or 'exit' to quit): ")
        if query.lower() == 'exit':
            if os.path.isdir(root_dir):
                shutil.rmtree(root_dir)
            break
        run_query(query, qa)
    if os.path.isdir(root_dir):
        shutil.rmtree(root_dir)


main()
