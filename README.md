<div align="center">
  <img src="/asset/icon.png" alt="CANVIEWER LOGO" width="120" />
  <h1>CANViewer</h1>
  <p>cross-platform CAN bus monitor, built on Python.</p>

  [![License](https://img.shields.io/github/license/TomiXRM/CANViewer)](https://github.com/TomiXRM/CANViewer/blob/main/LICENSE)
  [![GitHub stars](https://img.shields.io/github/stars/TomiXRM/CANViewer)](https://github.com/TomiXRM/CANViewer/stargazers)
  [![GitHub issues](https://img.shields.io/github/issues/TomiXRM/CANViewer)](https://github.com/TomiXRM/CANViewer/issues)
  [![GitHub release](https://img.shields.io/github/v/release/TomiXRM/CANViewer)](https://github.com/TomiXRM/CANViewer/releases)
</div>

![image1.png](./asset/image1.png)

SLCANやSocketCANデバイスをPCに接続して、PCから手軽にCAN通信を検証することができるアプリケーションです。
CANバス上に流れるデータの受信、定期送信や単発送信、標準IDと拡張IDの切り替え、10進数↔️16進数変換に対応しています。
Pythonベースで書かれているためMac,Ubuntu,Windows動作します(SocketCANはUbuntuのみ対応)

## Prerequisites

- CANデバイスが用意されていること(SLCANであれば[CANable2.0](https://canable.io)や[MKS CANable](https://ja.aliexpress.com/item/1005003746105255.html)など)
- Pythonがインストールされていること
- [Poetry](https://python-poetry.org)がインストールされていること(バージョン管理で使います)
- `make`が入っていると便利です

## Usage

1. ターミナルを開きます。
2. Pythonアプリケーションが格納されているディレクトリに移動します。
    
    ```bash
    cd CANViewerのディレクトリ
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
    poetry run python main.py
    ```
    または
    ```bash
    make run
    ```
5. SocketCANで動作させる場合のオプション
   ```bash
   poetry run python main.py -c socketcan
   ```

    

## CANViewerの機能
- **単発送信** : `Interval`に入力せずに`Start`ボタンを押す
- **インターバル送信** : `Interval`にインターバル送信したい間隔(ミリ秒)を入力して`Start`ボタンを押す
- **標準/拡張フォーマットの切り替え** : `StdID`/`ExtID`のクリックでフォーマットの切り替え
- **入力進数変更** : `DataFrame`のラベルをクリックすることで切り替え可能。また`Ctrl+H(J)`でHEX、`Ctrl+D(F)`でDECへの入力メソッド切り替えが可能


### インターバル送信
![interval.gif](./asset/interval.gif)

### 標準ID/拡張IDフォーマット切り替え
![id_format_switch.gif](./asset/id_format_switch.gif)

### 入力フォーマットの10進数(DEC),16進数(HEX)切り替え
![hex_dec_switch.gif](./asset/hex_dec_switch.gif)


## **NOTE**

- [Poetry](https://python-poetry.org)がインストールされていない場合は、事前にインストールする必要があります。
- Poetryを使用して依存関係を解決することで、Pythonアプリケーションの実行に必要なパッケージが自動的にインストールされます。

## ライセンス
このプロジェクトはLGPLライセンスです。 詳しくは[LICENSE](LICENSE)を確認ください