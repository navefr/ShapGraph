from flask import Flask
from pathlib import Path
import json

app = Flask(__name__)

data_path = Path("static_data")

@app.route("/")
def home():
    pass


def execute_query(query):
    """
    Execute an SQL query and return a list of results.
    None will be returned in the case of error during the query execution.

    :param query: is an SQL query.
    :return: list the SQL output tuples.
    """

    # Return a static result for the query:
    # SELECT t.title
    # FROM aka_name AS an,
    #      char_name AS chn,
    #      cast_info AS ci,
    #      company_name AS cn,
    #      movie_companies AS mc,
    #      name AS n,
    #      role_type AS rt,
    #      title AS t
    # WHERE ci.note in ('(voice)',
    #                   '(voice: Japanese version)',
    #                   '(voice) (uncredited)',
    #                   '(voice: English version)')
    #   AND cn.country_code ='[us]'
    #   AND mc.note IS NOT NULL
    #   AND (mc.note like '%(USA)%'
    #        OR mc.note like '%(worldwide)%')
    #   AND n.gender ='f'
    #   AND n.name like '%Ang%'
    #   AND rt.role ='actress'
    #   AND t.production_year BETWEEN 2005 AND 2015
    #   AND ci.movie_id = t.id
    #   AND t.id = mc.movie_id
    #   AND ci.movie_id = mc.movie_id
    #   AND mc.company_id = cn.id
    #   AND ci.role_id = rt.id
    #   AND n.id = ci.person_id
    #   AND chn.id = ci.person_role_id
    #   AND an.person_id = n.id
    #   AND an.person_id = ci.person_id
    # GROUP BY t.title;

    results = json.load(open(data_path/"query_answers.json", "r"))
    return results


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

