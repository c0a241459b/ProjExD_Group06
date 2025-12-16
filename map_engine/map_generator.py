# map_engine/map_generator.py
import pygame
import random
import os
from typing import List, Tuple, Optional
from .tile_selector import TileSelector, DEFAULT_TILE_SIZE

class MapGenerator:
    """
    ランダムなダンジョンマップを生成し、描画するクラス。
    
    部屋ベースのアルゴリズムを使用して、複数の部屋とそれらを接続する
    通路を持つマップを生成します。タイルベースの描画により、
    床と壁を視覚的に表現します。
    
    Attributes:
        width (int): マップの幅（タイル数）
        height (int): マップの高さ（タイル数）
        tile_size (int): 1タイルのピクセルサイズ
        room_count (int): 生成する部屋の数
        room_min_size (int): 部屋の最小サイズ（タイル数）
        room_max_size (int): 部屋の最大サイズ（タイル数）
        tilemap (List[List[int]]): 2次元配列のマップデータ（0=壁, 1=床）
        rooms (List[pygame.Rect]): 生成された部屋のリスト
        tile_selector (TileSelector): タイル画像を管理するオブジェクト
        floor_tileset (int): 床タイルのタイルセットインデックス
        floor_tile (int): 床タイルのタイルインデックス
        wall_tileset (int): 壁タイルのタイルセットインデックス
        wall_tile (int): 壁タイルのタイルインデックス
    """
    
    def __init__(self, width: int = 50, height: int = 50, tile_size: int = DEFAULT_TILE_SIZE, 
                 floor_tileset: int = 0, floor_tile: int = 0, 
                 wall_tileset: int = 0, wall_tile: int = 1):
        """
        MapGeneratorを初期化し、タイルセットを読み込む。
        
        マップの基本パラメータを設定し、タイルセット画像を検索して
        TileSelectorを初期化します。タイルセット画像が見つからない場合は
        例外を発生させます。
        
        Args:
            width (int, optional): マップの幅（タイル数）。デフォルトは50
            height (int, optional): マップの高さ（タイル数）。デフォルトは50
            tile_size (int, optional): 1タイルのサイズ（ピクセル）。
                デフォルトは DEFAULT_TILE_SIZE (48)
            floor_tileset (int, optional): 床タイルのタイルセット番号。デフォルトは0
            floor_tile (int, optional): 床タイルのインデックス。デフォルトは0
            wall_tileset (int, optional): 壁タイルのタイルセット番号。デフォルトは0
            wall_tile (int, optional): 壁タイルのインデックス。デフォルトは1
        
        Raises:
            FileNotFoundError: タイルセット画像が見つからない場合
            RuntimeError: TileSelector初期化時にエラーが発生した場合
        
        Notes:
            - タイルセット画像は複数のパスパターンで検索されます
            - 実行ディレクトリからの相対パスを想定しています
        
        Examples:
            >>> map_gen = MapGenerator(width=100, height=100, tile_size=32)
            タイルセット読み込み成功 (TS Index 0): tileset1.png (100 tiles)
        """
        self.width = width
        self.height = height
        self.tile_size = tile_size
        self.room_count = 5
        self.room_min_size = 6
        self.room_max_size = 15
        
        # タイルマップを0（壁）で初期化
        self.tilemap = [[0 for _ in range(height)] for _ in range(width)]
        self.rooms: List[pygame.Rect] = []
        
        # タイルセット画像の検索
        # 複数のパスパターンを試行して柔軟に対応
        possible_paths = [
            ["assets/tileset1.png", "assets/tileset2.png"],
            ["Assets/tileset1.png", "Assets/tileset2.png"],
            ["tileset1.png", "tileset2.png"],
        ]
        
        tileset_paths = None
        for paths in possible_paths:
            # main.pyからの相対パスを想定してチェック
            if os.path.exists(paths[0]): 
                # 存在するパスのみをフィルタリング
                tileset_paths = [p for p in paths if os.path.exists(p)]
                break
        
        if not tileset_paths:
            # すべてのパスパターンで見つからなかった場合
            raise FileNotFoundError(
                "タイルセット画像が見つかりません。assets/tileset1.png を配置してください。"
            )
        
        # TileSelectorの初期化
        self.tile_selector = TileSelector(tileset_paths, tile_size=tile_size) 
        
        # 使用するタイルの設定
        self.floor_tileset = floor_tileset
        self.floor_tile = floor_tile
        self.wall_tileset = wall_tileset
        self.wall_tile = wall_tile
    
    def set_tiles(self, floor_tileset: int, floor_tile: int, 
                  wall_tileset: int, wall_tile: int) -> None:
        """
        マップ描画に使用する床タイルと壁タイルを設定する。
        
        描画時に使用されるタイルを動的に変更できます。この設定は
        次回の draw() 呼び出し時から反映されます。
        
        Args:
            floor_tileset (int): 床タイルのタイルセット番号
            floor_tile (int): 床タイルのタイルインデックス
            wall_tileset (int): 壁タイルのタイルセット番号
            wall_tile (int): 壁タイルのタイルインデックス
        
        Notes:
            - インデックスの妥当性チェックは行われません
            - 無効なインデックスを指定すると、描画時にデフォルト描画が使われます
        
        Examples:
            >>> map_gen.set_tiles(0, 2, 1, 5)  # 異なるタイルに切り替え
            >>> map_gen.draw(screen)  # 新しいタイルで描画される
        """
        self.floor_tileset = floor_tileset
        self.floor_tile = floor_tile
        self.wall_tileset = wall_tileset
        self.wall_tile = wall_tile
    
    def generate(self) -> None:
        """
        新しいランダムマップを生成する。
        
        部屋ベースのアルゴリズムを使用してマップを生成します：
        1. 既存のマップデータをクリア
        2. ランダムな位置とサイズの部屋を複数生成
        3. 隣接する部屋をL字型の通路で接続
        
        Notes:
            - 部屋は重複する可能性があります
            - 通路は水平→垂直の順で作成されます
            - generate() を呼ぶたびに新しいマップが生成されます
        
        Side Effects:
            - self.rooms がクリアされ、新しい部屋リストが設定されます
            - self.tilemap が新しいマップデータで上書きされます
        
        Examples:
            >>> map_gen.generate()  # 新しいマップを生成
            >>> print(f"生成された部屋数: {len(map_gen.rooms)}")
            生成された部屋数: 5
        """
        # 既存の部屋リストをクリア
        self.rooms.clear()
        
        # マップを壁（0）で初期化
        for x in range(self.width):
            for y in range(self.height):
                self.tilemap[x][y] = 0
        
        # 指定された数の部屋を生成
        for i in range(self.room_count):
            # ランダムなサイズの部屋を生成
            w = random.randint(self.room_min_size, self.room_max_size)
            h = random.randint(self.room_min_size, self.room_max_size)
            # マップ境界内のランダムな位置
            x = random.randint(1, self.width - w - 1)
            y = random.randint(1, self.height - h - 1)
            
            # pygame.Rectで部屋を表現
            room = pygame.Rect(x, y, w, h)
            self.rooms.append(room)
            self.create_room(room)
            
            # 2番目以降の部屋は前の部屋と通路で接続
            if i > 0:
                prev_center = self.rooms[i - 1].center
                new_center = room.center
                self.create_corridor(prev_center, new_center)
    
    def create_room(self, room: pygame.Rect) -> None:
        """
        指定された矩形領域を床タイル（1）で埋める。
        
        部屋の範囲内のすべてのタイルを床（1）に設定します。
        範囲チェックにより、マップ境界外への書き込みを防ぎます。
        
        Args:
            room (pygame.Rect): 部屋の矩形領域
        
        Notes:
            - 部屋が重複する場合、後から作成された部屋が優先されます
            - マップ境界外の部分は無視されます
        
        Examples:
            >>> room = pygame.Rect(10, 10, 5, 5)
            >>> map_gen.create_room(room)
            # (10,10)から(14,14)の範囲が床になる
        """
        for x in range(room.left, room.right):
            for y in range(room.top, room.bottom):
                # マップ範囲内かチェック
                if 0 <= x < self.width and 0 <= y < self.height:
                    self.tilemap[x][y] = 1  # 床タイル
    
    def create_corridor(self, start: Tuple[int, int], end: Tuple[int, int]) -> None:
        """
        2点間をL字型の通路で接続する。
        
        始点から終点へ、まず水平方向に移動し、次に垂直方向に移動する
        L字型の通路を作成します。通路上のタイルはすべて床（1）になります。
        
        Args:
            start (Tuple[int, int]): 通路の始点座標 (x, y)
            end (Tuple[int, int]): 通路の終点座標 (x, y)
        
        Notes:
            - 通路は常に水平→垂直の順で作成されます
            - 既存の部屋や通路と重複しても問題ありません
            - マップ境界外への書き込みは範囲チェックで防がれます
        
        Examples:
            >>> map_gen.create_corridor((5, 5), (15, 10))
            # (5,5)→(15,5)→(15,10) のL字通路が作成される
        """
        x1, y1 = start
        x2, y2 = end
        
        # 水平方向の通路を作成
        step_x = 1 if x1 < x2 else -1
        x = x1
        while x != x2:
            if 0 <= x < self.width and 0 <= y1 < self.height:
                self.tilemap[x][y1] = 1  # 床タイル
            x += step_x
        
        # 垂直方向の通路を作成
        step_y = 1 if y1 < y2 else -1
        y = y1
        while y != y2:
            if 0 <= x2 < self.width and 0 <= y < self.height:
                self.tilemap[x2][y] = 1  # 床タイル
            y += step_y
    
    def draw(self, surface: pygame.Surface, camera_x: int = 0, camera_y: int = 0) -> None:
        """
        マップを画面に描画する（カメラオフセット対応）。
        
        カメラ位置を考慮して、画面に表示される範囲のタイルのみを描画します。
        描画は2パスで行われます：
        1. 床タイルの描画
        2. 壁タイルの描画（床の上に立つ壁のみ）
        
        Args:
            surface (pygame.Surface): 描画先のSurface
            camera_x (int, optional): カメラのX座標（ピクセル）。デフォルトは0
            camera_y (int, optional): カメラのY座標（ピクセル）。デフォルトは0
        
        Notes:
            - 画面外のタイルは描画されません（最適化）
            - 壁は床の上（y+1が床）にあるもののみ描画されます
            - タイルが取得できない場合はデフォルトの矩形が描画されます
        
        Algorithm:
            壁の描画ルール：
            - セル(x,y)が壁(0)で、その下のセル(x,y+1)が床(1)の場合のみ描画
            - これにより、床に立つ壁のみが視覚的に表現されます
        
        Examples:
            >>> screen = pygame.display.set_mode((800, 600))
            >>> map_gen.draw(screen, camera_x=100, camera_y=50)
            # カメラ位置(100,50)を基準にマップが描画される
        """
        screen_w, screen_h = surface.get_size()
        
        # カメラ位置から描画範囲を計算（画面に映る部分のみ）
        start_x = max(0, camera_x // self.tile_size)
        end_x = min(self.width, (camera_x + screen_w) // self.tile_size + 1)
        start_y = max(0, camera_y // self.tile_size)
        end_y = min(self.height, (camera_y + screen_h) // self.tile_size + 1)
        
        # 使用するタイル画像を取得
        floor_tile = self.tile_selector.get_tile(self.floor_tileset, self.floor_tile)
        wall_tile = self.tile_selector.get_tile(self.wall_tileset, self.wall_tile)
        
        # パス1: 床タイルの描画
        for x in range(start_x, end_x):
            for y in range(start_y, end_y):
                if self.tilemap[x][y] == 1:  # 床タイル
                    # ワールド座標からスクリーン座標への変換
                    screen_x = x * self.tile_size - camera_x
                    screen_y = y * self.tile_size - camera_y
                    
                    # 床の描画
                    if floor_tile:
                        # タイル画像が利用可能な場合
                        surface.blit(floor_tile, (screen_x, screen_y))
                    else:
                        # フォールバック：灰色の矩形
                        pygame.draw.rect(surface, (200, 200, 200), 
                                         (screen_x, screen_y, self.tile_size, self.tile_size))
        
        # パス2: 壁タイルの描画（床の上に立つ壁のみ）
        # 床の後に描画することで、正しいレイヤー順序を確保
        for x in range(start_x, end_x):
            for y in range(start_y, end_y):
                
                # 壁の描画条件：
                # - 現在のセル(x,y)が壁(0)である
                # - その下のセル(x,y+1)が床(1)である
                # これにより、床に立つ壁のみが描画されます
                
                if self.tilemap[x][y] == 0:  # 壁タイル
                    # 下のセルが床であるかチェック
                    if y < self.height - 1 and self.tilemap[x][y+1] == 1:
                        screen_x = x * self.tile_size - camera_x
                        screen_y = y * self.tile_size - camera_y

                        # 壁の描画
                        if wall_tile:
                            # タイル画像が利用可能な場合
                            surface.blit(wall_tile, (screen_x, screen_y))
                        else:
                            # フォールバック：茶色の矩形
                            pygame.draw.rect(surface, (80, 60, 40), 
                                             (screen_x, screen_y, self.tile_size, self.tile_size))
    
    def get_tile_at(self, x: int, y: int) -> int:
        """
        指定された座標のタイル値を取得する。
        
        Args:
            x (int): X座標（タイル単位）
            y (int): Y座標（タイル単位）
        
        Returns:
            int: タイル値（0=壁, 1=床）。範囲外の場合は0
        
        Examples:
            >>> tile = map_gen.get_tile_at(10, 10)
            >>> if tile == 1:
            ...     print("床タイルです")
        """
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.tilemap[x][y]
        return 0  # 範囲外は壁として扱う
    
    def is_walkable(self, x: int, y: int) -> bool:
        """
        指定された座標が通行可能か判定する。
        
        Args:
            x (int): X座標（タイル単位）
            y (int): Y座標（タイル単位）
        
        Returns:
            bool: 通行可能な場合True、それ以外False
        
        Examples:
            >>> if map_gen.is_walkable(player_x, player_y):
            ...     # プレイヤーを移動
        """
        return self.get_tile_at(x, y) == 1