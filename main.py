from flask import Flask
import psycopg2, web3, requests

connection = psycopg2.connect(
    database = "",
    user = "postgres",
    password = "pass"
)

cursor = connection.cursor()

app = Flask(__name__)

if __name__ == '__main__':
    app.run()