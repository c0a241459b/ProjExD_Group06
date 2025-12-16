import pygame
import random
import os
from typing import List, Tuple

# タイルの標準サイズ
DEFAULT_TILE_SIZE = 48 

class TileSelector:
    # __init__のtile_sizeデフォルト値を48に戻しました
    def __init__(self, tileset_images: List[str], tile_size=DEFAULT_TILE_SIZE): 
        """
        タイルセット画像からタイルを読み込む。
        画像は指定されたtile_size(48x48)で区切られ、1次元リストに格納されます。
        """
        self.tile_size = tile_size
        self.tileset_images = []  # 各タイルセット（画像ファイル）のタイル（Surface）リスト
        self.tileset_names = []   # 画像名
        
        for img_idx, img_path in enumerate(tileset_images):
            try:
                tileset = pygame.image.load(img_path).convert_alpha()
                img_width = tileset.get_width()
                img_height = tileset.get_height()
                
                # タイルサイズで分割できるグリッド数を計算
                width = img_width // tile_size
                height = img_height // tile_size
                
                tiles = []
                for y in range(height):
                    for x in range(width):
                        # 1タイル分のSurfaceを作成し、元のタイルセットから該当部分を切り出す
                        tile_surface = pygame.Surface((tile_size, tile_size), pygame.SRCALPHA)
                        tile_surface.blit(tileset, (0, 0), 
                                         (x * tile_size, y * tile_size, tile_size, tile_size))
                        
                        # 1次元リストにタイルを格納
                        # tile_idx = y * width + x 
                        tiles.append(tile_surface)
                        
                self.tileset_images.append(tiles)
                self.tileset_names.append(os.path.basename(img_path))
                print(f"タイルセット読み込み成功 (TS Index {img_idx}): {img_path}")
                print(f"  グリッド: {width}x{height} = {len(tiles)} tiles")
            except pygame.error as e:
                raise FileNotFoundError(f"画像ファイルが見つかりません: {img_path}")
    
    def get_tile(self, tileset_idx: int, tile_idx: int):
        """
        指定されたタイルセット（ファイル）とインデックス（リスト内の何番目）のタイルを取得
        
        :param tileset_idx: タイルセット画像リストのインデックス (0 = 1枚目, 1 = 2枚目...)
        :param tile_idx: タイルセット内のタイルのインデックス (左上から順に 0, 1, 2, ...)
        :return: pygame.Surface (タイル画像) または None
        """
        if 0 <= tileset_idx < len(self.tileset_images):
            tiles = self.tileset_images[tileset_idx]
            if 0 <= tile_idx < len(tiles):
                return tiles[tile_idx]
        return None
    
    def get_tileset_count(self):
        """読み込んだタイルセット（ファイル）の数を取得"""
        return len(self.tileset_images)
    
    def get_tile_count(self, tileset_idx):
        """指定されたタイルセットのタイル数を取得"""
        if 0 <= tileset_idx < len(self.tileset_images):
            return len(self.tileset_images[tileset_idx])
        return 0


