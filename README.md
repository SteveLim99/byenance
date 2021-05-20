# byenance

## Running the Development Environment
1. Create a file called "env" at ./ and enter the environmental variables as specified in ./env_example. There are 3 files to edit:
- database.env
- pgadmin.env
- api.env
2. Edit the database.env and pgadmin.env files accordingly to your preference, update api.env with your Binance API key. 
3. Skip this step if yarn is already installed globally. Otherwise, run the following command 
```
$ npm install --global yarn
```
4. Finally, deploy the docker containers 
```
$ docker-compose up
```
5. You can access the web-application at http://localhost:3000/
6. Removing the containers 
```
$ docker-compose down
