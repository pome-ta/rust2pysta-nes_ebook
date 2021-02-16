[repo / GitHub](https://github.com/bugzmanov/nes_ebook)


[gh-pages](https://bugzmanov.github.io/nes_ebook/)


# nes_ebook



## 📝 2021/02/12

###`as i8` の対応


数値の型が、変わる



- `u8`
	- 0 ~ 255
- `i8`
	- -128 ~ 127

- `u16`
	- 0 ~ 65535


いまのところ、`u8` のものを受けているので


`-0x100` で、`256`引くことで、数値を「ずらす」ことにしている



### `wrapping_neg()` の対応


なんか[読むに](https://qiita.com/dmkd3006/items/ab39c6fe69edcda44452)、その数値に（正の数）であれば、まるっと`-` を付ける？


``` .py
data = data * (-1) if data < 0 else data

```


正の数の時に`False` として、スルー。`0` も、`False` 判断になりそうなので、こんな形式に






## 📝 2021/02/11


## 📝 2021/02/10

一進一退をしてるので、経過のメモ。


[ch3.1](https://bugzmanov.github.io/nes_ebook/chapter_3_1.html) から[ch3.3](https://bugzmanov.github.io/nes_ebook/chapter_3_3.html) までは、そこそこにすんなりと。


[ch3.4](https://bugzmanov.github.io/nes_ebook/chapter_3_4.html) で見事にハマる（というか、ch3.1 〜.3 までもガバガバだったことが判明）



### 全体整理

実装にあたり

- nes の、CPU （6502）処理の理解
- Rust コードの読み方、書き方
- Python に書き換える技能

現在、全てにおいて欠落をしている。ch3.3 までは、CPU 理解を捨てRust のコードをPython に書き換えることに専念。



### Rust -> Python

`Cargo.lock`と`Cargo.toml は、調べたら負けだと思いシカト

`code/src` の`*.rs` に焦点をあてる。


`main.rs` は、`ハロワ`しか言ってなかった。`cpu.rs` へ。


#### pytest


後半は、ほぼテストぽくて、Pythonista では`pytest` を使うことに。`stash` 起動のプロンプト実行が面倒そうだったので、直接実行できる方法調べたら、あった。



[ここ](https://qiita.com/MENDY/items/1fc5143c1642ab58ec9b) とか、[ここ](https://www.qoosky.io/techs/bdd40188f7) を参考に。



オプションとかまで突っ込んでない


``` .py
pytest.main()
```

#### import

インポート処理がガバガバ。

``` .py
import sys
import pathlib
sys.path.append(str(pathlib.Path.cwd().parent))

from src.cpu import CPU

```


#### `cpu.py`

構造体を定義してるから、`ctypes` とか？と、思ったけどPythonista の`objc_util` 以外で私が理解（便利）だと思うものがなく、適当に`class` で処理


`{` `}` で囲まれた中の関数をインスタンスメソッドとして、`self` もPython の`self` 同等に処理



過去の経験で、引数・変数の型は書いておかないと死にそうなので、私のメモ的に文字列で表記（Rust の型表記）



`loop` は、`while True:`。`return` になってるところで`break` して逃す。


`match` は、`if` の分岐




Rust コード上の邪念（失礼）を排除したら。すんなりといけた



#### Status Register

`IntFlag` をなんか、前に見てて使ってみたくて（演算あるので）


初期状態を作りたくて、`NULL = 0` を定義。なるほど、中身は整数の演算なのね、と理解した雰囲気をだした


#### AddressingMode


`IntFlag` をいろいろ調べていたら、`NamedTuple` なるものをみつけたので、使ってる


`opcodes.py` の`Map` をするために、作ってるのだけど、こいつのせいで、


``` .py
AddressingMode = _AddressingMode()
import opcodes

```


が、中途半端な位置に。。。


一応、見本のRust コードとなるべく揃えたくて変な感じに（Pythonista 以外の能力が高いPycharm とかで、コードフォーマットすると、import の位置が、先頭に行くのでエラーを吐く）


### Rust のコード


playgroundやら、サーバー上で実行できるアプリなどで、変化をみたりして確認ひてる（地獄）



`hoge.wrapping_add(n)` が、数値の型でオーバーフローしたときにどうするのか？的なやつ


`add` やら`sub` やらある。


Python では、`if` で処理するか、指定型最大値を`&` （論理積）するか、検討中


#### bitflags

外部からインポートするみたいで、使われてる処理を[コード](https://docs.rs/bitflags/1.2.1/bitflags/) を参照しつつPython に書き落としてる


#### lazy_static

よーわからんけど、いまのところ問題ないからヨシ！


### ch3.3 のテストコード


テスト値が、cpu のリセット処理前に入れられてしまってるので通らないものがあり

ちょっともやる




### Rust 体験


ch3.4 から、地獄を見てて（ch3.3 は、テスト通らんし）


Pc にRust を入れて挙動確認。しようとしたけど、コンパイルでエラー吐いて実行できず。



そもそも、色々理解してないので、一回パスしてる










## 📝 2021/01/25

### CPU

CPUがアクセスできるリソースは、メモリマップとCPUレジスタの2つだけです。

プログラミングの観点からは、メモリマップは1バイトセルの連続配列にすぎません。  NES CPUは、メモリアドレス指定に16ビットを使用します。これは、65536(0x10000)の異なるメモリセルをアドレス指定できることを意味します。


- Program Counter (PC)
	- 次に実行される機械語命令のアドレスを保持します。
- Stack Pointer (SP)
	- メモリスペース[0x0100..0x1FF]はスタックに使用されます。 スタックポインタは、そのスペースの先頭のアドレスを保持します。  NESスタック（すべてのスタックとして）は上から下に大きくなります。バイトがスタックにプッシュされると、SPレジスタがデクリメントします。 バイトがスタックから取得されると、SPレジスタがインクリメントします。
- Accumulator (A)
	- 算術演算、論理演算、およびメモリアクセス演算の結果を格納します。 一部の操作の入力パラメーターとして使用されます。
- Index Register X (X)
	- 特定のメモリアドレッシングモードでオフセットとして使用されます（これについては後で詳しく説明します）。 補助記憶装置のニーズに使用できます（温度値の保持、カウンターとしての使用など）。
- Index Register Y (Y)
	- レジスタXと同様の使用例。
- Processor status (P)
	- 8ビットレジスタは、最後に実行された命令の結果に応じて設定または設定解除できる7つのステータスフラグを表します（たとえば、操作の結果が0の場合はZフラグが設定（1）され、未設定/消去（0）されます） そうでなければ）


### Rust のこと

fn 内で`;` が無ければ、return

mutを付けることでその関数内で変数の変更が可能になるということです


### その他

nes cpu は、リトルエンディアン
