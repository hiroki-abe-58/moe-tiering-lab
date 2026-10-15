# moe-tiering-lab

RTX 5090（VRAM 32GB）+ RAM 64GB の Windows PC で、約300BパラメータのMoEモデル（[Project Maya](https://github.com/mw00/project-maya) 経由の
GLM-5.3-Flash）を動かしたときの、測定・ツール・**否定的な結果**の記録です。エキスパートは VRAM / ピン留めRAM / SSD の階層に置かれます。

[English README (正本)](README.md)

これは fork ではなく、エンジンのコードは含みません。他者のエンジンを誠実に測るために作った道具と、その測定結果です。

## 分かったこと（1台のPC・1モデル。詳細と注意点は [docs/findings.md](docs/findings.md)）

| 問い | 結果 |
|---|---|
| decode の1トークンの時間はどこに使われるか | 既定の RAM tier 26GB では、decode 壁時間の**約54%**がエンジンの service thread の SSD 読み出し待ち（19.5回/トークン × 2.07ms。1回の待ち＝ミスのあった1層の route。定義は [findings §1](docs/findings.md)）。既定で decode 11.3〜11.7 tok/s、8K prefill 約1050 tok/s。 |
| Core Ultra 9 285K で CPU lane の P/E コア配置は効くか | **効かない。** 5条件×交互3回: +1.8%（スレッド数を減らしただけ）〜 −7.1%（Pコアのみ）。PRは作成していません。 |
| 何が効くか | **RAM tier のサイズ。** 実測: 10 / 18 / 26 GB → 6.9 / 8.8 / 11.2 tok/s。ページファイルを 48 GiB に増やしたあと、26 / 32 / 38 / 42 GB → **11.7 / 13.8 / 16.7 / 18.8 tok/s（+61%）**（各条件 n=3、ばらつき約1%以内）。この PC では commit limit（RAM＋ページファイル）が tier の上限でした（以前は約21〜26GB）。42GB 超は未試験（空きRAMが10GBまで減ったため）。 |
| tier が違うと生成トークンも変わるか | **既定の CPU lane では変わる**（貪欲デコードで tier 26 と 42 が分岐）。**`STRATA_GLM_CPU_LANE=0` なら変わらない**（ビット一致。MTP を強制有効にしても同じ）。1つの expert でも CPU 経路と GPU 経路は量子化レベルで差があり（倍精度参照に対する L2 誤差 2.9% 対 1.6%、1 expert での測定）、lane がどの expert を担当するかで文面が変わります。lane を切ると decode は 4〜10% 遅くなります。42課題の品質テスト: lane 切り 39/42、lane 入り 40/42（差は検出されず、この規模では検出もできません）。[詳細](results/phase3/exp5-determinism/SUMMARY.md)（英語）。 |
| 「WDDMはピン留めRAMを約70%に制限する」は成り立つか（[Maya #185](https://github.com/mw00/project-maya/issues/185)） | **どちらとも証明されていません。** 示せたのは「RTX 5090・VBS/HVCI有効で 44.5GB（RAMの70.2%）を拒否なしでピン留めできた」ことだけです。空きRAMが尽きて停止したため、44.5GB超の上限は存在も不在も確認できていません。ピン留めメモリは commit limit に 1:1 で課金されます。 |

未検証（findings 参照）: 分岐点でのロジット差、42GB超のtier、64K以上のコンテキスト、Linux、AMD、他のCPU。

## 内容

| | |
|---|---|
| [`scripts/maya_ab.py`](scripts/maya_ab.py) | Maya の `--bench` を包む、交互・順序反転のA/Bドライバ。中央値・範囲・%・「ノイズ超過」を出力し、RAM tier が実行間で変わると警告。設定ファイルは書き換えません |
| [`src/moelab/`](src/moelab) | `maya-bench.txt` と `glm stat:` 行のパーサ、統計、CPUコアクラスとアフィニティ（Windows） |
| [`tools/pin_probe/`](tools/pin_probe) | プロセスがピン留めできるホストメモリ量を、RAM・commit の数値と並べて測るCUDAプログラム |
| [`scripts/audit_windows.ps1`](scripts/audit_windows.ps1) | 読み取り専用のPC監査（ユーザー名・パスは置換。遅いStorageコマンドレットは不使用） |
| [`results/`](results) | 2つのスイープの生データと表、PC監査、Strata公式ベンチの報告 |
| [`docs/`](docs) | [methodology](docs/methodology.md)、[architecture](docs/architecture.md)、[findings](docs/findings.md)、[reproduction](docs/reproduction.md)（英語） |

テストはGPUもモデルも不要: `python -I -m unittest discover -s tests`（Python 3.10+、標準ライブラリのみ）。CIはLinuxとWindowsで実行します。

## 再現

コミットハッシュ、モデル、コマンドは [docs/reproduction.md](docs/reproduction.md)。概要:

```powershell
python scripts\maya_ab.py --maya-dir C:\path\to\project-maya --config maya-maya-s-v2-iq2_xxs.json `
    --common STRATA_GLM_RAM_GB=26 --cond base --cond lane8:STRATA_GLM_CPU_LANE=8 --rounds 3 --out results\my-run.json
```

## 制限

1台のPC、1モデル（`Maya-S-v2-IQ2_XXS`）、32Kコンテキスト、Maya v1.1.11のみ。各条件 n=3 で、「ノイズ超過」は保守的な目安であり有意性検定ではありません。
`results/` の Strata ベンチは別モデルであり、Strata対Mayaの比較にはなりません。モデルの重みは配布しません。

## 上流

- Project Maya: https://github.com/mw00/project-maya（MIT）— 測定対象のエンジン
- Strata: https://github.com/Niko1221/Strata（MIT）— Mayaの GLM コードの土台。Strata自体の対象は Qwen3.8-Flash-Next
- 議論: Maya [#185](https://github.com/mw00/project-maya/issues/185)（ピン留め。[`pin_probe` の実測を載せたコメント](https://github.com/mw00/project-maya/issues/185#issuecomment-6191964007)）、[#65](https://github.com/mw00/project-maya/issues/65) / [#67](https://github.com/mw00/project-maya/issues/67)（WindowsのSSD読み込み、v1.0.30で修正済み）、
  Strata [#2067](https://github.com/Niko1221/Strata/issues/2067)（GLM要望。確認時点でメンテナの回答なし）
- 確認した他の派生: [PolyStrata](https://github.com/VecSzn/PolyStrata)、[lighttransport/Strata](https://github.com/lighttransport/Strata)（いずれもMIT）

## クレジットとライセンス

エンジンの成果はすべて Strata と Project Maya の作者に帰属し、本リポジトリはそれを測定するだけです。MIT（[LICENSE](LICENSE)）。
本リポジトリの一部は AI コーディングアシスタント（Claude Code）で作成し、作者が確認・実行しています。
