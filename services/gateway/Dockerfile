FROM nginx:alpine

# Remove default config
RUN rm /etc/nginx/conf.d/default.conf

# Copy gateway config
COPY nginx.conf /etc/nginx/nginx.conf

# Landing page served at localhost/
COPY index.html /usr/share/nginx/default/index.html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
