from flask import Flask
from pathlib import Path
import json
import psycopg2

app = Flask(__name__)

data_path = Path("/Users/nafrost/Documents/Workspace/ShapGraph/app/ShapGraph/static_data")
ERROR = "Error"


def get_postgres_connection(db="amazon"):
    con_args = 'dbname={}'
    con_args = con_args.format(db)
    return psycopg2.connect(con_args)


@app.route("/query/<string:query>/")
def execute_query(query):
    """
    Execute an SQL query and return a list of results.
    None will be returned in the case of error during the query execution.

    :param query: is an SQL query.
    :return: list the SQL output tuples.
    """

    if query is None:
        return {ERROR: "Query is empty"}

    print(query)

    con = None
    cur = None
    ans = {ERROR: "Error during query processing"}
    try:
        con = get_postgres_connection()
        cur = con.cursor()

        print("got cursor")

        cur.execute("SET search_path TO public, provsql")
        cur.execute(query)
        res = cur.fetchall()

        print("Got %d results" % len(res))

        ans = {
            "schema": [desc[0] for desc in cur.description],
            "outputs": res
        }

    finally:
        if cur is not None:
            cur.close()
        if con is not None:
            con.close()

    return ans

@app.route("/contributing_facts/<string:facts>/")
def get_contributing_facts(facts):
    """
    Given a set of output tuple ids returns information and Shapley value of contributing facts.

    :param output_tuples: list of output tuples ids
    :return: information and Shapley value of contributing facts.
    """

    # Return a static result for selection of output tuples
    # ['fa85ca4b-b2fc-52fd-93ae-0c35833b5c9f',
    # '8e3ff9a1-8614-58bc-b864-c09feaf198bb',
    # '9a0b8421-25bc-5529-8162-345a15035fda']
    if facts is None:
        return {ERROR: "Facts are empty"}

    facts = {f.strip(): [0] for f in facts.split(",")}

    if len(facts) == 0:
        return {ERROR: "Facts are empty"}

    # contribution = json.load(open(data_path/"contribution.json", "r"))

    return facts


@app.route("/get_graph/<string:output_tuple>/")
def get_graph(output_tuple):
    """
    Given id of a single output tuple return the graph of contributing facts.

    :param output_tuple: id of an output tuple.
    :return: Provenance graph of the selected output tuple. Nodes of input gates contains the fact information and Shapley value.
    """

    if output_tuple is None:
        return {ERROR: "Output tuple is missing"}

    # Return a static result for output tuple 'fa85ca4b-b2fc-52fd-93ae-0c35833b5c9f'

    graph = json.load(open(data_path/"graph.json", "r"))

    return graph


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
