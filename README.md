
# CANViewer

CANAble2.0でCANをしゃべるくん
[GitHub - TomiXRM/CANViewer: CANAble2.0でCANをしゃべるくん](https://github.com/TomiXRM/CANViewer)

![image1.png](./asset/image1.png)

CANable2.0(slcan)でCAN通信をするGUIアプリケーションです。PyQt6で実装されています。

CANでデータを送信してCANを動かす時などに使えるおもちゃです。

※現在動作確認しているのはMacOSのみです

※現在送信にしか対応していないです。受信にも対応予定。

※いつかSocketCANにも対応させます

# **前提条件**

- CANable2.0デバイスが用意されていること
- Pythonがインストールされていること
- Poetryがインストールされていること

# 使用方法

1. ターミナルを開きます。
2. Pythonアプリケーションが格納されているディレクトリに移動します。
    
    ```bash
    cd path/to/your/python/application
    ```
    
3. Poetryを使用して依存関係を解決し、仮想環境を作成します。
    
    ```
    poetry install
    ```
    
4. アプリケーションを起動します。
    
    ```arduino
    poetry run python main.py
    ```
    

# CANViewerの機能

- インターバル送信
- 単発送信

# **注意事項**

- Poetryがインストールされていない場合は、事前にインストールする必要があります。
- Poetryを使用して依存関係を解決することで、Pythonアプリケーションの実行に必要なパッケージが自動的にインストールされます。
- **`poetry run`**を使用することで、Poetryが管理する仮想環境内でPythonアプリケーションを実行します。