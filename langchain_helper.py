from langchain.document_loaders import YoutubeLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.prompts.chat import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)
from langchain.chains import LLMChain
from langchain.vectorstores import FAISS
from dotenv import load_dotenv, find_dotenv
import os

load_dotenv(find_dotenv())
os.environ['OPENAI_API_KEY'] =  os.environ.get("OPEN_AI")
embeddings = OpenAIEmbeddings()

video_url = "https://www.youtube.com/watch?v=lG7Uxts9SXs&ab_channel=freeCodeCamp.org"

def create_vector_db_from_youtube_url(video_url):
    loader = YoutubeLoader.from_youtube_url(video_url)
    transcript = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    docs = text_splitter.split_documents(transcript)

    db = FAISS.from_documents(docs, embeddings)
    return db

def get_response_from_query(db, query, k=4):
    '''
        textdavinci can handle 4097 tokens
        query = question
        k will pass 4 documents because each document has 1000 tokens
    '''
    docs = db.similarity_search(query, k)
    docs_page_content = " ".join([d.page_content for d in docs])
    llm = ChatOpenAI(openai_api_key=os.environ.get("OPEN_AI"), 
                     model_name="gpt-3.5-turbo-1106", 
                     temperature=0.6, 
                     max_tokens=512)
    template = (
        """You are a helpful assistant that that can answer questions about youtube videos 
        based on the video's transcript.
        
        Answer the following question: {question}
        By searching the following video transcript: {docs}
        
        Only use the factual information from the transcript to answer the question.
        
        If you feel like you don't have enough information to answer the question, say "I don't know".
        
        Your answers should be verbose and detailed.
        """
        )
    system_message_prompt = SystemMessagePromptTemplate.from_template(template)
    human_template = "{docs}"
    human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)
    chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt, human_message_prompt])

    chain = LLMChain(llm=llm, prompt=chat_prompt)
    response = chain.run(question=query, docs=docs_page_content)
    response = response.replace("/n", "")
    return response


create_vector_db_from_youtube_url(video_url)
