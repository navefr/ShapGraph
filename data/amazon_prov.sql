\c amazon

\set ECHO none
CREATE EXTENSION "uuid-ossp";
CREATE EXTENSION provsql;

SET search_path TO public, provsql;
SET provsql.where_provenance = on;

SELECT add_provenance('items');
SELECT add_provenance('also_view');
SELECT add_provenance('also_buy');
SELECT add_provenance('category');
SELECT add_provenance('feature');
SELECT add_provenance('description');
SELECT add_provenance('review');

