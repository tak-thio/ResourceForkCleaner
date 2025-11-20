# 環境構築とビルド手順 (Setup & Build Guide)

このプロジェクトを開発・ビルドするための手順書です。

## 前提条件
- macOS (Apple Silicon / Intel)
- Homebrew がインストールされていること
- **Python 3.11** (ライブラリ `tkinterdnd2` との互換性のため推奨)

## 1. 環境セットアップ

### Python 3.11 のインストール
最新のPythonではなく、Tcl/Tk 8.6系を使用する3.11を利用します。
```bash
brew install python@3.11 python-tk@3.11
```

### 仮想環境の作成とライブラリインストール
プロジェクトルートで以下のコマンドを実行します。

```bash
# 仮想環境(venv)の作成
/opt/homebrew/bin/python3.11 -m venv venv

# 仮想環境のアクティベート（または直接パス指定でも可）
source venv/bin/activate

# 依存ライブラリのインストール
pip install tkinterdnd2 pyinstaller
```

## 2. アプリの起動（開発中）

コードを編集し、動作確認を行う場合は以下のコマンドで起動します。

```bash
./venv/bin/python resource_cleaner.py
```

## 3. アプリケーションのビルド (App化)

Mac用の `.app` 形式にパッケージングするには `PyInstaller` を使用します。
`tkinterdnd2` のファイルを正しく含めるために `--collect-all` オプションが必須です。

```bash
./venv/bin/pyinstaller --clean --noconsole --windowed \
    --name "ResourceForkCleaner" \
    --collect-all tkinterdnd2 \
    resource_cleaner.py
```

### 生成物
ビルドが成功すると、以下のフォルダにアプリが生成されます。
- `dist/ResourceForkCleaner.app`

このファイルを `/Applications` などに移動して使用できます。

## 4. トラブルシューティング

### "macOS 26 required..." エラー
- **原因**: macOS標準の古いPython/Tkinterが新しいmacOSのバージョン番号を解釈できないため。
- **対策**: Homebrewで新しいPythonをインストールして使用してください。

### "Unable to load tkdnd library" エラー
- **原因**: Pythonのバージョンと `tkinterdnd2` が依存するTcl/Tkのバージョンが不一致（例: Python 3.14 + Tcl 9.0 環境など）。
- **対策**: Python 3.11 (Tcl 8.6) 環境を使用してください。

### アプリが "開発元が未確認" で開けない
- **対策**: Finderでアプリアイコンを **Controlキーを押しながらクリック** し、「開く」を選択して承認してください。
