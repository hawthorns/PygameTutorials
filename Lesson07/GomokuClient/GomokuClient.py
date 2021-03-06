import socket
import threading
from queue import Queue

import pygame

from Lesson07.GomokuClient.ChessboardClient import ChessboardClient

message_queue = Queue()
send_queue = Queue()


def receive_message(server_socket):
    """接收server傳送的訊息"""
    while True:
        message = server_socket.recv(1024)
        if message == b'':
            break

        print(message)
        message_queue.put(message)

    # 向queue發送連線中斷通知
    # TODO


def send_message(server_socket):
    while True:
        msg = send_queue.get()

        server_socket.send(str.encode(msg))


class GomokuClient:
    def __init__(self):
        pygame.init()

        self.screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption("多人連線五子棋")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(r"C:\Windows\Fonts\SimHei.ttf", 24)
        self.going = True
        self.piece = 'wait'

        self.chessboard = ChessboardClient()

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(('127.0.0.1', 23000))

        s.send(str.encode('join_game'))
        threading.Thread(target=receive_message, args=(s,)).start()
        threading.Thread(target=send_message, args=(s,)).start()

        # 遊戲狀態
        # start_connect: 開始連線
        # wait_connect: 連線中...
        # wait_game: 等待遊戲開始
        # gaming: 遊戲進行中
        # game_over: 遊戲結束
        self.status = "wait_connect"

    def loop(self):
        while self.going:
            self.update()
            self.draw()
            self.clock.tick(60)

        pygame.quit()

    def update(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                self.going = False
            elif e.type == pygame.MOUSEBUTTONDOWN:
                self.handle_MOUSEBUTTONDOWN(e)

        # 檢查 Queue
        # 有的話取一個來處理
        if not message_queue.empty():
            job = message_queue.get()

            if job[0] == ord('0'):
                self.piece = job[1:].decode("utf-8")
                self.status = 'wait_game'
            elif job[0] == ord('1'):
                if job[1:] == b'game_start':
                    self.status = 'gaming'
            elif job[0] == ord('3'):
                if self.status == 'gaming':
                    pos_msg = job[1:].decode("utf-8")
                    r, c = pos_msg.split(',')
                    r = int(r)
                    c = int(c)

                    if self.chessboard.set_piece(r, c):
                        self.chessboard.check_win(r, c)

    def draw(self):
        self.screen.fill((255, 255, 255))
        self.screen.blit(self.font.render("FPS: {0:.2F}".format(self.clock.get_fps()), True, (0, 0, 0)), (10, 10))

        self.screen.blit(self.font.render(self.piece, True, (0, 0, 0)), (200, 10))

        self.chessboard.draw(self.screen)
        if self.chessboard.game_over:
            self.screen.blit(
                self.font.render("{0} Win".format("Black" if self.chessboard.winner == 'b' else "White"), True,
                                 (0, 0, 0)), (600, 10))

        status_text = self.status
        if self.status == 'wait_connect':
            status_text = '連線中...'
        elif self.status == 'wait_game':
            status_text = '等待遊戲開始'
        elif self.status == 'gaming':
            status_text = '遊戲進行中'
        elif self.status == 'game_over':
            status_text = '遊戲結束'

        self.screen.blit(self.font.render(status_text, True, (0, 0, 0)), (600, 40))

        pygame.display.update()

    def handle_MOUSEBUTTONDOWN(self, e):
        # 計算座標，檢查是否可以下子，在送出封包
        if self.status == 'gaming':
            if not self.chessboard.is_in_area(e.pos[0], e.pos[1]):
                return
            if not self.chessboard.is_my_turn(self.piece):
                return

            r, c = self.chessboard.get_r_c(e.pos[0], e.pos[1])

            if not self.chessboard.can_set_piece(r, c):
                return

            # 送出封包
            send_queue.put('3{0},{1}'.format(r, c))

if __name__ == '__main__':
    game = GomokuClient()
    game.loop()
