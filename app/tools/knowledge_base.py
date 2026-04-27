import glob
import os
import re

from llama_index.core import (
    Document,
    PromptTemplate,
    StorageContext,
    VectorStoreIndex,
    load_index_from_storage,
)
from llama_index.core.node_parser import HierarchicalNodeParser
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.retrievers import AutoMergingRetriever
from llama_index.core.tools import QueryEngineTool


class KnowledgeBase:
    def __init__(self):
        self.storage_dir = "./storage"
        self.data_dir = "./data/docs"
        self.index = self._get_or_create_index()

        self.storage_context = self.index.storage_context
        self.base_retriever = self.index.as_retriever(similarity_top_k=15)
        self.retriever = AutoMergingRetriever(
            self.base_retriever, self.storage_context, verbose=True
        )
        qa_prompt_tmpl_str = (
            "Eres el asesor de WhatsApp del taller Midas Querétaro. Respondes "
            "como una persona real por chat: en español, tono cercano, frases "
            "cortas (1 a 3 oraciones), sin markdown, sin listas con viñetas, "
            "sin títulos.\n\n"
            "REGLAS:\n"
            "1. Usa solo la información del contexto recuperado. No inventes "
            "servicios, precios, horarios, direcciones ni teléfonos.\n"
            "2. Si en el contexto no hay evidencia suficiente para responder con "
            "precisión, responde algo natural como: \"déjame confirmarte ese dato "
            "con un asesor y te aviso por aquí mismo\".\n"
            "3. Si el cliente pregunta por horarios, ubicación o contacto, dale "
            "el dato directo y breve, no copies tablas.\n"
            "4. Si hay ambigüedad, pídele al cliente el dato que falte (por "
            "ejemplo, modelo del auto o tipo de servicio).\n\n"
            "CONTEXTO:\n{context_str}\n\n"
            "PREGUNTA:\n{query_str}\n"
        )
        self.query_engine = RetrieverQueryEngine.from_args(
            self.retriever,
            text_qa_template=PromptTemplate(qa_prompt_tmpl_str),
        )
        self.knowledge_base_tool = QueryEngineTool.from_defaults(
            self.query_engine,
            name="midas_knowledge_base",
            description=(
                "Consulta la base de conocimiento del taller Midas Querétaro para "
                "responder preguntas sobre servicios (mantenimiento, frenos, "
                "suspensión, neumáticos, batería, aire acondicionado, etc.), "
                "ubicación, horarios, datos de contacto, garantías y filosofía "
                "del taller. Entrada: la pregunta del cliente en lenguaje natural."
            ),
        )

    def _get_or_create_index(self):
        print("[agente] Procesando index...")
        if not os.path.exists(self.storage_dir):
            # La primera vez (o tras borrar storage_multi_ficha) se indexa todo desde cero.
            print(f"[agente] Procesando archivos en {self.data_dir}...")
            # Lista que acumula todos los nodos de todos los archivos para un único índice.
            all_nodes = []

            files = glob.glob(os.path.join(self.data_dir, "*.md"))

            if not files:
                raise RuntimeError(f"No se encontraron archivos .md en {self.data_dir}")

            for file_path in files:
                # Nombre del archivo sin ruta (ej. "Nissan Sentra.md") para metadata y logs.
                file_name = os.path.basename(file_path)
                print(f"[agente] Procesando: {file_name}")

                # Lectura completa del archivo en UTF-8 para soportar acentos y caracteres especiales.
                with open(file_path, "r", encoding="utf-8") as f:
                    full_text = f.read()

                # --- FASE 1: EXTRACCIÓN DE TABLAS POR ARCHIVO ---
                # Patrón que busca bloques entre comentarios HTML. Acepta tanto "--" como "—" (em dash).
                # Grupos capturados (entre paréntesis): (1) título tras "TABLA COMIENZA - ", (2) contenido hasta "TABLA TERMINA", (3) título de cierre.
                # re.DOTALL hace que el punto coincida con saltos de línea, así el contenido puede ser multilínea.
                table_pattern = r"<!(?:--|—)\s*TABLA COMIENZA\s*-\s*(.*?)\s*(?:--|—)>\s*(.*?)\s*<!(?:--|—)\s*TABLA TERMINA\s*-\s*(.*?)\s*(?:--|—)>"
                tables_found = re.findall(table_pattern, full_text, re.DOTALL)
                # re.findall() devuelve una LISTA de TUPLAS: una tupla por cada match, con tantos elementos
                # como grupos capturados (.*?) haya en el patrón, EN EL MISMO ORDEN. Aquí: (grupo1, grupo2, grupo3).
                # No hay "nombres": title y content vienen del DESEMPAQUETADO POR POSICIÓN en el for.

                # Cada tabla se convierte en un Document con type="table" y name=título.
                # Así el retriever puede devolver tablas completas (especificaciones) cuando
                # la pregunta sea técnica; file_name evita mezclar datos de distintos modelos.
                for (
                    title,
                    content,
                    _,
                ) in (
                    tables_found
                ):  # posición 0 = title, 1 = content, 2 = descartado (_)
                    all_nodes.append(
                        Document(
                            text=content.strip(),
                            metadata={
                                "type": "table",
                                "name": title.strip(),
                                "file_name": file_name,  # Vital para no mezclar autos
                            },
                        )
                    )

                # --- FASE 2: NARRATIVA JERÁRQUICA POR ARCHIVO ---
                # Eliminamos del texto todas las tablas (los bloques que matchean table_pattern)
                # para no duplicar: las tablas ya están como Document arriba. El resto es
                # prosa (descripciones, diseño, tecnología, etc.).
                clean_narrative = re.sub(table_pattern, "", full_text, flags=re.DOTALL)
                narrative_doc = Document(
                    text=clean_narrative, metadata={"file_name": file_name}
                )

                # HierarchicalNodeParser crea nodos en tres niveles de tamaño (1024, 512, 128)
                # con overlap=40 para mantener continuidad. Los nodos grandes pueden tener
                # hijos más pequeños; el AutoMergingRetriever usará esa relación después.
                node_parser = HierarchicalNodeParser.from_defaults(
                    chunk_sizes=[1024, 512, 128], chunk_overlap=40
                )
                file_nodes = node_parser.get_nodes_from_documents([narrative_doc])
                all_nodes.extend(file_nodes)

            # --- FASE 3: ALMACENAMIENTO ÚNICO ---ss
            # StorageContext mantiene el docstore (nodos/documentos) y los stores del índice.
            # add_documents registra todos los nodos para que estén disponibles al cargar.
            storage_context = StorageContext.from_defaults()
            storage_context.docstore.add_documents(all_nodes)

            # VectorStoreIndex construye el índice vectorial a partir de los nodos,
            # usando Settings.embed_model para embeber cada nodo. Persistir guarda
            # en PERSIST_DIR todo lo necesario para reconstruir el índice sin reprocesar.
            index = VectorStoreIndex(all_nodes, storage_context=storage_context)
            index.storage_context.persist(persist_dir=self.storage_dir)
            return index
        else:
            # Si ya existen, solo los cargamos del disco (rápido y barato)
            storage_context = StorageContext.from_defaults(persist_dir=self.storage_dir)
            return load_index_from_storage(storage_context)
