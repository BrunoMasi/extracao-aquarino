from pathlib import Path
from datetime import date, timedelta
import requests
import pandas as pd

BASE_URL = "http://172.31.30.102/data.json"
PASTA_SAIDA = Path.home() / "Aquarino"
PASTA_SAIDA.mkdir(parents=True, exist_ok=True)

SENSORES = ["0", "1", "3", "4", "5", "6", "7", "8"]

INICIO = date(2026, 3, 15)
FIM = date(2026, 4, 15)

N_DIAS = 2
TIMEOUT = 15


def buscar_json(params):
    response = requests.get(BASE_URL, params=params, timeout=TIMEOUT)
    response.raise_for_status()
    return response.json()


def normalizar_resposta(payload, sensor_id=None, data_ref=None):
    if payload is None:
        return pd.DataFrame()

    if isinstance(payload, list):
        df = pd.DataFrame(payload)
    elif isinstance(payload, dict):
        df = pd.DataFrame([payload])
    else:
        return pd.DataFrame()

    if sensor_id is not None:
        df["sensor_id"] = sensor_id

    if data_ref is not None:
        df["data_ref"] = pd.to_datetime(data_ref)

    if "DT" in df.columns:
        df["DT"] = pd.to_datetime(df["DT"], errors="coerce")

    return df


try:
    sensores_info = buscar_json({"obj": "sensor", "_": ""})
    print("Sensores encontrados:")
    print(sensores_info)
except Exception as erro:
    print(f"Erro ao listar sensores: {erro}")


dfs = []

for dia_atual in pd.date_range(INICIO, FIM, freq="D"):
    ano = dia_atual.strftime("%Y")
    mes = dia_atual.strftime("%m")
    dia = dia_atual.strftime("%d")

    for sensor in SENSORES:
        print(f"Buscando sensor {sensor} em {dia_atual.date()}")

        try:
            resposta = buscar_json({
                "obj": "graph",
                "id": sensor,
                "Y": ano,
                "M": mes,
                "D": dia,
            })

            df_i = normalizar_resposta(
                resposta,
                sensor_id=sensor,
                data_ref=dia_atual.date(),
            )

            if not df_i.empty:
                dfs.append(df_i)

        except Exception as erro:
            print(f"Erro no sensor {sensor}, data {dia_atual.date()}: {erro}")

df_final = pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

arquivo_consolidado = PASTA_SAIDA / "dados_aquarino_consolidado.csv"
df_final.to_csv(arquivo_consolidado, index=False)
print(f"Arquivo consolidado salvo em: {arquivo_consolidado}")


hoje = date.today()

for i in range(N_DIAS + 1):
    dia_exportacao = hoje - timedelta(days=i + 1)

    ano = dia_exportacao.strftime("%Y")
    mes = dia_exportacao.strftime("%m")
    dia = dia_exportacao.strftime("%d")

    for sensor in SENSORES:
        print(f"Exportando sensor {sensor} em {dia_exportacao}")

        try:
            resposta = buscar_json({
                "obj": "graph",
                "id": sensor,
                "Y": ano,
                "M": mes,
                "D": dia,
            })

            df_i = normalizar_resposta(
                resposta,
                sensor_id=sensor,
                data_ref=dia_exportacao,
            )

            nome_arquivo = f"dados_aquarino_{ano}-{mes}-{dia}_sensor{sensor}.csv"
            caminho_arquivo = PASTA_SAIDA / nome_arquivo
            df_i.to_csv(caminho_arquivo, index=False)

        except Exception as erro:
            print(f"Falha ao exportar sensor {sensor} em {dia_exportacao}: {erro}")