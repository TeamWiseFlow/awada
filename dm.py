from websocket import create_connection
import concurrent.futures
import threading


def message_handler(message):
    """
    处理接收到的消息的函数。
    """
    print(f"Processing message: {message}")
    # 在这里添加您的消息处理逻辑
    # ...


def receive_messages(executor):
    """
    函数用于连接到WebSocket服务器并接收消息。
    使用executor提交任务来处理接收到的每条消息。
    """
    ws = None
    try:
        ws = create_connection("ws://0.0.0.0:8080/ws/publicMsg")
        while True:
            message = ws.recv()
            # 提交任务到线程池处理
            executor.submit(message_handler, message)
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if ws:
            ws.close()


def start_receiving():
    """
    启动一个线程来执行消息接收，并使用线程池处理消息。
    """
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:  # 调整max_workers根据实际需要
        thread = threading.Thread(target=receive_messages, args=(executor,))
        thread.daemon = True
        thread.start()
        # 线程将一直运行，直到接收消息的循环结束或遇到异常。
        # with语句会在主线程结束时自动关闭线程池，但通常需要更精细的控制逻辑来优雅地停止接收。


if __name__ == "__main__":
    print("Starting to receive messages...")
    start_receiving()
    # 根据实际需求，可能需要添加逻辑来控制程序的退出，比如通过特定信号或条件判断。
    while True:
        if input("Press q to exit:") == "q":
            break
