import subprocess
import requests
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains.llm import LLMChain
from dotenv import load_dotenv
import os
load_dotenv()

PROMETHEUS_URL = "http://localhost:9090/:9090/api/v1"



def pod_name():

    try:
        command = (
            "kubectl get pods -o jsonpath='{.items[5].metadata.name}' | awk '{gsub(/%/, \"\"); print}'"
        )
        # Execute the command in a shell
        pod_name = subprocess.check_output(command, shell=True, text=True).strip()
        return pod_name
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")
        return None
def get_logs(pod_name: str):

    logs = subprocess.check_output(["kubectl", "logs", pod_name, "-n", "default"]).decode("utf-8")
    return logs

def get_events():
    # Fetch events using kubectl
    events = subprocess.check_output(["kubectl", "get", "events", "-n", "default"]).decode("utf-8")
    return events


def get_metrics():
    query = 'sum(rate(container_cpu_usage_seconds_total[1m])) by (pod)'
    response = requests.get(f"{PROMETHEUS_URL}/query", params={"query": query})
    if response.status_code == 200:
        return response.json()

    return "Error fetching metrics"

def analyze_data(logs, metrics, events):

    llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    api_key=os.getenv("GENAI_API_KEY"),
    temperature=0.5

    )
    prompt = PromptTemplate(
            input_variables=["logs", "metrics", "events"],
            template=(
                "Analyze the following Kubernetes information:\n\n"
                "Logs:\n{logs}\n\n"
                "Metrics:\n{metrics}\n\n"
                "Events:\n{events}\n\n"
                "Identify anomalies and suggest corrective actions in concise and brief"
        )
    )

    chain = LLMChain(llm=llm, prompt=prompt)
    output = chain.invoke({'logs': logs, 'metrics': metrics, 'events': events})
    return output['text']


pod_name = pod_name()
logs = get_logs(pod_name)
events = get_events()
metrics = get_metrics()

analyse = analyze_data(logs, events, metrics)
print(analyse)



