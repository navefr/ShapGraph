FROM debian:buster
LABEL maintainer navefrost@mail.tau.ac.il

# Copy the source into /opt/shapgraph
COPY . /opt/shapgraph
WORKDIR /opt/shapgraph

USER root
RUN chmod -R 777 /opt/shapgraph/


# needed to build provsql the tools + libc6-i386 for running c2d
RUN apt-get update &&\
    apt-get -y install git build-essential curl\
               libc6-i386 unzip mercurial libgmp-dev libboost-dev

# Specify which version we are building against
ARG PSQL_VERSION=11
ENV PSQL_VERSION=$PSQL_VERSION

RUN apt-get update &&\
    apt-get -y install zlib1g-dev postgresql-${PSQL_VERSION} postgresql-server-dev-${PSQL_VERSION}

# Ensure a sane environment
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8 DEBIAN_FRONTEND=noninteractive

# Ensure that bash is the default shell
ENV SHELL=/bin/bash
        
# Install sudo, vim and pip3
RUN apt-get update &&\
    apt-get -y install sudo &&\
    apt-get -y install vim &&\
    apt-get -y install python3-pip

# Install libs required for scipy
RUN apt-get update &&\ 
    apt-get -y install --no-install-recommends gfortran libopenblas-dev liblapack-dev &&\
    rm -rf /var/lib/apt/lists/*

# Install python requierments
RUN yes | pip3 install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org numpy &&\
    yes | pip3 install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org scipy &&\
    yes | pip3 install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org psycopg2 &&\
    yes | pip3 install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org networkx &&\
    yes | pip3 install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org pandas &&\
    yes | pip3 install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org pathlib &&\
    yes | pip3 install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org tqdm &&\
    yes | pip3 install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org flask


    
############################## GETTING ADD-ON TOOLS ##############################   

RUN mkdir /tmp/tools/

# TOOL c2d
RUN curl 'http://reasoning.cs.ucla.edu/c2d/fetchme.php' \
         -H 'Content-Type: application/x-www-form-urlencoded'\
         --data 'os=Linux+i386&type=&s=&n=Pierre+Senellart+DOCKER&e=pierre@senellart.com&o=ENS'\
         -o /tmp/c2d.zip &&\
         unzip /tmp/c2d.zip -d /tmp/ &&\
         rm /tmp/c2d.zip &&\
         mv /tmp/c2d_linux /tmp/tools/c2d &&\
         chmod a+x /tmp/tools/c2d


# TOOL d4
RUN cd /tmp/ &&\
    git config --global http.sslverify false &&\
    git clone https://github.com/crillab/d4.git &&\
    cd d4 &&\
    make &&\
    mv d4 /tmp/tools

    
# mv the additional tools
RUN bash -c "mv /tmp/tools/* /usr/local/bin"

##############################   GETTING  PROVSQL  ##############################   

# Provsql will be built & run as user postgres
RUN cd /opt &&\
    git config --global http.sslverify false &&\
    git clone https://github.com/PierreSenellart/provsql.git &&\
    cd /opt/provsql
    

RUN chown -R postgres:postgres /opt/provsql
USER postgres

# Building
RUN cd /opt/provsql &&\
    make

# install provsql
USER root
RUN echo "shared_preload_libraries = 'provsql'" >> /etc/postgresql/${PSQL_VERSION}/main/postgresql.conf
RUN echo "local all all trust" > /etc/postgresql/${PSQL_VERSION}/main/pg_hba.conf  

RUN cd /opt/provsql &&\
    make install

USER postgres
#create a db test
RUN /etc/init.d/postgresql start &&\
    createuser -s test &&\
    createdb test &&\
    psql -f /opt/provsql/test/sql/setup.sql test test  &&\
    psql -f /opt/provsql/test/sql/add_provenance.sql test test &&\
    psql -f /opt/provsql/test/sql/formula.sql test test  &&\
    psql -f /opt/provsql/test/sql/security.sql test test &&\
    psql -c "ALTER ROLE test SET search_path TO public, provsql";     


############################## CREATE AMAZON DB  ##############################

EXPOSE 5432
EXPOSE 80

USER postgres

CMD ["/opt/shapgraph/docker/start.sh" ]