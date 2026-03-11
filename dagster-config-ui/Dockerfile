FROM node:24.14-alpine3.23 AS build-stage

WORKDIR /usr/src/app
ENV PROD='true'
COPY --chown=root:root --chmod=755 ["package.json", "yarn.lock", "quasar.config.ts", "index.html", "/usr/src/app/"]
RUN yarn install
COPY . .
RUN yarn run build


FROM nginx:1.29.5-alpine3.23-perl AS production-stage
COPY --from=build-stage /usr/src/app/dist/spa /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]

