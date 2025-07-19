# Usa un'immagine Python leggera
FROM python:3.10-slim

# Imposta la directory di lavoro
WORKDIR /app

# Copia i file del progetto
COPY . /app

# Installa le dipendenze
RUN pip install --no-cache-dir -r requirements.txt

# Espone la porta usata da Flask
EXPOSE 10000

# Comando di avvio del bot
CMD ["python", "bot.py"]
