# main.py
"""
モジュラーマップジェネレーター - メインエントリポイント

このスクリプトは、ランダムに生成されたダンジョンマップ上で
プレイヤーを操作できるゲームアプリケーションです。

主な機能:
- タイルベースのランダムマップ生成
- プレイヤーキャラクターの移動（WASD操作）
- カメラのプレイヤー追従
- スペースキーでマップ再生成

依存関係:
- pygame: ゲームエンジン
- map_engine: カスタムマップ生成モジュール
- move: プレイヤー移動モジュール

使用方法:
    $ python main.py
"""

import pygame
import os
import sys

# パッケージ内のクラスをインポート
# main.pyと同じディレクトリにmap_engineがあることを想定
from map_engine.map_generator import MapGenerator

# MapGenerator内で定義されているデフォルトサイズを取得
DEFAULT_TILE_SIZE = 48 


def main() -> None:
    """
    アプリケーションのメインループを実行する。
    
    Pygameを初期化し、マップとプレイヤーを生成してゲームループを開始します。
    ゲームループでは以下の処理が行われます：
    - イベント処理（終了、キー入力）
    - プレイヤー移動とカメラ更新
    - マップとプレイヤーの描画
    - UI情報の表示
    
    Raises:
        FileNotFoundError: タイルセット画像が見つからない場合
        RuntimeError: タイルセット読み込み時にエラーが発生した場合
    
    Notes:
        - 実行ファイルのディレクトリを作業ディレクトリに設定します
        - 60FPSで動作します
        - ESCキーまたはウィンドウ閉じるボタンで終了します
    """
    # 実行ファイルからの相対パスを基準にする
    # これにより、どこから実行してもassets/が正しく参照される
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Pygameの初期化
    # すべてのPygameモジュール（display, font, mixer等）を初期化
    pygame.init()
    
    # メインウィンドウの作成
    screen = pygame.display.set_mode((1000, 700)) 
    pygame.display.set_caption("Modular Map Generator")
    
    # FPS制御用のClockオブジェクト
    clock = pygame.time.Clock()
    
    try:
        # MapGeneratorの初期化
        # タイルセット画像が見つからない場合はここでエラーが発生します
        map_gen = MapGenerator(width=50, height=50, tile_size=DEFAULT_TILE_SIZE) 
    except (FileNotFoundError, RuntimeError) as e:
        # エラーメッセージを表示して終了
        print(f"エラー: {e}")
        pygame.quit()
        sys.exit()


    # --- タイル選択の固定設定 (48x48タイル用) ---
    # タイルセットとタイルインデックスの設定
    # TS0 = tileset1.png, TS1 = tileset2.png (存在する場合)
    # インデックス計算: tile_idx = y * (横のタイル数) + x 
    
    FLOOR_TILESET_IDX = 0  # 床タイルのタイルセット番号
    FLOOR_TILE_IDX = 0     # 床タイルのインデックス
    
    WALL_TILESET_IDX = 1   # 壁タイルのタイルセット番号
    WALL_TILE_IDX = 1      # 壁タイルのインデックス
    
    # タイルセットが1つしかない場合の対応
    # tileset2.pngが存在しない場合、tileset1.pngから壁タイルを取得
    if map_gen.tile_selector.get_tileset_count() <= 1:
        WALL_TILESET_IDX = 0  # 同じタイルセットを使用
        WALL_TILE_IDX = 1     # 異なるインデックスを使用
    
    # MapGeneratorに使用タイルを設定
    map_gen.set_tiles(
        FLOOR_TILESET_IDX, FLOOR_TILE_IDX,
        WALL_TILESET_IDX, WALL_TILE_IDX
    )
    # --- 固定設定ここまで ---
    
    # 初期マップの生成
    map_gen.generate()
    
    # プレイヤーの生成
    # 最初の部屋の中心にプレイヤーを配置
    from move import Player
    player = Player(
        map_gen.rooms[0].centerx,  # X座標（タイル単位）
        map_gen.rooms[0].centery,  # Y座標（タイル単位）
        tile_size=48
    )
    
    # カメラ移動速度（使用されていない - プレイヤー追従に置き換え）
    camera_speed = 10 
    
    # メインゲームループ
    running = True
    while running:
        # イベント処理ループ
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # ウィンドウの×ボタンが押された
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    # スペースキー: マップ再生成
                    map_gen.generate()
                    # プレイヤーを新しいマップの最初の部屋に配置
                    player.tile_x = map_gen.rooms[0].centerx
                    player.tile_y = map_gen.rooms[0].centery
        
        # プレイヤー移動処理（WASDキー）
        # 連続入力に対応するため、key.get_pressed()を使用
        keys = pygame.key.get_pressed()
        player.handle_input(keys, map_gen)
        
        # カメラをプレイヤーに追従させる
        # プレイヤーが画面中央に来るようにカメラ位置を計算
        camera_x, camera_y = player.get_camera_pos(
            800,  # 画面幅（プレイヤー中心計算用）
            600,  # 画面高（プレイヤー中心計算用）
            map_gen.width * map_gen.tile_size,   # マップ全体の幅（ピクセル）
            map_gen.height * map_gen.tile_size   # マップ全体の高さ（ピクセル）
        )
        
        # --- 描画フェーズ ---
        
        # 画面クリア（黒で塗りつぶし）
        screen.fill((0, 0, 0))
        
        # マップの描画（カメラオフセット適用）
        map_gen.draw(screen, camera_x, camera_y)
        
        # プレイヤーの描画（カメラオフセット適用）
        player.draw(screen, camera_x, camera_y)
        
        # --- UI表示 ---
        
        # フォントオブジェクトの作成
        font = pygame.font.Font(None, 24)  # デフォルトフォント、24ピクセル
        
        # 操作説明テキスト
        text1 = font.render("SPACE: Regenerate | Arrows: Move", True, (255, 255, 255))
        
        # タイル設定情報テキスト
        tile_info = (f"Floor: TS{map_gen.floor_tileset}[{map_gen.floor_tile}] | "
                     f"Wall: TS{map_gen.wall_tileset}[{map_gen.wall_tile}] (48x48 Tiles)")
        text2 = font.render(tile_info, True, (150, 200, 255))
        
        # テキストを画面左上に描画
        screen.blit(text1, (10, 10))
        screen.blit(text2, (10, 35))
        
        # 画面更新（ダブルバッファリング）
        pygame.display.flip()
        
        # FPS制限（60FPS）
        clock.tick(60)
    
    # ゲームループ終了後のクリーンアップ
    pygame.quit()


if __name__ == "__main__":
    """
    スクリプトとして直接実行された場合のみmain()を呼び出す。
    
    これにより、このファイルがモジュールとしてインポートされた場合は
    自動実行されません。
    """
    main()