# Noterm: notebook-terminal server

## 概略

このアプリケーションはアパッチサーバーにインスパイアしたもので、以下の機能を追加しました。

1. 最低限の通信量でサーバー上の画像、動画、テキストファイルのプレビューおよびサムネイルの表示を行います。
テキストファイルのプレビュー上では、シンプルな変更もできます。

2. 簡単操作で複数のターミナルを開きます。
開いたターミナルはリスト表示される。リストから対話したいターミナルを選択すると、コマンドラインによる対話を行うことができます。

3. シェル編集と実行機能:
選択したファイルを引数とした連続実行機能。
コマンドパレットを用いた汎用コマンドの登録と貼り付け

プレビューは都度、低解像度画像を生成するため、サーバーpcのcpu負荷は少しかかりますがトラフィックは最小限に押さえられます。

このアプリはトラフィックを極力抑えたい中継サーバーを経由しつつ、リモートからのファイル操作の利便性を上げたい用途に適しています。

## 注意事項

<font style="background-color:#ffccff;" color=red>

このアプリケーションは6666番ポートをデフォルトで開けて、ターミナル操作を受け付けます。

このアプリを動作させるときは、該当ポートが不特定多数からアクセス可能にならないようにするべきです。

</font>
ネットワークを介して本アプリをサーバーとなるpc上で実行する際は、例えばsshのポート転送機能を併用することで、http通信経路の暗号化と該当ポートの外部からのアクセス遮断を行うことができます。

(例)　ubuntuのFirewallで6666ポートを外部から遮断しつつ、sshのポート転送機能でサーバーの6666ポートにアクセスする方法。

    (server)
    $ sudo ufw allow 22/tcp
    $ (sudo ufw deny 6666)
    $ sudo ufw reload
    $ sudo ufw enable

    (client)
    $ ssh -f -N -L 6666:localhost:6666 user@ip_for_server

うまく接続できた場合、以下のコマンドでサーバーから応答が返ります。

    (client)
    $ curl http://localhost:6666/ls?.
    
    ...(response of server "ls .")...

不特定多数からの開かれたアクセスを受ける用途は考慮していないため、サーバーの通信プロトコルはhttpsではなくhttpを採用しています。

なお、ローカルネットワーク内に存在するPCの場合は、該当するポートを外部ネットワークにルーティングしなければOKです。

本来はこのアプリにJupyter Notebookのようなログイン機能を付加すべきなのですが、そこは今後のアップデートで対応とします。

現version(0.0.2)ではログイン機能がないため、他の人のアカウントのコマンド操作が出来てしまうリスクがあります。複数人で共有するPCで本アプリを使うことは避けた方が良いでしょう。

## how to install

サーバpcに対してpython>=3.6で、以下のコマンドでインストールできます:

    pip install -e git+(our github repogitory)

使用ライブラリはnumpy,opencv-python,glob2です。

インストール後、以下のコマンドでサーバ待ち受けに入ります。

    noterm [-p <port: default=6666>]


## how to use

### ページへのアクセス

