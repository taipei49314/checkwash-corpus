# checkwash-corpus 總結報告

日期：2026-09-01  
本 repo：https://github.com/taipei49314/checkwash-corpus

這一筆入帳把兩件已完成、且**不可混波**的紀錄寫進 ledger：

1. **Field-run `external-2026-09-01`**（複製，不是重掃）：13 庫、2300 analysed、74 blocked、engine_errors 0。引擎 pin 是 v0.1.49 `greenwash.pyz`（sha256 `ac6a6ea0…`）。裁決 67 false_positive / 7 spec_correct / 0 unclear；0/74 是 verification-layer tampering。這不是 v0.2.8 的數字。v0.2.2 修了這批最大 phantom 家族；2300 視窗還沒用 0.2.8 重掃。
2. **Wave 0 發表 pin** 改釘 Release `checkwash.pyz` v0.2.8（sha256 `83878db5…`）：attrs 2, click 13, flask 7, httpx 12, rich 6, starlette 2 = **42/1800**，blocked set 與 0.1.46 發表視窗 case-for-case 相同。typer / boto3 仍是 v0.2.1 pyz，未動。

74/2300 不進 `records/sweeps/`，也不進 wave0/wave1 headline。rich 已在 wave0；aiohttp/pandas/sqlalchemy 已在 wave1。

---

---

## 1. 這一輪做了什麼、沒做什麼

| 做了 | 沒做 |
|------|------|
| 建獨立 corpus repo（目錄、CLI、CI） | 沒有改 greenwash / SPEC / gating |
| wave 0：6 庫 clone + census + **sweep 1800 commits** | 沒有跑 wave 1 sweep（那是下一輪，要先有 clone） |
| wave 1：20 庫中 **19 庫 clone + census** | `great_expectations` clone 被 Windows 檔案鎖卡住，未普查 |
| GitHub 上 114 個已合併、碰到測試檔的 PR 摘錄 | 沒有把第三方原始碼推進 git |
| fetch 加上網路重試，避開 Windows rename | 沒有當這是 checkwash 判決 |

第三方樹只活在本機 `clones/`。git 裡的證據是 `records/`。

---

## 2. Wave 0 sweep — 複現發表數字

對 `greenwash/benchmarks/sweeps/*.json`（引擎 **0.1.46**）逐庫對帳。視窗 pin（newest / oldest）六庫全部相同。blocked commit 集合沒有多也沒有少。engine error 全 0。

| 庫 | 舊擋 (0.1.46) | 本輪 | block rate | opaque | pin |
|---|---:|---:|---:|---:|---|
| attrs | 2 | 2 | 0.67% | 2 | 相同 |
| click | 13 | 13 | 4.33% | 0 | 相同 |
| flask | 7 | 7 | 2.33% | 8 | 相同 |
| httpx | 12 | 12 | 4.00% | 5 | 相同 |
| rich | 6 | 6 | 2.00% | 1 | 相同 |
| starlette | 2 | 2 | 0.67% | 8 | 相同 |
| **合計** | **42 / 1800** | **42 / 1800** | **2.33%** | | |

紀錄：`records/sweeps/{attrs,click,flask,httpx,rich,starlette}.json`。

### 引擎版本字串在六次呼叫之間漂了

CLI 開跑時印的是 `checkwash 0.1.49`。各 sweep 檔自己記下的 `corpus.checkwash_version`：

| 庫（執行順序） | 記下的版本 |
|---|---|
| attrs、click | 0.1.49 |
| flask、httpx | 0.2.0 |
| rich、starlette | 0.2.1 |

原因：CLI 是 editable install，指向正在改名的 `feat/checkwash-identity-v0.2.0` 工作樹。**判決集合仍然與 0.1.46 發表視窗一致**；版本字串不能當成凍結 pin。下一輪 sweep 應改用 GitHub Release 的 **`checkwash.pyz`**（最新資產名；`greenwash.pyz` 只存在於 ≤v0.1.49 的舊 release），不要再吃這棵髒工作樹。

---

## 3. 功率普查 — 為什麼 wave 0 量不到某些規則

