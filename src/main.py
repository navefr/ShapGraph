from flask import Flask
from pathlib import Path
import psycopg2
import pandas as pd
import networkx as nx
import json
import subprocess
from logging.config import dictConfig
from circuit_shapley import CircuitShapley
from timeout import timeout as timeout_func
import copy


dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default'
    }},
    'root': {
        'level': 'DEBUG',
        'handlers': ['wsgi']
    }
})

app = Flask(__name__)

ERROR = "Error"

tables = ["items", "also_buy", "also_view", "category", "description", "feature", "review"]

path = Path("/opt/shapgraph")
provenance_path = path/"provenance"
provenance_path.mkdir(parents=True, exist_ok=True)


def close_con_and_cur(con, cur):
    if cur is not None:
        cur.close()
    if con is not None:
        con.close()


def get_postgres_connection(db="amazon"):
    con_args = 'dbname={}'
    con_args = con_args.format(db)
    return psycopg2.connect(con_args)


def get_connection_and_cursor(db="amazon"):
    con, cur = None, None
    try:
        con = get_postgres_connection(db)
        cur = con.cursor()
        cur.execute("SET search_path TO public, provsql")
    except Exception as e:
        close_con_and_cur(con, cur)
        raise e

    return con, cur


def fetch_facts_data(table_name):

    query = "select * from %s;" % table_name

    ans = None
    con, cur = None, None
    try:
        con, cur = get_connection_and_cursor()
        cur.execute(query)
        res = cur.fetchall()

        schema = [desc[0] for desc in cur.description]
        ans = {
            row[-1]: {
                "table_name": table_name,
                "data": {
                    col: val for col, val in zip(schema[:-1], row[:-1])
                }
            }
            for row in res
        }
    finally:
        close_con_and_cur(con, cur)

    return ans


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

    app.logger.debug("*** execute_query: processing \"%s\"" % query)

    ans = {ERROR: "Error during query processing"}
    con, cur = None, None
    try:
        con, cur = get_connection_and_cursor()

        app.logger.debug("*** execute_query: got cursor")

        cur.execute(query)
        res = cur.fetchall()

        app.logger.debug("*** execute_query: fetched %d results" % len(res))

        schema = [desc[0] for desc in cur.description]
        ans = {
            "schema": schema[:-1],
            "outputs": {x[-1]: x[:-1] for x in res}
        }

        for output_tuple, values in ans["outputs"].items():
            output_tuples_data[output_tuple] = {col: value for col, value in zip(ans["schema"], values)}

    except Exception as e:
        app.logger.error("*** execute_query: %s" % str(e))
    finally:
        close_con_and_cur(con, cur)

    return ans


