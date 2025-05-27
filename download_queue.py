"""
Spotify Downloader API - Educational Project
Copyright (c) 2025 https://github.com/gaab0418

This project is for educational purposes only.
Licensed under MIT License - see LICENSE file for details.


Sistema de filas para gerenciar downloads e processos
"""
import uuid
import time
import threading
import queue
import multiprocessing
from datetime import datetime
from typing import Dict, Any, Optional

# Não importar Session para evitar a tentação de passá-lo entre processos
# from sqlalchemy.orm import Session 

from models import Download
# Remover downloader da importação global para evitar pickle
# from downloader import SpotifyDownloader 
from config import MAX_CONCURRENT_DOWNLOADS

class DownloadQueueManager:
    """Gerenciador de fila de downloads com processos paralelos"""
    
    def __init__(self, db):
        """Inicializa o gerenciador de downloads"""
        self.db = db
        
        # Fila de prioridade para downloads (menor número = maior prioridade)
        self.queue = queue.PriorityQueue()
        
        # Dicionário para mapear download_id para processos
        self.active_downloads: Dict[str, multiprocessing.Process] = {}
        
        # Lock para acessar recursos compartilhados
        self.lock = threading.Lock()
        
        # Flag para sinalizar encerramento
        self.shutdown_flag = False
        
        # Thread de processamento da fila
        self.queue_thread = threading.Thread(target=self._process_queue, daemon=True)
        self.queue_thread.start()
        
        print(f"Gerenciador de downloads iniciado. Máximo de {MAX_CONCURRENT_DOWNLOADS} downloads simultâneos.")
        
    
    def enqueue_download(self, user_id: int, spotify_id: str, type_: str, priority: int = 5) -> str:
        """
        Adiciona um download à fila
        
        Args:
            user_id: ID do usuário solicitante
            spotify_id: ID do item no Spotify
            type_: Tipo do item (track ou playlist)
            priority: Prioridade (1-10, onde 1 é mais alta)
            
        Returns:
            download_id: ID único do download
        """
        # Gerar ID único para o download
        download_id = str(uuid.uuid4())
        
        # Criar registro no banco de dados
        download = Download(
            user_id=user_id,
            download_id=download_id,
            spotify_id=spotify_id,
            type=type_,
            status="na_fila",
            progress=0.0
        )
        
        self.db.add(download)
        self.db.commit()
        self.db.refresh(download)
        
        # Adicionar à fila de prioridade (com timestamp para desempate)
        timestamp = time.time()
        self.queue.put((priority, timestamp, {
            "download_id": download_id,
            "user_id": user_id,
            "spotify_id": spotify_id,
            "type": type_
        }))
        
        print(f"Download adicionado à fila: {download_id} (Prioridade: {priority})")
        return download_id
    
    def _process_queue(self):
        """Thread para processar a fila de downloads"""
        while not self.shutdown_flag:
            try:
                # Verificar se podemos iniciar mais downloads
                with self.lock:
                    if len(self.active_downloads) >= MAX_CONCURRENT_DOWNLOADS:
                        time.sleep(1)  # Aguardar se atingimos o limite
                        continue
                
                # Obter próximo download da fila
                try:
                    _, _, download_info = self.queue.get(timeout=1)
                except queue.Empty:
                    time.sleep(0.5)
                    continue

                # Iniciar o download em um processo separado
                download_id = download_info["download_id"]
                
                # Atualizar status no banco de dados
                download = self.db.query(Download).filter(Download.download_id == download_id).first()
                if not download:
                    self.queue.task_done()
                    continue
                
                # Atualizar status para 'processando'
                download.status = "processando"
                download.updated_at = datetime.utcnow()
                self.db.commit()
                
                # Iniciar processo de download - CORREÇÃO: Não passar objeto de sessão
                process = multiprocessing.Process(
                    target=self._download_worker_wrapper,
                    args=(
                        download_info["user_id"],
                        download_info["spotify_id"],
                        download_info["type"],
                        download_id
                    )
                )
                
                # Armazenar referência ao processo
                with self.lock:
                    self.active_downloads[download_id] = process
                
                # Iniciar processo
                process.start()
                print(f"Download iniciado em processo separado: {download_id}")
                
                # Marcar tarefa como concluída na fila
                self.queue.task_done()
                
                # Verificar e limpar downloads concluídos
                self._cleanup_completed_downloads()
                
            except Exception as e:
                print(f"Erro no processamento da fila: {str(e)}")
                time.sleep(1)
    
    @staticmethod
    def _download_worker_wrapper(user_id: int, spotify_id: str, type_: str, download_id: str):
        """
        Função wrapper para isolar a criação da sessão dentro do processo filho
        """
        try:
            # Importar módulos necessários dentro da função
            from database import SessionLocal
            from downloader import SpotifyDownloader
            
            # Criar nova sessão dentro do processo filho
            db = SessionLocal()
            
            try:
                # Inicializar downloader
                downloader = SpotifyDownloader(db, user_id)
                
                # Executar download de acordo com o tipo
                if type_ == "track":
                    downloader.download_track(spotify_id, download_id)
                elif type_ == "playlist":
                    downloader.download_playlist(spotify_id, download_id)
                else:
                    # Atualizar status para erro
                    download = db.query(Download).filter(Download.download_id == download_id).first()
                    if download:
                        download.status = "erro"
                        download.error_message = "Tipo de download inválido"
                        download.updated_at = datetime.utcnow()
                        db.commit()
            finally:
                # Garantir que a sessão seja fechada
                db.close()
        
        except Exception as e:
            print(f"Erro no worker de download {download_id}: {str(e)}")
            
            try:
                # Tentar atualizar status de erro no banco
                from database import SessionLocal
                db = SessionLocal()
                download = db.query(Download).filter(Download.download_id == download_id).first()
                if download:
                    download.status = "erro"
                    download.error_message = str(e)
                    download.updated_at = datetime.utcnow()
                    db.commit()
                db.close()
            except Exception as inner_e:
                print(f"Erro ao atualizar status do download {download_id}: {str(inner_e)}")
    
    def _cleanup_completed_downloads(self):
        """Remove referências a processos que já foram concluídos"""
        with self.lock:
            completed = []
            for download_id, process in self.active_downloads.items():
                if not process.is_alive():
                    process.join(timeout=0.1)  # Limpar recursos do processo
                    completed.append(download_id)
            
            # Remover downloads concluídos do dicionário ativo
            for download_id in completed:
                del self.active_downloads[download_id]
    
    def cancel_download(self, download_id: str, user_id: Optional[int] = None) -> bool:
        """
        Cancela um download em andamento ou na fila
        
        Args:
            download_id: ID do download a ser cancelado
            user_id: Se fornecido, verifica se o download pertence ao usuário
            
        Returns:
            bool: True se cancelado com sucesso, False caso contrário
        """
        # Verificar se o download existe e pertence ao usuário (se user_id fornecido)
        download = self.db.query(Download).filter(Download.download_id == download_id)
        if user_id is not None:
            download = download.filter(Download.user_id == user_id)
        
        download = download.first()
        
        if not download:
            return False
        
        # Atualizar status no banco de dados
        download.status = "cancelado"
        download.updated_at = datetime.utcnow()
        self.db.commit()
        
        # Se estiver em execução, encerrar o processo
        with self.lock:
            if download_id in self.active_downloads:
                process = self.active_downloads[download_id]
                if process.is_alive():
                    process.terminate()
                    process.join(timeout=1.0)
                
                # Remover do dicionário
                del self.active_downloads[download_id]
                return True
        
        # Se chegamos aqui, o download não estava ativo, mas foi marcado como cancelado no banco
        return True
    
    def get_queue_status(self):
        """Retorna informações sobre o estado atual da fila"""
        with self.lock:
            return {
                "active_downloads": len(self.active_downloads),
                "queue_size": self.queue.qsize(),
                "max_concurrent": MAX_CONCURRENT_DOWNLOADS
            }
    
    def shutdown(self):
        """Desliga o gerenciador de downloads"""
        print("Encerrando gerenciador de downloads...")
        self.shutdown_flag = True
        
        # Aguardar thread da fila finalizar
        if self.queue_thread.is_alive():
            self.queue_thread.join(timeout=2.0)
        
        # Encerrar todos os processos ativos
        with self.lock:
            for download_id, process in self.active_downloads.items():
                if process.is_alive():
                    print(f"Encerrando processo de download: {download_id}")
                    process.terminate()
                    process.join(timeout=1.0)
            
            self.active_downloads.clear()
        
        print("Gerenciador de downloads encerrado")

# Instância global do gerenciador de downloads
download_manager = None

def init_download_manager(db):
    """Inicializa o gerenciador de downloads"""
    global download_manager
    if download_manager is None:
        download_manager = DownloadQueueManager(db)
    return download_manager

def get_download_manager() -> DownloadQueueManager:
    """Retorna a instância global do gerenciador de downloads"""
    global download_manager
    if download_manager is None:
        raise RuntimeError("Gerenciador de downloads não inicializado")
    return download_manager