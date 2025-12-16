import pygame
import random
from typing import List, Tuple

class MapGenerator:
    def __init__(self, width=100, height=100, tile_size=16):
        self.width = width
        self.height = height
        self.tile_size = tile_size
        self.room_count = 5
        self.room_min_size = 6
        self.room_max_size = 15
        
        # タイルマップ (0=壁, 1=床)
        self.tilemap = [[0 for _ in range(height)] for _ in range(width)]
        self.rooms: List[pygame.Rect] = []
        
        # 画像の読み込み
        try:
            self.wall_tile = pygame.image.load("Assets/wall.png").convert_alpha()
            self.floor_tile = pygame.image.load("Assets/floor.png").convert_alpha()
            # タイルサイズにリサイズ
            self.wall_tile = pygame.transform.scale(self.wall_tile, (tile_size, tile_size))
            self.floor_tile = pygame.transform.scale(self.floor_tile, (tile_size, tile_size))
        except pygame.error as e:
            print(f"画像の読み込みエラー: {e}")
            print("Assets/wall.png と Assets/floor.png を用意してください")
            # フォールバック: 色で描画
            self.wall_tile = None
            self.floor_tile = None
    
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
        
        # 描画範囲を計算
        start_x = max(0, camera_x // self.tile_size)
        end_x = min(self.width, (camera_x + screen_w) // self.tile_size + 1)
        start_y = max(0, camera_y // self.tile_size)
        end_y = min(self.height, (camera_y + screen_h) // self.tile_size + 1)
        
        for x in range(start_x, end_x):
            for y in range(start_y, end_y):
                screen_x = x * self.tile_size - camera_x
                screen_y = y * self.tile_size - camera_y
                
                if self.tilemap[x][y] == 1:
                    # 床
                    if self.floor_tile:
                        surface.blit(self.floor_tile, (screen_x, screen_y))
                    else:
                        pygame.draw.rect(surface, (200, 200, 200), 
                                       (screen_x, screen_y, self.tile_size, self.tile_size))
                    
                    # 床の上（y-1の位置）に壁がある場合、床の上に壁を描画
                    if y > 0 and self.tilemap[x][y-1] == 0:
                        wall_y = screen_y - self.tile_size
                        if self.wall_tile:
                            surface.blit(self.wall_tile, (screen_x, wall_y))
                        else:
                            pygame.draw.rect(surface, (80, 60, 40), 
                                           (screen_x, wall_y, self.tile_size, self.tile_size))


def main():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Random Map Generator")
    clock = pygame.time.Clock()
    
    # マップジェネレーターの初期化
    map_gen = MapGenerator(width=100, height=100, tile_size=16)
    map_gen.generate()
    
    # カメラ位置
    camera_x = 0
    camera_y = 0
    camera_speed = 5
    
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
        camera_x = max(0, min(camera_x, map_gen.width * map_gen.tile_size - 800))
        camera_y = max(0, min(camera_y, map_gen.height * map_gen.tile_size - 600))
        
        # 描画
        screen.fill((0, 0, 0))
        map_gen.draw(screen, camera_x, camera_y)
        
        # UI表示
        font = pygame.font.Font(None, 36)
        text = font.render("SPACE: Regenerate | Arrows: Move", True, (255, 255, 255))
        screen.blit(text, (10, 10))
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()


if __name__ == "__main__":
    main()