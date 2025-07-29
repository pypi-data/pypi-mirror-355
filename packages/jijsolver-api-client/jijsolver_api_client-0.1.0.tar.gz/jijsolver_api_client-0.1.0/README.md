# JijSolver API Client

Jij 製の数理最適化ソルバーである JijSolver を 、Web API 経由で実行するための クライアントパッケージです。以下に使用方法を説明します。

## Quick Start

### アクセストークンの取得

JijSolver API を使用するには、事前にアクセストークンを取得する必要があります。無償版の利用申請方法は以下の通りです。

#### 利用申請方法

1. 以下リンク先のフォームから利用申請を行ってください。

   **申請フォーム**: [JijSolverAPI 無償版 利用申請フォーム](https://docs.google.com/forms/d/e/1FAIpQLScLTRxXGaN7egRkoYcq2ZvFoFXRyYInsmPXlyxk9pF11E9--g/viewform)

2. 申請されたメールアドレス宛に、アクセスに必要な情報（API サーバーのホスト名、アクセストークン）が届きます。

### インストール

JijSolver API のクライアントパッケージをインストールします：

```bash
pip install jijsolver-api-client
```

### 環境変数の設定

上記利用申請により入手した、以下の値を環境変数に設定します：

- **`JIJSOLVER_SERVER_HOST`**: API サーバーのホスト名

- **`JIJSOLVER_ACCESS_TOKEN`**: アクセストークン

### 設定例

環境変数の設定例：

```bash
export JIJSOLVER_SERVER_HOST="API サーバーのホスト名"
export JIJSOLVER_ACCESS_TOKEN="アクセストークン"
```

または Python コード内で設定する例：

```python
import os

os.environ["JIJSOLVER_SERVER_HOST"] = "API サーバーのホスト名"
os.environ["JIJSOLVER_ACCESS_TOKEN"] = "アクセストークン"
```

### リクエスト実行例

実行例の中で JijModeling を使用するため、事前にインストールしておきます。

```python
pip install jijmodeling
```

ナップサック問題を解く例：

```python

import os
import logging
import jijsolver
import jijmodeling as jm

logging.basicConfig(level=logging.INFO)

# ナップサック問題を定義
v = jm.Placeholder("v", ndim=1)  # アイテムの価値
w = jm.Placeholder("w", ndim=1)  # アイテムの重さ
W = jm.Placeholder("W")          # ナップサックの容量
N = v.len_at(0, latex="N")       # アイテム数
x = jm.BinaryVar("x", shape=(N,))  # 決定変数
i = jm.Element("i", belong_to=(0, N))

problem = jm.Problem("Knapsack", sense=jm.ProblemSense.MAXIMIZE)
problem += jm.sum(i, v[i] * x[i])  # 目的関数：価値の最大化
problem += jm.Constraint("weight", jm.sum(i, w[i] * x[i]) <= W)  # 重量制約

# インスタンスデータ
instance_data = {
    "v": [10, 13, 18, 31, 7, 15],   # アイテムの価値
    "w": [11, 15, 20, 35, 10, 33],  # アイテムの重さ
    "W": 47,                        # ナップサックの容量
}

# OMMX インスタンスを作成
interpreter = jm.Interpreter(instance_data)
instance = interpreter.eval_problem(problem)

# APIにリクエストを実行
solution = jijsolver.solve(instance, time_limit_sec=2.0)

print(f"Value of the objective function: {solution.objective}")
```

## API リファレンス

JijSolver API を使用して最適化問題を解きます。

**パラメータ:**

- `ommx_instance` (Instance): OMMX インスタンス
- `time_limit_sec` (float): 最大求解時間（秒）

**戻り値:**

- `Solution`: OMMX ソリューション

**例:**

```python
solution = jijsolver.solve(
    ommx_instance=problem_instance,
    time_limit_sec=2.0
)
```
