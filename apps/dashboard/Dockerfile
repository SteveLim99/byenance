FROM node:14.9
WORKDIR /app
COPY package*.json ./
COPY yarn*.lock ./
RUN yarn install --network-timeout 100000 
COPY . .
EXPOSE 3000

CMD [ "yarn", "start" ]