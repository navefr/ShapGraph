#!/bin/bash

echo " =====  Starting Postgres ... "
/etc/init.d/postgresql start
echo ""

psql -U postgres -f /opt/shapgraph/data/create_db/amazon_items.sql
psql -U postgres -f /opt/shapgraph/data/create_db/amazon_also_view.sql
psql -U postgres -f /opt/shapgraph/data/create_db/amazon_also_buy.sql
psql -U postgres -f /opt/shapgraph/data/create_db/amazon_category.sql
psql -U postgres -f /opt/shapgraph/data/create_db/amazon_feature.sql
psql -U postgres -f /opt/shapgraph/data/create_db/amazon_description.sql
psql -U postgres -f /opt/shapgraph/data/create_db/amazon_review.sql
psql -U postgres -f /opt/shapgraph/data/amazon_prov.sql

echo " =====  Created amazon database ... "

python3 /opt/shapgraph/src/main.py