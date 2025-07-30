"""
Limpa a padroniza os nomes das colunas de um DataFrame.
"""
import copy
import re
import unicodedata
import polars as pl


def limpa_colunas(df):
    """
    Verifica se o df se trata de um DataFrame (Pandas ou Polars) o um LazyFrame (Polars)
    e aplica a "limpeza" dos nomes das colunas de acordo.
    """

    df_copia = copy.deepcopy(df)
    
    if isinstance(df_copia, pl.LazyFrame):
        lista_nomes_original = df_copia.collect_schema().names()
        lista_nomes_ajustada = list(map(remove_acentos, lista_nomes_original))
        lista_nomes_ajustada = list(map(remove_caracteres_especiais, lista_nomes_ajustada))
        lista_nomes_ajustada = list(map(formata_como_snake_case, lista_nomes_ajustada))
        lista_nomes_ajustada = renomeia_duplicatas(lista_nomes_ajustada)
        
        df_copia = df_copia.rename(dict(zip(lista_nomes_original, lista_nomes_ajustada)))
        
    else:
        lista_nomes_original = df_copia.columns
        lista_nomes_ajustada = list(map(remove_acentos, lista_nomes_original))
        lista_nomes_ajustada = list(map(remove_caracteres_especiais, lista_nomes_ajustada))
        lista_nomes_ajustada = list(map(formata_como_snake_case, lista_nomes_ajustada))
        lista_nomes_ajustada = renomeia_duplicatas(lista_nomes_ajustada)
        
        df_copia.columns = lista_nomes_ajustada
    
    return df_copia


def limpa_string_snake(texto):
    texto = remove_acentos(texto)
    texto = remove_caracteres_especiais(texto)
    texto = formata_como_snake_case(texto)
    return texto


def limpa_string_caixa_alta(texto):
    texto = remove_acentos(texto)
    texto = remove_caracteres_especiais(texto)
    texto = formata_como_caixa_alta(texto)
    return texto


def limpa_string_caixa_alta_cidade(texto):
    texto = remove_acentos(texto)
    texto = remove_caracteres_especiais_cidade(texto)
    texto = formata_como_caixa_alta(texto)
    return texto


def remove_acentos(texto):
    """
    Substitui os caracteres por seus compatíveis no padrão Unicode,
    removendo qualquer acento, cedilha, til ou trema.
    """
    texto = (
        unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("utf-8")
    )
    return texto


def remove_caracteres_especiais(texto):
    """
    Substitui caracteres especiais contidos entre os colchetes da primeira
    expressão regular por espaços.
    Remove aspas simples, duplas e "backticks".
    """
    texto = re.sub(r"[!()*+\,\-./:;<=>?[\]^_{|}~]", " ", texto)
    texto = re.sub(r"[\"\'\`]", "", texto)
    return texto


def remove_caracteres_especiais_cidade(texto):
    """
    Substitui caracteres especiais contidos entre os colchetes da primeira
    expressão regular por espaços.
    Remove aspas duplas e "backticks".
    Diferente da "remove_caracteres_especiais", não remove
    aspas simples (apóstrofe) e nem hífen, com o intuito de manter os nomes
    de municípios como "Santa Bárbara d'Oeste" ou "Ji-Paraná".
    """
    texto = re.sub(r"[!()*+\,./:;<=>?[\]^_{|}~]", " ", texto)
    texto = re.sub(r"[\"\`]", "", texto)
    return texto


def formata_como_snake_case(texto):
    """
    Substitui qualquer quantidade consecutiva de espaços em branco por um
    único espaço.
    Remove espaços em branco no início e final do texto.
    Converte para letras minúsculas.
    Substitui espaços em branco por underscore.
    """
    texto = re.sub(" +", " ", texto).strip().lower()
    texto = texto.replace(" ", "_")
    return texto


def formata_como_caixa_alta(texto):
    """
    Substitui qualquer quantidade consecutiva de espaços em branco por um
    único espaço.
    Remove espaços em branco no início e final do texto.
    Converte para letras maiúsculas.
    """
    texto = re.sub(" +", " ", texto).strip().upper()
    return texto


def renomeia_duplicatas(lista_textos):
    """
    Adiciona sufixos às colunas com nome duplicado.
    """
    contagem = {}

    for i, col in enumerate(lista_textos):
        contagem_atual = contagem.get(col, 0)
        if contagem_atual > 0:
            lista_textos[i] = f"{col}_{contagem_atual}"
        contagem[col] = contagem_atual + 1

    return lista_textos
