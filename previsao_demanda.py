import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
import numpy as np
import datetime

def obter_dados(tipo, dias=30):
    conn = sqlite3.connect("banco.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT data, COUNT(*) 
        FROM requisicoes 
        WHERE tipo_sangue=? AND status='aprovada' 
        AND DATE(data) >= DATE('now', ?)
        GROUP BY DATE(data)
    """, (tipo, f"-{dias} day"))
    dados = cursor.fetchall()
    conn.close()

    if not dados:
        return None

    df = pd.DataFrame(dados, columns=["data", "quantidade"])
    df["data"] = pd.to_datetime(df["data"])
    df = df.set_index("data").resample("D").sum().fillna(0)
    df["dias"] = np.arange(len(df))
    return df

def prever(tipo_sangue, dias=7):
    df = obter_dados(tipo_sangue, dias)
    if df is None or df.empty:
        print(f"Nenhum dado para o tipo {tipo_sangue}.")
        return

    X = df[["dias"]]
    y = df["quantidade"]

    modelo = LinearRegression()
    modelo.fit(X, y)

    futuros = pd.DataFrame({"dias": [len(df), len(df)+1, len(df)+2]})
    predicoes = modelo.predict(futuros)

    print(f"📊 Previsão para os próximos dias ({tipo_sangue}):")
    for i, val in enumerate(predicoes):
        print(f"Dia {i+1}: {round(val)} unidades")

    # Exibe gráfico
    plt.plot(df.index, y, label="Histórico")
    plt.plot([df.index[-1] + pd.Timedelta(days=i) for i in range(1, 4)], predicoes, label="Previsão", linestyle="--")
    plt.title(f"Previsão de Demanda: {tipo_sangue}")
    plt.xlabel("Data")
    plt.ylabel("Quantidade")
    plt.legend()
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    prever("O+", dias=30)
