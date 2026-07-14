FROM node:22-bookworm-slim@sha256:53ada149d435c38b14476cb57e4a7da73c15595aba79bd6971b547ceb6d018bf
WORKDIR /service
RUN npm install -g @tobilu/qmd@2.5.3
COPY server.mjs ./server.mjs
EXPOSE 8181
CMD ["node", "server.mjs"]
