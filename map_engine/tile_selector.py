# map_engine/tile_selector.py
import pygame
import os
from typing import List, Optional

DEFAULT_TILE_SIZE = 48

class TileSelector:
    """
    タイルセット画像を読み込み、個別のタイルとして管理するクラス。
    
    複数のタイルセット画像（PNG等）を読み込み、指定されたタイルサイズで
    分割して保持します。各タイルはタイルセットインデックスとタイル
    インデックスで識別されます。
    
    Attributes:
        tile_size (int): 1タイルのピクセルサイズ（正方形を想定）
        tileset_images (List[List[pygame.Surface]]): 
            読み込んだタイルのリスト。[タイルセット番号][タイル番号]でアクセス
        tileset_names (List[str]): 各タイルセットのファイル名リスト
    """
    
    def __init__(self, tileset_images: List[str], tile_size: int = DEFAULT_TILE_SIZE): 
        """
        TileSelectorを初期化し、指定された画像ファイルからタイルを読み込む。
        
        タイルセット画像を読み込み、tile_sizeで指定されたサイズに分割して
        内部リストに格納します。画像は左上から右へ、上から下へ走査され、
        1次元インデックスとして管理されます。
        
        Args:
            tileset_images (List[str]): 読み込むタイルセット画像のパスリスト
            tile_size (int, optional): 1タイルのサイズ（ピクセル）。
                デフォルトは DEFAULT_TILE_SIZE (48)
        
        Raises:
            RuntimeError: pygame.image.load() が失敗した場合
        
        Notes:
            - 存在しないファイルパスは警告を出力してスキップされます
            - 各画像はアルファチャンネル付きで読み込まれます (convert_alpha)
            - タイルインデックスは行優先順序（row-major）で計算されます
        
        Examples:
            >>> selector = TileSelector(["assets/floor.png", "assets/walls.png"], 32)
            タイルセット読み込み成功 (TS Index 0): floor.png (100 tiles)
            タイルセット読み込み成功 (TS Index 1): walls.png (64 tiles)
        """
        self.tile_size = tile_size
        self.tileset_images = []  # タイルセットごとのタイルリスト
        self.tileset_names = []   # タイルセット名の管理
        
        for img_idx, img_path in enumerate(tileset_images):
            try:
                # ファイル存在確認：ロード前に事前チェック
                if not os.path.exists(img_path):
                     print(f"警告: ファイルが見つかりません - {img_path}")
                     continue

                # 画像の読み込み（アルファチャンネル対応）
                tileset = pygame.image.load(img_path).convert_alpha()
                img_width = tileset.get_width()
                img_height = tileset.get_height()
                
                # タイルセット内の横・縦のタイル数を計算
                width = img_width // tile_size
                height = img_height // tile_size
                
                # タイルを切り出して1次元リストに格納
                tiles = []
                for y in range(height):
                    for x in range(width):
                        # 透明度を持つ新しいSurfaceを作成
                        tile_surface = pygame.Surface((tile_size, tile_size), pygame.SRCALPHA)
                        # 元画像から指定位置のタイルを切り出してブリット
                        tile_surface.blit(tileset, (0, 0), 
                                         (x * tile_size, y * tile_size, tile_size, tile_size))
                        tiles.append(tile_surface)
                
                # タイルセットリストに追加
                self.tileset_images.append(tiles)
                self.tileset_names.append(os.path.basename(img_path))
                
                # デバッグ情報：読み込み成功を通知
                print(f"タイルセット読み込み成功 (TS Index {img_idx}): {img_path} ({len(tiles)} tiles)")
                
            except pygame.error as e:
                # Pygameの画像ロードエラーを捕捉し、より詳細なエラーに変換
                raise RuntimeError(f"タイルセット {img_path} のロード中にエラーが発生しました: {e}")
    
    def get_tile(self, tileset_idx: int, tile_idx: int) -> Optional[pygame.Surface]:
        """
        指定されたタイルセットとインデックスからタイルSurfaceを取得する。
        
        2次元的な指定（どのタイルセットの何番目のタイル）により、
        対応するpygame.Surfaceオブジェクトを返します。範囲外の
        インデックスが指定された場合はNoneを返します。
        
        Args:
            tileset_idx (int): タイルセットのインデックス（0から開始）
            tile_idx (int): タイルセット内のタイルインデックス（0から開始）
        
        Returns:
            Optional[pygame.Surface]: 
                指定されたタイルのSurface。無効なインデックスの場合はNone
        
        Notes:
            - インデックスは0から始まります
            - 範囲外チェックにより、クラッシュを防ぎます
            - Noneが返された場合、呼び出し側で適切に処理する必要があります
        
        Examples:
            >>> tile = selector.get_tile(0, 5)  # 最初のタイルセットの6番目のタイル
            >>> if tile:
            ...     screen.blit(tile, (x, y))
        """
        # タイルセットインデックスの範囲チェック
        if 0 <= tileset_idx < len(self.tileset_images):
            tiles = self.tileset_images[tileset_idx]
            # タイルインデックスの範囲チェック
            if 0 <= tile_idx < len(tiles):
                return tiles[tile_idx]
        # 無効なインデックスの場合はNoneを返す（防御的プログラミング）
        return None
    
    def get_tileset_count(self) -> int:
        """
        読み込まれたタイルセット（画像ファイル）の数を取得する。
        
        正常に読み込まれたタイルセット画像の総数を返します。
        これは self.tileset_images のリスト長に相当します。
        
        Returns:
            int: 読み込まれたタイルセットの数
        
        Notes:
            - 読み込みに失敗したファイルはカウントされません
            - この値は get_tile() のタイルセットインデックスの上限を示します
        
        Examples:
            >>> count = selector.get_tileset_count()
            >>> print(f"利用可能なタイルセット: {count}個")
            利用可能なタイルセット: 2個
        """
        return len(self.tileset_images)
    
    def get_tileset_name(self, tileset_idx: int) -> Optional[str]:
        """
        指定されたタイルセットのファイル名を取得する。
        
        Args:
            tileset_idx (int): タイルセットのインデックス（0から開始）
        
        Returns:
            Optional[str]: タイルセットのファイル名。無効なインデックスの場合はNone
        
        Examples:
            >>> name = selector.get_tileset_name(0)
            >>> print(name)
            'tileset1.png'
        """
        if 0 <= tileset_idx < len(self.tileset_names):
            return self.tileset_names[tileset_idx]
        return None
    
    def get_tile_count(self, tileset_idx: int) -> int:
        """
        指定されたタイルセット内のタイル総数を取得する。
        
        Args:
            tileset_idx (int): タイルセットのインデックス（0から開始）
        
        Returns:
            int: タイルセット内のタイル数。無効なインデックスの場合は0
        
        Notes:
            - この値は get_tile() のタイルインデックスの上限を示します
        
        Examples:
            >>> count = selector.get_tile_count(0)
            >>> print(f"タイルセット0には{count}個のタイルがあります")
            タイルセット0には100個のタイルがあります
        """
        if 0 <= tileset_idx < len(self.tileset_images):
            return len(self.tileset_images[tileset_idx])
        return 0