Census 掃的是 clone 裡所有可讀的 `.py`（跳過 `node_modules` / `__pycache__` / 大於 1MB 的檔）。probe 凍結在 `catalog/CATALOG.json`。

### Wave 0（發表用的六庫，在發表 pin 上）

| 庫 | patch sites | unittest `self.assert*` | approx | skip | `.py` 檔 |
|---|---:|---:|---:|---:|---:|
| attrs | 3 | 0 | 0 | 12 | 54 |
| click | 76 | 0 | 0 | 23 | 78 |
| flask | 37 | 0 | 0 | 2 | 83 |
| httpx | 8 | 0 | 0 | 1 | 60 |
| rich | 41 | 0 | 0 | 39 | 213 |
| starlette | 12 | 0 | 0 | 5 | 67 |
| **合計** | **177** | **0** | **0** | **82** | **555** |

這就是 THREATMODEL 90 / 86b 的測量，不是推測：

- `TEST_PATCHES_SUBJECT` 在 1800 commit 上 fire 0 次，因為這六個庫幾乎不 stub。
- `EXPECTED_VALUE_DERIVED` 的 unittest 路徑是死的，因為這六個庫 **0 條** `self.assert*`。

### Wave 1（19/20 庫，depth 400 的 HEAD）

| 庫 | patch sites | unittest | 2026-08-13 舊 census（patch） | 這一庫補的功率 |
|---|---:|---:|---:|---|
| airflow | 16,282 | 0 | 15,784 | mock |
| mlflow | 6,316 | 0 | 6,060 | mock |
| salt | 3,079 | **4,912** | 2,741 | mock + **unittest** |
| azure-cli | 1,503 | **11,276** | 372 | **unittest**（舊 census 明顯低估） |
| ray | 1,688 | 3,177 | 1,174 | 兩者 |
| django | 687 | **40,314** | 649 | **unittest 主場** |
| transformers | 301 | **24,127** | 310 | **unittest 主場** |
| moto | 692 | 14 | 481 | mock |
| sentry-python | 848 | 0 | 830 | mock |
| poetry | 437 | 0 | 469 | mock |
| aiohttp | 460 | 1 | 457 | mock |
| bokeh | 359 | 228 | 169 | 兩者 |
| pytest | 288 | 11 | 271 | collection 面 |
| localstack | 322 | 40 | 272 | mock；runner_files=52 |
| scrapy | 152 | 156 | 167 | 兩者 |
| pandas | 126 | 0 | 109 | 低 mock |
| sqlalchemy | 160 | 24 | 152 | 低 |
| typer | 112 | 0 | 104 | 小、便宜 sweep |
| boto3 | 76 | 74 | 75 | 低 |
| great_expectations | — | — | 374 | **clone 失敗，見 §5** |
| **合計（19 庫）** | **33,888** | **84,354** | | |

對照：

- patch：wave 0 = **177**，wave 1 = **33,888**（約 191×）。
- unittest：wave 0 = **0**，wave 1 = **84,354**。主場是 django、transformers、azure-cli、salt。

`azure-cli` 的舊 expansion 數字是 372 patch sites，本輪全樹掃到 1,503。兩個都留下：舊的是 2026-08-13 的一次計數，本輪是 depth-400 HEAD 的全 `.py` 掃描，probe 相同、範圍可能更寬。

---

## 4. 真實 PR 摘錄

`python -m corpus harvest-prs` 走 GitHub API，**不需要 clone**。只存測試檔 patch，有上限，身份是 `(owner_repo, pr_number, head_sha)`。這不是 checkwash 判決。

- 114 筆（wave 0 每庫最多 15 個合併 PR、wave 1 每庫最多 8 個）
- sqlalchemy / typer / boto3 最近 8 個合併 PR 沒碰到測試路徑，所以是 0 — 如實記錄，沒有硬塞
- great_expectations 有 5 筆 PR 摘錄（API 成功），clone 失敗不影響這批摘錄

---

## 5. 失敗，如實寫

