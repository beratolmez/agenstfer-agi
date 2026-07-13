FROM node:22-bookworm-slim
WORKDIR /service
RUN npm install -g @tobilu/qmd
COPY server.mjs ./server.mjs
EXPOSE 8181
CMD ["node", "server.mjs"]

