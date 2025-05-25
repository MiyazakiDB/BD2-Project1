import os
import pickle
import re
import json
from collections import defaultdict

import nltk

try:
    nltk.data.find('corpora/stopwords')
except nltk.downloader.DownloadError:
    nltk.download('stopwords')

try:
    nltk.data.find('tokenizers/punkt')
except nltk.downloader.DownloadError:
    nltk.download('punkt')

from nltk.stem.snowball import SnowballStemmer
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

class GINIndex:
    def __init__(self, index_file="gin_index.pkl", data_file="gin_data.jsonl", language="spanish"):
        self.inverted_index = defaultdict(set)
        self.index_file = index_file
        self.data_file = data_file

        self.language = language
        try:
            self.stemmer = SnowballStemmer(language)
            self.stop_words = set(stopwords.words(language))
        except OSError as e:
            print(f"Error al inicializar el stemmer para '{language}': {e}")
            self.stemmer = None
            self.stop_words = set()
        except LookupError:
            print(f"Recursos de NLTK para stopwords en '{language}' no encontrados.")
            self.stop_words = set()

            if not hasattr(self, 'stemmer'):
                self.stemmer = SnowballStemmer(language)

        self._load_index()

    def _load_index(self):
        if os.path.exists(self.index_file) and os.path.getsize(self.index_file) > 0:
            try:
                with open(self.index_file, "rb") as f:
                    self.inverted_index = pickle.load(f)
            except (pickle.UnpicklingError, EOFError, AttributeError, ImportError) as e:
                print(f"Warning: no se pudo cargar el archivo de indice GIN '{self.index_file}'. Error: {e}.")
                self.inverted_index = defaultdict(set)
        else:
            self.inverted_index = defaultdict(set)

    def save_index(self):
        try:
            with open(self.index_file, "wb") as f:
                pickle.dump(self.inverted_index, f)
        except Exception as e:
            print(f"Error al guardar el indice GIN en '{self.index_file}': {e}")

    def _tokenize(self, text: str) -> list[str]:
        if not isinstance(text, str) or not text.strip():
            return []

        text_lower = text.lower()
        try:
            words = word_tokenize(text_lower, language=self.language)
        except LookupError:
            print(f"Recurso 'punkt' de NLTK para tokenizacion en '{self.language}' no encontrado.")
            words = re.findall(r"\w+", text_lower)
        except Exception as e:
            print(f"Error durante word_tokenize: {e}.")
            words = re.findall(r"\w+", text_lower)

        processed_tokens = []
        for word in words:
            if word.isalnum() and word not in self.stop_words:
                if self.stemmer:
                    stemmed_word = self.stemmer.stem(word)
                    if stemmed_word:
                        processed_tokens.append(stemmed_word)
                elif word:
                     processed_tokens.append(word)

        return processed_tokens

    def _extract_text_from_record(self, record_data: dict, fields_to_index: list[str]) -> str:
        content_to_index = []
        for field in fields_to_index:
            field_value = record_data.get(field)
            if isinstance(field_value, str):
                content_to_index.append(field_value)
            elif isinstance(field_value, list):
                for item in field_value:
                    if isinstance(item, str):
                        content_to_index.append(item)
        return " ".join(content_to_index)

    def add_document(self, doc_position: int, text_content: str):
        tokens = self._tokenize(text_content)
        for token in tokens:
            self.inverted_index[token].add(doc_position)

    def remove_document(self, doc_position: int, text_content: str):
        tokens = self._tokenize(text_content)
        for token in tokens:
            self.inverted_index[token].discard(doc_position)
            if not self.inverted_index[token]:
                del self.inverted_index[token]

    def index_record_from_data(self, record_position: int, record_data: dict, fields_to_index: list[str]):
        text_to_index = self._extract_text_from_record(record_data, fields_to_index)
        if text_to_index:
            self.add_document(record_position, text_to_index)

    def remove_record_from_data(self, record_position: int, record_data: dict, fields_to_index: list[str]):
        text_that_was_indexed = self._extract_text_from_record(record_data, fields_to_index)
        if text_that_was_indexed:
            self.remove_document(record_position, text_that_was_indexed)

    def search(self, query: str, mode: str = "and") -> set[int]:
        tokens = self._tokenize(query)
        if not tokens:
            return set()

        result_sets = []
        for token in tokens:
            result_sets.append(self.inverted_index.get(token,set()))
            if mode == "and" and not result_sets[-1]:
                return set()

        if not result_sets:
            return set()

        if mode == "and":
            final_result = result_sets[0].copy()
            for i in range(1, len(result_sets)):
                final_result.intersection_update(result_sets[i])
            return final_result
        elif mode == "or":
            final_result = set()
            for s in result_sets:
                final_result.update(s)
            return final_result
        else:
            raise ValueError("Modo de busqueda no valido. Use 'and' o 'or'.") #TODO: implement NOT operator

    def _fetch_records_by_positions(self, positions: set[int]) -> list[dict]:
        if not positions:
            return []

        records = {}
        try:
            with open(self.data_file, "r", encoding="utf-8") as f:
                for pos_val in sorted(list(positions)):
                    f.seek(pos_val)
                    line = f.readline()
                    if line:
                        try:
                            records[pos_val] = json.loads(line.strip())
                        except json.JSONDecodeError:
                            print(f"Warning: error al decodificar JSON en posicion {pos_val} en '{self.data_file}'")
        except FileNotFoundError:
            print(f"Error: archivo de datos '{self.data_file}' no encontrado al intentar leer registros")
            return []
        except Exception as e:
            print(f"Error al leer registros de '{self.data_file}': {e}")
            return []

        return [records[pos] for pos in sorted(list(positions)) if pos in records]

    def search_and_retrieve(self, query: str, mode: str = "and") -> list[dict]:
        matching_positions = self.search(query, mode)
        return self._fetch_records_by_positions(matching_positions)

    def reindex_all(self, fields_to_index: list[str], progress_interval=1000):
        print(f"Reindexando todos los documentos de '{self.data_file}' para los campos: {fields_to_index} (idioma: {self.language})...")
        self.inverted_index.clear()
        count = 0
        try:
            with open(self.data_file, "r", encoding="utf-8") as f:
                while True:
                    position = f.tell()
                    line = f.readline()
                    if not line:
                        break

                    line_stripped = line.strip()
                    if not line_stripped:
                        continue

                    try:
                        record_data = json.loads(line_stripped)
                        self.index_record_from_data(position, record_data, fields_to_index)
                        count += 1
                        if count % progress_interval == 0:
                            print(f"  {count} registros procesados...")
                    except json.JSONDecodeError:
                        print(f"Warning: omitiendo linea no JSON en posicion {position} durante la reindexacion: '{line_stripped[:100]}...'")

            self.save_index()
            print(f"Reindexacion completada ({count} registros indexados)")
        except FileNotFoundError:
            print(f"Error: archivo de datos '{self.data_file}' no encontrado para reindexar")
        except Exception as e:
            print(f"Error durante la reindexacion: {e}")
