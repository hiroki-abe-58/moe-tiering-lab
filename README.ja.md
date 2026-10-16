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
| SSD 待ちはリーダー調整で縮むか | **この PC では縮みません。** 待ちの間、ドライブはどの tier でも約 6 GB/s を出しており（帯域律速）、1トークンの残りは約 36 ms のままです。スクリーニング（ほぼ2ラウンド）: CPU lane と SSD 読みの重ね合わせ +0.7%、リーダースレッド 0%、チャンク4分割 +2.1%、昇格系ノブ 0%。CPU/PCIe 分担の変更は +7.3%（Maya の較正ツールは +8.8%、1サンプル）でしたが、私の基準が未較正だったため、バグではなく環境ごとの調整項目です。上流への提案はしていません。[Exp6](results/phase3/exp6-io/SUMMARY.md)、[Exp7](results/phase3/exp7-opt/SUMMARY.md)（英語）。 |

| 同じ設定で起動し直すとなぜトークンが変わるか、直せるか（[Phase 4](results/phase4/SUMMARY.md)、英語） | **競合ではなく expert の置き場所の違いです。** VRAM の expert プールは起動時の空き VRAM で決まり（5回の起動で warm された expert が 9,453〜9,488 個）、lane の分担は僅差のタイミング計測で決まり、デコード中にも再計測とバックグラウンド移動があります。置き場所が同じなら lane 有効でもビット一致（1762/1762 位置）。プールサイズ・分担・バックグラウンド移動を固定すると、5回の起動で 70/70 組が一致（30分アイドル後も、空き VRAM が 300 MiB 少なくても）、速度は同じ（18.31 対 18.26 tok/s）。既定は 17/70。上流には文書セクションとして提案しました（[mw00/project-maya#224](https://github.com/mw00/project-maya/pull/224)）。 |
| CPU lane の演算をより厳密にすればトークンは GPU と揃うか | **揃いません。** lane の活性量子化をデバイスと同じ（32要素ブロック）にすると、倍精度参照に対する誤差は 1.73% → 1.09%、GPU の expert との差は 1.94% → 0.06%（デバイスの整数手順まで合わせると 9.8e-8）、デコード −0.5%／−3.6%。しかしルータの top-8 は 1e-6 超の差を数トークンで 25〜60% の層の別 expert 集合に増幅するため、lane 無効の実行からの分岐は全方式で 11〜17 トークン付近、42課題の品質も変わりません。上流には提案していません（参考ブランチを fork に置きました: [feat/cpu-lane-act-q8_1](https://github.com/hiroki-abe-58/project-maya/tree/feat/cpu-lane-act-q8_1)、単体テスト通過、最新 `main` 上でデコード −2.6%）。 |
| `STRATA_GLM_PCIE_SHARE=0.10` と既定の分担 | **デコード +8.6%**（18.13 → 19.69 tok/s、5ラウンド交互、範囲が重ならない）、prefill は不変。Maya の較正ツールが 0.10 を選んでいたため、エンジン変更は不要です。 |
| 1トークンの残り時間はどこへ行くか（Nsight Systems、46トークン） | 42GB tier で SSD 待ち 17ms、RAM tier expert の PCIe 取得 15ms、dense 計算 8ms、デバイスの空き ~12ms、CPU lane は隠れている（0.5ms）。`PCIE_SHARE=0.10` では取得が 4ms、lane 待ちが 11.7ms。[詳細](results/phase4/exp15-nsys/SUMMARY.md)（英語）。 |
| 「SSD は約 6 GB/s」はドライブの限界か | 実測: バッファなしの 1.1MB ランダム読みで、キュー深さ 9 で 6.55 GB/s（32 で 6.82）、80秒持続で 6.3 GB/s。 |

未検証（findings 参照）: 42GB超のtier、64K以上のコンテキストと長時間の連続運転試験（スクリプトはあるが未実行のため公開していません）、DFlash2／MTP／複数GPU、Linux、AMD、他のCPU。

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
