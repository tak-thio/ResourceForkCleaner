import os
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import tkinter.ttk as ttk
import threading
from tkinterdnd2 import DND_FILES, TkinterDnD

class ResourceForkCleanerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("リソースフォーク削除ツール")
        self.root.geometry("600x600")

        # 削除対象のリスト
        self.target_files = []
        self.is_processing = False
        self.stop_event = threading.Event()

        # --- D&D設定 ---
        # ウィンドウ全体をドロップ対象にする
        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind('<<Drop>>', self.drop_folder)

        # --- UIの構築 ---
        
        # 上部フレーム
        top_frame = tk.Frame(root, pady=10)
        top_frame.pack(fill=tk.X, padx=10)

        # ラベルを変更してD&D可能であることを明示
        self.btn_select = tk.Button(top_frame, text="フォルダを選択 (またはここにドロップ)", command=self.select_folder, height=2)
        self.btn_select.pack(fill=tk.X, pady=(0, 5))

        # 進捗状況フレーム
        progress_frame = tk.Frame(top_frame)
        progress_frame.pack(fill=tk.X, pady=5)

        self.lbl_status = tk.Label(progress_frame, text="フォルダを選択またはドロップしてください", fg="gray", anchor="w")
        self.lbl_status.pack(fill=tk.X)

        self.progress = ttk.Progressbar(progress_frame, orient="horizontal", length=100, mode="determinate")
        self.progress.pack(fill=tk.X, pady=5)

        # 中止ボタン
        self.btn_stop = tk.Button(top_frame, text="処理を中止", command=self.stop_processing, state='disabled', bg="#ffeba0")
        self.btn_stop.pack(anchor="e")

        # リスト表示エリア (スクロール可能)
        list_frame = tk.Frame(root)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        lbl_list = tk.Label(list_frame, text="検出されたファイル一覧:", anchor="w")
        lbl_list.pack(fill=tk.X)

        self.txt_list = scrolledtext.ScrolledText(list_frame, state='disabled', height=15)
        self.txt_list.pack(fill=tk.BOTH, expand=True)

        # 下部フレーム
        bottom_frame = tk.Frame(root, pady=10)
        bottom_frame.pack(fill=tk.X, padx=10)

        self.btn_delete = tk.Button(bottom_frame, text="一覧のファイルを削除する", command=self.confirm_delete, state='disabled', bg="#ffcccc", fg="red", height=2)
        self.btn_delete.pack(fill=tk.X)

    def drop_folder(self, event):
        if self.is_processing: return
        
        path = event.data
        # Mac等の場合、パスにスペースが含まれると {} で囲まれることがあるので除去
        if path.startswith('{') and path.endswith('}'):
            path = path[1:-1]
            
        if os.path.isdir(path):
            self.start_scan(path)
        else:
            messagebox.showwarning("無効なファイル", "フォルダをドロップしてください。\n(単一のフォルダのみ対応しています)")

    def select_folder(self):
        if self.is_processing: return
        
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.start_scan(folder_path)

    def stop_processing(self):
        if self.is_processing:
            if messagebox.askyesno("中止確認", "処理を中止しますか？"):
                self.stop_event.set()
                self.lbl_status.config(text="中止処理中...", fg="orange")

    def start_scan(self, folder_path):
        # UIのリセット
        self.target_files = []
        self.update_list_text("")
        self.btn_delete.config(state='disabled')
        self.btn_select.config(state='disabled')
        self.btn_stop.config(state='normal')
        self.progress.config(mode="indeterminate")
        self.progress.start(10)
        self.lbl_status.config(text=f"スキャン中: {os.path.basename(folder_path)}", fg="blue")
        
        self.stop_event.clear()
        self.is_processing = True
        
        # 別スレッドでスキャン実行
        thread = threading.Thread(target=self.scan_logic, args=(folder_path,))
        thread.start()

    def scan_logic(self, folder_path):
        found_files = []
        count = 0
        interrupted = False
        
        try:
            for root, dirs, files in os.walk(folder_path):
                if self.stop_event.is_set():
                    interrupted = True
                    break

                for file in files:
                    if self.stop_event.is_set():
                        interrupted = True
                        break

                    # リソースフォーク(._*) と .DS_Store を対象とする
                    if file.startswith("._") or file == ".DS_Store":
                        full_path = os.path.join(root, file)
                        found_files.append(full_path)
                        count += 1
                        
                        # 5000件ごとにステータス更新
                        if count % 5000 == 0:
                            self.update_status(f"スキャン中... {count} 個発見")

        except Exception as e:
            self.update_status(f"エラーが発生しました: {str(e)}")
        
        self.target_files = found_files
        self.root.after(0, lambda: self.finish_scan(interrupted))

    def finish_scan(self, interrupted):
        self.progress.stop()
        self.progress.config(mode="determinate", value=0)
        self.btn_stop.config(state='disabled')
        self.btn_select.config(state='normal')
        self.is_processing = False

        if interrupted:
            self.lbl_status.config(text="スキャンが中止されました。", fg="orange")
            return

        count = len(self.target_files)
        if count > 0:
            # リスト表示（2000件以上は省略）
            display_text = ""
            if count > 2000:
                display_text = "\n".join(self.target_files[:1000])
                display_text += f"\n\n... 他 {count - 1000} 件 (表示省略) ...\n"
            else:
                display_text = "\n".join(self.target_files)
            
            self.update_list_text(display_text)
            self.lbl_status.config(text=f"スキャン完了: {count} 個の不要ファイルが見つかりました。", fg="red")
            self.btn_delete.config(state='normal')
        else:
            self.update_list_text("不要なファイルは見つかりませんでした。")
            self.lbl_status.config(text="スキャン完了: 削除対象はありません。", fg="green")

    def confirm_delete(self):
        if not self.target_files: return
        
        ans = messagebox.askyesno("削除確認", f"{len(self.target_files)} 個のファイルを削除しますか？\nこの操作は取り消せません。")
        if ans:
            self.start_delete()

    def start_delete(self):
        self.btn_select.config(state='disabled')
        self.btn_delete.config(state='disabled')
        self.btn_stop.config(state='normal')
        self.lbl_status.config(text="削除中...", fg="blue")
        
        # プログレスバー設定
        self.progress.config(mode="determinate", maximum=len(self.target_files), value=0)
        
        self.stop_event.clear()
        self.is_processing = True
        
        thread = threading.Thread(target=self.delete_logic)
        thread.start()

    def delete_logic(self):
        deleted_count = 0
        errors = 0
        interrupted = False
        
        total = len(self.target_files)
        
        for i, file_path in enumerate(self.target_files):
            if self.stop_event.is_set():
                interrupted = True
                break

            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    deleted_count += 1
            except Exception:
                errors += 1
            
            # 100件ごとにUI更新（頻繁すぎると遅くなる）
            if i % 100 == 0:
                self.update_progress(i + 1, f"削除中... {i + 1}/{total}")

        self.root.after(0, lambda: self.finish_delete(deleted_count, errors, interrupted))

    def finish_delete(self, count, errors, interrupted):
        self.btn_stop.config(state='disabled')
        self.btn_select.config(state='normal')
        self.is_processing = False
        self.progress['value'] = 0

        if interrupted:
            msg = f"処理が中止されました。\n削除済み: {count} 個"
            self.lbl_status.config(text="処理中止", fg="orange")
            messagebox.showwarning("中止", msg)
        else:
            msg = f"処理完了: {count} 個削除しました。"
            if errors > 0:
                msg += f"\n({errors} 個のエラーが発生しました)"
            
            self.lbl_status.config(text=msg, fg="black")
            self.update_list_text("削除完了。")
            messagebox.showinfo("完了", msg)
        
        self.target_files = []

    # --- ヘルパーメソッド ---
    def update_status(self, text):
        self.root.after(0, lambda: self.lbl_status.config(text=text))

    def update_progress(self, value, text):
        def _update():
            self.progress['value'] = value
            self.lbl_status.config(text=text)
        self.root.after(0, _update)

    def update_list_text(self, text):
        self.root.after(0, lambda: self._set_text(text))
        
    def _set_text(self, text):
        self.txt_list.config(state='normal')
        self.txt_list.delete(1.0, tk.END)
        self.txt_list.insert(tk.END, text)
        self.txt_list.config(state='disabled')

if __name__ == "__main__":
    # TkinterDnD.Tk を使用してD&D対応のルートウィンドウを作成
    root = TkinterDnD.Tk()
    app = ResourceForkCleanerApp(root)
    root.mainloop()