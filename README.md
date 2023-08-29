# docker_compose_rasa_pt
Project in Docker and docker-compose to run instance rasa in language portugues pt

## Versions
rasa -  3.8.0a1-full
ubuntu - 

## comands
## Start rasa with 3.8.0a1-full
docker run -v $(pwd)/rasa:/app rasa/rasa:3.8.0a1-full init --no-prompt


# talk bot      
docker run -it -v $(pwd)/rasa:/app rasa/rasa:3.8.0a1-full shell debug

# Train model
docker run -v $(pwd)/rasa:/app rasa/rasa:3.8.0a1-full train --domain domain.yml --data data --out models

# Enable API
docker run -v $(pwd)/rasa:/app rasa/rasa:3.8.0a1-full --enable-api --cors "*"


# Inside container
docker exec -it docker_compose_rasa_pt_rasa_1 bash
rasa interactive


# Rasa X
docker run -v $(pwd)/rasa/rasa_x:/app rasa/rasa-x:latest init --no-prompt