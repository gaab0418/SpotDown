"""
Spotify Downloader API - Educational Project
Copyright (c) 2025 https://github.com/gaab0418

This project is for educational purposes only.
Licensed under MIT License - see LICENSE file for details.


Classe para download de músicas e playlists do Spotify
"""
import os
import re
import requests
import yt_dlp
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from sqlalchemy.orm import Session
from models import Download, SpotifyConfig

class SpotifyDownloader:
    """Classe para download de conteúdo do Spotify via YouTube"""
    
    def __init__(self, db: Session, user_id: int):
        """Inicializa o downloader com configurações do usuário"""
        self.db = db
        self.user_id = user_id
        
        # Obter configuração do usuário
        config = db.query(SpotifyConfig).filter(SpotifyConfig.user_id == user_id).first()
        
        if not config:
            raise ValueError("Usuário não possui configuração do Spotify")
        
        self.client_id = config.client_id
        self.client_secret = config.client_secret
        self.redirect_uri = config.redirect_uri
        self.download_path = config.download_path
        self.scope = "user-library-read playlist-read-private"
        
        # Verificar se as credenciais foram configuradas
        if not self.client_id or not self.client_secret:
            raise ValueError("Erro: Configure client_id e client_secret")
        
        # Criar diretório de downloads se não existir
        user_download_path = os.path.join(self.download_path, f"user_{user_id}")
        self.download_path = user_download_path
        
        if not os.path.exists(self.download_path):
            os.makedirs(self.download_path)
        
        # Inicializar cliente Spotify
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri,
            scope=self.scope,
            cache_path=f".spotify_cache_{user_id}"
        ))
    
    def update_download_status(self, download_id: str, status: str, message: str, progress: float = None, 
                              file_path: str = None, error_message: str = None, name: str = None, 
                              artist: str = None):
        """Atualiza o status de um download no banco de dados"""
        download = self.db.query(Download).filter(
            Download.download_id == download_id,
            Download.user_id == self.user_id
        ).first()
        
        if not download:
            return
        
        download.status = status
        
        if progress is not None:
            download.progress = progress
        
        if file_path:
            download.file_path = file_path
        
        if error_message:
            download.error_message = error_message
        
        if name:
            download.name = name
        
        if artist:
            download.artist = artist
        
        self.db.commit()
        self.db.refresh(download)
    
    def search_youtube(self, query):
        """Busca uma música no YouTube usando requisições diretas"""
        try:
            search_url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
            response = requests.get(search_url)
            
            # Extrair o vídeo ID do primeiro resultado usando regex
            video_ids = re.findall(r"watch\?v=(\S{11})", response.text)
            
            if not video_ids:
                return None
                
            # Pegar o primeiro resultado
            return video_ids[0]
        except Exception as e:
            print(f"Erro ao buscar no YouTube: {e}")
            return None
    
    def download_track(self, track_id, download_id):
        """Baixa uma faixa específica do Spotify"""
        try:
            # Atualizar status
            self.update_download_status(download_id, "processando", "Obtendo informações da faixa")
            
            # Obter informações da faixa
            track = self.sp.track(track_id)
            artist = track["artists"][0]["name"]
            title = track["name"]
            query = f"{artist} - {title}"
            
            # Atualizar nome e artista no banco de dados
            self.update_download_status(
                download_id, "processando", 
                f"Buscando: {query}", 
                name=title, artist=artist, progress=10.0
            )
            
            # Buscar no YouTube
            video_id = self.search_youtube(query)
            
            if not video_id:
                self.update_download_status(
                    download_id, "erro", 
                    f"Não foi possível encontrar: {query}", 
                    error_message=f"Não foi possível encontrar vídeo para: {query}"
                )
                return {"status": "erro", "message": f"Não foi possível encontrar: {query}"}
            
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            
            # Atualizar status
            self.update_download_status(
                download_id, "processando", 
                f"Baixando: {query}", 
                progress=30.0
            )
            
            # Sanitizar nome de arquivo
            safe_title = re.sub(r'[\\/*?:"<>|]', "", title)
            safe_artist = re.sub(r'[\\/*?:"<>|]', "", artist)
            filename = f"{safe_artist} - {safe_title}"
            file_path = os.path.join(self.download_path, f"{filename}.mp3")
            
            # Configurar opções de download
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(self.download_path, f"{filename}.%(ext)s"),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '320',
                }],
                'quiet': True,
                'no_warnings': True,
                'progress_hooks': [lambda d: self._progress_hook(d, download_id)]
            }
            
            # Baixar áudio
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
            
            # Atualizar status final
            self.update_download_status(
                download_id, "concluido", 
                f"Download concluído: {artist} - {title}", 
                file_path=file_path, 
                progress=100.0
            )
            
            return {
                "status": "concluido", 
                "message": f"Download concluído: {artist} - {title}",
                "file_path": file_path
            }
        
        except Exception as e:
            error_msg = str(e)
            self.update_download_status(
                download_id, "erro", 
                f"Erro ao baixar: {error_msg}",
                error_message=error_msg,
                progress=0.0
            )
            return {"status": "erro", "message": f"Erro ao baixar {track_id}: {error_msg}"}
    
    def _progress_hook(self, d, download_id):
        """Hook para acompanhar o progresso de download do yt-dlp"""
        if d['status'] == 'downloading':
            try:
                # Calcular progresso do download e conversão (50-95%)
                if 'total_bytes' in d and d['total_bytes'] > 0:
                    progress = float(d['downloaded_bytes'] / d['total_bytes']) * 45.0 + 50.0
                    self.update_download_status(
                        download_id, "processando", 
                        f"Baixando: {d.get('filename', 'arquivo')} - {d.get('_percent_str', '0%')}", 
                        progress=min(progress, 95.0)  # Limitar a 95% (reservando 5% para processamento final)
                    )
            except Exception:
                # Ignora erros de atualização de progresso
                pass
        elif d['status'] == 'finished':
            self.update_download_status(
                download_id, "processando", 
                "Convertendo para MP3...", 
                progress=95.0
            )
    
    def search(self, query, limit=5, search_type="track"):
        """Pesquisa faixas ou playlists no Spotify"""
        try:
            results = self.sp.search(q=query, limit=limit, type=search_type)
            
            items = []
            if search_type == "track":
                for track in results["tracks"]["items"]:
                    items.append({
                        "id": track["id"],
                        "name": track["name"],
                        "artist": track["artists"][0]["name"] if track["artists"] else None,
                        "type": "track",
                        "image_url": track["album"]["images"][0]["url"] if track["album"]["images"] else None
                    })
            elif search_type == "playlist":
                for playlist in results["playlists"]["items"]:
                    items.append({
                        "id": playlist["id"],
                        "name": playlist["name"],
                        "artist": playlist["owner"]["display_name"],
                        "type": "playlist",
                        "image_url": playlist["images"][0]["url"] if playlist["images"] else None
                    })
                    
            return items
        except Exception as e:
            raise Exception(f"Erro na pesquisa: {str(e)}")
    
    def download_playlist(self, playlist_id, download_id):
        """Baixa todas as faixas de uma playlist do Spotify"""
        try:
            # Atualizar status
            self.update_download_status(
                download_id, "processando", 
                "Obtendo informações da playlist", 
                progress=5.0
            )
            
            # Obter informações da playlist
            playlist = self.sp.playlist(playlist_id)
            playlist_name = playlist["name"]
            
            # Sanitizar nome da playlist
            safe_playlist_name = re.sub(r'[\\/*?:"<>|]', "", playlist_name)
            
            # Atualizar nome no banco de dados
            self.update_download_status(
                download_id, "processando", 
                f"Preparando download da playlist: {playlist_name}", 
                name=playlist_name, 
                progress=10.0
            )
            
            # Criar pasta específica para a playlist
            playlist_path = os.path.join(self.download_path, safe_playlist_name)
            if not os.path.exists(playlist_path):
                os.makedirs(playlist_path)
            
            # Backup da pasta de downloads original
            original_path = self.download_path
            self.download_path = playlist_path
            
            # Obter todas as faixas da playlist
            tracks = self.sp.playlist_tracks(playlist_id)
            total = tracks["total"]
            
            self.update_download_status(
                download_id, "processando", 
                f"Playlist com {total} faixas. Iniciando downloads...", 
                progress=15.0
            )
            
            # Baixar cada faixa
            success_count = 0
            failed_tracks = []
            
            # Calcular quanto cada faixa vale no progresso
            progress_per_track = 80.0 / total if total > 0 else 0
            current_progress = 15.0
            
            # Processar o primeiro lote de faixas
            for i, item in enumerate(tracks["items"]):
                if item["track"] is None:
                    continue
                    
                track = item["track"]
                current_progress += progress_per_track / 2
                
                self.update_download_status(
                    download_id, "processando", 
                    f"[{i+1}/{total}] Baixando: {track['name']}", 
                    progress=current_progress
                )

                try:
                    # Criar um ID temporário para a faixa (não salvo no banco)
                    track_temp_id = f"{download_id}_track_{i}"
                    
                    # Baixar a faixa
                    result = self._download_track_internal(track["id"], track_temp_id)
                    
                    if result.get("status") == "concluido":
                        success_count += 1
                        current_progress += progress_per_track / 2
                        self.update_download_status(
                            download_id, "processando", 
                            f"[{i+1}/{total}] Concluído: {track['name']}", 
                            progress=current_progress
                        )
                    else:
                        failed_tracks.append(f"{track['artists'][0]['name']} - {track['name']}")
                except Exception as track_error:
                    failed_tracks.append(f"{track['artists'][0]['name']} - {track['name']}")
            
            # Obter mais faixas se a playlist for grande
            while tracks["next"]:
                tracks = self.sp.next(tracks)
                for i, item in enumerate(tracks["items"]):
                    if item["track"] is None:
                        continue
                        
                    track = item["track"]
                    current_index = i + 1 + success_count + len(failed_tracks)
                    current_progress += progress_per_track / 2
                    
                    self.update_download_status(
                        download_id, "processando", 
                        f"[{current_index}/{total}] Baixando: {track['name']}", 
                        progress=current_progress
                    )
                    
                    try:
                        # Criar um ID temporário para a faixa (não salvo no banco)
                        track_temp_id = f"{download_id}_track_{current_index}"
                        
                        # Baixar a faixa
                        result = self._download_track_internal(track["id"], track_temp_id)
                        
                        if result.get("status") == "concluido":
                            success_count += 1
                            current_progress += progress_per_track / 2
                            self.update_download_status(
                                download_id, "processando", 
                                f"[{current_index}/{total}] Concluído: {track['name']}", 
                                progress=current_progress
                            )
                        else:
                            failed_tracks.append(f"{track['artists'][0]['name']} - {track['name']}")
                    except Exception as track_error:
                        failed_tracks.append(f"{track['artists'][0]['name']} - {track['name']}")
            
            # Restaurar caminho original
            self.download_path = original_path
            
            # Finalizar o download
            status_message = f"Download da playlist concluído: {success_count}/{total} faixas"
            if failed_tracks:
                status_message += f" ({len(failed_tracks)} falhas)"
            
            self.update_download_status(
                download_id, "concluido", 
                status_message, 
                file_path=playlist_path, 
                progress=100.0
            )
            
            return {
                "status": "concluido",
                "message": status_message,
                "playlist_path": playlist_path,
                "success": success_count,
                "total": total,
                "failed_tracks": failed_tracks
            }
        
        except Exception as e:
            error_msg = str(e)
            self.update_download_status(
                download_id, "erro", 
                f"Erro ao baixar playlist: {error_msg}",
                error_message=error_msg,
                progress=0.0
            )
            return {"status": "erro", "message": f"Erro ao baixar playlist {playlist_id}: {error_msg}"}
    
    def _download_track_internal(self, track_id, temp_id):
        """Versão simplificada de download_track para uso interno na playlist"""
        try:
            # Obter informações da faixa
            track = self.sp.track(track_id)
            artist = track["artists"][0]["name"]
            title = track["name"]
            query = f"{artist} - {title}"
            
            # Buscar no YouTube
            video_id = self.search_youtube(query)
            
            if not video_id:
                return {"status": "erro", "message": f"Não foi possível encontrar: {query}"}
            
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            
            # Sanitizar nome de arquivo
            safe_title = re.sub(r'[\\/*?:"<>|]', "", title)
            safe_artist = re.sub(r'[\\/*?:"<>|]', "", artist)
            filename = f"{safe_artist} - {safe_title}"
            
            # Configurar opções de download
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(self.download_path, f"{filename}.%(ext)s"),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '320',
                }],
                'quiet': True,
                'no_warnings': True,
            }
            
            # Baixar áudio
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
            
            return {"status": "concluido", "message": f"Concluído: {query}"}
        except Exception as e:
            return {"status": "erro", "message": f"Erro ao baixar {track_id}: {str(e)}"}