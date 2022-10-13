from flask import Flask, render_template, redirect
import psycopg2, requests, jyserver.Flask as jsf, json

connection = psycopg2.connect(
    database = "nft_db",
    user = "postgres",
    password = "pass"
)

cursor = connection.cursor()

app = Flask(__name__)

@jsf.use(app)
class JSF:
    def __init__(self):
        pass

    def getInfo(self, nft_address):
        self.js.window.location.replace(f'/{nft_address}')

@app.route('/')
def mainPage():
    return JSF.render(render_template('index.html'))

@app.route('/<nft_address>')
def nftInfo(nft_address):
    cursor.execute(f"SELECT * FROM nft WHERE mint = '{nft_address}'")
    fetch = cursor.fetchone()
    if fetch:
        cursor.execute(f"SELECT * FROM metaplex WHERE metaplex_id={fetch[4]}")
        metaplex = cursor.fetchone()
        response = requests.get(metaplex[1]).text
        metadata = json.loads(response)
        cursor.execute(f"SELECT * FROM owners WHERE owner_id = ANY(ARRAY{metaplex[5]})")
        owners = cursor.fetchall()
        return render_template('nft_info.html', fetch = fetch, metaplex = metaplex, metadata = metadata, owners = owners)
    else:
        url = f"https://solana-gateway.moralis.io/nft/mainnet/{nft_address}/metadata"
        headers = {
            "accept": "application/json",
            "X-API-Key": "test"
        }
        response = requests.get(url, headers=headers).text
        parse = json.loads(response)
        try:
            parse["mint"]
        except:
            return redirect('/')
        ids:list = []
        for i in parse["metaplex"]["owners"]:
            cursor.execute(f"""INSERT INTO owners (address, verified, share)
            VALUES ('{i["address"]}',
                    {i["verified"]},
                    {i["share"]}) RETURNING owner_id""")
            ids.append(int(cursor.fetchone()[0]))
            connection.commit()
        cursor.execute(f"""INSERT INTO metaplex ("metadataUri", "updateAuthority", "sellerFeeBasisPoints", "primarySaleHappened", "owners", "isMutable", "masterEdition")
        VALUES ('{parse["metaplex"]["metadataUri"]}',
                '{parse["metaplex"]["updateAuthority"]}',
                {parse["metaplex"]["sellerFeeBasisPoints"]},
                {parse["metaplex"]["primarySaleHappened"]},
                ARRAY {ids},
                {parse["metaplex"]["isMutable"]},
                {parse["metaplex"]["masterEdition"]}) RETURNING metaplex_id""")
        metaplex_id = int(cursor.fetchone()[0])
        connection.commit()
        cursor.execute(f"""INSERT INTO nft (mint, standard, name, symbol, metaplex_id)
        VALUES ('{parse["mint"]}',
                '{parse["standard"]}',
                '{parse["name"]}',
                '{parse["symbol"]}',
                {metaplex_id})""")
        connection.commit()
        return redirect(f'/{nft_address}')

if __name__ == '__main__':
    app.run()