# byenance

## Running the Development Environment
1. Create a file called "env" at ./ and enter the environmental variables as specified in ./env_example. It should be noted that the default env variables within pgadmin.env is already pre-filled. There are 3 files to edit:
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
5. You can access the web-application at http://localhost:3000/. It should be noted that the first time set up takes a little bit of time as it fetches and inserts a bulk of the historical data into the database instance. 
6. Removing the containers 
```
$ docker-compose down
```

## Using pgAdmin4 to Access the PostgreSQL Service. 
1. In ./docker-compose.yml, uncomment the pgadmin service as seen below:
```
  # pgadmin:
  #   image: dpage/pgadmin4
  #   container_name: pgadmin
  #   env_file:
  #     - ./env/pgadmin.env
  #   ports:
  #     - "8080:80"
  #   depends_on:
  #     - postgres
  #   logging:
  #     driver: "none"
```
2. Run the following command 
```
$ docker-compose up pgadmin
```
3. The pgadmin instance can be access at http://localhost:8080/ and you can connect to the database using the environment variables set in database.env.
4. To stop the pgAdmin4 service. Run the following command.
```
$ docker-compose stop pgadmin
```
