# Gemini PDF Extractor

Extrai informações estruturadas de arquivos PDF usando a API Gemini. Esta classe foi projetado para processar uma pasta de arquivos PDF usando prompts estruturados.

## Instalação

```bash
pip install datagem
```

## Chave da Gemini API

Para usar este pacote, você precisa ter uma chave da Gemini API. Caso você não tenha, você pode obtê-la no **Google AI Studio**: [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey).

## Uso

Você pode extrair as informações de todos os pdfs e todos os prompts usando o método `extract_all`. O método retorna um dicionário, em que as chaves são _prompts_ e os valores são `DataFrame` (do pandas).

```python
from datagem.pdf import DataExtractorPdf

extractor = DataExtractorPdf(
    api_key="SUA_CHAVE_API",
    path_files="caminho/para/seus_pdfs/",
    path_prompts="caminho/para/seus_prompts/"
)
resultados_dict = extractor.extract_all()
primeiro_dataframe = list(results_dict.values())[0]
print(primeiro_dataframe.head())
```

Você pode extrair as informações de alguns pdfs e alguns prompts usando o método `extract_partial`. O método retorna um dicionário, em que as chaves são _prompts_ e os valores são `DataFrame` (do pandas).

```python
from datagem.pdf import DataExtractorPdf

extractor = DataExtractorPdf(
    api_key="SUA_CHAVE_API",
    path_files="caminho/para/seus_pdfs/",
    path_prompts="caminho/para/seus_prompts/"
)
resultados_dict = extractor.extract_partial(prompts = ['prompt1.txt', 'prompt2.txt'],file = ['file1.pdf', 'file2.pdf', 'file3.pdf'])
primeiro_dataframe = list(results_dict.values())[0]
print(primeiro_dataframe.head())
```
