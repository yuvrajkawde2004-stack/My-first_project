docker stop goofy_lalande
docker rm goofy_lalande
docker build -t travel-owner-app:latest .
docker run -d -p 5000:5000 travel-owner-app:latest