ポート転送などでlocalhost:6666にサーバーの待ち受けポートを誘致した際、
ブラウザ(chromeは動作確認済。ブラウザ依存のコマンドは使っていないため、他ブラウザでも動くはず）でメインページにアクセスできます。

    http://localhost:6666/

ページにアクセスすると、左側にファイル選択フレーム、右側にコンテンツ表示フレームが表示
されます。

左側で任意のフォルダを掘ってファイルにたどり着くと、サムネイルおよびプレビュー表示ができます。

### ファイル操作

メイン部分のみの説明。

- サムネイル表示
    - サムネイル欄をクリックすると、そのファイルを中心として前後10ファイルが軽量なサムネイル画像として表示されます。

- プレビュー表示
    - ファイル名を左クリックするとプレビュー画面に大きめな低画質画像が表示されます。
    - ファイル名を右クリックすると元画像および動画が再生されます。

- ファイルのソート
    - リストのタイトルを左クリックするとソートの優先キーが変わります。右クリックでソートは解除されます。

- コマンド引数候補登録
    - リストのチェックをonにし、add argボタンを押下すると下部リストにファイルが追加されます。下部リストで$-となっている部分を選びチェックを押下すると、それに応じた引数が後述のシェル機能で使えるようになります。

- シェル読み込み
    - .shファイルを右クリックした場合、後述のシェル画面に内容がロードされます。

### 通信タブ

右上にあるCommボタンを押下すると通信画面が開きます。
- New Taskボタンで新しいターミナルを
開きます。
- 開いたTaskはタスクリストに追加されるため、左クリックで選択すると選択したタスクの背景が水色に変わります。再度選択したら黄色に変わります。
    - 水色: 5秒おきにターミナル表示が自動更新
    - 黄色: 自動更新オフ
- 選択したタスクの応答はページ右下部のターミナル画面上に表示されます。
- ターミナルにコマンドを打つ場合は、表示画面直上のテキスト入力画面をダブルクリックし、背景色を黄色にします。
- 背景色が黄色の状態で、コマンドを実行したい行にカーソルを移動し改行を行うと、該当行が実行されます。
- 入力欄を再度ダブルクリックすると背景が白色に戻り、改行キーは入力欄への改行入力に変わります。
- taskを止めたい場合は、以下のいずれかの方法で止めることができます。
    - exitコマンドをターミナルに打ち込む(推奨)
    - task名の左にあるstopボタンをダブルクリックして強制停止
- 停止したプロセスは停止した順に10個までログに残ります。


### シェル実行タブ

- シェル編集欄
    - 上部に上下2つに別れた入力欄。上側に入力すると、下側の欄に引数を置き換えたした結果が表示される。シェル実行は下の置き換えた表示で実行される。
- 引数欄
    - どの引数に何が置き換わるかを示したリスト。"$-"の変換ルールは講述する。
    - 引数はファイル操作で選択されたものがリストアップされる。
- コマンドパレット
    - 汎用的な命令をストックできるフレーム。
    - addでストックするコマンドを追加し、putで適用する。putを左クリックするとシェル入力欄に反映され、右クリックするとコマンド入力欄に入力される。
    - 編集や追加、削除した場合はsaveでshlistに反映させること。
    - 本ページの起動時にエラー表示がでることがあるが、それはデフォルトのshlistが存在しないことによる。
    - save,load,delは誤操作防止のためダブルクリックで有効。

### "$-"の置き換えルール

$-は複数ファイルを一気に実行する用途の引数である。

    $-=aa.txt,bb.sh,cc/dd

の3ファイルだったときを例にして説明する。

1. 1行ずつの置き換え

以下の、

    cp $- foo/bar_$-

は、

    cp aa.txt foo/bar_aa.txt
    cp bb.sh foo/bar_bb.sh
    cp cc/dd foo/bar_cc/dd

と置き換えられる。

2. ブロックごとの置き換え

以下の

    echo ${$- $-$} to${ $- $-$}

は、

    echo aa.txt aa.txtbb.sh bb.shcc/dd cc/dd to aa.txt aa.txt bb.sh bb.sh cc/dd cc/dd

と、${から$}までの間に存在する$-を同じファイルで置き換えてループ記述する。ループの境目で自動的なスペースは入らないので、前半のようにするとファイル名が繋がってしまうことは注意する。

${と$}の間は改行も入ってよいので、

    ${
    echo $-
    echo $-
    $}

と記載すると、

    echo aa.txt
    echo aa.txt
    
    echo bb.sh
    echo bb.sh
    
    echo cc/dd
    echo cc/dd

というコマンドに置き換わる。
echoの間に空行が出来るのは、${直後と$}直前に改行が含まれることによる。

3. ブロックのネスト非対応

ブロックのネストや多重処理は非対応です。たとえば以下のようなことはできません(v0.0.2)。

    echo${ $-$} > $-
    echo${ ${ $-$}$}

## 更新履歴

***
0.0.2 初版コミット

不安定性といくつかバグあり。かなりやっつけでコーディングしたため、サーバー側のpythonコード、ページのjavascriptともに結構ひどいことになってる。コメントはほぼ皆無。リファクタリング必須。

***

## おわりに

　このアプリはすべてAndroid端末で作成およびテストしたものです。pc環境での動作確認は十分ではないので、ご了承ください。<br>
　Androidからpcへのssh接続はConnectBotがおすすめ。curlでの接続確認にはTermuxがおすすめです。pythonはpydroid 3を使用（有料）。htmlはコードエディタを適当に。

　本アプリの使用は自己責任でおねがいします。使用したことにより発生したいかなる損害について一切責任を負いません。