1. **第一次 wave 1 fetch**：ray 連線被重設，隨後一批 `Could not resolve host: github.com`，typer 在 Windows 上 `tmp.rename(dest)` 權限錯誤，整個 fetch 以未捕捉的 `PermissionError` 炸掉。
2. **重試**：15 個缺的來源裡 14 個一次成功（含 ray、transformers、django、azure-cli）。`great_expectations` 留下半成品 `.git/objects`，Windows 鎖住目錄，rename / rmdir / 工具內 `_rmtree` 都拿不掉。**19/20 clone，不宣稱 20/20。**
3. **fetch 已改**：clone 改成直接寫入 `dest`（不再 rename）、網路錯誤重試 3 次、`OSError` 當成來源失敗而不是整個行程崩潰。`clones/great_expectations` 那把 Windows 鎖仍在：重開機後刪最省事；`Remove-Item -Force -Recurse` 若仍失敗，用 `handle.exe` 查佔用再刪。
4. **沒有 wave 1 sweep**。有 clone 還不夠；sweep 300 commit × 19 庫會是自己的一輪，而且 django / transformers 的 unittest 密度會讓引擎第一次真正碰到 86b。
5. **版本字串不可當作 pin**（§2）。

---

## 6. 這對 checkwash 意味著什麼

- **精度（wave 0）**：在這 1800 個人類 commit 上，0.1.46 → 本輪引擎沒有判決漂移。這是複現，不是新的精度宣稱。
- **召回的盲區是 corpus 的，不是「規則不存在」**：
  - 要量 `TEST_PATCHES_SUBJECT`，下一輪 sweep 應包含 airflow / mlflow / salt，而不是再掃 flask。
  - 要量 unittest 方言（86b），下一輪應包含 **django、transformers、azure-cli、salt**。
  - pytest 自己的 `testing/` 適合 collection-control 面。
- **localstack 的 runner_files=52**：wave 0 幾乎沒有 runner script 功率；這是 CI 弱化規則該去的地方。
- **不要把 1.50% FP 套到 wave 1**。greenwash 自己寫過：corpus 看不見的規則，零 FP 不是測量。

---

## 7. 建議的下一輪（仍不動 greenwash 源碼）

1. 清掉 `clones/great_expectations` 後 `python -m corpus fetch --id great_expectations`。重開機再刪最省事；`Remove-Item -Force -Recurse` 失敗時用 `handle.exe` 查誰佔著 `.git`。
2. Sweep 用 **最新 Release 的 `checkwash.pyz`**，不要再用 editable 髒樹，也不要下載舊名 `greenwash.pyz`（那只在 ≤v0.1.49）：
   `python -m corpus sweep --id django --engine checkwash.pyz`
3. 第一個有功率的 sweep 建議順序（小 → 貴）：
   1. `typer` / `boto3`（煙霧）
   2. `pytest`（collection）
   3. `salt` 或 `django`（unittest）
   4. `airflow`（mock，最大）
4. 每個新 sweep 單獨 adjudication，禁止跟 wave 0 的 42 筆混成一個 headline。`adjudication/TEMPLATE.json` 已經是鷹架：`(catalog_id, commit)` 必須與 sweep 的 `blocked_commits` 對齊、逐案對真實 diff 寫 `false_positive` / `spec_correct` / `unclear`，跟本輪 wave 0 對帳用的裁決法同一套。wave 1 sweep 落地時直接沿用，不必另起格式。

---

## 8. 檔案索引

| 路徑 | 內容 |
|------|------|
| `catalog/CATALOG.json` | 29 個來源、3 個 wave、凍結 probe |
| `records/sweeps/*.json` | wave 0 六份，本輪引擎重跑 |
| `records/census/*.json` | wave 0 六份 + wave 1 十九份 |
| `records/prs/` | 114 個真實 PR 測試檔摘錄 |
| `adjudication/TEMPLATE.json` | 逐案裁決鷹架；wave 1 sweep 沿用 |
| `SPEC.md` | 什麼算測量 |
| `clones/` | 本機快取，不進 git |

`python -m corpus status -v` 是現況的機器來源；本報告的數字全部從 `records/` 讀出，沒有手填。
