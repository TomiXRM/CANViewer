<div align="center">
  <img src="/asset/icon.png" alt="CANVIEWER LOGO" width="120" />
  <h1>CANViewer</h1>
  <p>cross-platform CAN bus monitor, built on Python.</p>

  [![License](https://img.shields.io/github/license/TomiXRM/CANViewer)](https://github.com/TomiXRM/CANViewer/blob/main/LICENSE)
  [![GitHub stars](https://img.shields.io/github/stars/TomiXRM/CANViewer)](https://github.com/TomiXRM/CANViewer/stargazers)
  [![GitHub issues](https://img.shields.io/github/issues/TomiXRM/CANViewer)](https://github.com/TomiXRM/CANViewer/issues)
  [![GitHub release](https://img.shields.io/github/v/release/TomiXRM/CANViewer)](https://github.com/TomiXRM/CANViewer/releases)
</div>


# CANViewer

CANAble2.0でCANをしゃべるくん
[GitHub - TomiXRM/CANViewer: CANAble2.0でCANをしゃべるくん](https://github.com/TomiXRM/CANViewer)

![image1.png](./asset/image1.png)

CANable2.0(slcan)でCAN通信をするGUIアプリケーションです。PyQt6で実装されています。

CANでデータを送信してCANを動かす時などに使えるおもちゃです。

Mac,Ubuntu,Windowsで動作確認済みです！

※現在送信にしか対応していないです。受信にも対応予定。

※いつかSocketCANにも対応させます

# **前提条件**

- CANable2.0(slcan)デバイスが用意されていること
- Pythonがインストールされていること
- Poetryがインストールされていること

# 使用方法

1. ターミナルを開きます。
2. Pythonアプリケーションが格納されているディレクトリに移動します。
    
    ```bash
    cd path/to/your/python/application
    ```
    
3. Poetryを使用して依存関係を解決し、仮想環境を作成します。
    
    ```bash
    poetry install
    ```
   または
   ```bash
   make install
   ```
    
4. アプリケーションを起動します。
    
    ```bash
    make
    ```
    

# CANViewerの機能

- 単発送信  
  `Interval`に入力せずに`Start`ボタンを押す
- インターバル送信  
  `Interval`に入力して`Start`ボタンを押す
- 標準フォーマットと拡張フォーマットの切り替え  
   `StdID`と`ExtID`を押すと切り替え

# **注意事項**

- Poetryがインストールされていない場合は、事前にインストールする必要があります。
- Poetryを使用して依存関係を解決することで、Pythonアプリケーションの実行に必要なパッケージが自動的にインストールされます。
- **`make`**を使用することで、Poetryが管理する仮想環境内でPythonアプリケーションを実行します。

# CANViewer

CAN talker with CANAble2.0
[GitHub - TomiXRM/CANViewer: CAN talker with CANAble2.0](https://github.com/TomiXRM/CANViewer)

![image1.png](./asset/image1.png)

A GUI application for CAN communication with CANable2.0 (slcan). Implemented with PyQt6.

A toy that can be used when sending data via CAN to operate CAN.

Operation confirmed on Mac, Ubuntu, and Windows!

*Currently only supports sending. Receiving will also be supported.

*We will make it compatible with SocketCAN someday.

# **Prerequisites**

- A CANable2.0 (slcan) device must be prepared.

- Python must be installed.

- Poetry must be installed.

# How to use

1. Open a terminal.

2. Change to the directory where the Python application is stored.

   ```bash
   cd path/to/your/python/application
   ```

3. Use Poetry to resolve dependencies and create a virtual environment.

   ```bash
   poetry install
   ```
   or
   ```bash
   make install
   ```

4. Start the application.

   ```bash
   make
   ```

# CANViewer features

- Single transmission  
   Click `Start`button **without** any input in `Interval`field
- Interval transmission  
   Click `Start`button **with** some input in `Interval`field
- Select ID format  
   Click `StdID`button or `ExtID`button

# **Notes**

- If Poetry is not installed, you must install it in advance.
- By using Poetry to resolve dependencies, packages required to run Python applications are automatically installed.
- By using **`make`**, Python applications are run in a virtual environment managed by Poetry.