# ShapGraph

## SetUp

#### lets say hat `github_repos` is where al the repos are.

### ShapGraph Setup:

#### - Get inside the main folder:
    cd ~/github_repos/ShapGraph/

#### - Run ShapGraph:
    docker-compose up -d --build

### ShapGraph host is on http://localhost:3001/

#### - Check if ShapGraph is up and running: http://localhost:3001/health

### Retool Setup:
Retool self-hosting setup documentation can be found [here](https://docs.retool.com/docs/self-hosted)

#### - Clone Retool on-premise:
    cd ~/github_repos/
    git clone https://github.com/tryretool/retool-onpremise.git
    cd ~/github_repos/retool-onpremise
    ./install.sh

#### - Open retool-onpremise `Dockerfile` for editing:
    nano Dockerfile

change "X.Y.Z" to "latest"

#### - Get Retool on-premise key [here](https://my.retool.com/)

#### - Open retool-onpremise `docker.env` file for editing:
    nano docker.env

#### - Write the licanse key you grot from retool inside `LICENSE_KEY`:

#### Change this fields inside `docker.env` To:
    ## License key
    LICENSE_KEY=<your-retool-on-premise-license-key>

    # Uncomment this line if HTTPS is not set up
    COOKIE_INSECURE=true

To save press control+x -> y -> enter :)

#### - Run Retool:
    docker-compose up -d --build

### Retool host is on http://localhost:3000/

#### - Upload the ShapGraph front from ` ~/github_repos/ShapGraph/retool/ShapGraph.json` [(documentation here)](https://docs.retool.com/docs/app-management#exporting-retool-apps)
##### TLDR: Click the `Create New` Button and then `From Json` and pick the [ShapGraph](./retool/ShapGraph.json) Json.

#### - Get your local IP Address:
dockers can't communicate via localhost.
##### Windows:
    ipconfig
##### Linux:
    ifconfig
copy the IPv4 address to the REST-API queries inside the Retool's ShapGraph project
#### - Click `Edit` on the ShapGraph App
#### - Open the left pannel in edit mode
#### - Change the top value called ip_address_default_value to use your IPv4 local address

Enjoy :)
