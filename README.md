# ShapGraph

## SetUp

#### lets say hat `github_repos` is where al the repos are.

#### - Get inside the main folder:
    cd ~/github_repos/ShapGraph/

#### - Run ShapGraph:
    docker-compose up -d --build

#### - Clone Retool on-premise:
    cd ~/github_repos/
    git clone https://github.com/tryretool/retool-onpremise.git
    cd ~/github_repos/retool-onpremise
    ./install.sh

#### - Open retool-onpremise `docker.env` file for editing:
    nano docker.env

#### Change this fields inside `docker.env` To:
    ## License key
    LICENSE_KEY=SSOP_554975be-39c4-4b2e-8373-1a8168f2e6a0

    # Uncomment this line if HTTPS is not set up
    COOKIE_INSECURE=true

To save press control+x -> y -> enter :)

#### - Run Retool:
    docker-compose up -d --build

#### - Upload the ShapGraph front from ` ~/github_repos/ShapGraph/retool/ShapGraph.json` (https://docs.retool.com/docs/app-management#exporting-retool-apps)