def hash_dir_structure(provenance_hash):
    prefix = provenance_hash.split('-')[0]
    assert len(prefix) == 8
    structure = [prefix[2 * i: 2 * (i + 1)] for i in range(len(prefix) // 2)]
    structure.append(provenance_hash)
    return structure


def export_provenance(cur, provenance_hash):

    app.logger.debug("*** export_provenance: export provenance for \"%s\"" % provenance_hash)

    cur_path = provenance_path / ('/'.join(hash_dir_structure(provenance_hash)))
    if cur_path.exists():
        app.logger.debug("*** export_provenance: \"%s\" provenance already exist" % provenance_hash)
        return

    cur_path.mkdir(parents=True, exist_ok=True)

    cur.execute("SELECT * FROM sub_circuit_for_where('%s')" % provenance_hash)
    res = cur.fetchall()
    provenance = pd.DataFrame(res, columns=["f", "t", "gate_type", "table_name", "nb_columns", "infos", "tuple_no"])

    app.logger.debug("*** export_provenance: \"%s\" provenance contain %d gates" % (provenance_hash, provenance.shape[0]))

    G = nx.DiGraph()
    gates = {}

    for _, row in provenance.iterrows():
        if row.f not in gates:
            gates[row.f] = {"type": row["gate_type"]}
        if row["gate_type"] in ["times", "plus"]:
            G.add_edge(row.f, row.t)

    gates_order = list(nx.topological_sort(G))
    for gate_id, gate_hash in enumerate(gates_order):
        gates[gate_hash]["id"] = gate_id + 1

    app.logger.debug("*** export_provenance: traversed \"%s\" provenance" % provenance_hash)

    clauses = [[1]]
    for gate in gates_order:
        gate_id = gates[gate]["id"]
        if gates[gate]["type"] == "times":
            wires = G.neighbors(gate)
            cur_clause = [gate_id]
            for in_gate in wires:
                in_gate_id = gates[in_gate]["id"]
                clauses.append([-gate_id, in_gate_id])
                cur_clause.append(-in_gate_id)
            clauses.append(cur_clause)
        elif gates[gate]["type"] == "plus":
            wires = G.neighbors(gate)
            cur_clause = [-gate_id]
            for in_gate in wires:
                in_gate_id = gates[in_gate]["id"]
                clauses.append([gate_id, -in_gate_id])
                cur_clause.append(in_gate_id)
            clauses.append(cur_clause)

    provenance["f_id"] = provenance.f.apply(lambda gate: gates[gate]["id"])
    provenance.to_csv(cur_path / "provenance_as_a_table.csv")

    app.logger.debug("*** export_provenance: \"%s\" table was written to %s" % (provenance_hash, str(cur_path / "provenance_as_a_table.csv")))

    with open(cur_path / "circuit", "w") as f:
        f.write("p cnf %d %d\n" % (len(gates), len(clauses)))
        for clause in clauses:
            for x in clause:
                f.write("%d " % x)
            f.write("0\n")

    app.logger.debug("*** export_provenance: \"%s\" circuit was written to %s" % (provenance_hash, str(cur_path / "circuit")))

    with open(cur_path / ("gates.json"), 'w') as f:
        json.dump(gates, f, indent=4)

    app.logger.debug("*** export_provenance: \"%s\" gates were written to %s" % (provenance_hash, str(cur_path / "gates.json")))


def knowledge_compilation(provenance_hash, timeout=60):
    app.logger.debug("*** knowledge_compilation: starting compilation of \"%s\"" % provenance_hash)

    circuit_fname = provenance_path / ('/'.join(hash_dir_structure(provenance_hash))) / "circuit"
    circuit_nnf_fname = provenance_path / ('/'.join(hash_dir_structure(provenance_hash))) / "circuit.nnf"
    if not circuit_fname.exists():
        app.logger.error("*** knowledge_compilation: \"%s\" circuit is missing" % provenance_hash)
        return "Exception - circuit is missing"

    if circuit_nnf_fname.exists():
        app.logger.debug("*** knowledge_compilation: \"%s\" nnf already exist" % provenance_hash)
        return "Success"

    proc = None
    try:
        proc = subprocess.Popen(["c2d", '-in', circuit_fname, '-smooth'])
        outs, errs = proc.communicate(timeout=timeout)
        if not circuit_nnf_fname.exists():
            app.logger.debug("*** knowledge_compilation: \"%s\" compiled file is missing" % provenance_hash)
            return "Exception - file not created"
        app.logger.debug("*** knowledge_compilation: compiled \"%s\" successfully" % provenance_hash)
        return "Success"
    except subprocess.TimeoutExpired:
        app.logger.error("*** knowledge_compilation: \"%s\" compilation timeout" % provenance_hash)
        if proc is not None:
            proc.kill()
        return "Timeout"
    except Exception as e:
        if proc is not None:
            proc.kill()
        app.logger.error("*** knowledge_compilation: \"%s\" compilation failed %s" % (provenance_hash, str(e)))
        return str(type(e))


def calc_shapley_values(provenance_hash, timeout=60):
    app.logger.debug("*** calc_shapley_values: starting exact shapley computation for \"%s\"" % provenance_hash)

    shapley_fname = provenance_path / ('/'.join(hash_dir_structure(provenance_hash))) / "shapley_values.json"

    if shapley_fname.exists():
        app.logger.debug("*** calc_shapley_values: \"%s\" shapley values already exist" % provenance_hash)
        with open(shapley_fname, "r") as f:
            shapley_values = json.load(f)
        return shapley_values

    nnf_fname = provenance_path / ('/'.join(hash_dir_structure(provenance_hash))) / "circuit.nnf"
    gates_fname = provenance_path / ('/'.join(hash_dir_structure(provenance_hash))) / "gates.json"

    def calc(nnf_fname, gates):
        c_shapley = CircuitShapley(nnf_fname,
                                   [gate_info["id"] for gate, gate_info in gates.items() if gate_info["type"] != "input"])
        return c_shapley.shapley_values()

    calc_timeout = timeout_func(timeout=timeout)(calc)
    try:
        with open(gates_fname, "r") as f:
            gates = json.load(f)

        shapley_values = calc_timeout(nnf_fname, gates)

        gate_id2hash = {gate_info["id"]: gate for gate, gate_info in gates.items()}
        shapley_values = {gate_id2hash[k]: float(v) for k, v in shapley_values.items()}

        app.logger.debug("*** calc_shapley_values: \"%s\" shapley value computation completed successfully" % provenance_hash)

        with open(shapley_fname, 'w') as f:
            json.dump(shapley_values, f, indent=4)

    except Exception as e:
        app.logger.error("*** calc_shapley_values: \"%s\" shapley value computation failed %s" % (provenance_hash, str(e)))
        shapley_values = e

    return shapley_values


@app.route("/contributing_facts/<string:output_tuples>/")
def get_contributing_facts(output_tuples):
    """
    Given a set of output tuple ids returns information and Shapley value of contributing facts.

    :param output_tuples: list of output tuples ids
    :return: information and Shapley value of contributing facts.
    """

    if output_tuples is None:
        return {ERROR: "Output tuples are empty"}

    app.logger.debug("*** get_contributing_facts: got output tuples \"%s\"" % output_tuples)

    output_tuples = {f.strip(): [0] for f in output_tuples.split(",")}

    app.logger.debug("*** get_contributing_facts: parsed to %d tuples" % len(output_tuples))

    if len(output_tuples) == 0:
        return {ERROR: "Output tuples are empty"}

    ans = {ERROR: "Failed to obtain contributions"}

    con, cur = None, None
    try:
        con, cur = get_connection_and_cursor()

        app.logger.debug("*** get_contributing_facts: got cursor")

        ans = {
            "outputs": {},
            "facts": {}
        }

        output2fact_contribution = {}

        for output_tuple in output_tuples:

            if output_tuple not in output_tuples_data:
                app.logger.error("*** get_contributing_facts: output tuple \"%s\" is invalid" % output_tuple)
                return {ERROR: "Output tuple \"%s\" is invalid" % output_tuple}

            ans["outputs"][output_tuple] = output_tuples_data[output_tuple]

            if output_tuple not in facts_data:
                export_provenance(cur, output_tuple)
                knowledge_compilation(output_tuple)
                shapley_values = calc_shapley_values(output_tuple)
                # TODO - handle the case of an error during the computations
            else:
                # In case the output tuple is simply a fact from the db - it is the only contributor
                shapley_values = {output_tuple: 1.0}

            for fact in shapley_values:
                if fact not in ans["facts"]:
                    ans["facts"][fact] = facts_data[fact]

            output2fact_contribution[output_tuple] = shapley_values

        for output_tuple in output_tuples:
            for fact in ans["facts"]:
                if fact not in output2fact_contribution[output_tuple]:
                    output2fact_contribution[output_tuple][fact] = 0

        ans["output2fact_contribution"] = output2fact_contribution

        app.logger.debug("*** get_contributing_facts: provenance export completed")

    except Exception as e:
        app.logger.error("*** execute_query: %s" % str(e))
    finally:
        close_con_and_cur(con, cur)

    return ans


@app.route("/graph/<string:output_tuple>/")
def get_graph(output_tuple):
    """
    Given id of a single output tuple return the graph of contributing facts.

    :param output_tuple: id of an output tuple.
    :return: Provenance graph of the selected output tuple. Nodes of input gates contains the fact information and Shapley value.
    """

    if output_tuple is None:
        return {ERROR: "Output tuple is missing"}

    app.logger.debug("*** graph: got output tuple \"%s\"" % output_tuple)

    ans = {ERROR: "Failed to generate graph"}

    con, cur = None, None
    try:
        con, cur = get_connection_and_cursor()

        app.logger.debug("*** graph: got cursor")

        ans = {}

        if output_tuple not in output_tuples_data:
            app.logger.error("*** graph: output tuple \"%s\" is invalid" % output_tuple)
            return {ERROR: "Output tuple \"%s\" is invalid" % output_tuple}

        if output_tuple not in facts_data:
            export_provenance(cur, output_tuple)
            knowledge_compilation(output_tuple)
            shapley_values = calc_shapley_values(output_tuple)
            # TODO - handle the case of an error during the computations

            provenance_table_path = provenance_path / ('/'.join(hash_dir_structure(output_tuple))) / "provenance_as_a_table.csv"
            if not provenance_table_path.exists():
                app.logger.error("*** graph: \"%s\" provenance table is missing" % output_tuple)
                return {ERROR: "Provenance table is missing"}
            df = pd.read_csv(provenance_table_path)
            
            # TODO - complete graph creation


        else:
            # In case the output tuple is simply a fact from the db - it is the only contributor
            ans = {output_tuple: copy.deepcopy(facts_data[output_tuple])}
            ans[output_tuple]["type"] = "input"
            ans[output_tuple]["in_edges"] = []
            ans[output_tuple]["shapley_value"] = 1.0

        app.logger.debug("*** graph: graph creation completed")

    except Exception as e:
        app.logger.error("*** graph: %s" % str(e))
    finally:
        close_con_and_cur(con, cur)

    return ans


if __name__ == '__main__':
    app.logger.info(" =====  Load facts provenance mapping ...")
    facts_data = {}
    for table_name in tables:
        facts_data.update(fetch_facts_data(table_name))
    app.logger.info(" =====  Loaded %d facts" % len(facts_data))
    output_tuples_data = {}

    app.run(host='0.0.0.0', port=80, debug=True)