class MapGenerator:
    def __init__(self, width=100, height=100, tile_size=DEFAULT_TILE_SIZE, 
                 floor_tileset=0, floor_tile=0, wall_tileset=0, wall_tile=1):
        self.width = width
        self.height = height
        self.tile_size = tile_size
        self.room_count = 5
        self.room_min_size = 6
        self.room_max_size = 15
        
        # タイルマップ (0=壁, 1=床)
        self.tilemap = [[0 for _ in range(height)] for _ in range(width)]
        self.rooms: List[pygame.Rect] = []
        
        # タイルセレクター初期化 (画像パスの確認は省略せずにそのまま)
        possible_paths = [
            ["Assets/tileset1.png", "Assets/tileset2.png"],
            ["assets/tileset1.png", "assets/tileset2.png"],
            ["tileset1.png", "tileset2.png"],
        ]
        
        tileset_paths = None
        for paths in possible_paths:
            if os.path.exists(paths[0]): 
                tileset_paths = [p for p in paths if os.path.exists(p)]
                break
        
        if not tileset_paths:
            raise FileNotFoundError(
                "タイルセット画像が見つかりません。\n"
                "Assets/tileset1.png (floor用) を配置してください。"
            )
        
        # MapGeneratorで設定されたtile_sizeを使用
        self.tile_selector = TileSelector(tileset_paths, tile_size=tile_size) 
        
        # 選択されたタイル（タイルセット番号, タイル番号）
        self.floor_tileset = floor_tileset
        self.floor_tile = floor_tile
        self.wall_tileset = wall_tileset
        self.wall_tile = wall_tile
    
    def set_tiles(self, floor_tileset, floor_tile, wall_tileset, wall_tile):
        """
        使用するタイルを設定する
        """
        self.floor_tileset = floor_tileset
        self.floor_tile = floor_tile
        self.wall_tileset = wall_tileset
        self.wall_tile = wall_tile
    
    # generate, create_room, create_corridor は変更なし (省略)

    def generate(self):
        """マップを生成"""
        self.rooms.clear()
        
        # 全体を壁で埋める
        for x in range(self.width):
            for y in range(self.height):
                self.tilemap[x][y] = 0
        
        # 部屋を生成
        for i in range(self.room_count):
            w = random.randint(self.room_min_size, self.room_max_size)
            h = random.randint(self.room_min_size, self.room_max_size)
            x = random.randint(1, self.width - w - 1)
            y = random.randint(1, self.height - h - 1)
            
            room = pygame.Rect(x, y, w, h)
            self.rooms.append(room)
            
            # 部屋の床を作成
            self.create_room(room)
            
            # 前の部屋と通路で繋ぐ
            if i > 0:
                prev_center = self.rooms[i - 1].center
                new_center = room.center
                self.create_corridor(prev_center, new_center)

    def create_room(self, room: pygame.Rect):
        """部屋の床を作成"""
        for x in range(room.left, room.right):
            for y in range(room.top, room.bottom):
                if 0 <= x < self.width and 0 <= y < self.height:
                    self.tilemap[x][y] = 1

    def create_corridor(self, start: Tuple[int, int], end: Tuple[int, int]):
        """L字型の通路を作成"""
        x1, y1 = start
        x2, y2 = end
        
        # 横方向の通路
        step_x = 1 if x1 < x2 else -1
        x = x1
        while x != x2:
            if 0 <= x < self.width and 0 <= y1 < self.height:
                self.tilemap[x][y1] = 1
            x += step_x
        
        # 縦方向の通路
        step_y = 1 if y1 < y2 else -1
        y = y1
        while y != y2:
            if 0 <= x2 < self.width and 0 <= y < self.height:
                self.tilemap[x2][y] = 1
            y += step_y
    
    def draw(self, surface: pygame.Surface, camera_x=0, camera_y=0):
        """マップを描画 (カメラオフセット対応)"""
        screen_w, screen_h = surface.get_size()
        
        start_x = max(0, camera_x // self.tile_size)
        end_x = min(self.width, (camera_x + screen_w) // self.tile_size + 1)
        start_y = max(0, camera_y // self.tile_size)
        end_y = min(self.height, (camera_y + screen_h) // self.tile_size + 1)
        
        floor_tile = self.tile_selector.get_tile(self.floor_tileset, self.floor_tile)
        wall_tile = self.tile_selector.get_tile(self.wall_tileset, self.wall_tile)
        
        for x in range(start_x, end_x):
            for y in range(start_y, end_y):
                screen_x = x * self.tile_size - camera_x
                screen_y = y * self.tile_size - camera_y
                
                if self.tilemap[x][y] == 1:
                    # 床
                    if floor_tile:
                        surface.blit(floor_tile, (screen_x, screen_y))
                    else:
                        pygame.draw.rect(surface, (200, 200, 200), 
                                         (screen_x, screen_y, self.tile_size, self.tile_size))
                    
                    # 床の上（y-1の位置）に壁がある場合、壁を描画
                    if y > 0 and self.tilemap[x][y-1] == 0:
                        wall_y = screen_y - self.tile_size
                        if wall_tile:
                            surface.blit(wall_tile, (screen_x, wall_y))
                        else:
                            pygame.draw.rect(surface, (80, 60, 40), 
                                             (screen_x, wall_y, self.tile_size, self.tile_size))

# TilePicker クラスは削除

def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    pygame.init()
    # 画面サイズを調整 (48x48タイルに合わせて、より大きく)
    screen = pygame.display.set_mode((1000, 700)) 
    pygame.display.set_caption("Tile Selector Map Generator (Fixed 48x48 Tiles)")
    clock = pygame.time.Clock()
    
    # マップジェネレーターの初期化 (tile_size=48)
    map_gen = MapGenerator(width=50, height=50, tile_size=DEFAULT_TILE_SIZE) 
    
    # --- タイル選択の固定設定 (48x48タイル用) ---
    
    # 読み込んだタイルセットはリストに格納されている:
    # TS Index 0: tileset1.png
    # TS Index 1: tileset2.png (もしあれば)
    
    # タイルセット内のインデックス計算方法 (例: 48x48タイルで、横に8枚並んでいるタイルセットの場合)
    # tile_idx = y * 8 + x 
    # 左上(0,0)が0、右下(7,7)が63
    
    # ----------------------------------------------------------------------
    # 床タイル設定: tileset1.png の 1番目のタイル (左上) を使用
    FLOOR_TILESET_IDX = 0 
    FLOOR_TILE_IDX = 0    
    
    # 壁タイル設定: tileset2.png の 2番目のタイル (横に1つずれた位置) を使用
    WALL_TILESET_IDX = 1  
    WALL_TILE_IDX = 49     
    
    # tileset2.png が存在しない場合は、代替として tileset1.png の別のタイルを使用
    if map_gen.tile_selector.get_tileset_count() <= 1:
        WALL_TILESET_IDX = 0
        WALL_TILE_IDX = 1  # tileset1.png の 2番目のタイルを使用
        
    map_gen.set_tiles(
        FLOOR_TILESET_IDX, FLOOR_TILE_IDX,
        WALL_TILESET_IDX, WALL_TILE_IDX
    )
    
    # --- タイル選択の固定設定ここまで ---
    
    map_gen.generate()
    
    # カメラ位置
    camera_x = 0
    camera_y = 0
    camera_speed = 10 # 48x48タイルに合わせて速度を調整
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    # スペースキーで再生成
                    map_gen.generate()
                    camera_x = 0
                    camera_y = 0
        
        # カメラ移動 (矢印キー)
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            camera_x -= camera_speed
        if keys[pygame.K_RIGHT]:
            camera_x += camera_speed
        if keys[pygame.K_UP]:
            camera_y -= camera_speed
        if keys[pygame.K_DOWN]:
            camera_y += camera_speed
        
        # カメラ位置の制限
        max_camera_x = max(0, map_gen.width * map_gen.tile_size - screen.get_width())
        max_camera_y = max(0, map_gen.height * map_gen.tile_size - screen.get_height())
        
        camera_x = max(0, min(camera_x, max_camera_x))
        camera_y = max(0, min(camera_y, max_camera_y))
        
        # 描画
        screen.fill((0, 0, 0))
        
        # マップ描画
        map_gen.draw(screen, camera_x, camera_y)
        
        # UI表示
        font = pygame.font.Font(None, 24)
        text1 = font.render("SPACE: Regenerate | Arrows: Move", True, (255, 255, 255))
        
        # 現在使用しているタイル情報（デバッグ用）
        tile_info = (f"Floor: TS{map_gen.floor_tileset}[{map_gen.floor_tile}] | "
                     f"Wall: TS{map_gen.wall_tileset}[{map_gen.wall_tile}] (48x48 Tiles)")
        text2 = font.render(tile_info, True, (150, 200, 255))
        
        screen.blit(text1, (10, 10))
        screen.blit(text2, (10, 35))
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()


if __name__ == "__main__":
    main()