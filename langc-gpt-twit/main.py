import os
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
root_dir = '/home/wim/code/personal/flakes/fws'
query = "Explain what is the goal of this code"

llm = ChatOpenAI(model='gpt-3.5-turbo', openai_api_key=openai_api_key)

# -----------------
# Vectorstore dance
# -----------------
embeddings = OpenAIEmbeddings(disallowed_special=(), openai_api_key=openai_api_key)

docs = []

# Go through each folder
# TODO skip .git folder
for dirpath, dirnames, filenames in os.walk(root_dir):

    if '.git' in dirnames:
        dirnames.remove('.git')

    # Go through each file
    for file in filenames:
        try:
            # Load up the file as a doc and split
            loader = TextLoader(os.path.join(dirpath, file), encoding='utf-8')
            docs.extend(loader.load_and_split())
        except Exception as e:
            pass

# print (f"You have {len(docs)} documents\n")
# print ("------ Start Document ------")
# print (docs[0].page_content[:300])

# Embed and store them in a docstore. This will make an API call to OpenAI
docsearch = FAISS.from_documents(docs, embeddings)

# Get our retriever ready
qa = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=docsearch.as_retriever())

output = qa.run(query)
print (output)