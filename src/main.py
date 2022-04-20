from flask import Flask
from pathlib import Path
import json
import psycopg2

app = Flask(__name__)

data_path = Path("static_data")


def get_postgres_connection(db="postgres"):
    user = "postgres"
    pwd = "postgres"
    host = "localhost"
    port = "5432"

    url = 'postgresql+psycopg2://{}:{}@{}/{}?client_encoding=utf8'
    url = url.format(user, pwd, host, port, db)
    conn_args = 'dbname={} user={} password={} host={} port={}'
    conn_args = conn_args.format(db, user, pwd, host, port)
    return psycopg2.connect(conn_args)

@app.route("/")
def home():
    pass


@app.route("/query/<string:query>/")
def execute_query(query):
    """
    Execute an SQL query and return a list of results.
    None will be returned in the case of error during the query execution.

    :param query: is an SQL query.
    :return: list the SQL output tuples.
    """

    if query is None:
        return None

    return "Hello"


def get_contributing_facts(output_tuples):
    """
    Given a set of output tuple ids returns information and Shapley value of contributing facts.

    :param output_tuples: list of output tuples ids
    :return: information and Shapley value of contributing facts.
    """

    # Return a static result for selection of output tuples
    # ['fa85ca4b-b2fc-52fd-93ae-0c35833b5c9f',
    # '8e3ff9a1-8614-58bc-b864-c09feaf198bb',
    # '9a0b8421-25bc-5529-8162-345a15035fda']

    contribution = json.load(open(data_path/"contribution.json", "r"))

    return contribution


def get_graph(output_tuple):
    """
    Given id of a single output tuple return the graph of contributing facts.

    :param output_tuple: id of an output tuple.
    :return: Provenance graph of the selected output tuple. Nodes of input gates contains the fact information and Shapley value.
    """

    # Return a static result for output tuple 'fa85ca4b-b2fc-52fd-93ae-0c35833b5c9f'

    graph = json.load(open(data_path/"graph.json", "r"))

    return graph


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
