from deckgen.decks.base import DeckGen
from prompteng.prompts.parser import QAParser 
from prompteng.pipelines.qa_pipeline import QAToolKit
from dotenv import load_dotenv
import os
def main():
    """
    Main function to run the DeckGen application.
    """
    # Load environment variables from .env file
    load_dotenv()
    text = """ 
    Discover Azure Functions

    Azure Functions is a serverless solution that allows you to write less code, maintain less infrastructure, and save on costs. Instead of worrying about deploying 
    and maintaining servers, the cloud infrastructure provides all the up-to-date resources needed to keep your applications running.
    We often build systems to react to a series of critical events. Whether you're building a web API, responding to database changes,
    processing IoT data streams, or even managing message queues - every application needs a way to run some code as these events occur.

    Azure Functions supports triggers, which are ways to start execution of your code, and bindings, 
    which are ways to simplify coding for input and output data. There are other integration and automation
    services in Azure and they all can solve integration problems and automate business processes.
    They can all define input, actions, conditions, and output.

    Compare Azure Functions and Azure Logic Apps
    Both Functions and Logic Apps are Azure Services that enable serverless workloads. Azure Functions is a serverless compute service,
    whereas Azure Logic Apps is a serverless workflow integration platform. Both can create complex orchestrations. 
    An orchestration is a collection of functions or steps, called actions in Logic Apps, that are executed to accomplish a complex task.

    For Azure Functions, you develop orchestrations by writing code and using the Durable Functions extension. 
    For Logic Apps, you create orchestrations by using a GUI or editing configuration files.
    """

    qa_toolkit = QAToolKit(input_text=text)
    qa_list = qa_toolkit.generate_qa()
    for qa in qa_list:
        print(f"Question: {qa['question']}")
        print(f"Answer: {qa['answer']}")
        print("-" * 40)
    