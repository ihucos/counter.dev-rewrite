FROM arm64v8/redis:alpine
EXPOSE 6379
# Enable AOF persistence + RDB snapshots
CMD ["redis-server", "--appendonly", "yes", "--save", "60", "1", "--save", "300", "10", "--save", "900", "1"]
