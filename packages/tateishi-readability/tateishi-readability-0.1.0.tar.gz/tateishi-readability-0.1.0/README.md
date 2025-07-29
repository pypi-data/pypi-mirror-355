# 概要
建石らが1988年に提案した線形式モデルの日本語リーダビリティ指標を計算するツールです。  
建石らの指標は、平均が50、標準偏差が10になるよう調整されており、値が高いほど読みやすいとする指標です。値に対する具体的な評価基準は定められていませんが、FREと同じような0〜100程度の評価基準が想定されていると考えられます。  
※論文の内容を基に開発しているため、論文に記載のない部分、誤植と見受けられる部分は適宜補っているため、多少誤差があるかもしれない点はご了承ください。  

# 評価式
```
RS = 0.05*pa+0.25*ph-0.19*pc-0.61*pk-1.34*ls-1.35*la+7.52*lh-22.1*lc-5.3*lk-3.87*cp+109.1

RS' = -0.12*ls-1.37*la+7.4*lh-23.18*lc-5.4*lk-4.67*cp+115.79
```
  
pa:アルファベット連の連全体に対する頻度（％）  
ph:ひらがな連の連全体に対する頻度（％）  
pc:漢字連の連全体に対する頻度（％）  
pk:カタカナ連の連全体に対する頻度（％）  
ls:文の平均長さ（文字）  
la:アルファベット連の平均長さ（文字）  
lh:ひらがな連の平均長さ（文字）  
lc:漢字連の平均長さ（文字）  
lk:カタカナ連の平均長さ（文字）  
cp:句点あたり読点の数  

# セットアップ
```
pip install tateishi-readability
```

# 使い方
```
>>> from tateishi_readability import *
>>> tateishi_readability("今日の天気は、晴れです。")
78.72666666666666
>>> tateishi_readability2("今日の天気は、晴れです。")
84.62
```

# ライセンス
- divide-char-type
	- Python Software Foundation License
	- Copyright (C) 2023- Shinya Akagi
- tateishi-readability
	- Python Software Foundation License
	- Copyright (C) 2025- Shinya Akagi

# 論文
- 建石由佳,小野芳彦,山田尚勇：日本文の読みやすさの評価式
	- 情報処理学会研究報告ヒューマンコンピュータインタラクション（HCI）,Vol.25,pp.1-8,1988
	- https://ipsj.ixsq.nii.ac.jp/records/37773

