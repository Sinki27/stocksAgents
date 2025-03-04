#IMPORT DA LIBS
import json
import os
from datetime import datetime

import yfinance as yf # type: ignore

from crewai import Agent, Task, Crew, Process # type: ignore

from langchain.tools import Tool # type: ignore
from langchain_openai import ChatOpenAI # type: ignore
from langchain_community.tools import DuckDuckGoSearchResults # type: ignore

import streamlit as st

# CRIANDO YAHOO FIANCE TOOL
def fetch_stock_price(ticket):
    stock = yf.download(ticket, start="2023-08-08", end="2024-08-08")
    return stock

yahoo_finance_tool = Tool(
    name = "Yahoo Finance Tool",
    description = "Fetches stock prices for {ticket} from the alst year about a specific stock from Yahoo Finance API",
    func= lambda ticket: fetch_stock_price(ticket)
)


# In[ ]:


# IMPORTANDO OPENAI LLM - GPT
#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
os.environ['OPENAI_API_KEY'] = st.secrets['OPENAI_API_KEY']
llm = ChatOpenAI(model="gpt-3.5-turbo")


# In[ ]:


stockPriceAnalyst = Agent(
    role = "Senior stock price Analyst",
    goal = "Find the {ticket} stock price and analyses trends",
    backstory = """ You're a highly experienced in analyzing the price of an specific stock and make predictions about its future price. """,
    verbose = True,
    llm= llm,
    max_iter = 5,
    memory = True,
    tools = [yahoo_finance_tool],
    allow_delegation = False
)


# In[ ]:


getStockPrice = Task(
    description = "Analyze the stock {ticket} price history and create a trend analyses of up, dowm or sideways",
    expected_output = """Specifiy the curretn trend stock price - up, down or sideways.
     eg. stock='APPL, price UP' 
    """,
    agent= stockPriceAnalyst
)


# In[ ]:


# IMPORTANT A TOOL DE SEARCH
search_tool = DuckDuckGoSearchResults(backend='news', num_results=10)


# In[ ]:


newsAnalyst = Agent(
    role = "Stock News Analyst",
    goal = """Create a short summary of the market news related to the stock {ticket} company. Specify the current trend - up, down or sideway with the news context. For each resquest stock asset, specify a numbet between 0 and 100, where 0 is extreme fear and 100 is extreme greeed.""",
    backstory = """ You're highly experienced in analyzing the market trends and news and have tracked assest for more then 10 tears.
    
    You're also master level analyts in the tradicional markets and have deep undersatnding of human psychology.

    You undersatnd news, theirs tittles and information, but you look at those with a helth dose of skepticism.
    You consider also the source of the news articles.
    """,
    verbose = True,
    llm= llm,
    max_iter = 5,
    memory = True,
    tools = [search_tool],
    allow_delegation = False
)


# In[ ]:


get_news = Task(
    description = f"""Take the stock and always include BTC to it (if not request).
    Use the search tool to search each one individually.

    The current date is {datetime.now()}.

    Compose the results into a helpfull report""",
    expected_output = """A summary of the overeal market and one sentence summary for each request asset.
    include a fear/greed score for each asset based on the news. Use format:
    <STOCK ASSET>
    <SUMMARY BASED ON NEWS>
    <TREND PREDICTION>
    <FEAR/GREED SCORE> 
""",
    agent= newsAnalyst
)


# In[ ]:


stockAnalystWrite = Agent(
    role = "Senior Stock Analyts Write",
    goal = """Analyze the trends price and news and write an insighfull compelling and informative 3 paragraph long newsletter based on the stock report and price trend """,
    backstory = """You're widely accepted as the best stock analyst in the market. You understand complex concepts and create compelling stories and narratives that resonate with wider audiences.

    You understand macro factors and combine multiple theories - eg. cycle theory and fundamental analyses. 
    You're able to hold multiple opnions when analyzing anything.
""",
    verbose = True,
    llm= llm,
    max_iter = 5,
    memory = True,
    allow_delegation = True
)

writeAnalyses = Task(
    description = """Use the stock price trend and the stock news repot to create an analyses and write the newsletter about the {ticket} company taht is brief highlights the most important points.
    Focus on the stock price trend, news and fear/greed score. What are the near future considerations?
    Include the previous analyses of stock trend and news summary.    
""",
    expected_output = """An eloquent 3 paragraphs newsletter formated as markdown in an easy readable manner. It should contain:

    - 3 bullets executive summary
    - Introduction - set the overall picture and spike up the interest
    - main part provides the meat of the analysis including the news summary and fead/greed scores
    - summary - key facts and concrete future trend prediction - upm down or sideways.
""",
    agent = stockAnalystWrite,
    context = [getStockPrice, get_news]
)

crew = Crew(
    agents= [stockPriceAnalyst, newsAnalyst, stockAnalystWrite],
    tasks= [getStockPrice, get_news, writeAnalyses],
    verbose = 2,
    process= Process.hierarchical,
    full_output= True,
    share_crew= False,
    manager_llm= llm,
    max_iter= 15
)


# results= crew.kickoff(inputs={'ticket': 'AAPL'})

with st.sidebar:
    st.header('Enter the Stock to Research')

    with st.form(key='research_form'):
        topic = st.text_input("Select the ticket")
        submit_buttton = st.form_submit_button(label = "Run Research")

if submit_buttton:
    if not topic:
        st.error("Please fill the ticket field")
    else:
        results = crew.kickoff(inputs={'ticket': topic})

        st.subheader("Results of your reseach:")
        st.write(results['final_output']
)